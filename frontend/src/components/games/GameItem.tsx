import ReactCountryFlag from "react-country-flag";
import { FaStar } from "react-icons/fa6";

import { countryCodeForTeam } from "../../functions/flags";
import { getReadableTextColor } from "../../functions/colors";
import { type GameScheduled } from "../../api/mlbAPI";
import { type ShowdownBotCardCompact } from "../../api/showdownBotCard";
import { CardItemCompact } from "../cards/CardItemCompact";

type GameItemProps = {
    game: GameScheduled;
    sportId?: number;
    isStarred?: boolean;
    onSelect?: (gamePk: number) => void;
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

export default function GameItem({ game, sportId, isStarred, onSelect }: GameItemProps) {
    const awayTeam = game.teams?.away?.team;
    const homeTeam = game.teams?.home?.team;
    const awayAbbr = awayTeam?.abbreviation || awayTeam?.name || "AWAY";
    const homeAbbr = homeTeam?.abbreviation || homeTeam?.name || "HOME";
    const awayScore = game.teams?.away?.score;
    const homeScore = game.teams?.home?.score;
    const codedGameState = game.status?.coded_game_state;
    const isFinal = codedGameState === 'F' || game.status?.status_code === 'F';
    const isNotStarted = codedGameState === 'P' || codedGameState === 'S';
    const isInProgress = !isFinal && !isNotStarted;
    const hasStarted = !isNotStarted;

    const awayCountryCode = countryCodeForTeam(sportId || 0, awayAbbr);
    const homeCountryCode = countryCodeForTeam(sportId || 0, homeAbbr);

    const awayBadgeBg = awayTeam?.primary_color ?? undefined;
    const awayBadgeText = awayBadgeBg ? getReadableTextColor(awayBadgeBg, '#ffffff') : undefined;
    const homeBadgeBg = homeTeam?.primary_color ?? undefined;
    const homeBadgeText = homeBadgeBg ? getReadableTextColor(homeBadgeBg, '#ffffff') : undefined;

    const awayRecord = game.teams?.away?.league_record;
    const homeRecord = game.teams?.home?.league_record;

    const batterName = game.linescore?.offense?.batter?.full_name;
    const livePitcherName = game.linescore?.defense?.pitcher?.full_name;
    const awayProbablePitcherName = game.teams?.away?.probable_pitcher?.full_name;
    const homeProbablePitcherName = game.teams?.home?.probable_pitcher?.full_name;
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
                        className={`h-2 w-2 rounded-full border ${outIndex < outs ? 'bg-yellow-400' : 'bg-(--text-secondary)/40'}`}
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

    const liveAtBatCardFallback = createPlaceholderCard(
        'at-bat',
        batterName,
        game.linescore?.offense?.team?.abbreviation || awayAbbr,
        'At Bat',
    );
    const livePitchingCardFallback = createPlaceholderCard(
        'pitching',
        livePitcherName,
        game.linescore?.defense?.team?.abbreviation || homeAbbr,
        'Pitching',
    );

    const awayProbableCardFallback = createPlaceholderCard(
        'away-probable',
        awayProbablePitcherName,
        awayAbbr,
        'Away Probable',
    );
    const homeProbableCardFallback = createPlaceholderCard(
        'home-probable',
        homeProbablePitcherName,
        homeAbbr,
        'Home Probable',
    );

    const winnerTeamAbbr = game.teams?.home?.is_winner ? homeAbbr : game.teams?.away?.is_winner ? awayAbbr : 'WIN';
    const loserTeamAbbr = game.teams?.home?.is_winner ? awayAbbr : game.teams?.away?.is_winner ? homeAbbr : 'LOSS';

    const winningPitcherCardFallback = createPlaceholderCard('winner', winningPitcherName, winnerTeamAbbr, 'Winning Pitcher');
    const losingPitcherCardFallback = createPlaceholderCard('loser', losingPitcherName, loserTeamAbbr, 'Losing Pitcher');

    const awayProbableCard = game.teams?.away?.probable_pitcher?.card || awayProbableCardFallback;
    const homeProbableCard = game.teams?.home?.probable_pitcher?.card || homeProbableCardFallback;
    const liveAtBatCard = game.linescore?.offense?.batter?.card || liveAtBatCardFallback;
    const livePitchingCard = game.linescore?.defense?.pitcher?.card || livePitchingCardFallback;
    const winningPitcherCard = game.decisions?.winner?.card || winningPitcherCardFallback;
    const losingPitcherCard = game.decisions?.loser?.card || losingPitcherCardFallback;
    const stateBadgeLabel = isFinal ? 'Final' : isInProgress ? 'Live' : 'Preview';
    const stateBadgeClasses = isFinal
        ? 'border-green-500/40 bg-green-500/10 text-green-300'
        : isInProgress
            ? 'border-yellow-500/40 bg-yellow-500/10 text-yellow-300'
            : 'border-(--divider) bg-(--background-primary) text-(--text-secondary)';

    return (
        <div
            className={`rounded-xl border bg-(--background-secondary) overflow-hidden p-3 ${isStarred ? 'border-yellow-400/50' : 'border-(--divider)'} ${onSelect ? 'cursor-pointer hover:border-(--text-secondary)/50 transition-colors' : ''}`}
            onClick={onSelect ? () => onSelect(game.game_pk) : undefined}
            role={onSelect ? "button" : undefined}
            tabIndex={onSelect ? 0 : undefined}
            onKeyDown={onSelect ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(game.game_pk); } } : undefined}
        >
            <div className="bg-(--background-primary) text-(--text-primary) rounded-md px-3 py-1 text-center text-sm font-bold flex items-center justify-center gap-1.5">
                {isStarred && <FaStar className="text-yellow-400 h-3 w-3 shrink-0" />}
                <span>{(game.series_description || game.description || "Game")}
                {game.series_game_number ? ` | Game ${game.series_game_number}` : ""}</span>
            </div>

            <div className="py-2 flex items-center justify-between gap-2">
                <div className="text-md font-extrabold text-(--text-primary)">
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
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${stateBadgeClasses}`}>
                    {stateBadgeLabel}
                </span>
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
                            <span
                                className={`text-lg font-black ${awayBadgeBg ? 'px-1.5 py-0.5 rounded' : 'text-(--text-primary)'}`}
                                style={awayBadgeBg ? { backgroundColor: awayBadgeBg, color: awayBadgeText } : undefined}
                            >{awayAbbr}</span>
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
                            <span
                                className={`text-lg font-black ${homeBadgeBg ? 'px-1.5 py-0.5 rounded' : 'text-(--text-primary)'}`}
                                style={homeBadgeBg ? { backgroundColor: homeBadgeBg, color: homeBadgeText } : undefined}
                            >{homeAbbr}</span>
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
            
            {isNotStarted && (
                <>
                    <div className="border-t border-(--divider) my-2" />
                    <div className="flex justify-between items-center">
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-black text-(--text-primary)">Away Probable</span>
                        </div>
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-black text-(--text-primary)">Home Probable</span>
                        </div>
                    </div>
                    <div className="pt-1 flex gap-2">
                        <CardItemCompact card={awayProbableCard} />
                        <CardItemCompact card={homeProbableCard} />
                    </div>
                </>
            )}

            {isInProgress && (
                <>
                    <div className="border-t border-(--divider) my-2" />
                    <div className="flex justify-between items-center">
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-black text-(--text-primary)">At Bat</span>
                        </div>
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-black text-(--text-primary)">Pitching</span>
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
                            <span className="text-[12px] font-black text-(--text-primary)">Winning Pitcher</span>
                        </div>
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-black text-(--text-primary)">Losing Pitcher</span>
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
