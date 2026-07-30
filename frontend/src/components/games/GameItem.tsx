import { FaStar } from "react-icons/fa6";

import type { GameView } from "../../domain/game";
import { cardKey } from "../../domain/players";
import { TeamChip } from "../shared/TeamChip";
import { type ShowdownBotCardCompact } from "../../api/showdownBotCard";
import { type CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { CardItemCompact, CardItemCompactFromCardDatabaseRecord } from "../cards/CardItemCompact";

type GameItemProps = {
    game: GameView;
    isStarred?: boolean;
    showMatchupDetails?: boolean;
    playerIdForLinescoreHighlight?: number;
    cardMap?: Record<string | number, CardDatabaseRecord>;
    isLoadingCards?: boolean;
    onSelect?: (gamePk: number) => void;
};

/** cardKey() is keyed on numeric MLB player ids; sim card_ids (strings) don't need the two-way suffix. */
const resolveCardKey = (id: number | string | undefined, role: "H" | "P"): string | undefined => {
    if (id == null) return undefined;
    return typeof id === "number" ? cardKey(id, role) : String(id);
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

const formatGameDate = (gameDate?: string, includeTime: boolean = false): string => {
    if (!gameDate) {
        return "TBD";
    }

    const parsedDate = new Date(gameDate);
    if (Number.isNaN(parsedDate.getTime())) {
        return "TBD";
    }

    return new Intl.DateTimeFormat(undefined, {
        month: 'short',
        day: 'numeric',
        hour: includeTime ? 'numeric' : undefined,
        minute: includeTime ? '2-digit' : undefined,
    }).format(parsedDate);
};

export default function GameItem({ game, isStarred, showMatchupDetails, playerIdForLinescoreHighlight, cardMap, isLoadingCards, onSelect }: GameItemProps) {
    const isFinal = game.state === 'FINAL';
    const isNotStarted = game.state === 'PREVIEW';
    const isPostponed = game.state === 'POSTPONED';
    const isInProgress = game.state === 'LIVE';
    const hasStarted = !isNotStarted;

    const awayRecord = game.away.record;
    const homeRecord = game.home.record;

    const batterName = game.situation?.batter?.name;
    const livePitcherName = game.situation?.pitcher?.name;
    const awayProbablePitcherName = game.away.probablePitcher?.name;
    const homeProbablePitcherName = game.home.probablePitcher?.name;
    const winningPitcherName = game.decisions?.winner?.name;
    const losingPitcherName = game.decisions?.loser?.name;

    // Card records from map — two-way players use a role suffix to pick the correct card.
    const awayProbableCardRecord = cardMap?.[resolveCardKey(game.away.probablePitcher?.id, 'P') ?? ''];
    const homeProbableCardRecord = cardMap?.[resolveCardKey(game.home.probablePitcher?.id, 'P') ?? ''];
    const liveAtBatCardRecord = cardMap?.[resolveCardKey(game.situation?.batter?.id, 'H') ?? ''];
    const livePitchingCardRecord = cardMap?.[resolveCardKey(game.situation?.pitcher?.id, 'P') ?? ''];
    const winningPitcherCardRecord = cardMap?.[resolveCardKey(game.decisions?.winner?.id, 'P') ?? ''];
    const losingPitcherCardRecord = cardMap?.[resolveCardKey(game.decisions?.loser?.id, 'P') ?? ''];

    const outs = Math.max(0, Math.min(3, game.situation?.outs ?? 0));
    const bases = game.situation?.bases;

    const liveBasesAndOuts = (
        <div className="flex-col gap-1 items-center px-4">
            <div className="relative w-8 h-8 mt-0.5 translate-x-0.5">
                <div className={`absolute top-0 left-1/2 transform -translate-x-1/2 w-2.5 h-2.5 rotate-45 ${
                    bases?.second ? 'bg-yellow-400' : 'bg-gray-400'
                }`} />
                <div className={`absolute bottom-1/3 left-0 w-2.5 h-2.5 rotate-45 ${
                    bases?.third ? 'bg-yellow-400' : 'bg-gray-400'
                }`} />
                <div className={`absolute bottom-1/3 right-0 w-2.5 h-2.5 rotate-45 ${
                    bases?.first ? 'bg-yellow-400' : 'bg-gray-400'
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

    const playerIdLinescoreMatch = playerIdForLinescoreHighlight
        ? (game.away.boxscore?.batting.find(p => p.id === playerIdForLinescoreHighlight && p.isInLineup) || game.home.boxscore?.batting.find(p => p.id === playerIdForLinescoreHighlight && p.isInLineup))
            || (game.away.boxscore?.pitching.find(p => p.id === playerIdForLinescoreHighlight) || game.home.boxscore?.pitching.find(p => p.id === playerIdForLinescoreHighlight))
        : undefined;
    const playerLinescoreSummary = playerIdLinescoreMatch ? (
        <div className="mt-2 px-3 py-1 rounded border border-yellow-400/50 bg-yellow-400/5 text-yellow-400 text-sm font-bold">
            {playerIdLinescoreMatch.name}: {playerIdLinescoreMatch.summary ?? '-'}
        </div>
    ) : null;

    const createPlaceholderCard = (
        idSuffix: string,
        name: string | undefined,
        team: string | undefined,
        detail: string,
    ): ShowdownBotCardCompact => ({
        id: `${game.id}-${idSuffix}`,
        name: name || 'TBD',
        year: game.date?.slice(0, 4) || '----',
        set: 'LIVE',
        points: 0,
        command: 0,
        is_pitcher: true,
        color_primary: '#1f2937',
        color_secondary: '#374151',
        team: team || 'N/A',
        positions_and_defense_string: detail,
        ip: null,
        outs: 0,
        speed: null,
        source: 'BOT',
        hand: null,
        hr_range: null,
    });

    const liveAtBatCardFallback = createPlaceholderCard('at-bat', batterName, game.away.team.abbreviation, 'At Bat');
    const livePitchingCardFallback = createPlaceholderCard('pitching', livePitcherName, game.home.team.abbreviation, 'Pitching');
    const awayProbableCardFallback = createPlaceholderCard('away-probable', awayProbablePitcherName, game.away.team.abbreviation, 'Away Probable');
    const homeProbableCardFallback = createPlaceholderCard('home-probable', homeProbablePitcherName, game.home.team.abbreviation, 'Home Probable');

    const winnerTeamAbbr = game.home.isWinner ? game.home.team.abbreviation : game.away.isWinner ? game.away.team.abbreviation : 'WIN';
    const loserTeamAbbr = game.home.isWinner ? game.away.team.abbreviation : game.away.isWinner ? game.home.team.abbreviation : 'LOSS';

    const winningPitcherCardFallback = createPlaceholderCard('winner', winningPitcherName, winnerTeamAbbr, 'Winning Pitcher');
    const losingPitcherCardFallback = createPlaceholderCard('loser', losingPitcherName, loserTeamAbbr, 'Losing Pitcher');

    const stateBadgeLabel = game.detailedState;
    const stateBadgeClasses = game.detailedState === 'Final'
        ? 'border-green-500/40 bg-(--success)/10 text-(--success)'
        : game.detailedState === 'Postponed'
            ? 'border-(--red)/40 bg-(--red)/10 text-(--red)'
            : isInProgress
                ? 'border-yellow-400/50 bg-yellow-400/5 text-yellow-400'
                : 'border-(--divider) bg-(--background-primary) text-(--text-secondary)';

    const gamePk = typeof game.id === 'number' ? game.id : Number(game.id);

    return (
        <div
            className={`rounded-xl border-2 bg-(--background-secondary) overflow-hidden p-3 ${isStarred ? 'border-yellow-400/50' : 'border-(--divider)'} ${onSelect ? 'cursor-pointer hover:border-(--text-secondary)/50 transition-colors' : ''}`}
            onClick={onSelect ? () => onSelect(gamePk) : undefined}
            role={onSelect ? "button" : undefined}
            tabIndex={onSelect ? 0 : undefined}
            onKeyDown={onSelect ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(gamePk); } } : undefined}
        >
            {game.seriesLabel && game.seriesLabel !== "Regular Season" && (
                <div className="bg-(--background-primary) text-(--text-primary) rounded-md px-3 py-1 text-center text-sm font-bold flex items-center justify-center gap-1.5">
                    <span>{game.seriesLabel}</span>
                </div>
                )
            }

            <div className="py-1 flex items-center justify-between gap-2">
                <div className="flex items-center space-x-1 text-sm font-extrabold text-(--text-primary)">
                    {isFinal && (
                        <span>{formatGameDate(game.date)}</span>
                    )}
                    {!isFinal && hasStarted && (
                        <span>{game.situation ? `${game.situation.isTop ? 'TOP' : 'BOT'} ${game.situation.inningLabel}` : ''}</span>
                    )}
                    {!isFinal && !hasStarted && (
                        <span>{formatGameTime(game.date)}</span>
                    )}
                    {isStarred && <FaStar className="text-yellow-400 h-3 w-3 shrink-0" />}
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
                        <TeamChip team={game.away.team} record={awayRecord} />
                        {hasStarted && game.away.score != null && (
                            <span className="font-black text-(--text-primary)">{game.away.score}</span>
                        )}
                    </div>

                    <div className="flex items-center justify-between gap-3">
                        <TeamChip team={game.home.team} record={homeRecord} />
                        {hasStarted && game.home.score != null && (
                            <span className="font-black text-(--text-primary)">{game.home.score}</span>
                        )}
                    </div>
                </div>

                {/* Live Bases and Outs */}
                {isInProgress && liveBasesAndOuts}

            </div>

            {isNotStarted && !isPostponed && showMatchupDetails && (
                <>
                    <div className="border-t border-(--divider) my-1" />
                    <div className="flex justify-between items-center">
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-bold text-(--quaternary)">Away Probable</span>
                        </div>
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-bold text-(--quaternary)">Home Probable</span>
                        </div>
                    </div>
                    <div className="pt-1 flex gap-2 items-center">
                        {awayProbableCardRecord
                            ? <CardItemCompactFromCardDatabaseRecord card={awayProbableCardRecord} hideDetails />
                            : <CardItemCompact card={awayProbableCardFallback} isLoading={isLoadingCards && game.away.probablePitcher?.id != null} hideDetails />}
                        <span className="text-[12px]">vs</span>
                        {homeProbableCardRecord
                            ? <CardItemCompactFromCardDatabaseRecord card={homeProbableCardRecord} hideDetails />
                            : <CardItemCompact card={homeProbableCardFallback} isLoading={isLoadingCards && game.home.probablePitcher?.id != null} hideDetails />}
                    </div>
                </>
            )}

            {isInProgress && showMatchupDetails && (
                <>
                    <div className="border-t border-(--divider) my-1" />
                    <div className="flex justify-between items-center">
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-bold text-(--quaternary)">At Bat</span>
                        </div>
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-bold text-(--quaternary)">Pitching</span>
                        </div>
                    </div>
                    <div className="pt-1 flex gap-2">
                        {liveAtBatCardRecord
                            ? <CardItemCompactFromCardDatabaseRecord card={liveAtBatCardRecord} hideDetails />
                            : <CardItemCompact card={liveAtBatCardFallback} isLoading={isLoadingCards && game.situation?.batter?.id != null} hideDetails />}
                        {livePitchingCardRecord
                            ? <CardItemCompactFromCardDatabaseRecord card={livePitchingCardRecord} hideDetails />
                            : <CardItemCompact card={livePitchingCardFallback} isLoading={isLoadingCards && game.situation?.pitcher?.id != null} hideDetails />}
                    </div>
                </>
            )}

            {isFinal && showMatchupDetails && (
                <>
                    <div className="border-t border-(--divider) my-1" />
                    <div className="flex justify-between items-center">
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-bold text-(--quaternary)">Winning Pitcher</span>
                        </div>
                        <div className="flex gap-1 items-center">
                            <span className="text-[12px] font-bold text-(--quaternary)">Losing Pitcher</span>
                        </div>
                    </div>
                    <div className="pt-1 flex gap-2">
                        {winningPitcherCardRecord
                            ? <CardItemCompactFromCardDatabaseRecord card={winningPitcherCardRecord} hideDetails />
                            : <CardItemCompact card={winningPitcherCardFallback} isLoading={isLoadingCards && game.decisions?.winner?.id != null} hideDetails />}
                        {losingPitcherCardRecord
                            ? <CardItemCompactFromCardDatabaseRecord card={losingPitcherCardRecord} hideDetails />
                            : <CardItemCompact card={losingPitcherCardFallback} isLoading={isLoadingCards && game.decisions?.loser?.id != null} hideDetails />}
                    </div>
                </>
            )}

            {playerLinescoreSummary && (
                <>
                    {playerLinescoreSummary}
                </>
            )}

        </div>
    );
}
