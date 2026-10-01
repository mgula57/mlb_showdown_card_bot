from pprint import pprint
from typing import List, Dict, Optional, Tuple
import statistics
import os
import csv
import json

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from math import ceil
from psycopg2 import sql

# Table
from prettytable import PrettyTable

# SHOWDOWN BOT
from ..database.postgres_db import PostgresDB, ExploreDataRecord, ExploreDataRecord, ImageMatchType
from ..shared.player_position import Position
from ..card.showdown_player_card import ShowdownPlayerCard, Expansion, Edition, ImageParallel, StatHighlightsType, SpecialEdition
from ..card.card_generation import generate_card
from ..card.stats.stats_period import TeamSelection
from ..card.utils.shared_functions import convert_year_string_to_list
from .selection import (
    PLAYER_SUBTYPES, PositionTarget, SelectionWeights, ShowdownBotSetPlayer, SlotGroup, SlotPosition, WeightedPlayerSelector
)

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def color_image_match(image_match_type: ImageMatchType) -> str:
    """Color code the image match type for terminal output"""
    if image_match_type == ImageMatchType.EXACT:
        return f"{Colors.GREEN}{image_match_type.value}{Colors.END}"
    elif image_match_type == ImageMatchType.TEAM_MATCH:
        return f"{Colors.YELLOW}{image_match_type.value}{Colors.END}"
    else:  # NO_MATCH or YEAR_MATCH
        return f"{Colors.RED}{image_match_type.value}{Colors.END}"

class PlayerTypeDistribution(BaseModel):
    """Distribution of player types in the set"""
    hitters_percentage: float = Field(0.65, ge=0, le=1, description="Percentage of hitters in set")
    starters_percentage: float = Field(0.20, ge=0, le=1, description="Percentage of starting pitchers in set") 
    relievers_percentage: float = Field(0.15, ge=0, le=1, description="Percentage of relief pitchers in set")
    
    def validate_total(self):
        """Ensure percentages add up to 1.0"""
        total = self.hitters_percentage + self.starters_percentage + self.relievers_percentage
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Player type percentages must sum to 1.0, got {total}")
        return self
    
class PointBucket(BaseModel):
    """A point range (inclusive) and the share of each player type's cards that should fall in it"""
    min_points: int = Field(10, ge=0, description="Lowest point value in the bucket (inclusive)")
    max_points: int = Field(..., ge=0, description="Highest point value in the bucket (inclusive)")
    percentage: float = Field(..., ge=0, le=1, description="Ideal share of each player type's cards in this bucket")

    @model_validator(mode='after')
    def validate_range(self) -> 'PointBucket':
        if self.min_points > self.max_points:
            raise ValueError(f"Point bucket min ({self.min_points}) must be <= max ({self.max_points})")
        return self

    @property
    def label(self) -> str:
        return f"{self.min_points}-{self.max_points} pts"

    def contains(self, player: ExploreDataRecord) -> bool:
        """Whether a player's card points fall within this bucket"""
        return player.points is not None and self.min_points <= player.points <= self.max_points

    @classmethod
    def validate_list(cls, buckets: List['PointBucket']) -> List['PointBucket']:
        """Buckets can't overlap (a card could satisfy two targets) and can't ask for more than 100% of a type"""
        ordered = sorted(buckets, key=lambda b: b.min_points)
        for previous, current in zip(ordered, ordered[1:]):
            if current.min_points <= previous.max_points:
                raise ValueError(f"Point buckets {previous.label} and {current.label} overlap")
        total = sum(b.percentage for b in buckets)
        if total > 1.0 + 1e-9:
            raise ValueError(f"Point bucket percentages must total 100% or less, got {total:.0%}")
        return buckets

    @classmethod
    def parse_cli(cls, value: str) -> List['PointBucket']:
        """Parse a CLI string like '10-50:0.15,60-100:0.10' into buckets"""
        buckets = []
        for chunk in value.split(','):
            point_range, percentage = chunk.strip().split(':')
            min_points, max_points = point_range.split('-')
            buckets.append(cls(min_points=int(min_points), max_points=int(max_points), percentage=float(percentage)))
        return buckets


