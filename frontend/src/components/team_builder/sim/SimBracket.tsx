import { useState } from 'react';
import { FaTrophy } from 'react-icons/fa6';
import type { SeasonSimSummary, SeriesMVP, SimGameStarter, SimSeriesLine, SimTeamIdentity } from '../../../api/sim';
import { TeamChip } from '../../shared/TeamChip';
import { fromSimTeamIdentity, fallbackIdentity } from '../../../domain/adapters/fromSim';
import { roundLabel } from './roundLabel';
import CardIdentityCell from '../../cards/card_elements/CardIdentityCell';
import { CardDetail } from '../../cards/CardDetail';
import { Modal } from '../../shared/Modal';
import { useCardDetailModal } from '../../../hooks/useCardDetailModal';

// Mirrors PostseasonRound in models.py (oldest to newest); WS is pulled out and rendered
// separately since it's the one round with no league.
const ROUND_ORDER = ['WC', 'DIV', 'CS', 'WS'];

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

/** Round + league + matchup uniquely identifies a series within one summary — the bracket never
 * has two series in the same round/league with the same two teams. */
function seriesKey(series: SimSeriesLine): string {
    return `${series.round}|${series.league ?? ''}|${series.home_team}|${series.away_team}`;
}

type IdentityLookup = (abbr: string | null) => SimTeamIdentity | null;

