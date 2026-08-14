import { useMemo } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import {
    FaTrophy, FaArrowRotateLeft, FaChartLine, FaCalendarDays, FaBaseballBatBall, FaBaseball,
    FaTableList, FaRankingStar, FaSitemap,
} from 'react-icons/fa6';
import type { AwardWinner, SeasonSimSummary } from '../../../api/sim';
import Standings from '../../seasons/Standings';
import { SimAwardsList } from './SimAwardsList';
import { SimBracket } from './SimBracket';
import { SimSummaryTab } from './SimSummaryTab';
import { SimStatsTable } from './SimStatsTable';
import { HITTER_COLUMNS, PITCHER_COLUMNS } from './simStatColumns';
import { useStandingsEntries, useIdentity, hashId, label } from './simStandings';
import { describePostseasonExit } from './postseasonExit';

const TAB_TRIGGER_CLASS =
    'relative flex items-center gap-1.5 px-4 py-2 text-sm rounded-lg transition-colors whitespace-nowrap cursor-pointer ' +
    'data-[state=active]:bg-(--background-quaternary) data-[state=active]:font-bold ' +
    'data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:font-medium data-[state=inactive]:hover:bg-(--divider)';
const TAB_ICON_CLASS = 'text-[12px]';

function ordinal(n: number): string {
    const suffix = ['th', 'st', 'nd', 'rd'][(n % 100 - 20) % 10] || ['th', 'st', 'nd', 'rd'][n % 100] || 'th';
    return `${n}${suffix}`;
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
    const postseasonExit = useMemo(() => describePostseasonExit(summary, teamKey), [summary, teamKey]);

    const awardsByCategory = useMemo(() => {
        const awards = summary.awards;
        if (!awards) return [];
        return [
            ...awards.mvp, ...awards.cy_young, ...awards.rookie_of_year, ...awards.silver_sluggers,
        ];
    }, [summary.awards]);
    const awardsByLeague = useMemo(() => {
        const byLeague = new Map<string, AwardWinner[]>();
        for (const award of awardsByCategory) {
            const bucket = byLeague.get(award.league) ?? [];
            bucket.push(award);
            byLeague.set(award.league, bucket);
        }
        return [...byLeague.entries()].sort(([a], [b]) => a.localeCompare(b));
    }, [awardsByCategory]);

    const outcome = team.is_champion
        ? 'Won the World Series'
        : postseasonExit
            ? `Lost ${postseasonExit.roundLabel} to ${postseasonExit.opponentAbbr}`
            : team.made_playoffs
                ? 'Made the playoffs'
                : 'Missed the playoffs';

    const outcomeColor = team.is_champion
        ? 'text-(--success)'
        : team.made_playoffs
            ? 'text-(--warning)'
            : 'text-(--error)';

    return (
        <div className="flex flex-col gap-4 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full md:px-4">
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

            <Tabs.Root defaultValue="summary" className="flex flex-col">
                <Tabs.List className="flex px-3 border-b border-(--divider) gap-x-1 py-1 overflow-x-auto scrollbar-hide">
                    <Tabs.Trigger value="summary" className={TAB_TRIGGER_CLASS}><FaChartLine className={TAB_ICON_CLASS} />Summary</Tabs.Trigger>
                    <Tabs.Trigger value="schedule" className={TAB_TRIGGER_CLASS}><FaCalendarDays className={TAB_ICON_CLASS} />Schedule</Tabs.Trigger>
                    <Tabs.Trigger value="batting" className={TAB_TRIGGER_CLASS}><FaBaseballBatBall className={TAB_ICON_CLASS} />Batting</Tabs.Trigger>
                    <Tabs.Trigger value="pitching" className={TAB_TRIGGER_CLASS}><FaBaseball className={TAB_ICON_CLASS} />Pitching</Tabs.Trigger>
                    <Tabs.Trigger value="standings" className={TAB_TRIGGER_CLASS}><FaTableList className={TAB_ICON_CLASS} />Standings</Tabs.Trigger>
                    <Tabs.Trigger value="leaders" className={TAB_TRIGGER_CLASS}><FaRankingStar className={TAB_ICON_CLASS} />League Leaders</Tabs.Trigger>
                    {awardsByLeague.length > 0 && (
                        <Tabs.Trigger value="awards" className={TAB_TRIGGER_CLASS}><FaTrophy className={TAB_ICON_CLASS} />Awards</Tabs.Trigger>
                    )}
                    {summary.postseason.length > 0 && (
                        <Tabs.Trigger value="postseason" className={TAB_TRIGGER_CLASS}><FaSitemap className={TAB_ICON_CLASS} />Postseason</Tabs.Trigger>
                    )}
                </Tabs.List>

                {/* Summary */}
                <Tabs.Content value="summary" className="focus:outline-none px-4 pt-3">
                    <SimSummaryTab summary={summary} teamKey={teamKey} />
                </Tabs.Content>

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
                    <SimStatsTable rows={hitters} columns={HITTER_COLUMNS} emptyLabel="No hitters on this roster." cardsEnabled />
                </Tabs.Content>

                <Tabs.Content value="pitching" className="focus:outline-none px-4 pt-3">
                    <SimStatsTable rows={pitchers} columns={PITCHER_COLUMNS} emptyLabel="No pitchers on this roster." cardsEnabled />
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
                        <SimStatsTable rows={summary.top_players?.position_player ?? []} columns={HITTER_COLUMNS} emptyLabel="No qualified hitters." cardsEnabled />
                    </div>
                    <div>
                        <p className="text-[12px] font-bold text-(--text-primary) mb-1">Top Starting Pitchers (ERA)</p>
                        <SimStatsTable rows={summary.top_players?.starting_pitcher ?? []} columns={PITCHER_COLUMNS} emptyLabel="No qualified starters." cardsEnabled />
                    </div>
                    <div>
                        <p className="text-[12px] font-bold text-(--text-primary) mb-1">Top Relief Pitchers (ERA)</p>
                        <SimStatsTable rows={summary.top_players?.relief_pitcher ?? []} columns={PITCHER_COLUMNS} emptyLabel="No qualified relievers." cardsEnabled />
                    </div>
                </Tabs.Content>

                {/* Awards */}
                {awardsByLeague.length > 0 && (
                    <Tabs.Content value="awards" className="focus:outline-none px-4 pt-3">
                        <SimAwardsList awardsByLeague={awardsByLeague} />
                    </Tabs.Content>
                )}

                {/* Postseason */}
                {summary.postseason.length > 0 && (
                    <Tabs.Content value="postseason" className="focus:outline-none px-4 pt-3">
                        <SimBracket summary={summary} highlightAbbr={teamKey} showGameResults />
                    </Tabs.Content>
                )}
            </Tabs.Root>
        </div>
    );
}
