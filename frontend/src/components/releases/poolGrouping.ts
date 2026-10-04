import type { ReleaseCard } from '../../api/releases';
import { FRANCHISE_CODE, PARENT_POSITION_ORDER, parentPositionGroup } from './SummaryCharts';

export type PoolGroupBy = 'none' | 'team' | 'league' | 'position' | 'type' | 'hand' | 'year' | 'points' | 'command' | 'speed' | 'ip';
export type PoolSortBy = 'set_number' | 'points' | 'name' | 'team' | 'position' | 'year' | 'command' | 'speed' | 'ip'
    | 'obp' | 'ops' | 'ops_plus' | 'era' | 'whip';
export type PoolSortDirection = 'asc' | 'desc';

export type PoolGroup = { key: string; label: string; cards: ReleaseCard[] };

export const POOL_GROUP_OPTIONS: { label: string; value: PoolGroupBy }[] = [
    { label: 'None', value: 'none' },
    { label: 'Team', value: 'team' },
    { label: 'League', value: 'league' },
    { label: 'Position', value: 'position' },
    { label: 'Player Type', value: 'type' },
    { label: 'Handedness', value: 'hand' },
    { label: 'Year', value: 'year' },
    { label: 'PTS Tier', value: 'points' },
    { label: 'Command', value: 'command' },
    { label: 'Speed', value: 'speed' },
    { label: 'IP', value: 'ip' },
];

export const POOL_SORT_OPTIONS: { label: string; value: PoolSortBy }[] = [
    { label: 'Set Number', value: 'set_number' },
    { label: 'PTS', value: 'points' },
    { label: 'Name', value: 'name' },
    { label: 'Team', value: 'team' },
    { label: 'Position', value: 'position' },
    { label: 'Year', value: 'year' },
    { label: 'Command', value: 'command' },
    { label: 'Speed', value: 'speed' },
    { label: 'IP', value: 'ip' },
    { label: 'Real OBP', value: 'obp' },
    { label: 'Real OPS', value: 'ops' },
    { label: 'Real OPS+', value: 'ops_plus' },
    { label: 'Real ERA', value: 'era' },
    { label: 'Real WHIP', value: 'whip' },
];

/** The direction that reads most naturally for each sort — best first (big numbers, except ERA/WHIP). */
export const POOL_SORT_DEFAULT_DIRECTION: Record<PoolSortBy, PoolSortDirection> = {
    set_number: 'asc',
    points: 'desc',
    name: 'asc',
    team: 'asc',
    position: 'asc',
    year: 'desc',
    command: 'desc',
    speed: 'desc',
    ip: 'desc',
    obp: 'desc',
    ops: 'desc',
    ops_plus: 'desc',
    era: 'asc',
    whip: 'asc',
};

// Scorecard order for hitters, then pitchers, so position groups read like a lineup card.
const POSITION_ORDER = ['C', 'CA', '1B', '2B', '3B', 'SS', 'IF', 'LF', 'LF/RF', 'CF', 'RF', 'OF', 'DH', 'STARTER', 'RELIEVER', 'CLOSER'];

function primaryPosition(card: ReleaseCard): string {
    return card.card_snapshot.positions_list?.[0] ?? card.card_snapshot.player_type ?? 'Unknown';
}

function franchiseTeam(card: ReleaseCard): string {
    const team = card.card_snapshot.team;
    return team ? (FRANCHISE_CODE[team] ?? team) : 'No Team';
}

/** Hitters (On-Base) always rank ahead of pitchers (Control) — the two scales aren't comparable. */
function commandSide(card: ReleaseCard): number {
    return card.card_snapshot.is_pitcher ? 1 : 0;
}

const ONBASE_LABEL = 'Onbase';
const CONTROL_LABEL = 'Control';

function commandGroupLabel(card: ReleaseCard): string {
    return `${card.card_snapshot.is_pitcher ? CONTROL_LABEL : ONBASE_LABEL} ${card.card_snapshot.command ?? 0}`;
}

/** Orders "Onbase N" / "Control N" keys: Onbase before Control, then command descending. */
function compareCommandGroupKeys(a: string, b: string): number {
    const parse = (key: string) => {
        const [side, command] = key.split(' ');
        return { side: side === CONTROL_LABEL ? 1 : 0, command: Number(command) };
    };
    const left = parse(a);
    const right = parse(b);
    return left.side - right.side || right.command - left.command;
}

type GroupKeyer = { keyFn: (card: ReleaseCard) => string; compareKeys: (a: string, b: string) => number };

