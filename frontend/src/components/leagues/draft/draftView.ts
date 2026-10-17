import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import type { DraftMyRoster, DraftPick, DraftState, LeagueSettings, LeagueTeam, LuxuryTax } from '../../../api/leagues';
import { TWO_WAY_PTS_MULTIPLIER, benchBullpenSlotCounts, effectiveBenchBullpenMinimums, getEligiblePositions } from '../../../domain/roster';
import { CardSource } from '../../../types/cardSource';
import type { DepthChartTeam } from '../../team_builder/DepthChartPanel';
import type { FieldViewRosterData } from '../../team_builder/FieldView';

export const LINEUP_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'];
const BULLPEN_POSITIONS = ['RP', 'CL'];
// What a drafted card counts for toward its team's points. Mirrors `DraftRoster` in
// mlb_showdown_bot/core/league/draft.py - keep the two in sync.
export const DRAFT_BENCH_PTS_MULTIPLIER = 0.2;

type RosterPointsSlot = { points: number; roster_position?: string; player_type?: string | null; bref_id?: string | null };

/** A roster's points: a bench card counts 1/5, and a two-way player's pitching card counts half
 *  when the roster also has his hitting card. Mirrors `DraftRoster.points`. */
export function rosterPoints(slots: RosterPointsSlot[]): number {
    const isPitcher = (slot: RosterPointsSlot) => slot.player_type?.toUpperCase() === 'PITCHER';
    const hitterIds = new Set(slots.filter(slot => !isPitcher(slot) && slot.bref_id).map(slot => slot.bref_id));
    const total = slots.reduce((sum, slot) => {
        const isTwoWayPitcher = isPitcher(slot) && hitterIds.has(slot.bref_id);
        const benchMultiplier = slot.roster_position === 'BE' ? DRAFT_BENCH_PTS_MULTIPLIER : 1;
        return sum + (slot.points ?? 0) * benchMultiplier * (isTwoWayPitcher ? TWO_WAY_PTS_MULTIPLIER : 1);
    }, 0);
    return Math.round(total);
}

/** What a team with `points` owes: the buy-in, plus a tax on every point over the cap (exactly
 *  at the cap is untaxed). Linear adds $1 per full 10 points over; exponential
 *  starts at $13 one point over and doubles about every 173 points. Whole dollars. */
export function luxuryTaxCost(points: number, cap: number, tax: LuxuryTax): { total: number; tax: number } {
    const over = points - cap;
    if (over <= 0) return { total: tax.buy_in, tax: 0 };
    const amount = tax.type === 'linear' ? Math.floor(over / 10) : Math.trunc(13.5 * Math.exp(over / 250));
    return { total: tax.buy_in + amount, tax: amount };
}

/** Lookups every draft view needs, derived once from the polled draft state. */
export function draftView(draft: DraftState, myMemberId: string | null) {
    const teamsByMember = new Map(draft.teams.map(team => [team.member_id, team]));
    const pickAt = new Map(draft.picks.map(pick => [`${pick.round}:${pick.member_id}`, pick]));
    const onTheClock = draft.on_the_clock_member_id ? teamsByMember.get(draft.on_the_clock_member_id) ?? null : null;
    return {
        teams: [...draft.teams].sort((a, b) => (a.draft_slot ?? 0) - (b.draft_slot ?? 0)),
        teamsByMember,
        /** The pick a team made in a round, if it has. */
        pickFor: (round: number, memberId: string) => pickAt.get(`${round}:${memberId}`) ?? null,
        onTheClock,
        isMyTurn: !!myMemberId && draft.on_the_clock_member_id === myMemberId,
        lastPick: draft.picks.length ? draft.picks[draft.picks.length - 1] : null,
        isComplete: draft.next_pick === null,
        draftedIds: draft.picks.map(pick => pick.release_card_id),
    };
}

export type DraftView = ReturnType<typeof draftView>;

/** One team's roster as drafted so far, shaped for `DepthChartPanel` (release card ids as card
 *  ids), plus how many required spots are still open. */
export function teamRoster(picks: DraftPick[], team: LeagueTeam, settings: LeagueSettings) {
    const mine = picks.filter(pick => pick.member_id === team.member_id);
    const ref = (pick: DraftPick) => ({ card_id: pick.release_card_id, card_source: CardSource.RELEASE });
    const lineupPicks = mine.filter(pick => LINEUP_POSITIONS.includes(pick.roster_position ?? ''));
    const pitcherPicks = mine.filter(pick => pick.roster_position?.startsWith('SP') || BULLPEN_POSITIONS.includes(pick.roster_position ?? ''));

    const depthChart: DepthChartTeam = {
        roster: mine.map(pick => ({ ...ref(pick), roster_position: pick.roster_position ?? 'BE', draft_order: pick.overall_pick, pick_source: 'DRAFT' })),
        lineups: [{
            name: 'Default',
            index: 0,
            slots: lineupPicks.map(pick => ({ ...ref(pick), field_position: pick.roster_position!, batting_order: LINEUP_POSITIONS.indexOf(pick.roster_position!) + 1 })),
        }],
        rotation: pitcherPicks.map(pick => ({ ...ref(pick), role: pick.roster_position! })),
        num_starters: settings.num_starters,
        roster_size: settings.roster_size,
        min_bench: settings.min_bench,
        min_bullpen: settings.min_bullpen,
        bench_pts_multiplier: DRAFT_BENCH_PTS_MULTIPLIER,
        two_way_pts_multiplier: TWO_WAY_PTS_MULTIPLIER,
    };
    return {
        depthChart,
        picksMade: mine.length,
        /** Spots that still have to be filled (lineup, rotation, bench/bullpen minimums). */
        required: requiredSpots(mine.map(pick => pick.roster_position ?? ''), settings),
        points: rosterPoints(mine),
    };
}

