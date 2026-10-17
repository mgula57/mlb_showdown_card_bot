"""Offline checks for the league draft (`core/league/draft.py`).

No database, no network: `FakeLeagueDB` implements just the PostgresDB methods `LeagueDraft`
calls, in memory, over a synthetic card pool. Run as `python tests/test_league_draft.py`.

Under test:
  1. ORDER - snake order slots, rounds, upcoming picks.
  2. ROSTER FIT - which roster position a card takes, slack, starters only in the rotation.
  3. FULL DRAFTS - all-bot drafts finish with complete, legal rosters (with and without a points
     cap, and with a pool that has no catchers left).
  4. HUMAN PICKS - turn order, pool membership, already-drafted cards (incl. the same source card
     in two editions), roster-fit rejections, and a stale board raising DraftConflict.
  5. ROSTER MOVES - moving a drafted player to an open spot or swapping two, eligibility, not
     opening a need the remaining picks can't fill, and a pick checked against a pre-move roster.
"""

import os
import sys
from pathlib import Path
from random import Random

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from pydantic import ValidationError

from mlb_showdown_bot.core.card.team_builder.autofill import OFFENSE_POSITIONS
from mlb_showdown_bot.core.league import (
    DraftCard, DraftConflict, DraftError, DraftRoster, LeagueDraft, LeagueRosterMove, LeagueSettings, SnakeOrder,
)

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  PASS  {label}")
    else:
        failures.append(f"{label}{f' -- {detail}' if detail else ''}")
        print(f"  FAIL  {label}{f' -- {detail}' if detail else ''}")


EDITION_A, EDITION_B = 'edition-a', 'edition-b'


def card_row(card_id: str, position: str, points: float, edition: str = EDITION_A, source: str | None = None) -> dict:
    is_pitcher = position in ('STARTER', 'RELIEVER', 'CLOSER')
    return {
        'release_card_id': card_id,
        'source_card_id': source or f"src-{card_id}",
        'name': f"{position} {card_id}",
        'points': points,
        'player_type': 'PITCHER' if is_pitcher else 'HITTER',
        'positions_and_defense': {position: 0},
        'is_small_sample_size': False,
        'edition_id': edition,
    }


def build_pool(seed: int = 7, catchers: int = 12) -> list[dict]:
    rng = Random(seed)
    counts = {'C': catchers, '1B': 10, '2B': 10, '3B': 10, 'SS': 10, 'LF/RF': 16, 'CF': 10, 'OF': 4, 'IF': 4, 'DH': 4,
              'STARTER': 30, 'RELIEVER': 30, 'CLOSER': 8}
    rows = []
    for position, count in counts.items():
        for i in range(count):
            rows.append(card_row(f"{position}-{i}", position, rng.randint(40, 600)))
    return rows


