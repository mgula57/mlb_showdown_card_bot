/**
 * @fileoverview The current pitcher-vs-batter spotlight: the roll about to happen. Shows both
 * cards with the Showdown advantage split between them. A wide game board gives each card a corner
 * through `MatchupSide`; a narrow one uses `GameMatchup`, the same full cards side by side when two
 * fit and stacked when they don't, so the chart is always there to show where a swing landed. Under
 * them, the rest of the batting club's order as it comes up, fading the further off each hitter is.
 */
import { useIsWiderThan } from "../../hooks/useIsWiderThan";
import type { GameView } from "../../domain/game";
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { CardItemFromCard, CardItemSkeleton } from "../cards/CardItem";
import type { AdvantageSide } from "../../domain/play";
import { CardItemCompactFromCard, CardItemCompactSkeleton } from "../cards/CardItemCompact";
import { hittersAfter } from "../../domain/lineup";
import { resolveCardKey } from "../../domain/players";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { BOARD_PANEL_CLASS } from "./boardStyles";
import { resolveMatchup, type MatchupSideData } from "./resolveMatchup";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

/** The on-deck hitter shows nearly in full; each one after fades a step further, down to a floor. */
const UP_NEXT_FADE = ["opacity-90", "opacity-75", "opacity-60"] as const;
const UP_NEXT_FADE_FLOOR = "opacity-45";

/** The batting club's order after the hitter at the plate, back around to him: who's on deck, in
 *  the hole and beyond. Falls back to the feed's on-deck and in-hole names when there's no box
 *  score to read the order from. */
function UpNext({ game, cardMap, isLoadingCards, onCardSelect }: {
    game: GameView;
    cardMap: CardMap;
    isLoadingCards?: boolean;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
}) {
    const situation = game.situation;
    if (!situation) return null;
    const batting = (situation.isTop ? game.away : game.home).boxscore?.batting ?? [];
    const upcoming = hittersAfter(batting, situation.batter?.id, 8);

    if (upcoming.length === 0) {
        const { onDeck, inHole } = situation;
        if (!onDeck && !inHole) return null;
        return (
            <div className={`${BOARD_PANEL_CLASS} flex flex-wrap items-center gap-x-4 px-2 py-0.5 text-[11px]`}>
                {onDeck && <span className="text-(--secondary)"><span className={CAPS_LABEL_CLASS}>On Deck</span> {onDeck.name}</span>}
                {inHole && <span className="text-(--secondary)"><span className={CAPS_LABEL_CLASS}>In Hole</span> {inHole.name}</span>}
            </div>
        );
    }

    return (
        <div className="@container space-y-1.5 pt-2">
            <div className={`${CAPS_LABEL_CLASS} px-0.5 text-(--text-primary)`}>Up next</div>
            {upcoming.map(({ line, spot }, i) => {
                const response = cardMap[resolveCardKey(line.id, "H") ?? ""];
                return (
                    // Faded by default; pointing at or tapping into one brings it up to full.
                    <div key={line.id} className={`flex items-center gap-2 transition-opacity hover:opacity-100 focus-within:opacity-100 ${UP_NEXT_FADE[i] ?? UP_NEXT_FADE_FLOOR}`}>
                        <span className="w-4 shrink-0 text-right text-[11px] font-semibold tabular-nums text-(--text-primary)">{spot}</span>
                        <div className="min-w-0 flex-1">
                            {response?.card ? (
                                <CardItemCompactFromCard card={response.card} className="w-full" onClick={() => onCardSelect?.(response)} />
                            ) : isLoadingCards ? (
                                <CardItemCompactSkeleton />
                            ) : (
                                <div className="truncate px-2 py-1 text-[12px] font-semibold text-(--text-primary)">{line.name}</div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

/** Room for two full cards side by side, charts and all. */
const FULL_ROW_MIN_WIDTH = 600;

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
    isLoadingCards?: boolean;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    /** Replay hides the day's PTS change for the same reason as the box-score line. */
    hideTrend?: boolean;
    /** Sim only: this side won the advantage roll. */
    hasAdvantage?: boolean;
    /** Sim only: the chart result the swing landed on, lit up on the winning card. */
    chartHighlight?: string;
};

export function MatchupSide({ side, isLoadingCards, onCardSelect, hideTrend, hasAdvantage, chartHighlight }: MatchupSideProps) {
    const { label, player, response, summary, advantagePct } = side;
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
                        <span className="tabular-nums text-(--text-primary)">{advantagePct}%</span> adv
                    </div>
                )}
            </div>

            {response?.card ? (
                <CardItemFromCard card={response.card} className="w-full" onClick={() => onCardSelect?.(response)} hasAdvantage={hasAdvantage} chartHighlight={chartHighlight} />
            ) : isLoadingCards ? (
                <CardItemSkeleton className="w-full" />
            ) : player.name ? (
                <div className="truncate rounded-card bg-(--background-secondary) px-2 py-1 text-sm font-semibold text-(--primary)">{player.name}</div>
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
    const [rowRef, isFullRow] = useIsWiderThan<HTMLDivElement>(FULL_ROW_MIN_WIDTH);
    const matchup = resolveMatchup(game, cardMap, hideStatlines);
    if (!matchup) return null;

    const shared = { isLoadingCards, onCardSelect, hideTrend: hideStatlines };

    return (
        <div ref={rowRef} className="mx-2 space-y-1.5">
            <div className={`grid gap-2 ${isFullRow ? "grid-cols-2" : "grid-cols-1"}`}>
                <MatchupSide {...shared} side={matchup.pitcher} hasAdvantage={advantage === "pitcher"} chartHighlight={advantage === "pitcher" ? swingResult : undefined} />
                <MatchupSide {...shared} side={matchup.hitter} hasAdvantage={advantage === "hitter"} chartHighlight={advantage === "hitter" ? swingResult : undefined} />
            </div>

            <UpNext game={game} cardMap={cardMap} isLoadingCards={isLoadingCards} onCardSelect={onCardSelect} />
        </div>
    );
}