class ShowdownBotSet(BaseModel):
    """Builds optimal MLB Showdown card sets based on real player stats"""
    
    set_size: int = Field(ge=1, le=1000, description="Total number of cards in the set")
    years: List[int] = Field(..., description="List of years to consider for player stats")
    showdown_sets: List[str] = Field(..., description="Showdown sets to consider for player selection")

    # Minimum requirements
    min_games_hitters: int = Field(60, description="Minimum games for hitters")
    min_ip_starters: int = Field(75, description="Minimum IP for starting pitchers") 
    min_ip_relievers: int = Field(30, description="Minimum IP for relief pitchers")

    # Player type distribution
    player_type_distribution: PlayerTypeDistribution = Field(default_factory=PlayerTypeDistribution)

    # War thresholds
    elite_war_threshold: float = Field(4.0, description="Minimum WAR for elite players")
    good_war_threshold: float = Field(2.0, description="Minimum WAR for good players")
    
    # Special inclusions
    include_all_stars: bool = Field(True, description="Include All-Star players")
    include_award_winners: bool = Field(True, description="Include Award-winning players")
    all_stars_only: bool = Field(False, description="Restrict the qualified player pool to players who received an All-Star selection that year")

    # Construction results
    final_players: Optional[List[ShowdownBotSetPlayer]] = Field(None, description="Final list of players selected for the set")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings surfaced during set construction (e.g. undersized player pool)")
    
    # Selection weights and position composition
    selection_weights: SelectionWeights = Field(default_factory=SelectionWeights)
    position_targets: List[PositionTarget] = Field(
        default_factory=list,
        description="Share of the set (and average points) per position, e.g. from a WOTC base set. Replaces player_type_distribution when set."
    )

    # Point bucket allocation (e.g. 15% of 10-50 pt cards, 10% of 60-100 pt cards)
    point_buckets: List[PointBucket] = Field(
        default_factory=list,
        description="Point ranges with an ideal share of each player type's cards (empty to skip)"
    )

    # Specific player IDs to include
    manually_included_ids: Optional[List[str]] = Field(
        None,
        description="Specific player IDs to always include in the set"
    )
    manually_excluded_ids: Optional[List[str]] = Field(
        None,
        description="Specific player IDs to always exclude from the set"
    )
    year_overrides: Optional[Dict[str, str]] = Field(
        None,
        description="Per-player year overrides keyed by bref_id (w/ type override). Cards for these players are generated live instead of pulled from dim_card. Ex: {'verlaju01': '2025-2026'}"
    )
    team_selection: TeamSelection = Field(
        TeamSelection.GAMES_PLAYED,
        description="For year-override cards, how to choose the card's team (GAMES_PLAYED, LAST_TEAM, FIRST_TEAM)"
    )
    csv_file_path: Optional[str] = Field(
        None,
        description="Path to CSV file with bref_id and year columns to load players from"
    )
    expansion_cards: Optional[List[ShowdownPlayerCard]] = Field(
        None,
        description="List of expansion cards loaded from CSV and database"
    )

    def _load_expansion_players_from_csv(self) -> List[Dict]:
        """Load expansion players from CSV file in core/set_builder folder.
        
        CSV MUST have columns: bref_id, year
        Additional columns (edition, etc.) are preserved and applied to cards.
        
        These are players from OTHER years to add as expansions.
        Returns list of dicts with all CSV columns.
        """
        if not self.csv_file_path:
            return []
        
        # Get the core/set_builder folder path
        this_folder = os.path.dirname(os.path.abspath(__file__))
        csv_full_path = os.path.join(this_folder, self.csv_file_path)
        
        if not os.path.exists(csv_full_path):
            print(f"Warning: CSV file not found at {csv_full_path}")
            return []
        
        expansion_players = []
        try:
            with open(csv_full_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                if reader.fieldnames is None or 'bref_id' not in reader.fieldnames or 'year' not in reader.fieldnames:
                    print(f"Warning: CSV must have 'bref_id' and 'year' columns. Found columns: {reader.fieldnames}")
                    return []
                
                for row in reader:
                    bref_id = row.get('bref_id', '').strip()
                    year_str = row.get('year', '').strip()
                    
                    if bref_id and year_str:
                        try:
                            year = int(year_str)
                            # Store all row data for later use
                            player_data = {
                                'bref_id': bref_id,
                                'year': str(year),
                                'player_id': f"{year}-{bref_id}",  # Create a player_id for DB lookup
                                # Include all other columns from CSV
                                **{k: v.strip() if isinstance(v, str) else v for k, v in row.items() if k not in ['bref_id', 'year']}
                            }
                            expansion_players.append(player_data)
                        except ValueError:
                            print(f"Warning: Could not parse year '{year_str}' for player {bref_id}")
            
            print(f"Loaded {len(expansion_players)} expansion player(s) from {self.csv_file_path}")
            if expansion_players and len(expansion_players[0]) > 3:
                extra_cols = [k for k in expansion_players[0].keys() if k not in ['bref_id', 'year', 'player_id']]
                print(f"  Additional columns found: {', '.join(extra_cols)}")
        except Exception as e:
            print(f"Error reading CSV file {csv_full_path}: {e}")
        
        return expansion_players

    def _load_expansion_cards_from_db(self, expansion_players: List[Dict], source_env: str = 'dev') -> List[ShowdownPlayerCard]:
        """Query database for expansion player cards and apply CSV attributes.
        
        Args:
            expansion_players: List of dicts with 'bref_id' and 'year' keys, plus optional attributes
            
        Returns:
            List of ShowdownPlayerCard objects with CSV attributes applied
        """
        if not expansion_players:
            return []
        
        db = PostgresDB(is_archive=(source_env == 'prod'))
        expansion_cards: List[ShowdownPlayerCard] = []
        
        player_ids = [player['player_id'] for player in expansion_players]
        filter_values = tuple(player_ids)
        try:
            query = sql.SQL("""
                SELECT
                    player_id,
                    showdown_set,
                    card_data
                FROM internal.dim_card
                WHERE player_id IN %s and showdown_set IN %s
            """)
            raw_cards = db.execute_query(query=query, filter_values=(filter_values, tuple(self.showdown_sets)))
            
            # Create a lookup map from player_id to CSV row data
            csv_data_lookup = {player['player_id']: player for player in expansion_players}
            
            for row in raw_cards:
                card_data = row.get('card_data') or {}
                player_id = row.get('player_id')
                
                # Merge CSV attributes into card_data, giving precedence to CSV values
                card = ShowdownPlayerCard(**card_data)
                csv_attributes = csv_data_lookup.get(player_id, {})
                for attr, value in csv_attributes.items():
                    match attr:
                        case "edition":
                            try:
                                value = Edition(value)
                            except ValueError:
                                print(f"Warning: Invalid edition '{value}' for player_id {player_id}")
                        case "parallel":
                            try:
                                value = ImageParallel(value)
                            except ValueError:
                                print(f"Warning: Invalid parallel '{value}' for player_id {player_id}")
                        case _:
                            pass  # Keep as string or original type
                    if hasattr(card, attr):
                        setattr(card, attr, value)
                    elif hasattr(card.image, attr):
                        setattr(card.image, attr, value)
                expansion_cards.append(card)
        except Exception as e:
            print(f"Error querying database for expansion players: {e}")

        # SORT BY EDITION (IF IT EXISTS), THEN BY YEAR THEN BY BREF ID
        expansion_cards.sort(key=lambda c: (
            c.image.edition.value if c.image and c.image.edition else 'ZZZ',  # Sort by edition if it exists, otherwise put at end
            c.image.set_year if c.image and c.image.set_year else 9999,  # Then sort by year if it exists
            c.bref_id or ''  # Finally sort by bref_id
        ))

        return expansion_cards

    @field_validator('point_buckets')
    @classmethod
    def validate_point_buckets(cls, buckets: List[PointBucket]) -> List[PointBucket]:
        return PointBucket.validate_list(buckets)

    @field_validator('position_targets')
    @classmethod
    def validate_position_targets(cls, targets: List[PositionTarget]) -> List[PositionTarget]:
        return PositionTarget.validate_list(targets)

    def build_set_player_list(self, show_team_breakdown: Optional[str] = None, source_env: str = "dev") -> None:
        """Build a complete set (base + expansions) based on configuration"""
        
        print(f"Building {self.set_size} card base set for {', '.join(map(str, self.years))}...")
        
        # 1. Get player pool
        player_pool = self._get_qualified_player_pool(source_env=source_env)
        print(f"Found {len(player_pool)} qualified players")
        
        if len(player_pool) < self.set_size:
            self._warn(f"Only {len(player_pool)} qualified players available for {self.set_size} card set")
        
        # 2. Calculate quality thresholds
        self._calculate_quality_thresholds(player_pool)
        
        # 3. Score players and fill the set by weighted selection
        player_pool = WeightedPlayerSelector.score_player_pool(player_pool, self.selection_weights, self._calculate_quality_score)
        selector = WeightedPlayerSelector(player_pool, self.set_size, self.selection_weights)
        final_players = self._select_players(selector)
        
        # 4. Swap cards to hit point bucket targets across the whole set
        final_players = self._enforce_point_buckets(final_players, player_pool)

        self._print_set_summary(final_players, selector.team_target, show_team_breakdown, player_pool)

        final_players = self._sort_and_number_players(final_players)
        
        # 5. Load and add expansion players from CSV (if provided)
        expansion_player_tuples = self._load_expansion_players_from_csv()
        if expansion_player_tuples:
            expansion_cards = self._load_expansion_cards_from_db(expansion_player_tuples, source_env=source_env)
            self.expansion_cards = expansion_cards
        
        self.final_players = final_players
        
        return

    def _generate_card_with_year_override(self, player: ShowdownBotSetPlayer, year_override: str) -> Optional[ShowdownPlayerCard]:
        """Generate a card live for a player whose stats should come from a different year combo (ex: '2025-2026').

        Multi-year cards don't exist in dim_card, so these are built through the full card
        generation pipeline. Returns None on failure so the caller can fall back to the
        single-year dim_card card.
        """
        print(f"Generating {player.name} live with year override '{year_override}'...")
        payload = generate_card(
            name=player.name,
            player_id=str(player.mlb_id),
            year=year_override,
            set=player.showdown_set,
            player_type_override=player.player_type_override,
            team_selection=self.team_selection,
            datasource = 'MLB_API'
        )
        error = payload.get('error')
        card_data = payload.get('card')
        if error or not card_data:
            print(f"Warning: year override failed for {player.name} ({error}). Falling back to {player.year} card.")
            return None
        return ShowdownPlayerCard(**card_data)

    def generate_showdown_cards_for_final_players(
        self,
        output_folder_path: str = None,
        set_name: Optional[str] = None,
        img_name_suffix: str = '',
        show: bool = False,
        skip_images: bool = False,
        export_data: bool = False,
        dark_mode: bool = False,
        variable_speed: bool = False,
        source_env: str = 'dev'
    ) -> None:
        """Generate card images for each item in final_players.

        Args:
            output_folder_path: Folder to export card images to.
            set_name: Optional set name to trigger set-numbered filenames.
            img_name_suffix: Optional suffix appended to image file names.
            show: Whether to open images after creation.
            skip_images: Whether to skip image generation.
            export_data: Whether to export player data to JSON file in output folder.
            dark_mode: Whether to render card images in dark mode.
            variable_speed: Whether to enable variable speed for 2000/2001 set cards. Recalculates speed and points.
            source_env: Environment to use for database access, e.g., 'dev' or 'prod'.

        Returns:
            None
        """

        if not self.final_players or len(self.final_players) == 0:
            return

        if not output_folder_path:
            # Set a default output path based on set name or timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_set_name = f"{set_name or 'showdown_set'}_{timestamp}"
            this_folder = os.path.dirname(os.path.abspath(__file__))
            output_folder_path = os.path.join(this_folder, "output", default_set_name)

        os.makedirs(output_folder_path, exist_ok=True)
        if not skip_images:
            os.makedirs(os.path.join(output_folder_path, "images"), exist_ok=True)

        player_pairs: List[Tuple[str, str]] = []
        for player in self.final_players:
            player_id = player.id
            showdown_set = player.showdown_set
            if not player_id or not showdown_set:
                continue
            player_pairs.append((player_id, showdown_set))

        if len(player_pairs) == 0:
            return

        # Keep unique pairs while preserving order
        unique_pairs = list(dict.fromkeys(player_pairs))

        placeholders = ", ".join(["(%s, %s)"] * len(unique_pairs))
        query_str = f"""
            SELECT DISTINCT ON (d.player_id, d.showdown_set)
                d.player_id,
                d.showdown_set,
                d.card_data
            FROM internal.dim_card d
            JOIN (VALUES {placeholders}) AS v(player_id, showdown_set)
              ON d.player_id = v.player_id
             AND d.showdown_set = v.showdown_set
            ORDER BY d.player_id, d.showdown_set, d.modified_date DESC
        """
        filter_values = tuple([value for pair in unique_pairs for value in pair])

        db = PostgresDB(is_archive=(source_env == 'prod'))
        raw_cards = db.execute_query(query=sql.SQL(query_str), filter_values=filter_values)

        card_lookup: Dict[Tuple[str, str], ShowdownPlayerCard] = {}
        for row in raw_cards:
            card_data = row.get('card_data') or {}
            try:
                card_lookup[(row.get('player_id'), row.get('showdown_set'))] = ShowdownPlayerCard(**card_data)
            except Exception:
                continue

        all_cards: list[ShowdownPlayerCard] = []
        total_cards = len(self.final_players)
        digits = max(3 if self.all_stars_only else 1, len(str(total_cards)))

        for player in self.final_players:
            player_id = player.id
            showdown_set = player.showdown_set
            year_override = (self.year_overrides or {}).get(player.bref_id_w_type_override)
            card = self._generate_card_with_year_override(player, year_override) if year_override else None
            if not card:
                card = card_lookup.get((player_id, showdown_set))
            if not card:
                continue
            set_number = player.set_number or 0
            card.image.set_number = str(set_number).zfill(digits)
            card.image.set_name = set_name or player.showdown_set
            card.image.show_year_text = False
            card.image.stat_highlights_type = StatHighlightsType.ALL if showdown_set in ['EXPANDED', 'CLASSIC'] else StatHighlightsType.NONE
            card.image.output_folder_path = os.path.join(output_folder_path, "images")
            card.image.is_bordered = True
            card.image.set_year = 2026
            card.image.is_dark_mode = dark_mode
            card.apply_variable_speed_00_01(variable_speed)
            card.stats_period.disable_display_text_on_card = True
            card.stats_period.team_selection = self.team_selection
            if self.all_stars_only:
                card.image.edition = Edition.ALL_STAR_GAME
                if year_override:
                    # Multi-year year strings don't match the exact-year checks in update_special_edition
                    try:
                        card.image.special_edition = SpecialEdition[f"ASG_{max(self.years)}"]
                    except KeyError:
                        pass
            if not skip_images:
                card.generate_card_image(show=show, img_name_suffix=img_name_suffix)
            
            all_cards.append(card)

        # Expansion cards (if any)
        if self.expansion_cards:
            prior_edition = None
            current_set_number = 1
            for card in self.expansion_cards:
                if not card.image:
                    continue
                if card.image.edition != prior_edition:
                    current_set_number = 1  # Reset set number for new edition
                card.image.set_number = f"{card.image.edition.value}{str(current_set_number).zfill(2)}"
                card.image.output_folder_path = os.path.join(output_folder_path, "images")
                card.image.is_bordered = True
                card.image.set_year = 2026
                card.image.is_dark_mode = dark_mode
                card.apply_variable_speed_00_01(variable_speed)
                card.image.set_name = f"{card.image.edition.value} Expansion"
                if not skip_images:
                    card.generate_card_image(show=show, img_name_suffix=img_name_suffix)
                all_cards.append(card)
                prior_edition = card.image.edition
                current_set_number += 1

        # EXPORT TO JSON WHERE THE PLAYER ID IS THE KEY AND SHOWDOWN CARD IS THE VALUE
        if export_data:
            export_path = os.path.join(output_folder_path, "data", "card_data.json")
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            export_dict = {}
            for card in all_cards:
                if card.bref_id and card.set:
                    key = card.id
                    export_dict[key] = card.as_json()
            with open(export_path, 'w') as f:
                json.dump(export_dict, f, indent=4)
            print(f"Exported card data to {export_path}")

        return
    
    def _get_qualified_player_pool(self, source_env: str = "dev") -> List[ExploreDataRecord]:
        """Get all qualified players for the season"""

        db = PostgresDB(is_archive=(source_env == "prod"))

        # Get all players from the season
        filters = {'year': [str(y) for y in self.years], 'showdown_set': self.showdown_sets, 'limit': 2000}
        if self.all_stars_only:
            filters['awards'] = ['AS']
        all_players = db.fetch_cards_bot(filters)

        print(f"Total players found in DB for years {self.years}: {len(all_players)}")

        # All-Star Game mode includes the entire roster, regardless of games/IP thresholds
        if self.all_stars_only:
            return [p for p in all_players if p.bref_id_w_type_override not in (self.manually_excluded_ids or [])]

        qualified_players = []
        
        for player in all_players:
            
            player_type = player.player_subtype  # Uses the property from ExploreDataRecord

            if player.bref_id_w_type_override in (self.manually_included_ids or []):
                qualified_players.append(player)
                continue
            
            if player.bref_id_w_type_override in (self.manually_excluded_ids or []):
                continue

            if self.all_stars_only and not player.has_award('AS'):
                continue

            # Apply minimum thresholds based on player type
            if player_type == 'POSITION_PLAYER':
                min_games_adjustment_ca = 0.80 if 'C' in player.primary_positions else 1.0
                if player.g >= (self.min_games_hitters * min_games_adjustment_ca):
                    qualified_players.append(player)
            elif player_type == 'STARTING_PITCHER':
                if player.real_ip and player.real_ip >= self.min_ip_starters:
                    qualified_players.append(player)
            elif player_type == 'RELIEF_PITCHER':
                if player.real_ip and player.real_ip >= self.min_ip_relievers:
                    qualified_players.append(player)
        
        return qualified_players

    def _calculate_quality_thresholds(self, player_pool: List[ExploreDataRecord]):
        """Calculate WAR thresholds for quality tiers"""
        wars = [p.war for p in player_pool if p.war is not None and p.war > 0]
        
        if not wars:
            return
        
        wars.sort(reverse=True)
        
        # Elite = top 15% by WAR
        elite_cutoff_index = int(len(wars) * 0.15)
        self.elite_war_threshold = wars[elite_cutoff_index] if elite_cutoff_index < len(wars) else wars[-1]
        
        # Good = top 50% by WAR  
        good_cutoff_index = int(len(wars) * 0.50)
        self.good_war_threshold = wars[good_cutoff_index] if good_cutoff_index < len(wars) else wars[-1]
        
        print(f"Quality thresholds - Elite: {self.elite_war_threshold:.1f} WAR, Good: {self.good_war_threshold:.1f} WAR")
    
    def _select_players(self, selector: WeightedPlayerSelector) -> List[ShowdownBotSetPlayer]:
        """Fill the set in passes, each relaxing what a slot accepts:
        
        1. Position targets (card's primary position) or player type distribution
        2. Position targets only: any position on the card, so thin positions borrow multi-position players
        3. Leftover slots by player type
        4. Anything still open, from any player type
        """
        manually_included_ids = set(self.manually_included_ids or [])
        
        if self.position_targets:
            counts = PositionTarget.allocate_counts({t.position: t.percentage for t in self.position_targets}, self.set_size)
            groups = [
                SlotGroup(t.position, counts[t.position], accepts=lambda p, slot=t.position: SlotPosition.primary_slot(p) == slot, avg_points=t.avg_points)
                for t in self.position_targets
            ]
        else:
            distribution = self.player_type_distribution
            counts = PositionTarget.allocate_counts({
                'POSITION_PLAYER': distribution.hitters_percentage,
                'STARTING_PITCHER': distribution.starters_percentage,
                'RELIEF_PITCHER': distribution.relievers_percentage,
            }, self.set_size)
            groups = [self._player_type_group(subtype, counts[subtype]) for subtype in PLAYER_SUBTYPES]
        
        for player in selector.player_pool:
            if player.bref_id_w_type_override in manually_included_ids:
                selector.add(player, next((g for g in groups if g.remaining and g.accepts(player)), None))
        
        selector.fill(groups)
        
        if self.position_targets:
            for group in groups:
                group.accepts = lambda p, slot=group.key: slot in SlotPosition.eligible_slots(p)
            selector.fill(groups)
            for group in groups:
                if group.remaining:
                    self._warn(f"Only found {len(group.members)} of {group.target} {group.key} cards, filled the rest with other {SlotPosition.player_subtype(group.key).replace('_', ' ').lower()}s")
                print(f"{group.key}: {len(group.members)}/{group.target} cards, avg {group.actual_avg_points or 0:.0f} pts (target {group.avg_points or 0:.0f})")
            leftover = {subtype: sum(g.remaining for g in groups if SlotPosition.player_subtype(g.key) == subtype) for subtype in PLAYER_SUBTYPES}
            selector.fill([self._player_type_group(subtype, count) for subtype, count in leftover.items()])
        
        selector.fill([SlotGroup('ANY', self.set_size - len(selector.selected), accepts=lambda p: True)])
        return selector.selected
    
    @staticmethod
    def _player_type_group(player_subtype: str, target: int) -> SlotGroup:
        return SlotGroup(player_subtype, target, accepts=lambda p: p.player_subtype == player_subtype)
    
    def _warn(self, warning: str) -> None:
        print(f"Warning: {warning}")
        self.warnings.append(warning)
    
    def _calculate_quality_score(self, player: ExploreDataRecord) -> float:
        """Raw quality: WAR plus All-Star/award bonuses. Playing time is weighted separately (see `WeightedPlayerSelector.volume`)."""
        
        score = max(player.war or 0.0, 0.0)
        
        if player.player_subtype == 'RELIEF_PITCHER' and player.primary_position == Position.CL:
            score += 1.0  # Small bonus for closers
        
        # Bonuses for special achievements
        if player.awards_list:
            award_summary = ','.join(player.awards_list)
            
            # All-Star bonus
            if 'AS' in award_summary and self.include_all_stars:
                score += 5.0
            
            # Award winner bonuses
            if self.include_award_winners:
                if 'MVP' in award_summary:
                    score += 15.0
                if 'CY' in award_summary:
                    score += 12.0
                if 'ROY' in award_summary:
                    score += 8.0
                if 'GG' in award_summary:
                    score += 5.0
                if 'SS' in award_summary:
                    score += 5.0
        
        return score
    
    def _enforce_point_buckets(self, selected_players: List[ShowdownBotSetPlayer], player_pool: List[ShowdownBotSetPlayer]) -> List[ShowdownBotSetPlayer]:
        """Swap cards so each player type hits every point bucket's target share of that type.
        
        Weighted selection doesn't look at point ranges, so buckets are enforced here against the
        whole set. For each type and each bucket below target, the highest priority unselected card in the
        bucket replaces the lowest priority card of the same type that is either outside every bucket or in a
        bucket already above its target. Swaps prefer removing a card from the incoming player's team to keep
        team balance, and never remove manually included players. Set size and type counts are unchanged.
        """
        if not self.point_buckets:
            return selected_players
        
        manually_included_ids = set(self.manually_included_ids or [])
        selected_ids = set(p.id for p in selected_players)
        unselected_players = [p for p in player_pool if p.id not in selected_ids]
        
        for player_subtype in ('POSITION_PLAYER', 'STARTING_PITCHER', 'RELIEF_PITCHER'):
            type_players = [p for p in selected_players if p.player_subtype == player_subtype]
            if not type_players:
                continue
            targets = [ceil(len(type_players) * bucket.percentage) for bucket in self.point_buckets]
            
            def bucket_index(player: ExploreDataRecord) -> Optional[int]:
                return next((i for i, bucket in enumerate(self.point_buckets) if bucket.contains(player)), None)
            
            def bucket_count(index: int) -> int:
                return len([p for p in type_players if bucket_index(p) == index])
            
            def is_removable(player: ShowdownBotSetPlayer) -> bool:
                if player.bref_id_w_type_override in manually_included_ids:
                    return False
                index = bucket_index(player)
                return index is None or bucket_count(index) > targets[index]
            
            candidates = sorted(
                (p for p in unselected_players if p.player_subtype == player_subtype),
                key=lambda x: x.priority_score, reverse=True
            )
            
            for index, bucket in enumerate(self.point_buckets):
                starting_count = bucket_count(index)
                for incoming in (c for c in candidates if bucket.contains(c)):
                    if bucket_count(index) >= targets[index]:
                        break
                    removable = [p for p in type_players if is_removable(p)]
                    if not removable:
                        break
                    outgoing = min(removable, key=lambda p: (p.team_id != incoming.team_id, p.priority_score))
                    type_players.remove(outgoing)
                    type_players.append(incoming)
                
                final_count = bucket_count(index)
                print(f"{player_subtype} {bucket.label}: {starting_count} -> {final_count} (target {targets[index]}, {bucket.percentage:.0%})")
                if final_count < targets[index]:
                    self._warn(f"Only reached {final_count} of {targets[index]} {player_subtype.replace('_', ' ').lower()} cards in the {bucket.label} bucket")
            
            selected_players = [p for p in selected_players if p.player_subtype != player_subtype] + type_players
        
        return selected_players
    
    def _print_set_summary(
        self,
        selected_players: List[ShowdownBotSetPlayer],
        team_target: float,
        show_team_breakdown: Optional[str] = None,
        player_pool: Optional[List[ShowdownBotSetPlayer]] = None
    ):
        """Print summary of the generated set"""
        
        print("\n" + "="*60)
        print("SET SUMMARY")
        print("="*60)
        
        # Player type breakdown
        hitters = [p for p in selected_players if p.player_subtype == 'POSITION_PLAYER']
        starters = [p for p in selected_players if p.player_subtype == 'STARTING_PITCHER']
        relievers = [p for p in selected_players if p.player_subtype == 'RELIEF_PITCHER']
        
        player_type_table = PrettyTable(field_names=["Type", "Count", "Percentage"])
        player_type_table.add_row(["Hitters", len(hitters), f"{(len(hitters)/len(selected_players))*100:.1f}%"])
        player_type_table.add_row(["Starters", len(starters), f"{(len(starters)/len(selected_players))*100:.1f}%"])
        player_type_table.add_row(["Relievers", len(relievers), f"{(len(relievers)/len(selected_players))*100:.1f}%"])
        print(f"Player Types:")
        print(player_type_table)
        
        # Team breakdown
        team_counts = {}
        for player in selected_players:
            team = player.team_id
            team_counts[team] = team_counts.get(team, 0) + 1
        
        team_dist_table = PrettyTable(field_names=["Team", "Count", "Target"])
        for team in sorted(team_counts.keys()):
            team_dist_table.add_row([team, team_counts[team], f"{team_target:.1f}"])
        print(f"\nTeam Distribution:")
        print(team_dist_table)

        # Position breakdown
        position_counts: Dict[Position, int] = {}
        position_10_20_pt_counts = {}
        positions_10_50_pt_counts = {}
        for player in selected_players:
            position = player.primary_position
            position_counts[position] = position_counts.get(position, 0) + 1
            if player.points <= 20:
                print(f"Counting 10-20-pt card for position {position.name}: {player.name}")
                position_10_20_pt_counts[position] = position_10_20_pt_counts.get(position, 0) + 1
            if player.points <= 50:
                positions_10_50_pt_counts[position] = positions_10_50_pt_counts.get(position, 0) + 1

        print(f"\nPosition Distribution:")
        position_dist_table = PrettyTable(field_names=["Position", "Count", "Pct", "10-20-pt Cards", "10-50-pt Cards"])
        for pos in sorted(position_counts.keys(), key=lambda x: x.ordering_index or 0, reverse=True):
            count = position_counts[pos]
            count_10_20 = position_10_20_pt_counts.get(pos, 0)
            count_10_50 = positions_10_50_pt_counts.get(pos, 0)
            position_dist_table.add_row([pos.name, count, f"{(count/len(selected_players))*100:.1f}%", count_10_20, count_10_50])
        print(position_dist_table)

        # RP/CL POINTS DISTRIBUTION (50-POINT BUCKETS)
        sp_point_buckets: Dict[int, int] = {}
        for player in selected_players:
            if player.primary_position not in (Position.RP, Position.CL):
                continue
            if player.points is None:
                continue
            bucket_start = int(player.points) // 50 * 50
            sp_point_buckets[bucket_start] = sp_point_buckets.get(bucket_start, 0) + 1

        if len(sp_point_buckets) > 0:
            print("\nRP/CL Points Distribution (50-pt buckets):")
            sp_points_table = PrettyTable(field_names=["Points", "Count"])
            for bucket_start in sorted(sp_point_buckets.keys()):
                bucket_end = bucket_start + 49
                sp_points_table.add_row([f"{bucket_start}-{bucket_end}", sp_point_buckets[bucket_start]])
            print(sp_points_table)

        print(f"Total Players Selected: {len(selected_players)} / {self.set_size}")

        # MISSING IMAGES
        top_players_missing_images = [p for p in selected_players if not p.image_match_type in (ImageMatchType.EXACT)]
        print(f"\nPlayers Missing Exact Images: {len(top_players_missing_images)}")
        top_players_missing_images.sort(key=lambda p: getattr(p, "priority_score", 0) or 0, reverse=True)
        tbl_missing = PrettyTable()
        tbl_missing.field_names = ["Name", "Score", "WAR", "Pos", "G", "GS", "ERA", "OPS", "Team", "Img", "PTS"]
        for player in top_players_missing_images[:20]:
            tbl_missing.add_row([
                player.name, f"{player.priority_score:.2f}" if player.priority_score is not None else "-", f"{player.war:.2f}" if player.war is not None else "N/A", 
                player.primary_position.name.replace('_', ''), player.g, player.gs or '-', player.real_earned_run_avg or "-", 
                player.real_onbase_plus_slugging or "-", player.team_id, color_image_match(player.image_match_type), player.points or "-"
            ])
        print(tbl_missing)

        # HIGHEST WAR PLAYERS NOT SELECTED
        if player_pool:
            selected_ids = {p.id for p in selected_players if p.id}
            unselected_players = [p for p in player_pool if p.id not in selected_ids]
            unselected_players.sort(
                key=lambda p: p.war if p.war is not None else -9999,
                reverse=True
            )

            top_unselected = unselected_players[:20]
            print(f"\nHighest WAR Players Not Selected: {len(unselected_players)} total")
            unselected_table = PrettyTable()
            unselected_table.field_names = ["Name", "WAR", "Pos", "G", "GS", "ERA", "OPS", "Team", "PTS"]
            for player in top_unselected:
                unselected_table.add_row([
                    player.name,
                    f"{player.war:.2f}" if player.war is not None else "N/A",
                    player.primary_position.name.replace('_', ''),
                    player.g,
                    player.gs or '-',
                    player.real_earned_run_avg or "-",
                    player.real_onbase_plus_slugging or "-",
                    player.team_id,
                    player.points or "-"
                ])
            print(unselected_table)

        if show_team_breakdown:
            print(f"\nDetailed Team Breakdown for {show_team_breakdown}:")
            team_players = [p for p in selected_players if p.team_id == show_team_breakdown]
            team_table = PrettyTable()
            team_table.field_names = ["Name", "Score", "WAR", "Pos", "G", "GS", "ERA", "OPS", "Img", "PTS"]
            for player in team_players:
                team_table.add_row([
                    player.name, f"{player.priority_score:.2f}" if getattr(player, "priority_score", None) is not None else "-", 
                    f"{player.war:.2f}" if player.war is not None else "N/A", player.primary_position.name.replace('_', ''), 
                    player.g, player.gs or '-', player.real_earned_run_avg or "-", 
                    player.real_onbase_plus_slugging or "-", color_image_match(player.image_match_type), player.points or "-"
                ])
            print(team_table)

        print("="*60 + "\n")

    def _sort_and_number_players(self, players: List[ShowdownBotSetPlayer]) -> List[ShowdownBotSetPlayer]:
        """Sort players by team then last name, and assign set numbers."""

        def last_name_key(full_name: str) -> str:
            if not full_name:
                return ""
            parts = full_name.strip().replace(',', '').split()
            # Skip generational suffixes so "Bobby Witt Jr." sorts under "Witt"
            suffixes = {'jr', 'sr', 'ii', 'iii', 'iv', 'v'}
            while len(parts) > 1 and parts[-1].lower().rstrip('.') in suffixes:
                parts.pop()
            if len(parts) == 0:
                return ""
            return parts[-1].lower()

        if self.all_stars_only:
            # AL players first, then NL, each sorted by last name
            league_order = {'AL': 0, 'NL': 1}
            for player in players:
                if (player.lg_id or '').upper() not in league_order:
                    print(f"Warning: {player.name} has league '{player.lg_id}', sorting after AL/NL")
            sorted_players = sorted(
                players,
                key=lambda p: (
                    league_order.get((p.lg_id or '').upper(), 2),
                    last_name_key(p.name),
                    (p.name or "").lower()
                )
            )
        else:
            sorted_players = sorted(
                players,
                key=lambda p: (
                    (p.team_id or "").lower(),
                    (p.bref_id_w_type_override or "").lower(),
                    last_name_key(p.name),
                    (p.name or "").lower()
                )
            )

        for index, player in enumerate(sorted_players, start=1):
            player.set_number = index

        return sorted_players


class AlgorithmPreviewRequest(BaseModel):
    """Validated web-request payload for the Edition Builder's Algorithm tab.

    A strict subset of `ShowdownBotSet`'s constructor fields — this is the API contract exposed
    to the browser, so fields like `final_players`, `expansion_cards`, and `csv_file_path` are
    intentionally excluded (they must never be attacker-settable from the web).
    """

    set_size: int = Field(..., ge=1, le=500)
    years: str = Field(..., description="Flexible year string, e.g. '2023', '2000-2004', '2006+2014'")
    showdown_sets: List[str] = Field(..., min_length=1)

    min_games_hitters: int = 60
    min_ip_starters: int = 75
    min_ip_relievers: int = 30

    player_type_distribution: PlayerTypeDistribution = Field(default_factory=PlayerTypeDistribution)

    include_all_stars: bool = True
    include_award_winners: bool = True
    all_stars_only: bool = False

    point_buckets: List[PointBucket] = Field(default_factory=list)

    selection_weights: SelectionWeights = Field(default_factory=SelectionWeights)
    position_targets: List[PositionTarget] = Field(default_factory=list)

    manually_included_ids: Optional[List[str]] = None
    manually_excluded_ids: Optional[List[str]] = None

    def to_showdown_bot_set(self) -> ShowdownBotSet:
        """Validate and construct the `ShowdownBotSet` this request describes."""
        if not self.position_targets:
            self.player_type_distribution.validate_total()
        return ShowdownBotSet(
            set_size=self.set_size,
            years=convert_year_string_to_list(self.years),
            showdown_sets=self.showdown_sets,
            min_games_hitters=self.min_games_hitters,
            min_ip_starters=self.min_ip_starters,
            min_ip_relievers=self.min_ip_relievers,
            player_type_distribution=self.player_type_distribution,
            include_all_stars=self.include_all_stars,
            include_award_winners=self.include_award_winners,
            all_stars_only=self.all_stars_only,
            point_buckets=self.point_buckets,
            selection_weights=self.selection_weights,
            position_targets=self.position_targets,
            manually_included_ids=self.manually_included_ids,
            manually_excluded_ids=self.manually_excluded_ids,
        )