class FakeLeagueDB:
    """In-memory stand-in for the PostgresDB league methods `LeagueDraft` uses."""

    def __init__(self, cards: list[dict], member_count: int, human_slots: tuple[int, ...] = ()):
        self.cards = {c['release_card_id']: c for c in cards}
        self.teams = [
            {'member_id': f"m{i}", 'team_id': f"t{i}", 'user_id': f"user{i}" if i in human_slots else None,
             'display_name': f"Team {i}", 'draft_slot': i}
            for i in range(member_count)
        ]
        self.picks: list[dict] = []
        self.roster: list[dict] = []
        self.status = 'drafting'
        self.reject_next_record = False

    def get_league_teams(self, season_id):
        return [dict(t) for t in self.teams]

    def get_league_roster_slots(self, season_id):
        return [dict(r) for r in self.roster]

    def get_league_draft_picks(self, season_id, include_card_data=False):
        return [dict(p) for p in self.picks]

    def _drafted(self, card: dict) -> bool:
        return any(p['release_card_id'] == card['release_card_id'] or p['source_card_id'] == card['source_card_id'] for p in self.picks)

    def fetch_league_card_pool(self, season_id, edition_ids):
        seen_sources, pool = set(), []
        for card in self.cards.values():
            if card['edition_id'] in edition_ids and not self._drafted(card) and card['source_card_id'] not in seen_sources:
                seen_sources.add(card['source_card_id'])
                pool.append(dict(card))
        return pool

    def fetch_league_draft_card(self, release_card_id, edition_ids):
        card = self.cards.get(release_card_id)
        if card is None or card['edition_id'] not in edition_ids:
            return None
        return dict(card)

    def _team_positions(self, team_id):
        member_id = next(t['member_id'] for t in self.teams if t['team_id'] == team_id)
        return sorted(r['roster_position'] for r in self.roster if r['member_id'] == member_id)

    def record_league_draft_pick(self, season_id, overall_pick, round, member_id, team_id, release_card_id,
                                 roster_position, is_auto, expected_positions=None):
        if self.reject_next_record:
            self.reject_next_record = False
            return False
        card = self.cards[release_card_id]
        if self.status != 'drafting' or len(self.picks) != overall_pick - 1 or self._drafted(card):
            return False
        if expected_positions is not None and self._team_positions(team_id) != sorted(expected_positions):
            return False
        self.picks.append({**card, 'overall_pick': overall_pick, 'round': round, 'member_id': member_id, 'is_auto': is_auto})
        self.roster.append({**card, 'member_id': member_id, 'card_id': release_card_id, 'roster_position': roster_position})
        return True

    def move_league_roster_slots(self, season_id, team_id, expected_positions, moves):
        if self._team_positions(team_id) != sorted(expected_positions):
            return False
        member_id = next(t['member_id'] for t in self.teams if t['team_id'] == team_id)
        for card_id, from_position, to_position in moves:
            slot = next((r for r in self.roster if r['member_id'] == member_id and r['card_id'] == card_id and r['roster_position'] == from_position), None)
            if slot is None:
                return False
            slot['roster_position'] = to_position
        return True

    def position_of(self, card_id):
        return next(r['roster_position'] for r in self.roster if r['card_id'] == card_id)

    def update_league_season_status(self, season_id, from_status, to_status):
        if self.status != from_status:
            return False
        self.status = to_status
        return True


def make_draft(db: FakeLeagueDB, settings: dict) -> LeagueDraft:
    league = {'league_id': 'L1', 'showdown_set': '2005', 'edition_ids': [EDITION_A, EDITION_B], 'settings': settings}
    return LeagueDraft(db, league, {'season_id': 'S1', 'status': 'drafting', 'seed': 1234})


def roster_problems(db: FakeLeagueDB, settings: LeagueSettings) -> list[str]:
    """Every way any team's finished roster breaks the league's roster rules."""
    problems = []
    for team in db.teams:
        slots = [r for r in db.roster if r['member_id'] == team['member_id']]
        positions = [r['roster_position'] for r in slots]
        if len(slots) != settings.roster_size:
            problems.append(f"{team['member_id']} has {len(slots)} cards, wants {settings.roster_size}")
        for pos in OFFENSE_POSITIONS:
            if positions.count(pos) != 1:
                problems.append(f"{team['member_id']} has {positions.count(pos)} at {pos}")
        for role in [f'SP{i}' for i in range(1, settings.num_starters + 1)]:
            if positions.count(role) != 1:
                problems.append(f"{team['member_id']} has {positions.count(role)} at {role}")
        if positions.count('RP') < settings.min_bullpen:
            problems.append(f"{team['member_id']} bullpen {positions.count('RP')} < {settings.min_bullpen}")
        if positions.count('BE') < settings.min_bench:
            problems.append(f"{team['member_id']} bench {positions.count('BE')} < {settings.min_bench}")
    drafted_sources = [p['source_card_id'] for p in db.picks]
    if len(drafted_sources) != len(set(drafted_sources)):
        problems.append("a card was drafted twice")
    return problems


