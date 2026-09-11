import { useMemo } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import {
    FaTrophy, FaArrowRotateLeft, FaChartLine, FaCalendarDays, FaBaseballBatBall, FaBaseball,
    FaTableList, FaRankingStar, FaSitemap, FaCheck, FaXmark, FaRightLeft, FaFire, FaSnowflake,
    FaChevronRight, FaDiceD20,
} from 'react-icons/fa6';
import type { ChallengeStanding, SeasonSimSummary } from '../../../api/sim';
import Standings from '../../seasons/Standings';
import CustomSelect from '../../shared/CustomSelect';
import { SimAwardsList } from './SimAwardsList';
import { SimBracket } from './SimBracket';
import { SimSummaryTab } from './SimSummaryTab';
import { SimTransactionsTab } from './SimTransactionsTab';
import { SimStatsTable } from './SimStatsTable';
import { HITTER_COLUMNS, PITCHER_COLUMNS, buildHitterTeamKpis, buildPitcherTeamKpis, buildLeagueStatsKpis } from './simStatColumns';
import { KpiTile } from './KpiTile';
import { useStandingsEntries, useIdentity, hashId, label } from './simStandings';
import { useClubSeason } from './simClubSeason';
import { describePostseasonExit } from './postseasonExit';
import { radixTabTriggerClass } from '../../shared/tabStyles';

const TAB_TRIGGER_CLASS = radixTabTriggerClass();
const TAB_ICON_CLASS = 'text-[12px]';

function ordinal(n: number): string {
    const suffix = ['th', 'st', 'nd', 'rd'][(n % 100 - 20) % 10] || ['th', 'st', 'nd', 'rd'][n % 100] || 'th';
    return `${n}${suffix}`;
}

type Props = {
    summary: SeasonSimSummary;
    /** Set only when this season was a Team Challenge attempt. */
    challengeResult?: 'passed' | 'failed' | null;
    /** Where this run lands on the challenge's leaderboard - drives the callout under the
     *  headline. Present only on a challenge run. */
    challengeStanding?: ChallengeStanding | null;
    /** Challenge runs only: open the challenge's own page + scoped leaderboard. When set, the
     *  "Leaderboard" standing tile becomes a link to it. */
    onOpenChallengeLeaderboard?: () => void;
    onRunAgain?: () => void;
    /** Challenge runs only: back into the team editor (roster pre-loaded, challenge primed) to
     *  tweak and re-run. Takes precedence over `onRunAgain` when set. */
    onTryAgain?: () => void;
    /** Club to focus on. Only meaningful for an open sim (no single team) - a takeover/challenge
     *  run always shows its own fixed team regardless of this prop. */
    focusAbbr?: string;
    /** Called when the user switches focus club via the header dropdown. The dropdown only
     *  renders for an open sim (`season_games` populated), so this is otherwise unused. */
    onFocusChange?: (abbr: string) => void;
};

