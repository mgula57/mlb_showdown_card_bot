import { useMemo } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { FaTrophy, FaArrowRotateLeft } from 'react-icons/fa6';
import type { SeasonSimSummary, SimStatLine, SimTeamIdentity } from '../../../api/sim';
import Standings from '../../seasons/Standings';
import type { Standings as StandingsGroup, TeamRecords } from '../../../api/mlbAPI';
import { SimBracket } from './SimBracket';

const TAB_TRIGGER_CLASS =
    'relative flex items-center px-4 py-2 text-sm rounded-lg transition-colors whitespace-nowrap cursor-pointer ' +
    'data-[state=active]:bg-(--background-quaternary) data-[state=active]:font-bold ' +
    'data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:font-medium data-[state=inactive]:hover:bg-(--divider)';

// Column sets mirror HITTER_CATEGORIES / PITCHER_CATEGORIES in reporting.py so the web tables
// and the CLI tables never drift. Keys are StatCategory values.
const HITTER_COLUMNS = ['g', 'pa', 'ba', 'obp', 'slg', 'ops', 'ops+', 'hr', 'rbi', 'bb', 'so', 'sb', 'r', 'wRC+', 'advantage_pct', 'own_chart_out_pct'];
const PITCHER_COLUMNS = ['g', 'era', 'whip', 'ip', 'er', 'so9', 'advantage_pct', 'own_chart_out_pct'];
const RATE_KEYS = new Set(['ba', 'obp', 'slg', 'ops', 'wOBA']);
const PERCENT_KEYS = new Set(['advantage_pct', 'own_chart_out_pct']);
// SHORT HEADERS FOR KEYS WHOSE UPPERCASED VALUE WOULDN'T FIT A COLUMN - MIRRORS StatCategory.abbreviation.
const COLUMN_LABELS: Record<string, string> = { advantage_pct: 'ADV%', own_chart_out_pct: 'OCHO%' };

function formatStat(key: string, value: number | undefined): string {
    if (value === undefined) return '—';
    if (PERCENT_KEYS.has(key)) return `${(value * 100).toFixed(1)}%`;
    if (RATE_KEYS.has(key)) return value.toFixed(3).replace(/^0\./, '.');
    if (key === 'era' || key === 'whip') return value.toFixed(2);
    if (key === 'ip' || key === 'so9') return value.toFixed(1);
    return String(Math.round(value));
}

function ordinal(n: number): string {
    const suffix = ['th', 'st', 'nd', 'rd'][(n % 100 - 20) % 10] || ['th', 'st', 'nd', 'rd'][n % 100] || 'th';
    return `${n}${suffix}`;
}

/** Standings.tsx keys teams by numeric id; sim teams only have schedule-key strings, so derive one. */
function hashId(value: string): number {
    let hash = 0;
    for (let i = 0; i < value.length; i++) {
        hash = (hash * 31 + value.charCodeAt(i)) | 0;
    }
    return hash;
}

/** Reshapes sim standings into the [leagueAbbr, Standings[]][] shape the shared Standings component expects. */
function useStandingsEntries(summary: SeasonSimSummary): [string, StandingsGroup[]][] {
    return useMemo(() => (
        Object.entries(summary.standings.divisions).map(([division, records]) => {
            const league = records[0]?.league ?? division;
            const teamRecords: TeamRecords[] = records.map(record => ({
                team: {
                    id: hashId(record.name),
                    name: record.identity?.name ?? record.name,
                    abbreviation: record.identity?.abbreviation ?? record.name,
                    primary_color: record.identity?.primary_color ?? undefined,
                },
                season: summary.year,
                league_record: { wins: record.wins, losses: record.losses },
                games_back: record.games_back === null ? undefined : String(record.games_back),
                showdown_points: record.points,
            }));
            const standing: StandingsGroup = {
                standingsType: 'regularSeason',
                division: { id: hashId(division), name: division },
                team_records: teamRecords,
            };
            return [league, [standing]];
        })
    ), [summary]);
}

/** Resolve a schedule key to its branding. The takeover team's key is the club it replaced. */
function useIdentity(summary: SeasonSimSummary) {
    return (abbr: string | null): SimTeamIdentity | null => (abbr ? summary.identities[abbr] ?? null : null);
}

function label(identity: SimTeamIdentity | null, fallback: string): string {
    return identity?.abbreviation ?? fallback;
}