def misplaced(db: FakeLeagueDB) -> list[str]:
    """Drafted cards sitting in a spot their card can't play."""
    bad = []
    for slot in db.roster:
        card = DraftCard.from_row(db.cards[slot['card_id']])
        pos = slot['roster_position']
        if pos in OFFENSE_POSITIONS and not card.can_play(pos):
            bad.append(f"{card.name} at {pos}")
        if pos.startswith('SP') and not card.is_starter:
            bad.append(f"{card.name} at {pos}")
        if pos == 'RP' and (not card.is_pitcher or card.is_starter):
            bad.append(f"{card.name} at RP")
    return bad


# ----------------------------------------------------------
print("ORDER")
order = SnakeOrder(team_count=4, rounds=3)
check("12 total picks", order.total_picks == 12)
check("round 1 runs slot 0 to 3", [order.slot_for_pick(p) for p in range(1, 5)] == [0, 1, 2, 3])
check("round 2 runs slot 3 to 0", [order.slot_for_pick(p) for p in range(5, 9)] == [3, 2, 1, 0])
check("pick 9 starts round 3 at slot 0", order.round_for_pick(9) == 3 and order.slot_for_pick(9) == 0)
check("upcoming stops at the last pick", order.upcoming(11, 5) == [(11, 2), (12, 3)])

# ----------------------------------------------------------
print("\nSETTINGS")
try:
    LeagueSettings(roster_size=20, min_bench=4, min_bullpen=5, num_starters=5)
    check("roster smaller than the minimums is rejected", False)
except ValidationError:
    check("roster smaller than the minimums is rejected", True)
check("default settings fit", LeagueSettings().hard_minimum == 20)

# ----------------------------------------------------------
print("\nROSTER FIT")
settings = LeagueSettings(roster_size=12, min_bench=0, min_bullpen=1, num_starters=2)
roster = DraftRoster(settings=settings)
ss_2b = DraftCard.from_row({**card_row('x', 'SS', 300), 'positions_and_defense': {'SS': 4, '2B': 3}})
check("SS/2B card fills SS first", roster.slot_for(ss_2b) == 'SS')
roster.positions.append('SS')
check("then fills 2B", roster.slot_for(ss_2b) == '2B')
infielder = DraftCard.from_row(card_row('if', 'IF', 200))
check("IF card can play 1B", infielder.can_play('1B') and not infielder.can_play('C'))
outfielder = DraftCard.from_row(card_row('of', 'OF', 200))
check("OF card can play CF and LF", outfielder.can_play('CF') and outfielder.can_play('LF'))
starter = DraftCard.from_row(card_row('sp', 'STARTER', 300))
roster.positions += ['SP1', 'SP2']
check("starter is rejected once the rotation is full", roster.slot_for(starter) is None)
check("rejection says the rotation is full", roster.rejection_reason(starter) == "Your rotation is full.")
reliever = DraftCard.from_row(card_row('rp', 'RELIEVER', 100))
check("reliever fills the bullpen minimum", roster.slot_for(reliever) == 'RP')
check("no slack in a 12-card roster with 12 hard needs", roster.slack == 0)
roster.positions.append('RP')
check("a second reliever has no room (needs remain, no slack)", roster.slot_for(reliever) is None)
dh_only = DraftCard.from_row(card_row('dh', 'DH', 250))
check("DH-only hitter goes to DH", roster.slot_for(dh_only) == 'DH')

print("\nROSTER POINTS")
points_roster = DraftRoster(settings=settings)
two_way_hitter = DraftCard.from_row({**card_row('ohtani-h', 'DH', 400), 'bref_id': 'ohtansh01'})
two_way_pitcher = DraftCard.from_row({**card_row('ohtani-p', 'STARTER', 300), 'bref_id': 'ohtansh01'})
points_roster.add('DH', two_way_hitter)
points_roster.add('BE', DraftCard.from_row(card_row('bench', 'SS', 100)))
check("a bench card counts 1/5 of its points", points_roster.points == 420, str(points_roster.points))
points_roster.add('SP1', two_way_pitcher)
check("a two-way player's pitching card counts half", points_roster.points == 570, str(points_roster.points))
check("the pitching card is discounted even when drafted first",
      DraftRoster(settings=settings, positions=['SP1', 'DH'], cards=[two_way_pitcher, two_way_hitter]).points == 550)
