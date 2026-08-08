import { FaTrophy } from 'react-icons/fa6';
import type { SeasonSimSummary, SimSeriesLine, SimTeamIdentity } from '../../../api/sim';
import { TeamChip } from '../../shared/TeamChip';
import { fromSimTeamIdentity, fallbackIdentity } from '../../../domain/adapters/fromSim';

// Mirrors PostseasonRound in models.py (oldest to newest); WS is pulled out and rendered
// separately since it's the one round with no league.
const ROUND_ORDER = ['WC', 'DIV', 'CS', 'WS'];

function roundLabel(round: string, league: string | null): string {
    switch (round) {
        case 'WC': return league ? `${league} Wild Card` : 'Wild Card';
        case 'DIV': return league ? `${league}DS` : 'Division Series';
        case 'CS': return league ? `${league}CS` : 'Championship Series';
        case 'WS': return 'World Series';
        default: return round;
    }
}

/** Groups a league's series by round, in play order — however many rounds that league's format actually used. */
function groupByRound(seriesList: SimSeriesLine[]): [string, SimSeriesLine[]][] {
    const byRound = new Map<string, SimSeriesLine[]>();
    for (const series of seriesList) {
        const bucket = byRound.get(series.round) ?? [];
        bucket.push(series);
        byRound.set(series.round, bucket);
    }
    return ROUND_ORDER.filter(round => byRound.has(round)).map(round => [round, byRound.get(round)!]);
}

type IdentityLookup = (abbr: string | null) => SimTeamIdentity | null;

function Matchup({ series, identityFor, highlightAbbr }: { series: SimSeriesLine; identityFor: IdentityLookup; highlightAbbr?: string | null }) {
    const rows = [
        { abbr: series.away_team, wins: series.away_team_wins },
        { abbr: series.home_team, wins: series.home_team_wins },
    ];
    const isHighlighted = highlightAbbr != null && (series.away_team === highlightAbbr || series.home_team === highlightAbbr);

    return (
        <div className={`flex flex-col gap-1 rounded-lg border bg-(--background-tertiary) px-2.5 py-1.5 min-w-[150px] ${isHighlighted ? 'border-(--showdown-blue)' : 'border-(--divider)'}`}>
            {rows.map(row => {
                const identity = identityFor(row.abbr);
                const isWinner = series.winner === row.abbr;
                return (
                    <div key={row.abbr} className={`flex items-center justify-between gap-3 ${isWinner ? 'text-(--text-primary)' : 'text-(--text-tertiary)'}`}>
                        <TeamChip team={identity ? fromSimTeamIdentity(identity) : fallbackIdentity(row.abbr)} size="sm" />
                        <span className={`text-[12px] tabular-nums ${isWinner ? 'font-bold' : ''}`}>{row.wins}</span>
                    </div>
                );
            })}
        </div>
    );
}

function LeagueColumns({ league, rounds, identityFor, highlightAbbr }: {
    league: string;
    rounds: [string, SimSeriesLine[]][];
    identityFor: IdentityLookup;
    highlightAbbr?: string | null;
}) {
    return (
        <div className="flex items-stretch gap-6">
            {rounds.map(([round, seriesList]) => (
                <div key={round} className="flex flex-col gap-2">
                    <p className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary) text-center">
                        {roundLabel(round, league)}
                    </p>
                    <div className="flex flex-1 flex-col justify-around gap-4">
                        {seriesList.map((series, i) => (
                            <Matchup key={i} series={series} identityFor={identityFor} highlightAbbr={highlightAbbr} />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

function WorldSeriesPanel({ series, champion, identityFor, highlightAbbr }: {
    series: SimSeriesLine | null;
    champion: string | null;
    identityFor: IdentityLookup;
    highlightAbbr?: string | null;
}) {
    if (!series) return null;
    return (
        <div className="flex flex-col items-center justify-center gap-2 self-stretch px-2">
            <p className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">World Series</p>
            <Matchup series={series} identityFor={identityFor} highlightAbbr={highlightAbbr} />
            {champion && (
                <p className="flex items-center gap-1.5 text-[12px] font-bold text-(--text-primary) whitespace-nowrap">
                    <FaTrophy className="text-(--secondary)" />
                    {identityFor(champion)?.abbreviation ?? champion} won the World Series
                </p>
            )}
        </div>
    );
}

type Props = {
    summary: SeasonSimSummary;
    /** Schedule key of the sim'd team, so its matchups can be picked out of the bracket. */
    highlightAbbr?: string | null;
};

/**
 * Postseason bracket: two mirrored league columns (round by round, oldest to newest) converging
 * on a World Series panel in the middle — the classic postseason-picture layout. The round list
 * per league is derived from whatever series the sim actually produced, so it adapts on its own
 * to every format the engine supports (WC3's wild-card-plus-byes, WC1's no-wild-card-round,
 * pre-1969's LCS-less single World Series, etc.) without hardcoding a team count.
 */
export function SimBracket({ summary, highlightAbbr }: Props) {
    const identityFor: IdentityLookup = abbr => (abbr ? summary.identities[abbr] ?? null : null);

    const worldSeries = summary.postseason.find(series => series.round === 'WS') ?? null;
    const leagueSeries = summary.postseason.filter(series => series.round !== 'WS');
    const leagues = Array.from(new Set(leagueSeries.map(series => series.league).filter((l): l is string => !!l))).sort();

    // Anything that isn't a clean 2-league bracket (custom tournaments/round robins, or a format
    // with no league-scoped rounds at all) falls back to a flat list instead of a forced mirror.
    if (leagues.length !== 2) {
        return (
            <div className="flex flex-col gap-4">
                <WorldSeriesPanel series={worldSeries} champion={summary.champion} identityFor={identityFor} highlightAbbr={highlightAbbr} />
                {leagueSeries.length > 0 && (
                    <div className="flex flex-col gap-1.5">
                        {leagueSeries.map((series, i) => (
                            <div key={i} className="flex items-center gap-2 text-[12px] rounded-lg bg-(--background-tertiary) px-3 py-2">
                                <span className="text-(--text-tertiary) w-24 shrink-0 font-semibold">{roundLabel(series.round, series.league)}</span>
                                <span className="text-(--text-primary)">
                                    {identityFor(series.away_team)?.abbreviation ?? series.away_team} ({series.away_team_wins})
                                    {' @ '}
                                    {identityFor(series.home_team)?.abbreviation ?? series.home_team} ({series.home_team_wins})
                                </span>
                                {series.winner && (
                                    <span className="ml-auto font-bold text-(--showdown-blue)">
                                        {identityFor(series.winner)?.abbreviation ?? series.winner}
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    const [leagueA, leagueB] = leagues;
    const roundsA = groupByRound(leagueSeries.filter(s => s.league === leagueA));
    const roundsB = [...groupByRound(leagueSeries.filter(s => s.league === leagueB))].reverse();

    return (
        <div className="overflow-x-auto py-2">
            <div className="flex items-stretch justify-center gap-6 min-w-max px-2">
                <LeagueColumns league={leagueA} rounds={roundsA} identityFor={identityFor} highlightAbbr={highlightAbbr} />
                <WorldSeriesPanel series={worldSeries} champion={summary.champion} identityFor={identityFor} highlightAbbr={highlightAbbr} />
                <LeagueColumns league={leagueB} rounds={roundsB} identityFor={identityFor} highlightAbbr={highlightAbbr} />
            </div>
        </div>
    );
}
