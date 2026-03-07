from pprint import pprint
from typing import List, Dict, Optional, Tuple
import statistics
import os
import csv
import json

from pydantic import BaseModel, Field
from datetime import datetime
from math import ceil
from psycopg2 import sql

# Table
from prettytable import PrettyTable

# SHOWDOWN BOT
from ..database.postgres_db import PostgresDB, ExploreDataRecord, ExploreDataRecord, ImageMatchType
from ..shared.player_position import Position
from ..card.showdown_player_card import ShowdownPlayerCard, Expansion, Edition, ImageParallel

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

class TeamAllocation(BaseModel):
    """How many players each team should get"""
    team_id: str
    team_name: str
    target_count: int
    min_count: int = Field(ge=1)
    max_count: int
    actual_count: int = 0

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
    

class ShowdownBotSetPlayer(ExploreDataRecord):
    """Extended player record for set building"""
    
    priority_score: float = 0.0  # Calculated priority score for selection

    set_number: Optional[int] = None  # Assigned set number for the player


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

    # Construction results
    final_players: Optional[List[ShowdownBotSetPlayer]] = Field(None, description="Final list of players selected for the set")
    
    # 10-50 point card allocation
    ideal_low_point_percentage: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Ideal percentage of 10-50 point cards in the set (None to skip)"
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

    def _load_expansion_cards_from_db(self, expansion_players: List[Dict]) -> List[ShowdownPlayerCard]:
        """Query database for expansion player cards and apply CSV attributes.
        
        Args:
            expansion_players: List of dicts with 'bref_id' and 'year' keys, plus optional attributes
            
        Returns:
            List of ShowdownPlayerCard objects with CSV attributes applied
        """
        if not expansion_players:
            return []
        
        db = PostgresDB(is_archive=False)
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

    def build_set_player_list(self, show_team_breakdown: Optional[str] = None) -> None:
        """Build a complete set (base + expansions) based on configuration"""
        
        print(f"Building {self.set_size} card base set for {', '.join(map(str, self.years))}...")
        
        # 1. Get player pool
        player_pool = self._get_qualified_player_pool()
        print(f"Found {len(player_pool)} qualified players")
        
        if len(player_pool) < self.set_size:
            print(f"Warning: Only {len(player_pool)} qualified players available for {self.set_size} card set")
        
        # 2. Calculate quality thresholds
        self._calculate_quality_thresholds(player_pool)
        
        # # 3. Get team allocations
        team_allocations = self._calculate_team_allocations(player_pool)
        
        # 4. Select players by team and type
        selected_players = self._select_players(player_pool, team_allocations)

        # 5. Redistribute unused slots
        final_players = self._redistribute_unused_slots(player_pool, team_allocations, selected_players)
        
        self._print_set_summary(final_players, team_allocations, show_team_breakdown, player_pool)

        final_players = self._sort_and_number_players(final_players)
        
        # 6. Load and add expansion players from CSV (if provided)
        expansion_player_tuples = self._load_expansion_players_from_csv()
        if expansion_player_tuples:
            expansion_cards = self._load_expansion_cards_from_db(expansion_player_tuples)
            self.expansion_cards = expansion_cards
        
        self.final_players = final_players
        
        return

    def generate_showdown_cards_for_final_players(
        self,
        output_folder_path: str = None,
        set_name: Optional[str] = None,
        img_name_suffix: str = '',
        show: bool = False,
        skip_images: bool = False,
        export_data: bool = False
    ) -> None:
        """Generate card images for each item in final_players.

        Args:
            output_folder_path: Folder to export card images to.
            set_name: Optional set name to trigger set-numbered filenames.
            img_name_suffix: Optional suffix appended to image file names.
            show: Whether to open images after creation.
            skip_images: Whether to skip image generation.
            export_data: Whether to export player data to JSON file in output folder.

        Returns:
            None
        """

        if not self.final_players or len(self.final_players) == 0:
            return

        if not output_folder_path:
            # Set a default output path based on set name or timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_set_name = set_name or f"showdown_set_{timestamp}"
            this_folder = os.path.dirname(os.path.abspath(__file__))
            output_folder_path = os.path.join(this_folder, "output", default_set_name)

        os.makedirs(output_folder_path, exist_ok=True)

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

        db = PostgresDB(is_archive=False)
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
        digits = max(1, len(str(total_cards)))

        for player in self.final_players:
            player_id = player.id
            showdown_set = player.showdown_set
            card = card_lookup.get((player_id, showdown_set))
            if not card:
                continue
            set_number = player.set_number or 0
            card.image.set_number = str(set_number).zfill(digits)
            card.image.set_name = set_name or player.showdown_set
            card.image.output_folder_path = os.path.join(output_folder_path, "images")
            card.image.is_bordered = True
            card.image.set_year = 2026
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
    
    def _get_qualified_player_pool(self) -> List[ExploreDataRecord]:
        """Get all qualified players for the season"""

        db = PostgresDB(is_archive=False)
        
        # Get all players from the season
        all_players = db.fetch_cards_bot(
            {'year': [str(y) for y in self.years], 'showdown_set': self.showdown_sets, 'limit': 2000},
        )

        print(f"Total players found in DB for years {self.years}: {len(all_players)}")
        
        qualified_players = []
        
        for player in all_players:
            
            player_type = player.player_subtype  # Uses the property from ExploreDataRecord

            if player.bref_id_w_type_override in (self.manually_included_ids or []):
                qualified_players.append(player)
                continue
            
            if player.bref_id_w_type_override in (self.manually_excluded_ids or []):
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
    
    def _calculate_team_allocations(self, player_pool: List[ExploreDataRecord]) -> Dict[str, TeamAllocation]:
        """Calculate how many players each team should get"""
        
        # Get all teams with qualified players
        teams = list(set(p.team_id for p in player_pool if p.team_id))
        teams.sort()

        target_count = max(1, self.set_size // len(teams))
                
        # Convert to TeamAllocation objects
        team_allocations = {}
        for team_id in teams:
            team_allocations[team_id] = TeamAllocation(
                team_id=team_id,
                team_name=team_id,
                target_count=target_count,
                min_count=max(1, target_count - 2),  # Allow some flexibility
                max_count=target_count + 2
            )
        
        return team_allocations
    
    def _select_players(self, player_pool: List[ExploreDataRecord], team_allocations: Dict[str, TeamAllocation]) -> List[ShowdownBotSetPlayer]:
        """Select players for the set based on allocations"""
        
        selected_players: List[ShowdownBotSetPlayer] = []
        
        # Group players by team
        players_by_team: Dict[str, List[ShowdownBotSetPlayer]] = {}
        for player in player_pool:
            team = player.team_id
            if team not in players_by_team:
                players_by_team[team] = []
            players_by_team[team].append(player)

        # Select players for each team
        for team_id, allocation in team_allocations.items():
            if team_id not in players_by_team:
                continue
                
            team_players = players_by_team[team_id]
            selected_team_players = self._select_team_players(team_players, allocation.target_count)
            selected_players.extend(selected_team_players)
            allocation.actual_count = len(selected_team_players)
        
        return selected_players
    
    def _select_team_players(self, team_players: List[ExploreDataRecord], target_count: int) -> List[ShowdownBotSetPlayer]:
        """Select players for a specific team"""
        
        # Separate by player type
        hitters = [p for p in team_players if p.player_subtype == 'POSITION_PLAYER']
        starters = [p for p in team_players if p.player_subtype == 'STARTING_PITCHER']  
        relievers = [p for p in team_players if p.player_subtype == 'RELIEF_PITCHER']
        
        # Calculate target counts for each type
        target_hitters = max(1, round(target_count * self.player_type_distribution.hitters_percentage))
        target_starters = max(0, round(target_count * self.player_type_distribution.starters_percentage))
        target_relievers = target_count - target_hitters - target_starters
        
        selected = []
        
        # Select hitters
        selected_hitters = self._select_by_quality(hitters, target_hitters)
        selected.extend(selected_hitters)
        
        # Select starters
        selected_starters = self._select_by_quality(starters, target_starters)
        selected.extend(selected_starters)
        
        # Select relievers
        selected_relievers = self._select_by_quality(relievers, target_relievers)
        selected.extend(selected_relievers)
        
        return selected
    
    def _select_by_quality(self, players: List[ExploreDataRecord], target_count: int) -> List[ShowdownBotSetPlayer]:
        """Select players based on quality distribution"""
        
        if not players or target_count <= 0:
            return []
        
        # Sort players by quality (WAR, with special considerations)
        players_with_priority: List[Tuple[ShowdownBotSetPlayer, float]] = []
        for player in players:
            priority_score = self._calculate_priority_score(player)
            updated_player = ShowdownBotSetPlayer(
                **player.model_dump(),
                priority_score=priority_score
            )
            players_with_priority.append((updated_player, priority_score))
        
        num_players_manually_included = len([p for p in players if p.bref_id_w_type_override in (self.manually_included_ids or [])])
        cap = max(target_count, num_players_manually_included)

        players_with_priority.sort(key=lambda x: (x[0].bref_id_w_type_override in (self.manually_included_ids or []), x[1]), reverse=True)

        # Select top players up to target count
        selected = [p[0] for p in players_with_priority[:cap]]
        
        return selected
    
    def _calculate_priority_score(self, player: ExploreDataRecord) -> float:
        """Calculate priority score for player selection"""
        
        score = 0.0
        war = player.war or 0.0
        
        # Base score from WAR
        score += max(war, 0.0)

        # Incorporate games played / innings pitched
        match player.player_subtype:
            case 'POSITION_PLAYER':
                score += (player.g / 162) * 5.0  # Up to 5 point bonus for full season
            case 'STARTING_PITCHER' | 'RELIEF_PITCHER':
                is_sp = player.player_subtype == 'STARTING_PITCHER'
                ip = player.real_ip or 0
                max_ip = 180 if is_sp else 70

                # REMOVE GS IP FOR RELIEVERS
                ip_gs = player.gs * 5
                gs = player.gs or 0
                if not is_sp and ip_gs and gs > 0:
                    ip -= (ip_gs * gs)

                score += (ip / max_ip) * 5.0  # Up to 5 point bonus for full season

                if player.primary_position == Position.CL:
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
    
    def _redistribute_unused_slots(self, player_pool: List[ExploreDataRecord], team_allocations: Dict[str, TeamAllocation], selected_players: List[ExploreDataRecord]) -> List[ShowdownBotSetPlayer]:
        """Redistribute unused slots when teams don't have enough qualified players
        
        Prioritizes maintaining player type distribution (hitters/starters/relievers percentages).
        
        If ideal_low_point_percentage is set:
        - First fills slots to reach target player type distribution
        - Then balances low-point card percentages within each type
        - Finally fills any remaining slots with highest priority players
        
        If ideal_low_point_percentage is None:
        - Fills slots to reach target player type distribution with highest priority players
        """
        
        # Calculate how many slots are unused
        total_selected = len(selected_players)
        unused_slots = self.set_size - total_selected
        
        if unused_slots <= 0:
            return [ShowdownBotSetPlayer(**p.model_dump()) for p in selected_players]
        
        print(f"Redistributing {unused_slots} unused slots...")
        
        # Get all unselected players
        ids = set(p.id for p in selected_players)
        unselected_players = [p for p in player_pool if p.id not in ids]
        print(f"Found {len(unselected_players)} unselected players for redistribution. There are {len(player_pool)} total qualified players.")
        
        # Calculate current player type counts
        current_hitters = len([p for p in selected_players if p.player_subtype == 'POSITION_PLAYER'])
        current_starters = len([p for p in selected_players if p.player_subtype == 'STARTING_PITCHER'])
        current_relievers = len([p for p in selected_players if p.player_subtype == 'RELIEF_PITCHER'])
        
        # Calculate target percentages for final set
        target_hitters_pct = self.player_type_distribution.hitters_percentage
        target_starters_pct = self.player_type_distribution.starters_percentage
        target_relievers_pct = self.player_type_distribution.relievers_percentage
        
        # Calculate current percentages
        current_hitters_pct = current_hitters / total_selected if total_selected > 0 else 0
        current_starters_pct = current_starters / total_selected if total_selected > 0 else 0
        current_relievers_pct = current_relievers / total_selected if total_selected > 0 else 0
        
        # Calculate deficits (how far below target each type is)
        hitters_deficit = target_hitters_pct - current_hitters_pct
        starters_deficit = target_starters_pct - current_starters_pct
        relievers_deficit = target_relievers_pct - current_relievers_pct
        
        print(f"Current percentages - Hitters: {current_hitters_pct:.1%} (target {target_hitters_pct:.1%}), Starters: {current_starters_pct:.1%} (target {target_starters_pct:.1%}), Relievers: {current_relievers_pct:.1%} (target {target_relievers_pct:.1%})")
        print(f"Deficits - Hitters: {hitters_deficit:+.1%}, Starters: {starters_deficit:+.1%}, Relievers: {relievers_deficit:+.1%}")
        
        # Distribute unused slots proportionally based on deficits
        # Only allocate to types that are below target
        total_deficit = max(0, hitters_deficit) + max(0, starters_deficit) + max(0, relievers_deficit)
        
        if total_deficit > 0:
            # Allocate proportionally to deficits
            hitters_allocation = round(unused_slots * (max(0, hitters_deficit) / total_deficit))
            starters_allocation = round(unused_slots * (max(0, starters_deficit) / total_deficit))
            relievers_allocation = unused_slots - hitters_allocation - starters_allocation
        else:
            # All types at or above target, distribute evenly by target percentages
            hitters_allocation = round(unused_slots * target_hitters_pct)
            starters_allocation = round(unused_slots * target_starters_pct)
            relievers_allocation = unused_slots - hitters_allocation - starters_allocation
        
        print(f"Allocating unused slots - Hitters: {hitters_allocation}, Starters: {starters_allocation}, Relievers: {relievers_allocation}")
        
        # Separate unselected players by type and calculate priority scores
        unselected_hitters = []
        unselected_starters = []
        unselected_relievers = []
        
        for player in unselected_players:
            priority_score = self._calculate_priority_score(player)
            player_with_score = ShowdownBotSetPlayer(**player.model_dump(), priority_score=priority_score)
            
            if player.player_subtype == 'POSITION_PLAYER':
                unselected_hitters.append(player_with_score)
            elif player.player_subtype == 'STARTING_PITCHER':
                unselected_starters.append(player_with_score)
            elif player.player_subtype == 'RELIEF_PITCHER':
                unselected_relievers.append(player_with_score)
        
        # Sort each type by priority
        unselected_hitters.sort(key=lambda x: x.priority_score, reverse=True)
        unselected_starters.sort(key=lambda x: x.priority_score, reverse=True)
        unselected_relievers.sort(key=lambda x: x.priority_score, reverse=True)
        
        # If no ideal low point percentage, just fill with highest priority maintaining type distribution
        if self.ideal_low_point_percentage is None:
            print("No ideal low-point percentage set, filling proportionally by deficit.")
            additional_players = []
            additional_players.extend(unselected_hitters[:hitters_allocation])
            additional_players.extend(unselected_starters[:starters_allocation])
            additional_players.extend(unselected_relievers[:relievers_allocation])
            
            # If we still have slots (due to rounding or lack of players), fill with highest priority overall
            slots_after_type_balance = unused_slots - len(additional_players)
            if slots_after_type_balance > 0:
                print(f"Filling {slots_after_type_balance} remaining slots with highest priority players (any type)")
                # Get remaining unselected players
                used_ids = set(p.id for p in additional_players)
                remaining_hitters = [p for p in unselected_hitters[hitters_allocation:] if p.id not in used_ids]
                remaining_starters = [p for p in unselected_starters[starters_allocation:] if p.id not in used_ids]
                remaining_relievers = [p for p in unselected_relievers[relievers_allocation:] if p.id not in used_ids]
                
                all_remaining = remaining_hitters + remaining_starters + remaining_relievers
                all_remaining.sort(key=lambda x: x.priority_score, reverse=True)
                additional_players.extend(all_remaining[:slots_after_type_balance])
            
            selected_players.extend(additional_players)
            return selected_players
        
        # If ideal low point percentage is set, balance low-point cards within each type
        print(f"Ideal low-point percentage set to {self.ideal_low_point_percentage:.1%}, balancing within each player type.")
        additional_players = []
        for unselected_list, allocation in [
            (unselected_hitters, hitters_allocation),
            (unselected_starters, starters_allocation),
            (unselected_relievers, relievers_allocation)
        ]:
            if allocation <= 0:
                continue
            
            # Calculate current low-point percentage in this type
            current_type_players = [p for p in selected_players if p.player_subtype == unselected_list[0].player_subtype]
            current_low_point_count = len([p for p in current_type_players if p.points is not None and p.points <= 50])
            current_type_count = len(current_type_players)
            current_low_point_pct = (current_low_point_count / current_type_count) if current_type_count > 0 else 0.0
            
            # Determine how many low-point cards to add
            desired_low_point_count = ceil((current_type_count + allocation) * self.ideal_low_point_percentage)
            low_point_needed = max(0, desired_low_point_count - current_low_point_count)
            high_point_needed = allocation - low_point_needed
            
            print(f"For {unselected_list[0].player_subtype}, current low-point pct: {current_low_point_pct:.1%}, need {low_point_needed} low-point and {high_point_needed} high-point cards.")
            
            # Select low-point cards
            low_point_candidates = [p for p in unselected_list if p.points is not None and p.points <= 50]
            high_point_candidates = [p for p in unselected_list if p.points is None or p.points > 50]
            
            additional_players.extend(low_point_candidates[:low_point_needed])
            additional_players.extend(high_point_candidates[:high_point_needed])
        
        selected_players.extend(additional_players)
        return selected_players
    
    def _print_set_summary(
        self,
        selected_players: List[ShowdownBotSetPlayer],
        team_allocations: Dict[str, TeamAllocation],
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
            team_allocation = team_allocations.get(team, None)
            target_count = team_allocation.target_count if team_allocation else 0
            actual = team_counts[team]
            team_dist_table.add_row([team, actual, target_count])
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
            if len(parts) == 0:
                return ""
            return parts[-1].lower()

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