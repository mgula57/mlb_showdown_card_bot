import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import type { DraftMyRoster, DraftPick, DraftState, LeagueSettings, LeagueTeam } from '../../../api/leagues';
import { benchBullpenSlotCounts, effectiveBenchBullpenMinimums, getEligiblePositions } from '../../../domain/roster';
import { CardSource } from '../../../types/cardSource';
import type { DepthChartTeam } from '../../team_builder/DepthChartPanel';
import type { FieldViewRosterData } from '../../team_builder/FieldView';

export const LINEUP_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'];
const BULLPEN_POSITIONS = ['RP', 'CL'];

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
    const bullpenCount = mine.filter(pick => BULLPEN_POSITIONS.includes(pick.roster_position ?? '')).length;
    const benchCount = mine.filter(pick => pick.roster_position === 'BE').length;
    const rotationCount = pitcherPicks.length - bullpenCount;

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
        bench_pts_multiplier: 1,
    };
    return {
        depthChart,
        picksMade: mine.length,
        /** Spots that still have to be filled (lineup, rotation, bench/bullpen minimums). */
        required: (LINEUP_POSITIONS.length - lineupPicks.length) + (settings.num_starters - rotationCount)
            + Math.max(0, settings.min_bullpen - bullpenCount)
            + Math.max(0, settings.min_bench - benchCount),
        points: mine.reduce((total, pick) => total + (pick.points ?? 0), 0),
    };
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
