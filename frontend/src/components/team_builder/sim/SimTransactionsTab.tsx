import { useMemo, type ReactNode } from 'react';
import { FaRightLeft, FaUserInjured, FaArrowUp, FaArrowRotateLeft } from 'react-icons/fa6';
import type { SeasonSimSummary } from '../../../api/sim';
import { TeamChip } from '../../shared/TeamChip';
import { fromSimTeamIdentity, fallbackIdentity } from '../../../domain/adapters/fromSim';
import { useIdentity } from './simStandings';
import { KpiTile } from './KpiTile';

const TXN_META: Record<string, { label: string; icon: typeof FaUserInjured; color: string }> = {
    IL: { label: 'To the IL', icon: FaUserInjured, color: 'text-(--error)' },
    UP: { label: 'Called up', icon: FaArrowUp, color: 'text-(--showdown-blue)' },
    ACT: { label: 'Activated', icon: FaArrowRotateLeft, color: 'text-(--text-secondary)' },
};

function shortDate(iso: string): string {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function SectionCard({ title, count, children }: { title: string; count?: number; children: ReactNode }) {
    return (
        <div className="rounded-xl bg-(--background-tertiary) p-3 flex flex-col gap-2 min-w-0">
            <p className="text-[12px] font-bold text-(--text-primary)">
                {title}
                {count != null && <span className="text-(--text-tertiary) font-semibold"> · {count}</span>}
            </p>
            {children}
        </div>
    );
}

type Props = {
    summary: SeasonSimSummary;
    /** Schedule key the result screen is focused on. */
    teamKey: string;
};

/**
 * Everything that happened to the focused club's roster over the season: trade-deadline moves
 * (`enable_trade_deadline`) and 40-man moves (`enable_injuries`). Both lists are already scoped —
 * an open sim carries every club's rows, a takeover run only its own — so this just filters to
 * `teamKey` and renders.
 */
export function SimTransactionsTab({ summary, teamKey }: Props) {
    const identityFor = useIdentity(summary);

    const trades = useMemo(
        () => (summary.deadline_trades ?? []).filter(t => t.from_team === teamKey || t.to_team === teamKey),
        [summary.deadline_trades, teamKey],
    );
    const transactions = useMemo(
        () => (summary.transactions ?? []).filter(t => t.team === teamKey),
        [summary.transactions, teamKey],
    );
    const roll = summary.injury_summary?.[teamKey];

    const otherTrades = (summary.deadline_trades ?? []).length - trades.length;

    return (
        <div className="flex flex-col gap-4">
            {roll && (
                <div className="grid grid-cols-3 gap-2">
                    <KpiTile label="IL Stints" value={String(roll.stints)} />
                    <KpiTile label="Games Missed" value={String(roll.games_missed)} />
                    <KpiTile label="Call-ups" value={String(roll.callups)} />
                </div>
            )}

            <SectionCard title="Deadline Moves" count={trades.length || undefined}>
                {trades.length > 0 ? (
                    <div className="flex flex-col gap-1.5">
                        {trades.map((trade, i) => {
                            const acquired = trade.to_team === teamKey;
                            const otherKey = acquired ? trade.from_team : trade.to_team;
                            const otherIdentity = identityFor(otherKey);
                            const record = acquired ? trade.to_team_record : trade.from_team_record;
                            return (
                                <div key={i} className="flex items-center gap-2 text-[12px] rounded-lg bg-(--background-secondary) px-3 py-2">
                                    <FaRightLeft className={`shrink-0 ${acquired ? 'text-(--success)' : 'text-(--error)'}`} />
                                    <span className={`font-bold w-9 shrink-0 ${acquired ? 'text-(--success)' : 'text-(--error)'}`}>
                                        {acquired ? 'IN' : 'OUT'}
                                    </span>
                                    <span className="font-bold text-(--text-primary)">{trade.player_name}</span>
                                    {trade.position && <span className="text-(--text-tertiary)">{trade.position}</span>}
                                    <span className="text-(--text-tertiary)">{acquired ? 'from' : 'to'}</span>
                                    <TeamChip team={otherIdentity ? fromSimTeamIdentity(otherIdentity) : fallbackIdentity(otherKey)} size="sm" />
                                    <span className="text-(--text-tertiary) ml-auto whitespace-nowrap">{record} · {shortDate(trade.date)}</span>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <p className="text-[13px] text-(--text-tertiary) py-1">
                        No deadline moves for this club{otherTrades > 0 ? ` — ${otherTrades} elsewhere in the league.` : '.'}
                    </p>
                )}
            </SectionCard>

            <SectionCard title="Roster Moves" count={transactions.length || undefined}>
                {transactions.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-[12px] whitespace-nowrap">
                            <thead>
                                <tr className="text-(--text-tertiary) border-b border-(--divider)">
                                    <th className="text-left font-semibold py-2 pr-3">Date</th>
                                    <th className="text-left font-semibold py-2 pr-3">Move</th>
                                    <th className="text-left font-semibold py-2 pr-3">Player</th>
                                    <th className="text-left font-semibold py-2 pr-3">Detail</th>
                                </tr>
                            </thead>
                            <tbody>
                                {transactions.map((t, i) => {
                                    const meta = TXN_META[t.type];
                                    const Icon = meta?.icon;
                                    const detail = t.type === 'IL'
                                        ? [t.il_days != null ? `~${t.il_days}d` : null, t.related_player_name ? `${t.related_player_name} up` : null].filter(Boolean).join(' · ')
                                        : t.type === 'ACT'
                                            ? [t.games_missed != null ? `missed ${t.games_missed}` : null, t.related_player_name ? `${t.related_player_name} down` : null].filter(Boolean).join(' · ')
                                            : (t.related_player_name ? `for ${t.related_player_name}` : t.detail);
                                    return (
                                        <tr key={i} className="border-b border-(--divider)/50">
                                            <td className="py-1.5 pr-3 text-(--text-tertiary)">{shortDate(t.date)}</td>
                                            <td className={`py-1.5 pr-3 font-semibold ${meta?.color ?? 'text-(--text-secondary)'}`}>
                                                <span className="inline-flex items-center gap-1.5">
                                                    {Icon && <Icon className="text-[10px]" />}
                                                    {meta?.label ?? t.type}
                                                </span>
                                            </td>
                                            <td className="py-1.5 pr-3 text-(--text-primary)">
                                                {t.player_name}
                                                {t.position && <span className="text-(--text-tertiary)"> · {t.position}</span>}
                                            </td>
                                            <td className="py-1.5 pr-3 text-(--text-tertiary)">{detail}</td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-[13px] text-(--text-tertiary) py-1">
                        No roster moves{summary.injury_summary ? ' for this club.' : ' — injuries were off for this run.'}
                    </p>
                )}
            </SectionCard>
        </div>
    );
}