function Matchup({ series, identityFor, highlightAbbr, isSelected, onSelect }: {
    series: SimSeriesLine;
    identityFor: IdentityLookup;
    highlightAbbr?: string | null;
    isSelected?: boolean;
    onSelect?: () => void;
}) {
    const rows = [
        { abbr: series.away_team, wins: series.away_team_wins },
        { abbr: series.home_team, wins: series.home_team_wins },
    ];
    const isHighlighted = highlightAbbr != null && (series.away_team === highlightAbbr || series.home_team === highlightAbbr);

    return (
        <div
            role={onSelect ? 'button' : undefined}
            onClick={onSelect}
            className={`
                flex flex-col gap-1 rounded-lg border bg-(--background-tertiary) px-2.5 py-1.5 min-w-24 max-w-48
                ${onSelect ? 'cursor-pointer hover:bg-(--background-quaternary)' : ''}
                ${isSelected ? 'border-(--showdown-blue) ring-1 ring-(--showdown-blue)' : isHighlighted ? 'border-(--showdown-blue)' : 'border-(--divider)'}
            `}
        >
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

function LeagueColumns({ league, rounds, identityFor, highlightAbbr, selectedKey, onSelectSeries }: {
    league: string;
    rounds: [string, SimSeriesLine[]][];
    identityFor: IdentityLookup;
    highlightAbbr?: string | null;
    selectedKey: string | null;
    onSelectSeries?: (series: SimSeriesLine) => void;
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
                            <Matchup
                                key={i} series={series} identityFor={identityFor} highlightAbbr={highlightAbbr}
                                isSelected={selectedKey === seriesKey(series)}
                                onSelect={onSelectSeries ? () => onSelectSeries(series) : undefined}
                            />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

function WorldSeriesPanel({ series, champion, identityFor, highlightAbbr, selectedKey, onSelectSeries }: {
    series: SimSeriesLine | null;
    champion: string | null;
    identityFor: IdentityLookup;
    highlightAbbr?: string | null;
    selectedKey: string | null;
    onSelectSeries?: (series: SimSeriesLine) => void;
}) {
    if (!series) return null;
    return (
        <div className="flex flex-col items-center justify-center gap-2 self-stretch px-2">
            <p className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">World Series</p>
            <Matchup
                series={series} identityFor={identityFor} highlightAbbr={highlightAbbr}
                isSelected={selectedKey === seriesKey(series)}
                onSelect={onSelectSeries ? () => onSelectSeries(series) : undefined}
            />
            {champion && (
                <p className="flex items-center gap-1.5 text-[12px] font-bold text-(--text-primary) whitespace-nowrap">
                    <FaTrophy className="text-(--secondary)" />
                    {identityFor(champion)?.abbreviation ?? champion} won the World Series
                </p>
            )}
        </div>
    );
}

/** One starting pitcher as a clickable card chip — command badge + name + points, opening the
 * real Showdown card modal, the same display/click behavior the League Leaders tables use. */
function StarterChip({ starter, identity, onOpen, isFetching }: {
    starter: SimGameStarter | null | undefined;
    identity: SimTeamIdentity | null;
    onOpen: (starter: SimGameStarter) => void;
    isFetching: boolean;
}) {
    if (!starter) return <span className="text-(--text-tertiary)">—</span>;
    const clickable = !!starter.card_source;
    return (
        <button
            type="button"
            disabled={!clickable}
            onClick={clickable ? () => onOpen(starter) : undefined}
            className={`text-left rounded-md ${clickable ? 'cursor-pointer hover:bg-(--background-primary)/50' : ''} ${isFetching ? 'opacity-50' : ''}`}
        >
            <CardIdentityCell
                name={starter.name}
                hasCard={clickable}
                isPitcher
                primaryColor={identity?.primary_color}
                secondaryColor={identity?.secondary_color}
                command={starter.command}
                team={identity?.abbreviation}
                points={starter.points}
            />
        </button>
    );
}

/** Per-game results for one or all postseason series, one section per series (in bracket order:
 * WC → DIV → CS → WS) the way the Schedule tab breaks the regular season into months. Each
 * section header carries the series result and, for the LCS / World Series, the series MVP. */
function PostseasonGameResults({ seriesList, seriesMvps, identityFor, selectedKey }: {
    seriesList: SimSeriesLine[];
    seriesMvps: SeriesMVP[];
    identityFor: IdentityLookup;
    selectedKey: string | null;
}) {
    const { selected, open, close, isFetching } = useCardDetailModal();
    const openStarter = (starter: SimGameStarter) => open(starter.id, starter.card_source ?? 'BOT');
    const abbr = (team: string | null) => (team ? identityFor(team)?.abbreviation ?? team : '—');
    const mvpFor = (series: SimSeriesLine) =>
        seriesMvps.find(m => m.round === series.round && (m.league ?? null) === (series.league ?? null));

    const shown = (selectedKey ? seriesList.filter(s => seriesKey(s) === selectedKey) : seriesList)
        .filter(s => (s.games ?? []).length > 0);
    const hasStarters = shown.some(s => (s.games ?? []).some(g => g.home_starting_pitcher || g.away_starting_pitcher));
    const colCount = hasStarters ? 7 : 4;

    if (shown.length === 0) {
        return <p className="text-[13px] text-(--text-tertiary) py-6 text-center">No game data available for this series.</p>;
    }

    return (
        <div className="overflow-x-auto border border-(--divider) rounded-xl">
            <table className="w-full text-[12px] whitespace-nowrap">
                <thead>
                    <tr className="text-(--text-tertiary) border-b border-(--divider)">
                        <th className="text-left font-semibold py-2 px-3">Game</th>
                        <th className="text-left font-semibold py-2 pr-2">Matchup</th>
                        <th className="text-right font-semibold py-2 px-2">Score</th>
                        <th className="text-right font-semibold py-2 px-2">Winner</th>
                        {hasStarters && <th className="text-left font-semibold py-2 px-2" colSpan={3}>Starting Pitchers</th>}
                    </tr>
                </thead>
                {shown.map(series => {
                    const mvp = mvpFor(series);
                    const loser = series.winner === series.home_team ? series.away_team : series.home_team;
                    const winnerWins = series.winner === series.home_team ? series.home_team_wins : series.away_team_wins;
                    const loserWins = series.winner === series.home_team ? series.away_team_wins : series.home_team_wins;
                    return (
                        <tbody key={seriesKey(series)}>
                            <tr className="bg-(--background-tertiary)">
                                <td colSpan={colCount} className="py-1.5 px-2">
                                    <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                                        <span className="font-bold text-(--text-primary)">{roundLabel(series.round, series.league)}</span>
                                        {series.winner ? (
                                            <span className="font-semibold tabular-nums text-(--text-tertiary)">
                                                {abbr(series.winner)} def. {abbr(loser)} {winnerWins}–{loserWins}
                                            </span>
                                        ) : (
                                            <span className="tabular-nums text-(--text-tertiary)">
                                                {abbr(series.away_team)} {series.away_team_wins}–{series.home_team_wins} {abbr(series.home_team)}
                                            </span>
                                        )}
                                        {mvp && (
                                            <span className="flex items-center gap-1 text-(--text-tertiary)">
                                                <FaTrophy className="text-[10px] text-(--secondary)" />
                                                Series MVP:
                                                <button
                                                    type="button"
                                                    onClick={() => open(mvp.player.id, mvp.player.card_source ?? 'BOT')}
                                                    className="font-semibold text-(--text-secondary) hover:text-(--text-primary) cursor-pointer"
                                                >
                                                    {mvp.player.name}
                                                </button>
                                                <span>· {mvp.value_label}</span>
                                            </span>
                                        )}
                                    </div>
                                </td>
                            </tr>
                            {(series.games ?? []).map((game, i) => (
                                <tr key={i} className="border-b border-(--divider)/50">
                                    <td className="py-1.5 pl-4 pr-3 text-(--text-tertiary)">
                                        G{i + 1} <span className="text-(--text-tertiary)/70">· {game.date}</span>
                                    </td>
                                    <td className="py-1.5 pr-3 text-(--text-primary)">
                                        {abbr(game.away_team)}{' @ '}{abbr(game.home_team)}
                                    </td>
                                    <td className="text-right py-1.5 px-2 tabular-nums text-(--text-secondary)">
                                        {game.away_score}–{game.home_score}
                                    </td>
                                    <td className="text-right py-1.5 px-2 font-bold text-(--showdown-blue)">
                                        {abbr(game.winner)}
                                    </td>
                                    {hasStarters && (
                                        <>
                                            <td className="py-1.5 pl-2 pr-1">
                                                <StarterChip
                                                    starter={game.away_starting_pitcher} identity={identityFor(game.away_team)}
                                                    onOpen={openStarter} isFetching={!!game.away_starting_pitcher && isFetching(game.away_starting_pitcher.id)}
                                                />
                                            </td>
                                            <td className="py-1.5 px-1 text-[10px] text-(--text-tertiary)">vs</td>
                                            <td className="py-1.5 pl-1 pr-2">
                                                <StarterChip
                                                    starter={game.home_starting_pitcher} identity={identityFor(game.home_team)}
                                                    onOpen={openStarter} isFetching={!!game.home_starting_pitcher && isFetching(game.home_starting_pitcher.id)}
                                                />
                                            </td>
                                        </>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    );
                })}
            </table>
            <div className={selected ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={close} isVisible={!!selected}>
                    <CardDetail showdownBotCardData={selected} hideTrendGraphs={true} context="sim_result" parent="sim_result" />
                </Modal>
            </div>
        </div>
    );
}

type Props = {
    summary: SeasonSimSummary;
    /** Schedule key of the sim'd team, so its matchups can be picked out of the bracket. */
    highlightAbbr?: string | null;
    /** Renders a per-game results table below the bracket, filterable by clicking a matchup. */
    showGameResults?: boolean;
};

/**
 * Postseason bracket: two mirrored league columns (round by round, oldest to newest) converging
 * on a World Series panel in the middle — the classic postseason-picture layout. The round list
 * per league is derived from whatever series the sim actually produced, so it adapts on its own
 * to every format the engine supports (WC3's wild-card-plus-byes, WC1's no-wild-card-round,
 * pre-1969's LCS-less single World Series, etc.) without hardcoding a team count.
 */
export function SimBracket({ summary, highlightAbbr, showGameResults = false }: Props) {
    const identityFor: IdentityLookup = abbr => (abbr ? summary.identities[abbr] ?? null : null);
    const [selectedKey, setSelectedKey] = useState<string | null>(null);
    const onSelectSeries = showGameResults
        ? (series: SimSeriesLine) => setSelectedKey(prev => (prev === seriesKey(series) ? null : seriesKey(series)))
        : undefined;

    const worldSeries = summary.postseason.find(series => series.round === 'WS') ?? null;
    const leagueSeries = summary.postseason.filter(series => series.round !== 'WS');
    const leagues = Array.from(new Set(leagueSeries.map(series => series.league).filter((l): l is string => !!l))).sort();

    const gameResults = showGameResults && (
        <PostseasonGameResults
            seriesList={summary.postseason}
            seriesMvps={summary.awards?.series_mvps ?? []}
            identityFor={identityFor}
            selectedKey={selectedKey}
        />
    );

    // Anything that isn't a clean 2-league bracket (custom tournaments/round robins, or a format
    // with no league-scoped rounds at all) falls back to a flat list instead of a forced mirror.
    if (leagues.length !== 2) {
        return (
            <div className="flex flex-col gap-4">
                <WorldSeriesPanel series={worldSeries} champion={summary.champion} identityFor={identityFor} highlightAbbr={highlightAbbr} selectedKey={selectedKey} onSelectSeries={onSelectSeries} />
                {leagueSeries.length > 0 && (
                    <div className="flex flex-col gap-1.5">
                        {leagueSeries.map((series, i) => (
                            <div
                                key={i}
                                role={onSelectSeries ? 'button' : undefined}
                                onClick={onSelectSeries ? () => onSelectSeries(series) : undefined}
                                className={`
                                    flex items-center gap-2 text-[12px] rounded-lg bg-(--background-tertiary) px-3 py-2
                                    ${onSelectSeries ? 'cursor-pointer hover:bg-(--background-quaternary)' : ''}
                                    ${selectedKey === seriesKey(series) ? 'ring-1 ring-(--showdown-blue)' : ''}
                                `}
                            >
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
                {gameResults}
            </div>
        );
    }

    const [leagueA, leagueB] = leagues;
    const roundsA = groupByRound(leagueSeries.filter(s => s.league === leagueA));
    const roundsB = [...groupByRound(leagueSeries.filter(s => s.league === leagueB))].reverse();

    return (
        <div className="flex flex-col gap-4">
            <div className="overflow-x-auto py-2 scrollbar-hide">
                <div className="flex items-stretch justify-center gap-6 min-w-max px-2">
                    <LeagueColumns league={leagueA} rounds={roundsA} identityFor={identityFor} highlightAbbr={highlightAbbr} selectedKey={selectedKey} onSelectSeries={onSelectSeries} />
                    <WorldSeriesPanel series={worldSeries} champion={summary.champion} identityFor={identityFor} highlightAbbr={highlightAbbr} selectedKey={selectedKey} onSelectSeries={onSelectSeries} />
                    <LeagueColumns league={leagueB} rounds={roundsB} identityFor={identityFor} highlightAbbr={highlightAbbr} selectedKey={selectedKey} onSelectSeries={onSelectSeries} />
                </div>
            </div>
            {gameResults}
        </div>
    );
}