/** Spots a roster holding `positions` still has to fill: the lineup, the rotation, and the
 *  bench / bullpen minimums. Mirrors `DraftRoster.hard_needs` in mlb_showdown_bot/core/league/draft.py. */
export function requiredSpots(positions: string[], settings: LeagueSettings): number {
    const count = (matches: (position: string) => boolean) => positions.filter(matches).length;
    const rotationRoles = Array.from({ length: settings.num_starters }, (_, i) => `SP${i + 1}`);
    return LINEUP_POSITIONS.filter(position => !positions.includes(position)).length
        + rotationRoles.filter(role => !positions.includes(role)).length
        + Math.max(0, settings.min_bullpen - count(position => BULLPEN_POSITIONS.includes(position)))
        + Math.max(0, settings.min_bench - count(position => position === 'BE'));
}

/** Whether moving players so the roster holds `after` (from `before`) still leaves enough picks
 *  to fill every spot - or at least no fewer than before. Mirrors `LeagueRosterMove`. */
export function keepsRosterFillable(before: string[], after: string[], settings: LeagueSettings): boolean {
    const slack = (positions: string[]) => settings.roster_size - positions.length - requiredSpots(positions, settings);
    return slack(after) >= 0 || slack(after) >= slack(before);
}

/** A drafted roster as `FieldView`'s roster data, with the same bench / bullpen row counts the
 *  depth chart works out so both views show the open spots. */
export function fieldRosterData(depthChart: DepthChartTeam): FieldViewRosterData {
    const lineup = depthChart.lineups[0];
    const bucketMins = effectiveBenchBullpenMinimums(depthChart);
    const benchCount = depthChart.roster.filter(slot => slot.roster_position === 'BE').length;
    const bullpenCount = depthChart.rotation.filter(slot => !slot.role.startsWith('SP')).length;
    return {
        roster: depthChart.roster,
        rotation: depthChart.rotation,
        benchPtsMultiplier: depthChart.bench_pts_multiplier,
        twoWayPtsMultiplier: depthChart.two_way_pts_multiplier,
        minBench: bucketMins.bench,
        minBullpen: bucketMins.bullpen,
        maxRotation: depthChart.num_starters,
        draftSlots: benchBullpenSlotCounts({
            rosterSize: depthChart.roster_size,
            rosterCount: depthChart.roster.length,
            lineup: { filled: lineup.slots.length, target: 9 },
            rotation: { filled: depthChart.rotation.length - bullpenCount, target: depthChart.num_starters },
            bench: { filled: benchCount, target: bucketMins.bench },
            bullpen: { filled: bullpenCount, target: bucketMins.bullpen },
            benchMin: depthChart.min_bench,
            bullpenMin: depthChart.min_bullpen,
        }),
    };
}

/** Roster positions the drafter may choose for `card`: an open spot it can play, or a bench /
 *  bullpen spot while under the minimum or with picks to spare. Mirrors
 *  `DraftRoster.legal_slots` in mlb_showdown_bot/core/league/draft.py - keep the two in sync. */
export function legalDraftSlots(card: CardDatabaseRecord, roster: DraftMyRoster, settings: LeagueSettings): string[] {
    if (roster.picks_left <= 0) return [];
    const hasSlack = roster.slack > 0;
    return getEligiblePositions(card, settings.num_starters).filter(position => {
        if (position === 'BE') return roster.bench_count < settings.min_bench || hasSlack;
        if (position === 'RP') return roster.bullpen_count < settings.min_bullpen || hasSlack;
        return roster.open_field_positions.includes(position) || roster.open_rotation_roles.includes(position);
    });
}

/** "Aaron Judge" -> "A. Judge", for tight board cells. */
export function shortName(name: string): string {
    const parts = name.trim().split(/\s+/);
    if (parts.length < 2) return name;
    return `${parts[0][0]}. ${parts.slice(1).join(' ')}`;
}

/** The roster position a pick shows on the board - its slot, or the card's own positions. */
export function pickPositionLabel(pick: DraftPick): string {
    if (pick.roster_position) return pick.roster_position;
    return Object.keys(pick.positions_and_defense ?? {}).join('/');
}
