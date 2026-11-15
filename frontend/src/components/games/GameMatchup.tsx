/**
 * @fileoverview The current pitcher-vs-batter spotlight: the roll about to happen. Shows both
 * cards with the Showdown advantage split between them. A wide game board gives each card a corner
 * through `MatchupSide`; a narrow one uses `GameMatchup`, a row of compact cards with the winner of
 * a sim roll lifted to a full card so its chart can show where the swing landed.
 */
import type { GameView } from "../../domain/game";
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { CardItemFromCard, CardItemSkeleton } from "../cards/CardItem";
import type { AdvantageSide } from "../../domain/play";
import { CardItemCompactFromCard } from "../cards/CardItemCompact";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { BOARD_PANEL_CLASS } from "./boardStyles";
import { resolveMatchup, type MatchupSideData } from "./resolveMatchup";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

function PointsTrend({ card }: { card?: ShowdownBotCardAPIResponse }) {
    const change = card?.in_season_trends?.pts_change.day;
    if (change == null || change === 0) return null;
    return (
        <span className={`text-[10px] font-semibold tabular-nums ${change >= 0 ? "text-(--green)" : "text-(--red)"}`}>
            {change >= 0 ? "+" : ""}{change} PTS
        </span>
    );
}

type MatchupSideProps = {
    side: MatchupSideData;
    /** `compact` has no chart, for a row without the width for one. */
    variant?: "full" | "compact";
    isLoadingCards?: boolean;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    /** Replay hides the day's PTS change for the same reason as the box-score line. */
    hideTrend?: boolean;
    /** Sim only: this side won the advantage roll. */
    hasAdvantage?: boolean;
    /** Sim only: the chart result the swing landed on, lit up on the winning card. */
    chartHighlight?: string;
};

export function MatchupSide({ side, variant = "full", isLoadingCards, onCardSelect, hideTrend, hasAdvantage, chartHighlight }: MatchupSideProps) {
    const { label, player, response, summary, advantagePct } = side;
    const isCompact = variant === "compact";
    // A finished game's last frame has a pitcher but no one left to bat.
    if (!player) return null;

    return (
        <div className="min-w-0 space-y-1">
            <div className={`${BOARD_PANEL_CLASS} flex items-center justify-between gap-1.5 px-2 py-0.5`}>
                <div className="flex min-w-0 items-center gap-2">
                    <span className={`${CAPS_LABEL_CLASS} text-(--text-primary)`}>{label}</span>
                    {summary && <span className="truncate text-[11px] tabular-nums text-(--text-primary)">{summary}</span>}
                    {!hideTrend && <PointsTrend card={response} />}
                </div>
                {advantagePct != null && (
                    <div className="text-[11px] font-semibold text-(--text-primary) text-nowrap">
                        <span className="tabular-nums text-(--text-primary)">{advantagePct}%</span>{isCompact ? " adv" : " advantage"}
                    </div>
                )}
            </div>

            {response?.card ? (
                isCompact ? (
                    <CardItemCompactFromCard card={response.card} className="w-full" onClick={() => onCardSelect?.(response)} hasAdvantage={hasAdvantage} />
                ) : (
                    <CardItemFromCard card={response.card} className="w-full" onClick={() => onCardSelect?.(response)} hasAdvantage={hasAdvantage} chartHighlight={chartHighlight} />
                )
            ) : isLoadingCards ? (
                <CardItemSkeleton className="w-full" />
            ) : player.name ? (
                <div className="truncate rounded-card bg-(--background-secondary) px-2 py-1 text-sm font-semibold text-(--primary)">{player.name}</div>
            ) : isCompact ? (
                <CardItemCompactFromCard card={undefined} className="w-full opacity-50" />
            ) : (
                <CardItemFromCard card={undefined} className="w-full opacity-50" />
            )}
        </div>
    );
}

type GameMatchupProps = {
    game: GameView;
    cardMap: CardMap;
    isLoadingCards?: boolean;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    /** See `resolveMatchup`. */
    hideStatlines?: boolean;
    advantage?: AdvantageSide;
    swingResult?: string;
};

export default function GameMatchup({ game, cardMap, isLoadingCards, onCardSelect, hideStatlines = false, advantage, swingResult }: GameMatchupProps) {
    const matchup = resolveMatchup(game, cardMap, hideStatlines);
    if (!matchup) return null;

    const shared = { isLoadingCards, onCardSelect, hideTrend: hideStatlines };
    const winner = advantage ? matchup[advantage] : undefined;
    const { onDeck, inHole } = game.situation ?? {};

    return (
        <div className="relative mx-2 space-y-1.5">
            <div className={`grid grid-cols-2 gap-2 ${winner?.response?.card ? "invisible" : ""}`}>
                <MatchupSide {...shared} side={matchup.pitcher} variant="compact" hasAdvantage={advantage === "pitcher"} />
                <MatchupSide {...shared} side={matchup.hitter} variant="compact" hasAdvantage={advantage === "hitter"} />
            </div>

            {(onDeck || inHole) && (
                <div className={`${BOARD_PANEL_CLASS} flex flex-wrap items-center gap-x-4 px-2 py-0.5 text-[11px]`}>
                    {onDeck && <span className="text-(--secondary)"><span className={CAPS_LABEL_CLASS}>On Deck</span> {onDeck.name}</span>}
                    {inHole && <span className="text-(--secondary)"><span className={CAPS_LABEL_CLASS}>In Hole</span> {inHole.name}</span>}
                </div>
            )}

            {/* Lifted over the row and whatever sits below it, so the layout holds still through
                the reveal. */}
            {winner?.response?.card && (
                <div className="absolute inset-x-0 top-0 z-20">
                    <MatchupSide {...shared} side={winner} hasAdvantage chartHighlight={swingResult} />
                </div>
            )}
        </div>
    );
}
