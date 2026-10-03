import type { ReleaseCard } from '../../api/releases';
import { FRANCHISE_CODE, PARENT_POSITION_ORDER, parentPositionGroup } from './SummaryCharts';

export type PoolGroupBy = 'none' | 'team' | 'position' | 'type' | 'command' | 'speed' | 'ip';
export type PoolSortBy = 'set_number' | 'points' | 'name' | 'team' | 'position' | 'command' | 'speed' | 'ip';
export type PoolSortDirection = 'asc' | 'desc';

export type PoolGroup = { key: string; label: string; cards: ReleaseCard[] };

export const POOL_GROUP_OPTIONS: { label: string; value: PoolGroupBy }[] = [
    { label: 'None', value: 'none' },
    { label: 'Team', value: 'team' },
    { label: 'Position', value: 'position' },
    { label: 'Player Type', value: 'type' },
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
    { label: 'Command', value: 'command' },
    { label: 'Speed', value: 'speed' },
    { label: 'IP', value: 'ip' },
];

/** The direction that reads most naturally for each sort — big numbers first for PTS/Command/Speed/IP. */
export const POOL_SORT_DEFAULT_DIRECTION: Record<PoolSortBy, PoolSortDirection> = {
    set_number: 'asc',
    points: 'desc',
    name: 'asc',
    team: 'asc',
    position: 'asc',
    command: 'desc',
    speed: 'desc',
    ip: 'desc',
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

/** Speed only applies to hitters and IP only to pitchers; `null` for cards the stat doesn't apply to. */
type SideStat = { value: (card: ReleaseCard) => number | null; label: string; missingLabel: string };

const SIDE_STATS: Record<'speed' | 'ip', SideStat> = {
    speed: { value: card => card.card_snapshot.is_pitcher ? null : (card.card_snapshot.speed ?? 0), label: 'Speed', missingLabel: 'Pitchers' },
    ip: { value: card => card.card_snapshot.is_pitcher ? (card.card_snapshot.ip ?? 0) : null, label: 'IP', missingLabel: 'Hitters' },
};

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

function lastName(name: string | undefined): string {
    const parts = (name ?? '').trim().split(/\s+/);
    const last = parts[parts.length - 1]?.replace('.', '').toUpperCase();
    return parts.length > 1 && ['JR', 'SR', 'II', 'III', 'IV', 'V'].includes(last) ? parts[parts.length - 2] : (parts[parts.length - 1] ?? '');
}

function compareBySort(a: ReleaseCard, b: ReleaseCard, sortBy: PoolSortBy): number {
    switch (sortBy) {
        case 'points': return (a.card_snapshot.points ?? 0) - (b.card_snapshot.points ?? 0);
        case 'command': return (a.card_snapshot.command ?? 0) - (b.card_snapshot.command ?? 0);
        case 'speed':
        case 'ip': return (SIDE_STATS[sortBy].value(a) ?? 0) - (SIDE_STATS[sortBy].value(b) ?? 0);
        case 'name': return lastName(a.card_snapshot.name).localeCompare(lastName(b.card_snapshot.name));
        case 'team': return franchiseTeam(a).localeCompare(franchiseTeam(b));
        case 'position': return POSITION_ORDER.indexOf(primaryPosition(a)) - POSITION_ORDER.indexOf(primaryPosition(b));
        case 'set_number':
        default: return (a.card_number ?? Infinity) - (b.card_number ?? Infinity);
    }
}

const GROUPERS: Record<Exclude<PoolGroupBy, 'none'>, GroupKeyer> = {
    team: { keyFn: franchiseTeam, compareKeys: (a, b) => a.localeCompare(b) },
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
        // Speed only applies to hitters and IP to pitchers, so cards without the stat always trail.
        if (sortBy === 'speed' || sortBy === 'ip') {
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