check("a two-way player's pitching card alone isn't discounted",
      DraftRoster(settings=settings, positions=['SP1'], cards=[two_way_pitcher]).points == 300)
same_side = DraftCard.from_row({**card_row('ohtani-h2', 'DH', 400), 'bref_id': 'ohtansh01'})
check("two hitting cards of one player aren't discounted",
      DraftRoster(settings=settings, positions=['DH', 'BE'], cards=[two_way_hitter, same_side]).points == 480)

# ----------------------------------------------------------
print("\nFULL ALL-BOT DRAFT")
default_settings = LeagueSettings()
db = FakeLeagueDB(build_pool(), member_count=4)
draft = make_draft(db, default_settings.model_dump())
made = draft.run_bot_picks()
check("every pick made", len(made) == 4 * default_settings.roster_size, f"{len(made)} picks")
check("season moved to setup", db.status == 'setup')
problems = roster_problems(db, default_settings)
check("every roster is complete and legal", not problems, '; '.join(problems[:5]))
bad = misplaced(db)
check("no card out of position", not bad, ', '.join(bad[:5]))
check("bot picks are all auto", all(p['is_auto'] for p in db.picks))
first_round_points = [db.cards[p['release_card_id']]['points'] for p in db.picks[:4]]
check("bots take high-value cards early", min(first_round_points) >= 450, str(first_round_points))

print("\nPOINTS CAP")
capped = LeagueSettings(pts_cap=7500)  # 4 ROSTERS NEED >= ~4,700 EACH FROM THIS POOL
db = FakeLeagueDB(build_pool(seed=11), member_count=4)
capped_draft = make_draft(db, capped.model_dump())
capped_draft.run_bot_picks()
team_points = {member_id: round(roster.points) for member_id, roster in capped_draft.board().rosters.items()}
check("draft finishes under a cap", db.status == 'setup')
check("every team is at or under the cap", all(points <= 7500 for points in team_points.values()), str(team_points))
check("rosters still complete under a cap", not roster_problems(db, capped))

tight = LeagueSettings(roster_size=12, min_bench=0, min_bullpen=1, num_starters=2, pts_cap=900)
db = FakeLeagueDB(build_pool(seed=11), member_count=2, human_slots=(0,))
priciest = max((c for c in db.cards.values() if c['player_type'] == 'HITTER'), key=lambda c: c['points'])
try:
    make_draft(db, tight.model_dump()).make_pick('m0', False, priciest['release_card_id'])
    check("human pick that blows a tight cap is rejected", False, f"{priciest['points']} pts accepted")
except DraftError as e:
    check("human pick that blows a tight cap is rejected", 'cap' in str(e), str(e))

print("\nTHIN POOL")
db = FakeLeagueDB(build_pool(seed=3, catchers=2), member_count=4)
make_draft(db, default_settings.model_dump()).run_bot_picks()
check("draft finishes with only 2 catchers for 4 teams", db.status == 'setup')
catchers_out_of_position = [m for m in misplaced(db) if m.endswith(' at C')]
check("the 2 teams without a catcher play someone out of position at C", len(catchers_out_of_position) == 2, str(catchers_out_of_position))

# ----------------------------------------------------------
print("\nHUMAN PICKS")
pool = build_pool(seed=5)
pool.append(card_row('dupe-b', 'SS', 500, edition=EDITION_B, source='src-SS-0'))  # SAME CARD AS SS-0, OTHER EDITION
pool.append(card_row('other-ed', 'SS', 500, edition='edition-not-in-league'))
db = FakeLeagueDB(pool, member_count=3, human_slots=(0, 1))
draft = make_draft(db, default_settings.model_dump())


def raises(fn, exc) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