function StatTable({ rows, columns, emptyLabel }: { rows: SimStatLine[]; columns: string[]; emptyLabel: string }) {
    if (rows.length === 0) {
        return <p className="text-[13px] text-(--text-tertiary) py-6 text-center">{emptyLabel}</p>;
    }
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-[12px] whitespace-nowrap">
                <thead>
                    <tr className="text-(--text-tertiary) border-b border-(--divider)">
                        <th className="text-left font-semibold py-2 pr-3">Player</th>
                        <th className="text-left font-semibold py-2 pr-3">Team</th>
                        <th className="text-left font-semibold py-2 pr-3">Pos</th>
                        {columns.map(key => (
                            <th key={key} className="text-right font-semibold py-2 px-2">{COLUMN_LABELS[key] ?? key.toUpperCase()}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map(row => (
                        <tr key={row.id} className="border-b border-(--divider)/50">
                            <td className="text-left py-1.5 pr-3 font-medium text-(--text-primary)">{row.name}</td>
                            <td className="text-left py-1.5 pr-3 text-(--text-tertiary)">{row.team ?? '—'}</td>
                            <td className="text-left py-1.5 pr-3 text-(--text-tertiary)">{row.position ?? '—'}</td>
                            {columns.map(key => (
                                <td key={key} className="text-right py-1.5 px-2 tabular-nums text-(--text-secondary)">
                                    {formatStat(key, row.stats[key])}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

type Props = {
    summary: SeasonSimSummary;
    onRunAgain?: () => void;
};

export function SimResult({ summary, onRunAgain }: Props) {
    const identityFor = useIdentity(summary);
    const team = summary.team;
    const teamKey = team.replaced_abbr ?? '';
    const teamName = team.identity?.name || team.identity?.abbreviation || 'Your team';

    const hitters = useMemo(() => summary.players.filter(p => p.player_type === 'Hitter'), [summary.players]);
    const pitchers = useMemo(() => summary.players.filter(p => p.player_type === 'Pitcher'), [summary.players]);
    const standingsEntries = useStandingsEntries(summary);

    const outcome = team.is_champion
        ? 'Won the World Series'
        : team.made_playoffs
            ? 'Made the playoffs'
            : 'Missed the playoffs';
    
    const outcomeColor = team.is_champion
        ? 'text-(--success)'
        : team.made_playoffs
            ? 'text-(--warning)'
            : 'text-(--error)';

    return (
        <div className="flex flex-col gap-4 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
            {/* Headline */}
            <div className="px-4 flex items-start justify-between gap-3">
                <div>
                    <p className="text-[12px] text-(--text-tertiary)">
                        {summary.year} · Set {summary.set}
                        {team.replaced_abbr ? ` · took over ${team.replaced_abbr}` : ''}
                        {summary.seed !== null ? ` · seed ${summary.seed}` : ''}
                    </p>
                    <h1 className="text-[24px] font-black text-(--text-primary) leading-tight">
                        {team.wins}<span className="text-(--text-tertiary)">–</span>{team.losses}
                        {team.is_champion && <FaTrophy className="inline ml-2 text-[18px] text-(--secondary)" />}
                    </h1>
                    <p className={`text-[13px] ${outcomeColor}`}>
                        {teamName} · {outcome}
                        {team.division && team.division_rank
                            ? ` · ${ordinal(team.division_rank)} in the ${team.division}`
                            : ''}
                    </p>
                </div>
                {onRunAgain && (
                    <button
                        type="button"
                        onClick={onRunAgain}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-(--background-tertiary) text-[12px] font-bold text-(--text-primary) hover:opacity-90 transition-opacity cursor-pointer shrink-0"
                    >
                        <FaArrowRotateLeft className="text-[10px]" />
                        Run again
                    </button>
                )}
            </div>

            {/* Headline numbers */}
            <div className="px-4 grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                    { label: 'Win %', value: team.win_pct.toFixed(3).replace(/^0\./, '.') },
                    { label: 'Points', value: team.points.toLocaleString() },
                    { label: 'Longest W streak', value: String(team.longest_win_streak) },
                    { label: 'Longest L streak', value: String(team.longest_losing_streak) },
                ].map(stat => (
                    <div key={stat.label} className="rounded-lg bg-(--background-tertiary) px-3 py-2">
                        <p className="text-[11px] text-(--text-tertiary)">{stat.label}</p>
                        <p className="text-[16px] font-bold text-(--text-primary) tabular-nums">{stat.value}</p>
                    </div>
                ))}
            </div>

            <Tabs.Root defaultValue="schedule" className="flex flex-col">
                <Tabs.List className="flex px-3 border-b border-(--divider) gap-x-1 py-1 overflow-x-auto">
                    <Tabs.Trigger value="schedule" className={TAB_TRIGGER_CLASS}>Schedule</Tabs.Trigger>
                    <Tabs.Trigger value="batting" className={TAB_TRIGGER_CLASS}>Batting</Tabs.Trigger>
                    <Tabs.Trigger value="pitching" className={TAB_TRIGGER_CLASS}>Pitching</Tabs.Trigger>
                    <Tabs.Trigger value="standings" className={TAB_TRIGGER_CLASS}>Standings</Tabs.Trigger>
                    <Tabs.Trigger value="leaders" className={TAB_TRIGGER_CLASS}>League Leaders</Tabs.Trigger>
                    {summary.postseason.length > 0 && (
                        <Tabs.Trigger value="postseason" className={TAB_TRIGGER_CLASS}>Postseason</Tabs.Trigger>
                    )}
                </Tabs.List>

                {/* Schedule */}
                <Tabs.Content value="schedule" className="focus:outline-none px-4 pt-3">
                    <div className="flex flex-wrap gap-1 mb-4">
                        {summary.games.map((game, i) => (
                            <div
                                key={i}
                                title={`${game.date} ${game.is_home ? 'vs' : '@'} ${label(identityFor(game.opponent), game.opponent)} — ${game.runs_scored}-${game.runs_allowed}`}
                                className={`h-4 w-4 rounded-sm ${game.is_win ? 'bg-(--showdown-blue)' : 'bg-(--background-quaternary)'}`}
                            />
                        ))}
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-[12px] whitespace-nowrap">
                            <thead>
                                <tr className="text-(--text-tertiary) border-b border-(--divider)">
                                    <th className="text-left font-semibold py-2 pr-3">Date</th>
                                    <th className="text-left font-semibold py-2 pr-3">Opponent</th>
                                    <th className="text-right font-semibold py-2 px-2">Score</th>
                                    <th className="text-right font-semibold py-2 px-2">Result</th>
                                    <th className="text-right font-semibold py-2 px-2">Record</th>
                                </tr>
                            </thead>
                            <tbody>
                                {summary.games.map((game, i) => (
                                    <tr key={i} className="border-b border-(--divider)/50">
                                        <td className="py-1.5 pr-3 text-(--text-tertiary)">{game.date}</td>
                                        <td className="py-1.5 pr-3 text-(--text-primary)">
                                            {game.is_home ? 'vs ' : '@ '}
                                            {label(identityFor(game.opponent), game.opponent)}
                                        </td>
                                        <td className="text-right py-1.5 px-2 tabular-nums text-(--text-secondary)">
                                            {game.runs_scored}–{game.runs_allowed}
                                        </td>
                                        <td className={`text-right py-1.5 px-2 font-bold ${game.is_win ? 'text-(--showdown-blue)' : 'text-(--text-tertiary)'}`}>
                                            {game.is_win ? 'W' : 'L'}
                                        </td>
                                        <td className="text-right py-1.5 px-2 tabular-nums text-(--text-tertiary)">
                                            {game.wins}–{game.losses}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Tabs.Content>

                <Tabs.Content value="batting" className="focus:outline-none px-4 pt-3">
                    <StatTable rows={hitters} columns={HITTER_COLUMNS} emptyLabel="No hitters on this roster." />
                </Tabs.Content>

                <Tabs.Content value="pitching" className="focus:outline-none px-4 pt-3">
                    <StatTable rows={pitchers} columns={PITCHER_COLUMNS} emptyLabel="No pitchers on this roster." />
                </Tabs.Content>

                {/* Standings */}
                <Tabs.Content value="standings" className="focus:outline-none px-4 pt-3">
                    <Standings
                        standingsEntries={standingsEntries}
                        selectedTeamId={teamKey ? hashId(teamKey) : null}
                    />
                </Tabs.Content>

                {/* League leaders */}
                <Tabs.Content value="leaders" className="focus:outline-none px-4 pt-3 flex flex-col gap-5">
                    <div>
                        <p className="text-[12px] font-bold text-(--text-primary) mb-1">Top Hitters (OPS)</p>
                        <StatTable rows={summary.top_players?.position_player} columns={HITTER_COLUMNS} emptyLabel="No qualified hitters." />
                    </div>
                    <div>
                        <p className="text-[12px] font-bold text-(--text-primary) mb-1">Top Starting Pitchers (ERA)</p>
                        <StatTable rows={summary.top_players?.starting_pitcher} columns={PITCHER_COLUMNS} emptyLabel="No qualified starters." />
                    </div>
                    <div>
                        <p className="text-[12px] font-bold text-(--text-primary) mb-1">Top Relief Pitchers (ERA)</p>
                        <StatTable rows={summary.top_players?.relief_pitcher} columns={PITCHER_COLUMNS} emptyLabel="No qualified relievers." />
                    </div>
                </Tabs.Content>

                {/* Postseason */}
                {summary.postseason.length > 0 && (
                    <Tabs.Content value="postseason" className="focus:outline-none px-4 pt-3">
                        <SimBracket summary={summary} highlightAbbr={teamKey} />
                    </Tabs.Content>
                )}
            </Tabs.Root>
        </div>
    );
}
