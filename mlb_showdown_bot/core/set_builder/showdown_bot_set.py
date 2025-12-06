from pprint import pprint
from typing import List, Dict, Optional, Tuple
import statistics
from ..database.postgres_db import PostgresDB, ExploreDataRecord, ExploreDataRecord, ImageMatchType
from pydantic import BaseModel, Field
from datetime import datetime

# Table
from prettytable import PrettyTable

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

    def build_set(self) -> List[ExploreDataRecord]:
        """Build a complete set based on configuration"""
        print(f"Building {self.set_size} card set for {', '.join(map(str, self.years))}...")
        
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
        
        self._print_set_summary(final_players, team_allocations)
        
        return
    
    def _get_qualified_player_pool(self) -> List[ExploreDataRecord]:
        """Get all qualified players for the season"""

        db = PostgresDB(is_archive=True)
        
        # Get all players from the season
        all_players = db.fetch_explore_data(
            {'year': [str(y) for y in self.years], 'showdown_set': self.showdown_sets, 'limit': 2000},
        )

        print(f"Total players found in DB for years {self.years}: {len(all_players)}")
        
        qualified_players = []
        
        for player in all_players:
            # Skip if no stats
            if not player.card_data.stats or len(player.card_data.stats) == 0:
                continue
            
            player_type = player.player_subtype  # Uses the property from ExploreDataRecord
            
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
        players_with_priority = []
        for player in players:
            priority_score = self._calculate_priority_score(player)
            updated_player = ShowdownBotSetPlayer(
                **player.model_dump(),
                priority_score=priority_score
            )
            players_with_priority.append((updated_player, priority_score))
        
        players_with_priority.sort(key=lambda x: x[1], reverse=True)
        
        # Select top players up to target count
        selected = [p[0] for p in players_with_priority[:target_count]]
        
        return selected
    
    def _calculate_priority_score(self, player: ExploreDataRecord) -> float:
        """Calculate priority score for player selection"""
        
        score = 0.0
        war = player.war or 0.0
        
        # Base score from WAR
        score += war * 2.0

        # Incorporate games played / innings pitched
        match player.player_subtype:
            case 'POSITION_PLAYER':
                score += (player.g / 162) * 5.0  # Up to 5 point bonus for full season
            case 'STARTING_PITCHER' | 'RELIEF_PITCHER':
                ip = player.ip or 0
                max_ip = 175 if player.player_subtype == 'STARTING_PITCHER' else 70
                score += (ip / max_ip) * 5.0  # Up to 5 point bonus for full season
        
        # Bonuses for special achievements
        if player.card_data.stats:
            award_summary = player.card_data.stats.get('award_summary', '')
            
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
    
    def _redistribute_unused_slots(self, player_pool: List[ExploreDataRecord], team_allocations: Dict[str, TeamAllocation], selected_players: List[ExploreDataRecord]) -> List[ExploreDataRecord]:
        """Redistribute unused slots when teams don't have enough qualified players"""
        
        # Calculate how many slots are unused
        total_selected = len(selected_players)
        unused_slots = self.set_size - total_selected
        
        if unused_slots <= 0:
            return selected_players
        
        print(f"Redistributing {unused_slots} unused slots...")
        
        # Get all unselected players
        unselected_players = [p for p in player_pool if p not in selected_players]
        
        # Sort by priority score
        unselected_with_priority = []
        for player in unselected_players:
            priority_score = self._calculate_priority_score(player)
            unselected_with_priority.append((player, priority_score))

            if player.team_id == 'NYM':
                print(f"NYM | {player.name} | {priority_score:.2f}")
        
        unselected_with_priority.sort(key=lambda x: x[1], reverse=True)
        
        # Take the best remaining players
        additional_players = [p[0] for p in unselected_with_priority[:unused_slots]]
        selected_players.extend(additional_players)
        
        return selected_players
    
    def _print_set_summary(self, selected_players: List[ShowdownBotSetPlayer], team_allocations: Dict[str, TeamAllocation]):
        """Print summary of the generated set"""
        
        print("\n" + "="*60)
        print("SET SUMMARY")
        print("="*60)
        
        # Player type breakdown
        hitters = [p for p in selected_players if p.player_subtype == 'POSITION_PLAYER']
        starters = [p for p in selected_players if p.player_subtype == 'STARTING_PITCHER']
        relievers = [p for p in selected_players if p.player_subtype == 'RELIEF_PITCHER']
        
        print(f"Player Types:")
        print(f"  Hitters: {len(hitters)} ({len(hitters)/len(selected_players)*100:.1f}%)")
        print(f"  Starters: {len(starters)} ({len(starters)/len(selected_players)*100:.1f}%)")
        print(f"  Relievers: {len(relievers)} ({len(relievers)/len(selected_players)*100:.1f}%)")
        
        # Team breakdown
        print(f"\nTeam Distribution:")
        team_counts = {}
        for player in selected_players:
            team = player.team_id
            team_counts[team] = team_counts.get(team, 0) + 1
        
        for team in sorted(team_counts.keys()):
            team_allocation = team_allocations.get(team, None)
            target_count = team_allocation.target_count if team_allocation else 0
            actual = team_counts[team]
            print(f"  {team}: {actual} players (target: {target_count})")
        
        # Quality breakdown
        wars = [p.war for p in selected_players if p.war is not None]
        if wars:
            print(f"\nWAR Distribution:")
            print(f"  Average WAR: {statistics.mean(wars):.2f}")
            print(f"  Median WAR: {statistics.median(wars):.2f}")
            print(f"  Total WAR: {sum(wars):.1f}")
            print(f"  Range: {min(wars):.1f} to {max(wars):.1f}")

        # Position breakdown
        position_counts = {}
        for player in selected_players:
            position = player.primary_positions[0]
            position_counts[position] = position_counts.get(position, 0) + 1
        print(f"\nPosition Distribution:")
        for pos in sorted(position_counts.keys()):
            count = position_counts[pos]
            print(f"  {pos}: {count} players")

        print(f"Total Players Selected: {len(selected_players)} / {self.set_size}")

        # MISSING IMAGES
        top_players_missing_images = [p for p in selected_players if not p.image_match_type in (ImageMatchType.EXACT, ImageMatchType.TEAM_MATCH) and p.team_id == 'ATH']
        print(f"\nPlayers Missing Exact Images: {len(top_players_missing_images)}")
        top_players_missing_images.sort(key=lambda p: p.priority_score or 0, reverse=True)
        tbl_missing = PrettyTable()
        tbl_missing.field_names = ["Name", "Score", "WAR", "Pos", "G", "GS", "Team", "Img"]
        for player in top_players_missing_images[:20]:
            tbl_missing.add_row([player.name, f"{player.priority_score:.2f}" if player.priority_score is not None else "N/A", f"{player.war:.2f}" if player.war is not None else "N/A", player.primary_positions[0], player.g, player.gs or 0, player.team_id, player.image_match_type.value])
        print(tbl_missing)

        print("="*60 + "\n")