check("member off the clock can't pick", raises(lambda: draft.make_pick('m1', False, 'C-0'), DraftError))
check("card outside the league's editions is rejected", raises(lambda: draft.make_pick('m0', False, 'other-ed'), DraftError))
pick = draft.make_pick('m0', False, 'SS-0')
check("on-clock member picks SS-0 into SS", pick['roster_position'] == 'SS' and pick['overall_pick'] == 1)
check("same card from another edition is already drafted", raises(lambda: draft.make_pick('m1', False, 'dupe-b'), DraftError))
check("commissioner can pick for the team on the clock", draft.make_pick('m0', True, 'C-0')['member_id'] == 'm1')
check("bot seat makes picks 3 and 4 (snake turn), then hands back to m1", len(draft.run_bot_picks()) == 2 and draft.board().on_the_clock['member_id'] == 'm1')

db.reject_next_record = True
check("stale board raises DraftConflict", raises(lambda: draft.make_pick('m2', True, 'C-1'), DraftConflict))
check("the retry goes through", draft.make_pick('m2', True, 'C-1')['overall_pick'] == 5)

starters_db = FakeLeagueDB(build_pool(seed=9), member_count=2, human_slots=(0,))
starters_draft = make_draft(starters_db, LeagueSettings(roster_size=12, min_bench=0, min_bullpen=1, num_starters=2).model_dump())
for pick_number in range(1, 5):  # SNAKE: m0, m1, m1, m0 - m0 TAKES A STARTER AT PICKS 1 AND 4
    team = starters_draft.board().on_the_clock
    starters_draft.make_pick(team['member_id'], True, f"STARTER-{pick_number}" if team['member_id'] == 'm0' else None)
check("m0 is back on the clock at pick 5", starters_draft.board().on_the_clock['member_id'] == 'm0')
check("third starter for a 2-man rotation is rejected", raises(lambda: starters_draft.make_pick('m0', False, 'STARTER-20'), DraftError))
check("auto-pick for a human seat fills a need", starters_draft.make_pick('m0', True, None)['is_auto'])

# CHOSEN ROSTER POSITION
chosen_db = FakeLeagueDB(build_pool(seed=11), member_count=2, human_slots=(0, 1))
chosen_draft = make_draft(chosen_db, default_settings.model_dump())
fresh = DraftRoster(settings=default_settings)
ss_card = DraftCard.from_row(card_row('x', 'SS', 100))
check("legal slots for an SS: SS, DH, bench", fresh.legal_slots(ss_card) == ['SS', 'DH', 'BE'], str(fresh.legal_slots(ss_card)))
check("legal slots for an IF include every infield spot", {'1B', '2B', '3B', 'SS'} <= set(fresh.legal_slots(DraftCard.from_row(card_row('y', 'IF', 100)))))
check("a hitter can't be drafted at a spot it can't play", raises(lambda: chosen_draft.make_pick('m0', False, 'SS-0', 'C'), DraftError))
check("a hitter can be drafted at DH by choice", chosen_draft.make_pick('m0', False, 'SS-0', 'DH')['roster_position'] == 'DH')
check("a hitter can be drafted to the bench by choice", chosen_draft.make_pick('m1', False, 'C-0', 'BE')['roster_position'] == 'BE')
check("a starter can't be drafted into the bullpen", raises(lambda: chosen_draft.make_pick('m1', False, 'STARTER-0', 'RP'), DraftError))
check("a starter can take a chosen rotation role", chosen_draft.make_pick('m1', False, 'STARTER-0', 'SP2')['roster_position'] == 'SP2')


# ----------------------------------------------------------
print("\nROSTER MOVES")

move_settings = LeagueSettings(roster_size=16, min_bench=1, min_bullpen=1, num_starters=2)
move_db = FakeLeagueDB(build_pool(seed=13), member_count=2, human_slots=(0, 1))
move_draft = make_draft(move_db, move_settings.model_dump())
season = {'season_id': 'S1', 'status': 'drafting'}
move_league = {'league_id': 'L1', 'edition_ids': [EDITION_A, EDITION_B], 'settings': move_settings.model_dump()}
mover = LeagueRosterMove(move_db, move_league, season, move_db.teams[0])
# m0 drafts at picks 1, 4, 5: an IF at 2B, a SS at SS, a starter at SP1
move_draft.make_pick('m0', False, 'IF-0', '2B')
move_draft.make_pick('m1', False, 'C-0')
move_draft.make_pick('m1', False, 'C-1')
move_draft.make_pick('m0', False, 'SS-0', 'SS')
move_draft.make_pick('m0', False, 'STARTER-0', 'SP1')

