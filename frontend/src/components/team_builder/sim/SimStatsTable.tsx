import { useMemo, useState } from 'react';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa6';
import type { SimStatLine, SimTeamIdentity } from '../../../api/sim';
import CardIdentityCell from '../../cards/card_elements/CardIdentityCell';
import { CardDetail } from '../../cards/CardDetail';
import { Modal } from '../../shared/Modal';
import { COLUMN_LABELS, formatStat, SIM_STATS_TOOLTIP } from './simStatColumns';
import { useCardLinks } from './useCardLinks';

type SortKey = 'name' | 'team' | 'position' | string;
type SortState = { key: SortKey; dir: 'asc' | 'desc' } | null;

function sortValue(row: SimStatLine, key: SortKey): string | number {
    switch (key) {
        case 'name': return row.name;
        case 'team': return row.team ?? '';
        case 'position': return row.position ?? '';
        default: return row.stats[key] ?? -Infinity;
    }
}

function SortHeader({ label, active, dir, onClick, align = 'right' }: { label: string; active: boolean; dir?: 'asc' | 'desc'; onClick: () => void; align?: 'left' | 'right' }) {
    const Icon = !active ? FaSort : dir === 'asc' ? FaSortUp : FaSortDown;
    return (
        <th className={`${align === 'right' ? 'text-right' : 'text-left'} font-semibold py-2 px-2`}>
            <button
                type="button"
                onClick={onClick}
                className={`inline-flex items-center gap-1 cursor-pointer hover:text-(--text-primary) ${active ? 'text-(--text-primary)' : ''} ${align === 'right' ? 'flex-row-reverse' : ''}`}
            >
                {label}
                <Icon className="text-[9px]" />
            </button>
        </th>
    );
}

type Props = {
    rows: SimStatLine[];
    columns: string[];
    emptyLabel: string;
    /** Fetches and links each row to its real Showdown card via `SimStatLine.card_source` —
     * populated for every player, not just the user's own roster (see `SeasonSummaryBuilder._line`). */
    cardsEnabled?: boolean;
    /** Schedule key -> branding (`SeasonSimSummary.identities`). When a row's `team` resolves
     * here, its identity colors win over the card's own archived colors — a takeover/tournament
     * team's players should show that team's colors, not whatever real club they used to play for. */
    identities?: Record<string, SimTeamIdentity>;
};

/**
 * Sortable stat table shared by Batting, Pitching, League Leaders and Awards. `cardsEnabled`
 * additionally links each row to its real Showdown Bot card via the same (card_id, card_source)
 * pair `useCardMap` already fetches roster cards with in `TeamDetail.tsx` — no re-derivation.
 */
export function SimStatsTable({ rows, columns, emptyLabel, cardsEnabled = false, identities }: Props) {
    const [sort, setSort] = useState<SortState>(null);

    const { recordFor, isLoadingCard, selected, selectedSimStats, open, close, isFetching } = useCardLinks(rows, cardsEnabled);

    const sortedRows = useMemo(() => {
        if (!sort) return rows;
        const dirMul = sort.dir === 'asc' ? 1 : -1;
        return [...rows].sort((a, b) => {
            const av = sortValue(a, sort.key);
            const bv = sortValue(b, sort.key);
            if (typeof av === 'string' || typeof bv === 'string') {
                return dirMul * String(av).localeCompare(String(bv));
            }
            return dirMul * (av - bv);
        });
    }, [rows, sort]);

    const toggleSort = (key: SortKey) => {
        setSort(prev => {
            if (prev?.key === key) return { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' };
            return { key, dir: (key === 'name' || key === 'team' || key === 'position') ? 'asc' : 'desc' };
        });
    };

    if (rows.length === 0) {
        return <p className="text-[13px] text-(--text-tertiary) py-6 text-center">{emptyLabel}</p>;
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-[12px] whitespace-nowrap">
                <thead>
                    <tr className="text-(--text-tertiary) border-b border-(--divider)">
                        <SortHeader label="Player" align="left" active={sort?.key === 'name'} dir={sort?.dir} onClick={() => toggleSort('name')} />
                        <SortHeader label="Team" align="left" active={sort?.key === 'team'} dir={sort?.dir} onClick={() => toggleSort('team')} />
                        <SortHeader label="Pos" align="left" active={sort?.key === 'position'} dir={sort?.dir} onClick={() => toggleSort('position')} />
                        {columns.map(key => (
                            <SortHeader key={key} label={COLUMN_LABELS[key] ?? key.toUpperCase()} active={sort?.key === key} dir={sort?.dir} onClick={() => toggleSort(key)} />
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {sortedRows.map(row => {
                        const record = recordFor(row);
                        const clickable = !!record;
                        const teamIdentity = identities?.[row.team ?? ''];
                        return (
                            <tr
                                key={row.id}
                                className={`border-b border-(--divider)/50 ${clickable ? 'cursor-pointer hover:bg-(--background-primary)/50' : ''}`}
                                onClick={clickable ? () => open(record!.card_id, record!.source, row.stats) : undefined}
                            >
                                <td className="py-1.5 pr-3 text-left">
                                    {cardsEnabled ? (
                                        <CardIdentityCell
                                            name={row.name} hasCard={!!record} isLoadingCard={isLoadingCard(row) || (record ? isFetching(record.card_id) : false)}
                                            isPitcher={record?.is_pitcher}
                                            primaryColor={teamIdentity?.primary_color ?? record?.color_primary}
                                            secondaryColor={teamIdentity?.secondary_color ?? record?.color_secondary}
                                            command={record?.command} team={row.team} points={record?.points}
                                        />
                                    ) : (
                                        <span className="font-medium text-(--text-primary)">{row.name}</span>
                                    )}
                                </td>
                                <td className="text-left py-1.5 pr-3 text-(--text-tertiary)">{row.team ?? '—'}</td>
                                <td className="text-left py-1.5 pr-3 text-(--text-tertiary)">{row.position ?? '—'}</td>
                                {columns.map(key => (
                                    <td key={key} className="text-right py-1.5 px-2 tabular-nums text-(--text-secondary)">
                                        {formatStat(key, row.stats[key])}
                                    </td>
                                ))}
                            </tr>
                        );
                    })}
                </tbody>
            </table>
            <div className={selected ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={close} isVisible={!!selected}>
                    <CardDetail showdownBotCardData={selected} hideTrendGraphs={true} context="sim_result" parent="sim_result" simStats={selectedSimStats} tooltip={selectedSimStats ? SIM_STATS_TOOLTIP : undefined} />
                </Modal>
            </div>
        </div>
    );
}
