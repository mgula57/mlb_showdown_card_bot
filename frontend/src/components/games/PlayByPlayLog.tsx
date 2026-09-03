import { useEffect, useMemo, useRef, useState } from "react";
import type { PlayEntry } from "../../domain/play";
import { resolveCardKey } from "../../domain/players";
import { ordinal } from "../../functions/formatters";
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
    const [scoringOnly, setScoringOnly] = useState(false);

    const scoringCount = useMemo(() => plays.filter((play) => play.isScoringPlay).length, [plays]);
    const visiblePlays = useMemo(
        () => (scoringOnly ? plays.filter((play) => play.isScoringPlay) : plays),
        [plays, scoringOnly],
    );

    const checkScroll = () => {
        const el = scrollRef.current;
        if (!el) return;
        const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 4;
        setShowBottomFade(el.scrollHeight > el.clientHeight && !atBottom);
    };

    // Re-check once card content finishes loading in (row heights settle) and whenever the visible
    // list changes (live polling can grow it, and the filter can shrink it).
    useEffect(() => {
        checkScroll();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [visiblePlays, isLoadingCards]);

    const filterToggle = (
        <button
            type="button"
            onClick={() => setScoringOnly((on) => !on)}
            disabled={scoringCount === 0 && !scoringOnly}
            aria-pressed={scoringOnly}
            className={`cursor-pointer rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                scoringOnly
                    ? 'border-(--green)/40 bg-(--green)/10 text-(--green)'
                    : 'border-(--divider) text-(--secondary) hover:text-(--primary)'
            }`}
        >
            Scoring{scoringCount > 0 ? ` (${scoringCount})` : ''}
        </button>
    );

    const list = visiblePlays.length === 0 ? (
        <div className="py-6 text-center text-sm text-(--secondary)">
            {scoringOnly && plays.length > 0 ? 'No scoring plays yet.' : 'No plays yet.'}
        </div>
    ) : (
        <div className="relative @container">
            <div ref={scrollRef} onScroll={checkScroll} className={`${maxHeightClassName} overflow-y-auto space-y-3 pr-1`}>
                {visiblePlays.map((play, index) => {
                    const previous = visiblePlays[index - 1];
                    const showDivider = !previous || previous.inning !== play.inning || previous.isTop !== play.isTop;
                    // Plays run newest-first, so the handoff in a taken-over game is the point where
                    // the entry ABOVE this one is simulated and this one is still real.
                    const showTakeover = previous?.source === 'SIM' && play.source === 'MLB';
                    const batterCardResponse = cardMap[resolveCardKey(play.batterId, 'H') ?? ''];
                    const pitcherCardResponse = cardMap[resolveCardKey(play.pitcherId, 'P') ?? ''];

                    return (
                        <div key={play.id}>
                            {showTakeover && (
                                <div className="flex items-center gap-2 py-2">
                                    <div className="h-px flex-1 bg-(--divider)" />
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-(--secondary)">Took over here</span>
                                    <div className="h-px flex-1 bg-(--divider)" />
                                </div>
                            )}
                            {showDivider && (
                                <div className="text-sm w-full text-center font-black text-(--primary) pt-1 pb-2">
                                    {inningLabel(play.inning, play.isTop)}
                                </div>
                            )}
                            <div className="flex items-start gap-3 p-3 rounded-xl bg-primary border border-(--divider)/50">
                                <div className="grid grid-cols-1 @[500px]:grid-cols-2 gap-1 min-w-24 @[300px]:min-w-32">
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

    // Embedded, the parent owns the heading, so the toggle sits on its own right-aligned row.
    if (embedded) {
        return (
            <div>
                <div className="mb-2 flex justify-end">{filterToggle}</div>
                {list}
            </div>
        );
    }

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3">
            <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-xs font-bold uppercase tracking-wide text-(--secondary)">Play-by-Play</div>
                {filterToggle}
            </div>
            {list}
        </div>
    );
}