/** Stats that only apply to one side (Speed/OBP/OPS to hitters, IP/ERA/WHIP to pitchers); `null` for
 * cards the stat doesn't apply to, or whose real-life stat is missing from the snapshot. */
type SideStat = { value: (card: ReleaseCard) => number | null; label: string; missingLabel: string };

type SideStatKey = 'speed' | 'ip' | 'obp' | 'ops' | 'ops_plus' | 'era' | 'whip';

const hitterStat = (label: string, value: (card: ReleaseCard) => number | null | undefined): SideStat =>
    ({ value: card => card.card_snapshot.is_pitcher ? null : (value(card) ?? null), label, missingLabel: 'Pitchers' });
const pitcherStat = (label: string, value: (card: ReleaseCard) => number | null | undefined): SideStat =>
    ({ value: card => card.card_snapshot.is_pitcher ? (value(card) ?? null) : null, label, missingLabel: 'Hitters' });

const SIDE_STATS: Record<SideStatKey, SideStat> = {
    speed: hitterStat('Speed', card => card.card_snapshot.speed ?? 0),
    ip: pitcherStat('IP', card => card.card_snapshot.ip ?? 0),
    obp: hitterStat('OBP', card => card.card_snapshot.real_onbase_perc),
    ops: hitterStat('OPS', card => card.card_snapshot.real_onbase_plus_slugging),
    ops_plus: hitterStat('OPS+', card => card.card_snapshot.real_onbase_plus_slugging_plus),
    era: pitcherStat('ERA', card => card.card_snapshot.real_earned_run_avg),
    whip: pitcherStat('WHIP', card => card.card_snapshot.real_whip),
};

function isSideStat(key: PoolSortBy): key is SideStatKey {
    return key in SIDE_STATS;
}

/** 0 when the card has the stat, 1 when it doesn't — cards without it trail in either direction. */
function sideStatMissing(card: ReleaseCard, stat: SideStat): number {
    return stat.value(card) === null ? 1 : 0;
}

/** Groups "Speed N" / "IP N" by value descending, with the not-applicable group last. */
function sideStatGrouper(stat: SideStat): GroupKeyer {
    return {
        keyFn: card => {
            const value = stat.value(card);
            return value === null ? stat.missingLabel : `${stat.label} ${value}`;
        },
        compareKeys: (a, b) => {
            const parse = (key: string) => key === stat.missingLabel ? -Infinity : Number(key.split(' ')[1]);
            return parse(b) - parse(a);
        },
    };
}

/** First year of the card's year string ("2001", "2000-2004", "CAREER" → 0). */
function cardYear(card: ReleaseCard): number {
    const year = parseInt(String(card.card_snapshot.year ?? ''), 10);
    return Number.isNaN(year) ? 0 : year;
}

const PTS_TIER_SIZE = 100;

function pointsTierLabel(card: ReleaseCard): string {
    const floor = Math.floor((card.card_snapshot.points ?? 0) / PTS_TIER_SIZE) * PTS_TIER_SIZE;
    return `${floor}-${floor + PTS_TIER_SIZE - 1} PTS`;
}

/** "Bats L/R/S" for hitters, "LHP/RHP" for pitchers. Hand is stored as "Left"/"Right"/"Both" or a single letter. */
function handLabel(card: ReleaseCard): string {
    const letter = (card.card_snapshot.hand ?? '').trim().charAt(0).toUpperCase();
    if (!letter) return 'Unknown';
    if (card.card_snapshot.is_pitcher) return `${letter}HP`;
    return `Bats ${letter === 'B' ? 'S' : letter}`;
}

const HAND_ORDER = ['Bats R', 'Bats L', 'Bats S', 'RHP', 'LHP', 'Unknown'];

/** Orders group keys by their leading number ("2001", "300-399 PTS") descending; non-numeric keys ("Unknown") last. */
function descendingNumericKeys(a: string, b: string): number {
    const parse = (key: string) => { const n = parseInt(key, 10); return Number.isNaN(n) ? -Infinity : n; };
    return parse(b) - parse(a);
}

function lastName(name: string | undefined): string {
    const parts = (name ?? '').trim().split(/\s+/);
    const last = parts[parts.length - 1]?.replace('.', '').toUpperCase();
    return parts.length > 1 && ['JR', 'SR', 'II', 'III', 'IV', 'V'].includes(last) ? parts[parts.length - 2] : (parts[parts.length - 1] ?? '');
}

