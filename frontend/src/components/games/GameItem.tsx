import ReactCountryFlag from "react-country-flag";

import { countryCodeForTeam } from "../../functions/flags";
import { type GameScheduled } from "../../api/mlbAPI";
import { type ShowdownBotCardCompact } from "../../api/showdownBotCard";
import { CardItemCompact } from "../cards/CardItemCompact";

type GameItemProps = {
    game: GameScheduled;
    sportId?: number;
};

const formatGameTime = (gameDate?: string): string => {
    if (!gameDate) {
        return "TBD";
    }

    const parsedDate = new Date(gameDate);
    if (Number.isNaN(parsedDate.getTime())) {
        return "TBD";
    }

    return new Intl.DateTimeFormat(undefined, {
        hour: 'numeric',
        minute: '2-digit',
    }).format(parsedDate);
};

export default function GameItem({ game, sportId }: GameItemProps) {
    const awayTeam = game.teams?.away?.team;
    const homeTeam = game.teams?.home?.team;
    const awayAbbr = awayTeam?.abbreviation || awayTeam?.name || "AWAY";
    const homeAbbr = homeTeam?.abbreviation || homeTeam?.name || "HOME";
    const awayScore = game.teams?.away?.score;
    const homeScore = game.teams?.home?.score;
    const isFinal = game.status?.coded_game_state === 'F' || game.status?.status_code === 'F';
    const hasStarted = game.status?.coded_game_state === 'F' || game.status?.coded_game_state === 'I' || game.status?.coded_game_state === 'P' || game.status?.coded_game_state === 'L' || game.status?.coded_game_state === 'M' || game.status?.coded_game_state === 'D';
    const isInProgress = hasStarted && !isFinal;

    const awayCountryCode = countryCodeForTeam(sportId || 0, awayAbbr);
    const homeCountryCode = countryCodeForTeam(sportId || 0, homeAbbr);

    const awayRecord = game.teams?.away?.league_record;
    const homeRecord = game.teams?.home?.league_record;

    const batterName = game.linescore?.offense?.batter?.full_name;
    const livePitcherName = game.linescore?.defense?.pitcher?.full_name;
    const winningPitcherName = game.decisions?.winner?.full_name;
    const losingPitcherName = game.decisions?.loser?.full_name;

    const inningHalf = (game.linescore?.inning_half || game.linescore?.inning_state || '').toUpperCase();
    const inningNumber = game.linescore?.current_inning_ordinal || game.linescore?.current_inning || '';
    const outs = Math.max(0, Math.min(3, game.linescore?.outs ?? 0));

    const hasRunnerOnFirst = !!game.linescore?.offense?.first;
    const hasRunnerOnSecond = !!game.linescore?.offense?.second;
    const hasRunnerOnThird = !!game.linescore?.offense?.third;

    const liveBasesAndOuts = (
        <div className="flex-col gap-1 items-center px-4">
            <div className="relative w-8 h-8 mt-0.5 translate-x-0.5">
                <div className={`absolute top-0 left-1/2 transform -translate-x-1/2 w-2.5 h-2.5 rotate-45 ${
                    hasRunnerOnSecond ? 'bg-yellow-400' : 'bg-gray-400'
                }`} />
                <div className={`absolute bottom-1/3 left-0 w-2.5 h-2.5 rotate-45 ${
                    hasRunnerOnThird ? 'bg-yellow-400' : 'bg-gray-400'
                }`} />
                <div className={`absolute bottom-1/3 right-0 w-2.5 h-2.5 rotate-45 ${
                    hasRunnerOnFirst ? 'bg-yellow-400' : 'bg-gray-400'
                }`} />
            </div>

            <div className="flex items-center gap-1.5">
                {[0, 1, 2].map((outIndex) => (
                    <span
                        key={outIndex}
                        className={`h-2 w-2 rounded-full border ${outIndex < outs ? 'bg-(--text-primary)' : 'bg-(--text-secondary)/40'}`}
                    />
                ))}
            </div>
        </div>
    );

    const createPlaceholderCard = (
        idSuffix: string,
        name: string | undefined,
        team: string | undefined,
        detail: string,
    ): ShowdownBotCardCompact => ({
        id: `${game.game_pk}-${idSuffix}`,
        name: name || 'TBD',
        year: game.season || game.official_date?.slice(0, 4) || '----',
        set: 'LIVE',
        points: 0,
        command: 0,
        is_pitcher: true,
        color_primary: '#1f2937',
        color_secondary: '#374151',
        team: team || 'N/A',
        positions_and_defense_string: detail,
        ip: null,
    });

    const liveAtBatCard = createPlaceholderCard(
        'at-bat',
        batterName,
        game.linescore?.offense?.team?.name || awayAbbr,
        'At Bat',
    );
    const livePitchingCard = createPlaceholderCard(
        'pitching',
        livePitcherName,
        game.linescore?.defense?.team?.name || homeAbbr,
        'Pitching',
    );

    const winnerTeamAbbr = game.teams?.home?.is_winner ? homeAbbr : game.teams?.away?.is_winner ? awayAbbr : 'WIN';
    const loserTeamAbbr = game.teams?.home?.is_winner ? awayAbbr : game.teams?.away?.is_winner ? homeAbbr : 'LOSS';

    const winningPitcherCard = createPlaceholderCard('winner', winningPitcherName, winnerTeamAbbr, 'Winning Pitcher');
    const losingPitcherCard = createPlaceholderCard('loser', losingPitcherName, loserTeamAbbr, 'Losing Pitcher');

    return (
        <div
            className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-hidden p-3"
        >
            <div className="bg-(--background-primary) text-(--text-primary) rounded-md px-3 py-1 text-center text-sm font-bold">
                {(game.series_description || game.description || "Game")}
                {game.series_game_number ? ` | Game ${game.series_game_number}` : ""}
            </div>

            <div className="py-2 text-md font-extrabold text-(--text-primary)">
                {isFinal && (
                    <><span>FINAL</span></>
                )}
                {!isFinal && hasStarted && (
                    <span>{inningHalf && inningNumber ? `${inningHalf} ${inningNumber}` : ''}</span>
                )}
                {!isFinal && !hasStarted && (
                    <span>{formatGameTime(game.game_date)}</span>
                )}
            </div>

            <div className="border-t border-(--divider)" />

            <div className="flex items-center gap-4">

                {/* Teams and Scores */}
                <div className="w-full space-y-2 py-2">
                    <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2 min-w-0">
                            {sportId === 51 && awayCountryCode && (
                                <ReactCountryFlag countryCode={awayCountryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                            )}
                            <span className="text-lg font-black text-(--text-primary)">{awayAbbr}</span>
                            {awayRecord && (
                                <span className="text-[11px] font-semibold text-(--text-secondary)">{awayRecord.wins ?? 0} - {awayRecord.losses ?? 0}</span>
                            )}
                        </div>
                        {hasStarted && awayScore != null && (
                            <span className="text-lg font-black text-(--text-primary)">{awayScore}</span>
                        )}
                    </div>

                    <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2 min-w-0">
                            {sportId === 51 && homeCountryCode && (
                                <ReactCountryFlag countryCode={homeCountryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                            )}
                            <span className="text-lg font-black text-(--text-primary)">{homeAbbr}</span>
                            {homeRecord && (
                                <span className="text-[12px] font-semibold text-(--text-secondary)">{homeRecord.wins ?? 0} - {homeRecord.losses ?? 0}</span>
                            )}
                        </div>
                        {hasStarted && homeScore != null && (
                            <span className="text-lg font-black text-(--text-primary)">{homeScore}</span>
                        )}
                    </div>
                </div>
                
                {/* Live Bases and Outs */}
                {isInProgress && liveBasesAndOuts}

            </div>
            

            {!isFinal && (
                <>
                    <div className="border-t border-(--divider) my-2" />
                    <div className="flex justify-between items-center">
                        <div className="flex gap-1 items-center">
                            <span className="text-sm font-black text-(--text-primary)">At Bat</span>
                        </div>
                        <div className="flex gap-1 items-center">
                            <span className="text-sm font-black text-(--text-primary)">Pitching</span>
                        </div>
                    </div>
                    <div className="pt-1 flex gap-2">
                        <CardItemCompact card={liveAtBatCard} />
                        <CardItemCompact card={livePitchingCard} />
                    </div>
                </>
            )}

            {isFinal && (
                <>
                    <div className="border-t border-(--divider) my-2" />
                    <div className="flex justify-between items-center">
                        <div className="flex gap-1 items-center">
                            <span className="text-sm font-black text-(--text-primary)">Winning Pitcher</span>
                        </div>
                        <div className="flex gap-1 items-center">
                            <span className="text-sm font-black text-(--text-primary)">Losing Pitcher</span>
                        </div>
                    </div>
                    <div className="pt-1 flex gap-2">
                        <CardItemCompact card={winningPitcherCard} />
                        <CardItemCompact card={losingPitcherCard} />
                    </div>
                </>
            )}

        </div>
    );
}
