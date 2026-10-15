import type { DraftPick, DraftState, LeagueSettings, LeagueTeam } from '../../../api/leagues';

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

/** One team's roster as drafted so far, grouped the way the team panel shows it. */
export function teamRoster(picks: DraftPick[], team: LeagueTeam, settings: LeagueSettings) {
    const mine = picks.filter(pick => pick.member_id === team.member_id);
    const at = (position: string) => mine.find(pick => pick.roster_position === position) ?? null;
    const rotationRoles = Array.from({ length: settings.num_starters }, (_, i) => `SP${i + 1}`);
    const bullpen = mine.filter(pick => BULLPEN_POSITIONS.includes(pick.roster_position ?? ''));
    const bench = mine.filter(pick => pick.roster_position === 'BE');

    const openLineup = LINEUP_POSITIONS.filter(pos => !at(pos)).length;
    const openRotation = rotationRoles.filter(role => !at(role)).length;
    const required = openLineup + openRotation
        + Math.max(0, settings.min_bullpen - bullpen.length)
        + Math.max(0, settings.min_bench - bench.length);
    return {
        lineup: LINEUP_POSITIONS.map(position => ({ position, pick: at(position) })),
        rotation: rotationRoles.map(position => ({ position, pick: at(position) })),
        bullpen,
        bench,
        picksMade: mine.length,
        picksLeft: settings.roster_size - mine.length,
        /** Spots that still have to be filled (lineup, rotation, bench/bullpen minimums). */
        required,
        points: mine.reduce((total, pick) => total + (pick.points ?? 0), 0),
    };
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
