import type { ReactNode } from "react";
import { FaStar } from "react-icons/fa6";
import { FaTerminal } from "react-icons/fa";

import type { GameView } from "../../domain/game";
import { resolveCardKey } from "../../domain/players";
import { TeamChip } from "../shared/TeamChip";
import { type ShowdownBotCardCompact } from "../../api/showdownBotCard";
import { type CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { CardItemCompact, CardItemCompactFromCardDatabaseRecord } from "../cards/CardItemCompact";
import { BasesDiamond } from "./BasesDiamond";
import { GameStatePlate } from "./GameStatePlate";
import { Plate } from "../shared/Plate";
import { buttonClass } from "../shared/buttonStyles";
import { FIELD_LABEL_CLASS } from "../shared/fieldStyles";
import { NEUTRAL_TEAM_COLOR, NEUTRAL_TEAM_COLOR_SECONDARY } from '../../functions/colors';

type GameItemProps = {
    game: GameView;
    isStarred?: boolean;
    showMatchupDetails?: boolean;
    playerIdForLinescoreHighlight?: number;
    cardMap?: Record<string | number, CardDatabaseRecord>;
    isLoadingCards?: boolean;
    onSelect?: (gamePk: number) => void;
    onSimSelect?: (gamePk: number) => void;
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

export default function GameItem({ game, isStarred, showMatchupDetails, playerIdForLinescoreHighlight, cardMap, isLoadingCards, onSelect, onSimSelect }: GameItemProps) {
    const isFinal = game.state === 'FINAL';
    const isNotStarted = game.state === 'PREVIEW';
    const isPostponed = game.state === 'POSTPONED';
    const isInProgress = game.state === 'LIVE';
    const hasStarted = !isNotStarted;

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

    const liveBasesAndOuts = (
        <BasesDiamond bases={game.situation?.bases} outs={game.situation?.outs ?? 0} className="px-4" />
    );

    const playerIdLinescoreMatch = playerIdForLinescoreHighlight
        ? (game.away.boxscore?.batting.find(p => p.id === playerIdForLinescoreHighlight && p.isInLineup) || game.home.boxscore?.batting.find(p => p.id === playerIdForLinescoreHighlight && p.isInLineup))
            || (game.away.boxscore?.pitching.find(p => p.id === playerIdForLinescoreHighlight) || game.home.boxscore?.pitching.find(p => p.id === playerIdForLinescoreHighlight))
        : undefined;
    const playerLinescoreSummary = playerIdLinescoreMatch ? (
        <div className="mt-2 px-3 py-1 rounded-control border border-(--gold)/50 bg-(--gold)/5 text-(--gold) text-sm font-bold">
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
        color_primary: NEUTRAL_TEAM_COLOR,
        color_secondary: NEUTRAL_TEAM_COLOR_SECONDARY,
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

    const gamePk = typeof game.id === 'number' ? game.id : Number(game.id);

    return (
        <div
            className={`rounded-card border bg-(--background-secondary) overflow-hidden p-3 ${isStarred ? 'border-(--gold)/60' : 'border-(--divider)'} ${onSelect ? 'cursor-pointer hover:border-(--rule-strong) transition-colors' : ''}`}
            onClick={onSelect ? () => onSelect(gamePk) : undefined}
            role={onSelect ? "button" : undefined}
            tabIndex={onSelect ? 0 : undefined}
            onKeyDown={onSelect ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(gamePk); } } : undefined}
        >
            {game.seriesLabel && game.seriesLabel !== "Regular Season" && (
                <Plate variant="navy" size="sm" className="mb-1.5">{game.seriesLabel}</Plate>
            )}

            <div className="pb-2 flex items-center justify-between gap-2">
                <div className="flex items-center gap-1 text-[13px] font-semibold uppercase tabular-nums text-(--text-secondary)">
                    {isFinal && (
                        <span>{formatGameDate(game.date)}</span>
                    )}
                    {!isFinal && hasStarted && (
                        <span>{game.situation ? `${game.situation.isTop ? 'TOP' : 'BOT'} ${game.situation.inningLabel}` : ''}</span>
                    )}
                    {!isFinal && !hasStarted && (
                        <span>{formatGameTime(game.date)}</span>
                    )}
                    {isStarred && <FaStar className="text-(--gold) h-3 w-3 shrink-0" />}
                </div>
                <GameStatePlate state={game.state} detailedState={game.detailedState} />
            </div>

            <div className="border-t border-(--divider)" />

            <div className="flex items-center gap-4">

                {/* Teams and Scores */}
                <div className="w-full space-y-2 py-2">
                    {[game.away, game.home].map(side => (
                        <div key={side.team.abbreviation} className="flex items-center justify-between gap-3">
                            <TeamChip team={side.team} record={side.record} />
                            {hasStarted && side.score != null && (
                                <span className="font-display-upright text-[22px] leading-none tabular-nums text-(--text-primary)">{side.score}</span>
                            )}
                        </div>
                    ))}
                </div>

                {/* Sim this - shown in place of the score for games that haven't started */}
                {isNotStarted && onSimSelect && (
                    <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); onSimSelect(gamePk); }}
                        className={buttonClass('primary', 'sm')}
                    >
                        <FaTerminal className="h-3 w-3" />
                        Sim it
                    </button>
                )}

                {/* Live Bases and Outs */}
                {isInProgress && liveBasesAndOuts}

            </div>

            {isNotStarted && !isPostponed && showMatchupDetails && (
                <MatchupRow
                    labels={['Away Probable', 'Home Probable']}
                    separator="vs"
                    left={awayProbableCardRecord
                        ? <CardItemCompactFromCardDatabaseRecord card={awayProbableCardRecord} hideDetails />
                        : <CardItemCompact card={awayProbableCardFallback} isLoading={isLoadingCards && game.away.probablePitcher?.id != null} hideDetails />}
                    right={homeProbableCardRecord
                        ? <CardItemCompactFromCardDatabaseRecord card={homeProbableCardRecord} hideDetails />
                        : <CardItemCompact card={homeProbableCardFallback} isLoading={isLoadingCards && game.home.probablePitcher?.id != null} hideDetails />}
                />
            )}

            {isInProgress && showMatchupDetails && (
                <MatchupRow
                    labels={['At Bat', 'Pitching']}
                    left={liveAtBatCardRecord
                        ? <CardItemCompactFromCardDatabaseRecord card={liveAtBatCardRecord} hideDetails />
                        : <CardItemCompact card={liveAtBatCardFallback} isLoading={isLoadingCards && game.situation?.batter?.id != null} hideDetails />}
                    right={livePitchingCardRecord
                        ? <CardItemCompactFromCardDatabaseRecord card={livePitchingCardRecord} hideDetails />
                        : <CardItemCompact card={livePitchingCardFallback} isLoading={isLoadingCards && game.situation?.pitcher?.id != null} hideDetails />}
                />
            )}

            {isFinal && showMatchupDetails && (
                <MatchupRow
                    labels={['Winning Pitcher', 'Losing Pitcher']}
                    left={winningPitcherCardRecord
                        ? <CardItemCompactFromCardDatabaseRecord card={winningPitcherCardRecord} hideDetails />
                        : <CardItemCompact card={winningPitcherCardFallback} isLoading={isLoadingCards && game.decisions?.winner?.id != null} hideDetails />}
                    right={losingPitcherCardRecord
                        ? <CardItemCompactFromCardDatabaseRecord card={losingPitcherCardRecord} hideDetails />
                        : <CardItemCompact card={losingPitcherCardFallback} isLoading={isLoadingCards && game.decisions?.loser?.id != null} hideDetails />}
                />
            )}

            {playerLinescoreSummary}

        </div>
    );
}

/** Two labeled compact cards side by side under the score: probables, the live at-bat, or the decisions. */
function MatchupRow({ labels, left, right, separator }: { labels: [string, string]; left: ReactNode; right: ReactNode; separator?: string }) {
    return (
        <>
            <div className="border-t border-(--divider) my-1" />
            <div className="flex justify-between items-center">
                <span className={FIELD_LABEL_CLASS}>{labels[0]}</span>
                <span className={FIELD_LABEL_CLASS}>{labels[1]}</span>
            </div>
            <div className="pt-1 flex gap-2 items-center">
                {left}
                {separator && <span className="text-[12px] text-(--text-tertiary)">{separator}</span>}
                {right}
            </div>
        </>
    );
}
