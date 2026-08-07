/**
 * @fileoverview The current pitcher-vs-batter spotlight: the roll about to happen. Shows both
 * cards, the Showdown advantage split between them, and the live count.
 *
 * The count is MLB-only — a sim plate appearance is one pitch roll plus one swing roll, with no
 * ball/strike state to show — so when `balls`/`strikes` are absent this falls back to the most
 * recent play's rolls, which is the equivalent "what just happened" readout for a sim game.
 */
import type { GameView, PlayerRef } from "../../domain/game";
import type { PlayEntry } from "../../domain/play";
import { resolveCardKey } from "../../domain/players";
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { CardItemFromCard, CardItemSkeleton } from "../cards/CardItem";
import { CardItemCompactFromCard } from "../cards/CardItemCompact";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

type GameMatchupProps = {
    game: GameView;
    /** Newest-first; only the latest entry is read, for the sim roll readout. */
    plays?: PlayEntry[];
    cardMap: CardMap;
    isLoadingCards?: boolean;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    className?: string;
    isCompactCards?: boolean;
};

/**
 * Share of d20 rolls that leave the pitcher with the advantage. A Showdown plate appearance
 * gives the hitter the advantage when `control + roll <= onbase`, so the pitcher keeps it on
 * `20 - (onbase - control)` of the twenty faces.
 */
const pitcherAdvantagePct = (control: number, onbase: number): number => {
    const favorable = 20 - (onbase - control);
    return Math.round((Math.max(0, Math.min(20, favorable)) / 20) * 100);
};

function PointsTrend({ card }: { card?: ShowdownBotCardAPIResponse }) {
    const change = card?.in_season_trends?.pts_change.day;
    if (change == null || change === 0) return null;
    return (
        <span className={`text-[10px] font-semibold ${change >= 0 ? "text-(--green)" : "text-(--red)"}`}>
            {change >= 0 ? "+" : ""}{change} PTS today
        </span>
    );
}

function MatchupSide({
    label, player, response, summary, advantage, isLoadingCards, isCompact, onCardSelect,
}: {
    label: string;
    player?: PlayerRef;
    response?: ShowdownBotCardAPIResponse;
    summary?: string;
    advantage?: number;
    isLoadingCards?: boolean;
    isCompact?: boolean;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
}) {
    return (
        <div className="min-w-0 space-y-1.5">
            <div className="flex w-full items-baseline justify-between gap-1.5">
                <div className="flex min-w-0 items-center gap-2">
                    <span className="text-[10px] font-semibold uppercase tracking-[1px] text-(--secondary)">{label}</span>
                    {summary && <span className="truncate text-[10px] text-(--secondary)">{summary}</span>}
                    <PointsTrend card={response} />
                </div>
                {advantage != null && (
                    <div className="text-[11px] font-bold text-(--secondary)">
                        <span className="text-(--primary)">{advantage}%</span> advantage
                    </div>
                )}
                
            </div>

            {response?.card ? (
                isCompact ? (
                    <CardItemCompactFromCard card={response.card} className="w-full" onClick={() => onCardSelect?.(response)} />
                ) : (
                    <CardItemFromCard card={response.card} className="w-full" onClick={() => onCardSelect?.(response)} />
                )
            ) : isLoadingCards ? (
                <CardItemSkeleton className="w-full" />
            ) : player?.name ? (
                <div className="truncate text-sm font-semibold text-(--primary)">{player.name}</div>
            ) : (
                isCompact ? (
                    <CardItemCompactFromCard card={undefined} className="w-full opacity-50" />
                ) : (
                    <CardItemFromCard card={undefined} className="w-full opacity-50" />
                )
            )}

            
        </div>
    );
}

export default function GameMatchup({ game, plays, cardMap, isLoadingCards, onCardSelect, className = "", isCompactCards = false, }: GameMatchupProps) {
    const situation = game.situation;
    if (!situation) return null;

    const { batter, pitcher } = situation;
    const batterResponse = cardMap[resolveCardKey(batter?.id, "H") ?? ""];
    const pitcherResponse = cardMap[resolveCardKey(pitcher?.id, "P") ?? ""];

    // Box score lines give each side's day so far ("2-for-4", "5.0 IP, 3 ER").
    const battingSide = situation.isTop ? game.away : game.home;
    const fieldingSide = situation.isTop ? game.home : game.away;
    const batterSummary = battingSide.boxscore?.batting.find((line) => line.id === batter?.id)?.summary;
    const pitcherSummary = fieldingSide.boxscore?.pitching.find((line) => line.id === pitcher?.id)?.summary;

    const control = pitcherResponse?.card?.chart.command;
    const onbase = batterResponse?.card?.chart.command;
    const pitcherAdvantage = control != null && onbase != null ? pitcherAdvantagePct(control, onbase) : undefined;

    return (
        <div className={`@container rounded-xl border border-(--divider) bg-(--background-secondary)/30 mx-4 p-4 ${className}`}>
            <div 
                className={`
                    ${isCompactCards ? "grid grid-cols-2" : "grid grid-cols-1 @[600px]:grid-cols-2 "}
                    items-start gap-3 sm:gap-3
                `}>
                    <MatchupSide
                        label="Pitching"
                        player={pitcher}
                        response={pitcherResponse}
                        summary={pitcherSummary}
                        advantage={pitcherAdvantage}
                        isLoadingCards={isLoadingCards}
                        onCardSelect={onCardSelect}
                        isCompact={isCompactCards}
                    />                

                    <MatchupSide
                        label="At Bat"
                        player={batter}
                        response={batterResponse}
                        summary={batterSummary}
                        advantage={pitcherAdvantage != null ? 100 - pitcherAdvantage : undefined}
                        isLoadingCards={isLoadingCards}
                        onCardSelect={onCardSelect}
                        isCompact={isCompactCards}
                    />
            </div>

            {(situation.onDeck || situation.inHole) && (
                <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-(--divider) pt-2 text-[11px]">
                    {situation.onDeck && (
                        <span className="text-(--secondary)">
                            <span className="font-bold uppercase tracking-wide">On Deck</span> {situation.onDeck.name}
                        </span>
                    )}
                    {situation.inHole && (
                        <span className="text-(--secondary)">
                            <span className="font-bold uppercase tracking-wide">In Hole</span> {situation.inHole.name}
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}