function compareBySort(a: ReleaseCard, b: ReleaseCard, sortBy: PoolSortBy): number {
    switch (sortBy) {
        case 'points': return (a.card_snapshot.points ?? 0) - (b.card_snapshot.points ?? 0);
        case 'command': return (a.card_snapshot.command ?? 0) - (b.card_snapshot.command ?? 0);
        case 'year': return cardYear(a) - cardYear(b);
        case 'speed':
        case 'ip':
        case 'obp':
        case 'ops':
        case 'ops_plus':
        case 'era':
        case 'whip': return (SIDE_STATS[sortBy].value(a) ?? 0) - (SIDE_STATS[sortBy].value(b) ?? 0);
        case 'name': return lastName(a.card_snapshot.name).localeCompare(lastName(b.card_snapshot.name));
        case 'team': return franchiseTeam(a).localeCompare(franchiseTeam(b));
        case 'position': return POSITION_ORDER.indexOf(primaryPosition(a)) - POSITION_ORDER.indexOf(primaryPosition(b));
        case 'set_number':
        default: return (a.card_number ?? Infinity) - (b.card_number ?? Infinity);
    }
}

const GROUPERS: Record<Exclude<PoolGroupBy, 'none'>, GroupKeyer> = {
    team: { keyFn: franchiseTeam, compareKeys: (a, b) => a.localeCompare(b) },
    league: { keyFn: card => card.card_snapshot.league || 'Unknown', compareKeys: (a, b) => a.localeCompare(b) },
    position: {
        keyFn: primaryPosition,
        compareKeys: (a, b) => {
            const index = (key: string) => POSITION_ORDER.includes(key) ? POSITION_ORDER.indexOf(key) : POSITION_ORDER.length;
            return index(a) - index(b);
        },
    },
    type: {
        keyFn: card => parentPositionGroup(card.card_snapshot),
        compareKeys: (a, b) => PARENT_POSITION_ORDER.indexOf(a as typeof PARENT_POSITION_ORDER[number]) - PARENT_POSITION_ORDER.indexOf(b as typeof PARENT_POSITION_ORDER[number]),
    },
    hand: { keyFn: handLabel, compareKeys: (a, b) => HAND_ORDER.indexOf(a) - HAND_ORDER.indexOf(b) },
    year: { keyFn: card => String(cardYear(card) || 'Unknown'), compareKeys: descendingNumericKeys },
    points: { keyFn: pointsTierLabel, compareKeys: descendingNumericKeys },
    command: { keyFn: commandGroupLabel, compareKeys: compareCommandGroupKeys },
    speed: sideStatGrouper(SIDE_STATS.speed),
    ip: sideStatGrouper(SIDE_STATS.ip),
};

/** Sorts `cards` and splits them into labelled groups (a single unlabelled group when not grouping).
 * Groups keep a fixed order; the sort applies within each group. */
export function groupAndSortCards(cards: ReleaseCard[], groupBy: PoolGroupBy, sortBy: PoolSortBy, direction: PoolSortDirection): PoolGroup[] {
    const factor = direction === 'desc' ? -1 : 1;
    const sorted = [...cards].sort((a, b) => {
        // Cards without a set number always trail, whichever way the numbers run.
        if (sortBy === 'set_number' && (a.card_number === null || b.card_number === null)) return compareBySort(a, b, sortBy);
        // On-Base and Control live on different scales, so hitters stay ahead of pitchers in either direction.
        if (sortBy === 'command') return commandSide(a) - commandSide(b) || factor * compareBySort(a, b, sortBy);
        // One-sided stats (Speed/IP/real-life rates) — cards without the stat always trail.
        if (isSideStat(sortBy)) {
            const stat = SIDE_STATS[sortBy];
            return sideStatMissing(a, stat) - sideStatMissing(b, stat) || factor * compareBySort(a, b, sortBy);
        }
        return factor * compareBySort(a, b, sortBy);
    });
    if (groupBy === 'none') return [{ key: 'all', label: '', cards: sorted }];

    const { keyFn, compareKeys } = GROUPERS[groupBy];
    const byKey = new Map<string, ReleaseCard[]>();
    for (const card of sorted) {
        const key = keyFn(card);
        byKey.set(key, [...(byKey.get(key) ?? []), card]);
    }
    return [...byKey.entries()]
        .sort(([a], [b]) => compareKeys(a, b))
        .map(([key, groupCards]) => ({ key, label: key, cards: groupCards }));
}

/** Trims groups to the first `limit` cards overall, dropping groups that end up empty. */
export function takeFromGroups(groups: PoolGroup[], limit: number): PoolGroup[] {
    let remaining = limit;
    const result: PoolGroup[] = [];
    for (const group of groups) {
        if (remaining <= 0) break;
        result.push({ ...group, cards: group.cards.slice(0, remaining) });
        remaining -= group.cards.length;
    }
    return result;
}