mover.move('IF-0', '3B')
check("move into an open spot it can play", move_db.position_of('IF-0') == '3B')
check("a SS can't move to C", raises(lambda: mover.move('SS-0', 'C'), DraftError))
check("can't move into a filled spot without swapping", raises(lambda: mover.move('IF-0', 'SS'), DraftConflict))
check("swap is rejected when the other player can't play the mover's spot", raises(lambda: mover.move('IF-0', 'SS', swap_with_card_id='SS-0'), DraftError))
check("a hitter and a pitcher can't swap", raises(lambda: mover.move('SS-0', 'SP1', swap_with_card_id='STARTER-0'), DraftError))
mover.move('IF-0', 'DH')
mover.move('IF-0', 'SS', swap_with_card_id='SS-0')
check("swap moves the IF to SS", move_db.position_of('IF-0') == 'SS')
check("swap moves the SS to DH", move_db.position_of('SS-0') == 'DH', move_db.position_of('SS-0'))
mover.move('STARTER-0', 'SP2')
check("a starter moves to another rotation role", move_db.position_of('STARTER-0') == 'SP2')
check("a starter can't move into the bullpen", raises(lambda: mover.move('STARTER-0', 'RP'), DraftError))
mover.move('SS-0', 'BE')
check("a hitter moves to the bench while there are picks to spare", move_db.position_of('SS-0') == 'BE')
check("another team's player can't be moved", raises(lambda: mover.move('C-0', 'DH'), DraftError))

move_draft.make_pick(None, True, 'C-2')  # PICKS 6 AND 7 ARE m1'S, THEN m0 IS UP AGAIN
move_draft.make_pick(None, True, 'C-3')
stale = move_draft.board()
mover.move('SS-0', 'DH')
check("a pick checked against a roster that moved since is a conflict",
      raises(lambda: move_draft._record(stale, stale.on_the_clock, DraftCard.from_row(move_db.cards['C-5']), 'C', is_auto=False), DraftConflict))
check("the pick goes through on a fresh board", move_draft.make_pick('m0', False, 'C-5', 'C')['roster_position'] == 'C')

# A FULL ROSTER CAN SWAP BUT NOT OPEN A SPOT
full_db = FakeLeagueDB(build_pool(seed=17), member_count=2)
full_draft = make_draft(full_db, move_settings.model_dump())
full_draft.run_bot_picks()
full_season = {'season_id': 'S1', 'status': 'setup'}
full_mover = LeagueRosterMove(full_db, move_league, full_season, full_db.teams[0])
m0_slots = [r for r in full_db.roster if r['member_id'] == 'm0']
dh = next(r['card_id'] for r in m0_slots if r['roster_position'] == 'DH')
check("a full roster can't open a lineup spot", raises(lambda: full_mover.move(dh, 'BE'), DraftError))
bench = next((r['card_id'] for r in m0_slots if r['roster_position'] == 'BE'), None)
if bench:
    full_mover.move(bench, 'DH', swap_with_card_id=dh)
    check("a full roster can swap a bench bat in at DH", full_db.position_of(bench) == 'DH' and full_db.position_of(dh) == 'BE')
check("no moves once the season is over",
      raises(lambda: LeagueRosterMove(full_db, move_league, {'season_id': 'S1', 'status': 'complete'}, full_db.teams[0]).move(dh, 'BE'), DraftError))

# ----------------------------------------------------------

if failures:
    print(f"\n{len(failures)} CHECK(S) FAILED:")
    for line in failures:
        print(f"  - {line}")
    sys.exit(1)
print("\nAll checks passed.")
