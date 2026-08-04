import { useEffect, useRef, useState } from "react";
import type { PlayEntry } from "../../domain/play";
import { resolveCardKey } from "../../domain/players";
import { CardItemCompactFromCard } from "../cards/CardItemCompact";
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

type PlayByPlayLogProps = {
    plays: PlayEntry[];
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
    /** True when nested inside another panel — drops the outer border/background/heading so it
     * reads as one continuous surface with its parent. */
    embedded?: boolean;
    /** Height cap on the scroll area. Defaults to a short strip; a dedicated column passes
     * `max-h-none` so it renders at natural height instead, letting that column's own
     * `overflow-y-auto` be the single scroll container rather than nesting one scrollbar inside
     * another (which also sidesteps depending on a percentage-height chain through the grid). */
    maxHeightClassName?: string;
};

const ORDINAL_SUFFIXES: Record<number, string> = { 1: "st", 2: "nd", 3: "rd" };

const ordinal = (n: number): string => {
    const suffix = n % 100 >= 11 && n % 100 <= 13 ? "th" : ORDINAL_SUFFIXES[n % 10] ?? "th";
    return `${n}${suffix}`;
};

const inningLabel = (inning: number, isTop: boolean): string => `${isTop ? "Top" : "Bot"} ${ordinal(inning)}`;

/** A single player's mini-card in a play row, capped to a fixed width (CardItemCompact fills
 * whatever width it's given, so the cap has to live on this wrapper, not on the card itself). */
function MiniCard({
    cardResponse, fallbackName, onCardSelect, isLoadingCards,
}: {
    cardResponse?: ShowdownBotCardAPIResponse;
    fallbackName: string;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
}) {
    const card = cardResponse?.card;
    return (
        <div className="min-w-24">
            {card ? (
                <CardItemCompactFromCard card={card} hideDetails onClick={cardResponse ? () => onCardSelect?.(cardResponse) : undefined} />
            ) : isLoadingCards ? (
                <div className="h-11 rounded-lg bg-(--background-quaternary) animate-pulse" />
            ) : (
                <div className="text-xs font-semibold text-(--primary) truncate pt-1">{fallbackName}</div>
            )}
        </div>
    );
}

export default function PlayByPlayLog({ plays, cardMap, onCardSelect, isLoadingCards, embedded, maxHeightClassName = "max-h-64" }: PlayByPlayLogProps) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const [showBottomFade, setShowBottomFade] = useState(false);

    const checkScroll = () => {
        const el = scrollRef.current;
        if (!el) return;
        const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 4;
        setShowBottomFade(el.scrollHeight > el.clientHeight && !atBottom);
    };

    // Re-check once card content finishes loading in (row heights settle) and whenever the play
    // list itself changes (live polling can grow it).
    useEffect(() => {
        checkScroll();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [plays, isLoadingCards]);

    if (plays.length === 0) return null;

    const list = (
        <div className="relative @container">
            <div ref={scrollRef} onScroll={checkScroll} className={`${maxHeightClassName} overflow-y-auto space-y-3 pr-1`}>
                {plays.map((play, index) => {
                    const previous = plays[index - 1];
                    const showDivider = !previous || previous.inning !== play.inning || previous.isTop !== play.isTop;
                    const batterCardResponse = cardMap[resolveCardKey(play.batterId, 'H') ?? ''];
                    const pitcherCardResponse = cardMap[resolveCardKey(play.pitcherId, 'P') ?? ''];

                    return (
                        <div key={play.id}>
                            {showDivider && (
                                <div className="text-sm w-full text-center font-black text-(--primary) pt-1 pb-2">
                                    {inningLabel(play.inning, play.isTop)}
                                </div>
                            )}
                            <div className="flex items-start gap-3 p-3 rounded-xl border border-(--divider)/50">
                                <div className="grid grid-cols-1 @[300px]:grid-cols-2 gap-1">
                                    <MiniCard cardResponse={pitcherCardResponse} fallbackName={play.pitcherName} onCardSelect={onCardSelect} isLoadingCards={isLoadingCards} />
                                    <MiniCard cardResponse={batterCardResponse} fallbackName={play.batterName} onCardSelect={onCardSelect} isLoadingCards={isLoadingCards} />
                                </div>
                                <div className="min-w-0 flex-1 pt-0.5">
                                    <div className="flex flex-wrap items-center gap-1.5">
                                        <span className={`inline-block rounded-full border px-2 py-0.5 text-[11px] font-bold ${
                                            play.isScoringPlay
                                                ? 'border-(--green)/40 text-(--green)'
                                                : 'border-(--divider) text-(--secondary)'
                                        }`}>
                                            {play.event}
                                        </span>
                                        {/* Sim games resolve a plate appearance with two d20s instead of a pitch count. */}
                                        {play.roll && (
                                            <span className="rounded-full bg-(--background-tertiary) px-2 py-0.5 text-[10px] font-bold tracking-wide text-(--secondary)">
                                                P {play.roll.pitchRoll} · S {play.roll.swingRoll}
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-sm text-(--primary) mt-1">
                                        {play.description}
                                        {play.outs != null && (
                                            <span className="font-bold"> {play.outs} out{play.outs !== 1 ? 's' : ''}</span>
                                        )}
                                    </p>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
            <div
                className={`absolute bottom-0 inset-x-0 h-10 bg-linear-to-t from-(--background-secondary) to-transparent pointer-events-none transition-opacity duration-300 ${
                    showBottomFade ? 'opacity-100' : 'opacity-0'
                }`}
            />
        </div>
    );

    if (embedded) {
        return list;
    }

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3">
            <div className="text-xs font-bold uppercase tracking-wide text-(--secondary) mb-2">Play-by-Play</div>
            {list}
        </div>
    );
}