export function SimResult({ summary, challengeResult, challengeStanding, onOpenChallengeLeaderboard, onRunAgain, onTryAgain, focusAbbr, onFocusChange }: Props) {
    const identityFor = useIdentity(summary);
    const isOpenSim = (summary.season_games?.length ?? 0) > 0;
    const isResumed = Object.keys(summary.seeded_records ?? {}).length > 0;
    const clubAbbr = focusAbbr ?? summary.team?.replaced_abbr ?? Object.keys(summary.identities)[0] ?? '';
    const { team, games, players } = useClubSeason(summary, clubAbbr);
    const teamKey = team?.replaced_abbr ?? clubAbbr;
    const teamName = team?.identity?.name || team?.identity?.abbreviation || 'Your team';

    const hitters = useMemo(() => players.filter(p => p.player_type === 'Hitter'), [players]);
    const pitchers = useMemo(() => players.filter(p => p.player_type === 'Pitcher'), [players]);
    const hitterKpis = useMemo(() => buildHitterTeamKpis(hitters), [hitters]);
    const pitcherKpis = useMemo(() => buildPitcherTeamKpis(pitchers), [pitchers]);
    const leagueStatsKpis = useMemo(() => buildLeagueStatsKpis(summary.league_totals), [summary.league_totals]);
    const standingsEntries = useStandingsEntries(summary);
    const postseasonExit = useMemo(() => describePostseasonExit(summary, teamKey), [summary, teamKey]);

    const gamesByMonth = useMemo(() => {
        type MonthGroup = { key: string; label: string; games: typeof games; wins: number; losses: number; temp: 'hot' | 'cold' | null };
        const groups: MonthGroup[] = [];
        for (const game of games) {
            const d = new Date(`${game.date}T00:00:00`);
            const key = `${d.getFullYear()}-${d.getMonth()}`;
            let group = groups.length > 0 && groups[groups.length - 1].key === key ? groups[groups.length - 1] : null;
            if (!group) {
                group = { key, label: d.toLocaleDateString(undefined, { month: 'long' }), games: [], wins: 0, losses: 0, temp: null };
                groups.push(group);
            }
            group.games.push(game);
            if (game.is_win) group.wins += 1;
            else group.losses += 1;
        }

        // Fold a short leading/trailing month (spring-training tail in March, Game 163 / early
        // October) into its neighbor so the schedule isn't broken up by a two-game "month".
        const MIN_MONTH_GAMES = 15;
        const merge = (into: MonthGroup, other: MonthGroup, prepend: boolean) => {
            into.games = prepend ? [...other.games, ...into.games] : [...into.games, ...other.games];
            into.wins += other.wins;
            into.losses += other.losses;
            into.label = prepend ? `${other.label} / ${into.label}` : `${into.label} / ${other.label}`;
        };
        if (groups.length > 1 && groups[0].games.length < MIN_MONTH_GAMES) {
            merge(groups[1], groups[0], true);
            groups.shift();
        }
        if (groups.length > 1 && groups[groups.length - 1].games.length < MIN_MONTH_GAMES) {
            merge(groups[groups.length - 2], groups[groups.length - 1], false);
            groups.pop();
        }

        // Flag a month hot/cold once its win% clears ~.575 / .425 — near-.500 months stay unmarked.
        for (const group of groups) {
            const total = group.wins + group.losses;
            const pct = total > 0 ? group.wins / total : 0.5;
            group.temp = pct >= 0.575 ? 'hot' : pct <= 0.425 ? 'cold' : null;
        }
        return groups;
    }, [games]);

    const clubOptions = useMemo(() => (
        Object.entries(summary.identities)
            .map(([abbr, identity]) => ({
                value: abbr,
                label: `${identity.name || identity.abbreviation}${summary.takeover_abbrs?.includes(abbr) ? ' ★' : ''}`,
            }))
            .sort((a, b) => a.label.localeCompare(b.label))
    ), [summary.identities, summary.takeover_abbrs]);

    const hasAwards = useMemo(() => {
        const awards = summary.awards;
        return !!awards && (awards.mvp.length + awards.cy_young.length + awards.rookie_of_year.length + awards.silver_sluggers.length + (awards.series_mvps?.length ?? 0)) > 0;
    }, [summary.awards]);

    const hasTransactions = (summary.deadline_trades?.length ?? 0) > 0 || (summary.transactions?.length ?? 0) > 0;

    // GUARD AFTER EVERY HOOK CALL ABOVE, NEVER BEFORE - team CAN ONLY BE NULL IF clubAbbr DOESN'T
    // MATCH ANY STANDINGS ROW, WHICH SHOULDN'T HAPPEN IN PRACTICE, BUT AN EARLY RETURN AMONG HOOK
    // CALLS WOULD BREAK THE RULES OF HOOKS THE MOMENT IT DID.
    if (!team) return null;

    const outcome = team.is_champion
        ? 'Won the World Series'
        : postseasonExit
            ? `Lost ${postseasonExit.roundLabel} to ${postseasonExit.opponentAbbr}`
            : team.made_playoffs
                ? 'Made the playoffs'
                : 'Missed the playoffs';

    const outcomeColor = (team.is_champion || challengeResult === 'passed')
        ? '--success'
        : team.made_playoffs
            ? '--warning'
            : '--error';

    return (
        <div className="flex flex-col gap-2 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full md:px-4">
            {/* Headline */}
            <div className="px-4 flex items-center justify-between gap-3">
                <div >
                    <div className="flex items-center gap-1.5 flex-wrap">
                        <p className="text-[12px] text-(--text-tertiary)">
                            {summary.year} · Set {summary.set}
                            {!isOpenSim && team.replaced_abbr ? ` · took over ${team.replaced_abbr}` : ''}
                            {summary.seed !== null ? ` · seed ${summary.seed}` : ''}
                            {isResumed ? ' · resumed mid-season' : ''}
                            {summary.real_stats_as_of ? ` · stats as of ${new Date(summary.real_stats_as_of).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}` : ''}
                        </p>
                        {isOpenSim && onFocusChange && (
                            <CustomSelect
                                value={clubAbbr}
                                onChange={onFocusChange}
                                options={clubOptions}
                                buttonClassName="text-[11px] py-0.5 px-2 rounded-md bg-(--background-tertiary) text-(--text-primary) text-nowrap cursor-pointer"
                            />
                        )}
                    </div>
                    <h1 className="text-[24px] font-black text-(--text-primary) leading-tight">
                        {team.wins}<span className="text-(--text-tertiary)">-</span>{team.losses}
                        {team.is_champion && <FaTrophy className="inline ml-2 text-[18px] text-(--secondary)" />}
                    </h1>
                    <p className={`text-[13px] ${outcomeColor}`}>
                        {teamName}
                        {` ·  ${team.points} PTS`}
                    </p>
                </div>

                <div className={`flex flex-col items-center space-y-0 px-4 py-2 rounded-xl bg-(${outcomeColor})/15 font-bold text-(${outcomeColor})`}>
                    {challengeResult && (
                        <div className={`text-[12px] text-tertiary flex items-center gap-1 `}>
                            {challengeResult === 'passed' ? <FaCheck /> : <FaXmark />}
                            {challengeResult === 'passed' ? 'Challenge passed' : 'Challenge failed'}
                        </div>
                    )}
                    <div className="text-[15px]">
                        {team.division && team.division_rank
                            ? `${ordinal(team.division_rank)} in the ${team.division}`
                            : ''}
                    </div>
                    <div className={`text-[12px] text-tertiary`}>{outcome}</div>
                    {(onTryAgain || onRunAgain) && (
                        <button
                            type="button"
                            onClick={onTryAgain ?? onRunAgain}
                            className="flex items-center gap-1.5 px-3 py-1 mt-1 rounded-lg bg-(--background-tertiary) text-[12px] font-bold text-(--text-primary) hover:opacity-90 transition-opacity cursor-pointer shrink-0"
                        >
                            <FaArrowRotateLeft className="text-[10px]" />
                            {onTryAgain ? 'Edit & Try Again' : 'Run again'}
                        </button>
                    )}
                </div>

            </div>

            {challengeStanding && (
                <div className="mx-4 flex flex-wrap items-stretch gap-2 text-[12px]">
                    <div className="flex flex-col rounded-lg bg-(--background-tertiary) px-3 py-2">
                        <span className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">Attempt</span>
                        <span className="font-black text-(--text-primary)">#{challengeStanding.attempts}</span>
                    </div>
                    <div className="flex flex-col rounded-lg bg-(--background-tertiary) px-3 py-2">
                        <span className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">Budget</span>
                        <span className="font-black text-(--text-primary) tabular-nums">
                            {challengeStanding.roster_points ?? '?'}
                            {challengeStanding.pts_limit != null && (
                                <span className="font-semibold text-(--text-tertiary)"> / {challengeStanding.pts_limit} pts</span>
                            )}
                        </span>
                        {challengeStanding.pts_limit != null && challengeStanding.roster_points != null && (
                            <span className="text-[10px] text-(--text-tertiary)">
                                {challengeStanding.pts_limit - challengeStanding.roster_points >= 0
                                    ? `${challengeStanding.pts_limit - challengeStanding.roster_points} under cap`
                                    : `${challengeStanding.roster_points - challengeStanding.pts_limit} over cap`}
                            </span>
                        )}
                    </div>
                    {(() => {
                        const inner = (
                            <>
                                <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">
                                    Leaderboard
                                    {onOpenChallengeLeaderboard && <FaChevronRight className="text-[8px]" />}
                                </span>
                                <span className="font-black text-(--text-primary)">
                                    {challengeStanding.rank != null
                                        ? `${ordinal(challengeStanding.rank)} of ${challengeStanding.entrants}`
                                        : `${challengeStanding.entrants} entered`}
                                </span>
                                <span className={`text-[10px] font-bold ${challengeStanding.is_best ? 'text-(--success)' : 'text-(--text-tertiary)'}`}>
                                    {challengeStanding.is_best ? 'New personal best' : "Didn't beat your best"}
                                </span>
                            </>
                        );
                        return onOpenChallengeLeaderboard ? (
                            <button
                                type="button"
                                onClick={onOpenChallengeLeaderboard}
                                className="flex flex-col text-left rounded-lg bg-(--background-tertiary) px-3 py-2 hover:bg-(--divider) transition-colors cursor-pointer"
                            >
                                {inner}
                            </button>
                        ) : (
                            <div className="flex flex-col rounded-lg bg-(--background-tertiary) px-3 py-2">{inner}</div>
                        );
                    })()}
                </div>
            )}

            <Tabs.Root defaultValue="summary" className="flex flex-col">
                <Tabs.List className="flex px-3 border-b border-(--divider) gap-x-1 py-1 overflow-x-auto scrollbar-hide">
                    <Tabs.Trigger value="summary" className={TAB_TRIGGER_CLASS}><FaChartLine className={TAB_ICON_CLASS} />Summary</Tabs.Trigger>
                    <Tabs.Trigger value="schedule" className={TAB_TRIGGER_CLASS}><FaCalendarDays className={TAB_ICON_CLASS} />Schedule</Tabs.Trigger>
                    {summary.postseason.length > 0 && (
                        <Tabs.Trigger value="postseason" className={TAB_TRIGGER_CLASS}><FaSitemap className={TAB_ICON_CLASS} />Postseason</Tabs.Trigger>
                    )}
                    <Tabs.Trigger value="batting" className={TAB_TRIGGER_CLASS}><FaBaseballBatBall className={TAB_ICON_CLASS} />Batting</Tabs.Trigger>
                    <Tabs.Trigger value="pitching" className={TAB_TRIGGER_CLASS}><FaBaseball className={TAB_ICON_CLASS} />Pitching</Tabs.Trigger>
                    <Tabs.Trigger value="standings" className={TAB_TRIGGER_CLASS}><FaTableList className={TAB_ICON_CLASS} />Standings</Tabs.Trigger>
                    <Tabs.Trigger value="leaders" className={TAB_TRIGGER_CLASS}><FaRankingStar className={TAB_ICON_CLASS} />League Leaders</Tabs.Trigger>
                    {hasTransactions && (
                        <Tabs.Trigger value="transactions" className={TAB_TRIGGER_CLASS}><FaRightLeft className={TAB_ICON_CLASS} />Transactions</Tabs.Trigger>
                    )}
                    {hasAwards && (
                        <Tabs.Trigger value="awards" className={TAB_TRIGGER_CLASS}><FaTrophy className={TAB_ICON_CLASS} />Awards</Tabs.Trigger>
                    )}
                    <Tabs.Trigger value="league_stats" className={TAB_TRIGGER_CLASS}><FaDiceD20 className={TAB_ICON_CLASS} />League Stats</Tabs.Trigger>

                </Tabs.List>

                {/* Summary */}
                <Tabs.Content value="summary" className="focus:outline-none px-4 pt-3">
                    <SimSummaryTab summary={summary} teamKey={teamKey} />
                </Tabs.Content>

                {/* Schedule */}
                <Tabs.Content value="schedule" className="focus:outline-none px-4 pt-3">
                    <div className="flex flex-wrap gap-1 mb-4">
                        {games.map((game, i) => (
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
                            {gamesByMonth.map(month => (
                                <tbody key={month.key}>
                                    <tr className="bg-(--background-tertiary)">
                                        <td colSpan={5} className="py-1.5 px-2 font-bold text-(--text-primary)">
                                            {month.label} 
                                            <span className="ml-2 font-semibold tabular-nums text-(--text-tertiary)">{month.wins}-{month.losses}</span>
                                            {month.temp === 'hot' && <FaFire className="inline ml-2 -mt-0.5 text-(--error)" title="Hot month" />}
                                            {month.temp === 'cold' && <FaSnowflake className="inline ml-2 -mt-0.5 text-(--showdown-blue)" title="Cold month" />}
                                        </td>
                                    </tr>
                                    {month.games.map((game, i) => (
                                        <tr key={`${month.key}-${i}`} className="border-b border-(--divider)/50">
                                            <td className="py-1.5 pl-4 pr-3 text-(--text-tertiary)">{game.date}</td>
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
                            ))}
                        </table>
                    </div>
                </Tabs.Content>

                <Tabs.Content value="batting" className="focus:outline-none px-4 pt-3">
                    {hitterKpis.length > 0 && (
                        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-3">
                            {hitterKpis.map(kpi => <KpiTile key={kpi.label} label={kpi.label} value={kpi.value} />)}
                        </div>
                    )}
                    <SimStatsTable rows={hitters} columns={HITTER_COLUMNS} emptyLabel="No hitters on this roster." cardsEnabled identities={summary.identities} />
                </Tabs.Content>

                <Tabs.Content value="pitching" className="focus:outline-none px-4 pt-3">
                    {pitcherKpis.length > 0 && (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                            {pitcherKpis.map(kpi => <KpiTile key={kpi.label} label={kpi.label} value={kpi.value} />)}
                        </div>
                    )}
                    <SimStatsTable rows={pitchers} columns={PITCHER_COLUMNS} emptyLabel="No pitchers on this roster." cardsEnabled identities={summary.identities} />
                </Tabs.Content>

                {/* League Stats */}
                <Tabs.Content value="league_stats" className="focus:outline-none px-4 pt-3">
                    {leagueStatsKpis.length > 0 ? (
                        <>
                            <p className="text-[11px] text-(--text-tertiary) mb-2">
                                League-wide across the full season — not specific to {teamName}.
                            </p>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-3">
                                {leagueStatsKpis.map(kpi => <KpiTile key={kpi.label} label={kpi.label} value={kpi.value} />)}
                            </div>
                        </>
                    ) : (
                        <p className="text-[12px] text-(--text-tertiary)">No league stats to show.</p>
                    )}
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
                        <SimStatsTable rows={summary.top_players?.position_player ?? []} columns={HITTER_COLUMNS} emptyLabel="No qualified hitters." cardsEnabled identities={summary.identities} />
                    </div>
                    <div>
                        <p className="text-[12px] font-bold text-(--text-primary) mb-1">Top Starting Pitchers (ERA)</p>
                        <SimStatsTable rows={summary.top_players?.starting_pitcher ?? []} columns={PITCHER_COLUMNS} emptyLabel="No qualified starters." cardsEnabled identities={summary.identities} />
                    </div>
                    <div>
                        <p className="text-[12px] font-bold text-(--text-primary) mb-1">Top Relief Pitchers (ERA)</p>
                        <SimStatsTable rows={summary.top_players?.relief_pitcher ?? []} columns={PITCHER_COLUMNS} emptyLabel="No qualified relievers." cardsEnabled identities={summary.identities} />
                    </div>
                </Tabs.Content>

                {/* Transactions */}
                {hasTransactions && (
                    <Tabs.Content value="transactions" className="focus:outline-none px-4 pt-3">
                        <SimTransactionsTab summary={summary} teamKey={teamKey} />
                    </Tabs.Content>
                )}

                {/* Awards */}
                {hasAwards && summary.awards && (
                    <Tabs.Content value="awards" className="focus:outline-none px-2 pt-3">
                        <SimAwardsList awards={summary.awards} identities={summary.identities} />
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
