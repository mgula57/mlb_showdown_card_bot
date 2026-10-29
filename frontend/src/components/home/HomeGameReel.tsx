/**
 * @fileoverview The Home hero's game reel: a passive, looping `GameField` that replays one
 * scoring half-inning from each of a handful of real games (`SHOWCASE_GAMES`), with Showdown
 * dice synthesized from the players' archived cards (`withSyntheticRolls`). When a half-inning
 * ends, it crossfades to the next game.
 *
 * Split in two the same way `GameDetailPlayback` is: `HomeGameReel` owns loading and rotation,
 * and `ReelSegmentPlayer` only mounts once a timeline exists, so it can call `useGamePlayback`
 * unconditionally.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { FaChevronRight, FaForward } from "react-icons/fa6";

import { fetchGameBoxscore } from "../../api/mlbAPI";
import { fetchArchivedCardMap, type ShowdownBotCard, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { fromMlbTimeline } from "../../domain/adapters/fromMlbApi";
import { advantageSideOf } from "../../domain/play";
import { SeededRandom, sliceScoringHalfInning, withSyntheticRolls } from "../../domain/syntheticRolls";
import type { GameTimeline } from "../../domain/timeline";
import { useGamePlayback } from "../../hooks/useGamePlayback";
import { usePrefersReducedMotion } from "../../hooks/usePrefersReducedMotion";
import GameField, { FIELD_PLOP_MS, FieldArt } from "../games/GameField";
import { TeamChip } from "../shared/TeamChip";
import { useSiteSettings } from "../shared/SiteSettingsContext";
import { SHOWCASE_GAMES, type ShowcaseGame } from "./showcaseGames";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;
type ReelSegment = { game: ShowcaseGame; timeline: GameTimeline; cardMap: CardMap };

/** How long the finished half-inning sits on screen before the reel moves on. */
const SEGMENT_HOLD_MS = 3000;
const CROSSFADE_MS = 400;
/** How far (as a % of the width) the grass fades in from each side — one value so the left and
 *  right edges always match. */
const GRASS_FADE_X_PCT = 9;
const GRASS_FADE_MASK = [
    "linear-gradient(to bottom, transparent 0%, black 14%, black 65%, transparent 100%)",
    `linear-gradient(to right, transparent 0%, black ${GRASS_FADE_X_PCT}%, black ${100 - GRASS_FADE_X_PCT}%, transparent 100%)`,
].join(", ");
const GRASS_FADE_STYLE: React.CSSProperties = {
    maskImage: GRASS_FADE_MASK,
    WebkitMaskImage: GRASS_FADE_MASK,
    maskComposite: "intersect",
    WebkitMaskComposite: "source-in",
};
/** Translucent framing for text over the grass — matches GameDetail's ScoreHeader. */
const OVER_GRASS_PANEL = "rounded-card border border-(--divider) bg-(--background-secondary)/90";
/** Fixed height + gap of the score row above the field. Shared by the player, the skeleton and the
 *  field-art underlay, which relies on it to line up with the field without measuring. */
const HEADER_ROW = "h-9 mb-2";

// Browser-session cache — the reel loops, so each game is fetched at most once per set.
const _segmentCache = new Map<string, Promise<ReelSegment>>();

/** One game's playable half-inning: the boxscore → full timeline → a random scoring half-inning,
 *  then archived cards for just the players in it, then dice for each of its plays. A card
 *  lookup failure still yields a playable segment (results without dice). */
const loadSegment = (game: ShowcaseGame, showdownSet: string): Promise<ReelSegment> => {
    const cacheKey = `${game.gamePk}:${showdownSet}`;
    const cached = _segmentCache.get(cacheKey);
    if (cached) return cached;

    const promise = fetchGameBoxscore(game.gamePk).then(async (boxscore) => {
        const segment = sliceScoringHalfInning(fromMlbTimeline(boxscore), new SeededRandom(`${game.gamePk}-${Date.now()}`));
        const ids = new Set<string>();
        for (const frame of segment.frames) {
            const { batter, pitcher } = frame.view.situation ?? {};
            for (const id of [frame.play?.batterId, frame.play?.pitcherId, batter?.id, pitcher?.id]) {
                if (id != null && id !== "") ids.add(String(id));
            }
        }
        const cardMap = await fetchArchivedCardMap([...ids], game.season, showdownSet, "home-game-reel").catch(() => ({}));
        return { game, cardMap, timeline: withSyntheticRolls(segment, cardMap) };
    });
    // A failed load shouldn't stick — drop it so the next lap retries.
    promise.catch(() => _segmentCache.delete(cacheKey));
    _segmentCache.set(cacheKey, promise);
    return promise;
};

const shuffled = <T,>(items: T[]): T[] => {
    const copy = [...items];
    for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
};

/** True while `ref`'s element is on screen and the tab is visible. */
function useIsOnScreen(ref: React.RefObject<HTMLElement | null>): boolean {
    const [isIntersecting, setIsIntersecting] = useState(true);
    const [isTabVisible, setIsTabVisible] = useState(() => !document.hidden);

    useEffect(() => {
        const element = ref.current;
        if (!element) return;
        const observer = new IntersectionObserver(([entry]) => setIsIntersecting(entry.isIntersecting), { threshold: 0.25 });
        observer.observe(element);
        return () => observer.disconnect();
    }, [ref]);

    useEffect(() => {
        const onVisibility = () => setIsTabVisible(!document.hidden);
        document.addEventListener("visibilitychange", onVisibility);
        return () => document.removeEventListener("visibilitychange", onVisibility);
    }, []);

    return isIntersecting && isTabVisible;
}

export default function HomeGameReel({ onCardSelect }: { onCardSelect?: (card: ShowdownBotCard) => void }) {
    const { userShowdownSet } = useSiteSettings();
    const prefersReducedMotion = usePrefersReducedMotion();
    const containerRef = useRef<HTMLDivElement>(null);
    const isOnScreen = useIsOnScreen(containerRef);

    const order = useMemo(() => shuffled(SHOWCASE_GAMES), []);
    const [position, setPosition] = useState(0);
    const [segment, setSegment] = useState<ReelSegment | null>(null);
    const [isFading, setIsFading] = useState(false);
    const failuresRef = useRef(0);
    const isFadingRef = useRef(false);
    const [isUnavailable, setIsUnavailable] = useState(false);

    const game = order[position % order.length];
    const nextGame = order[(position + 1) % order.length];

    useEffect(() => {
        let cancelled = false;
        loadSegment(game, userShowdownSet)
            .then((loaded) => {
                if (cancelled) return;
                failuresRef.current = 0;
                setSegment(loaded);
                isFadingRef.current = false;
                setIsFading(false);
                // Warm the next game while this one plays.
                loadSegment(nextGame, userShowdownSet).catch(() => {});
            })
            .catch(() => {
                if (cancelled) return;
                failuresRef.current += 1;
                if (failuresRef.current >= order.length) setIsUnavailable(true);
                else setPosition((p) => p + 1);
            });
        return () => { cancelled = true; };
    }, [game, nextGame, userShowdownSet, order.length]);

    // Stable so the finished-segment hold timer isn't reset by unrelated re-renders of Home.
    const advance = useCallback(() => {
        if (isFadingRef.current) return;
        isFadingRef.current = true;
        setIsFading(true);
        window.setTimeout(() => setPosition((p) => p + 1), CROSSFADE_MS);
    }, []);

    if (isUnavailable) return null;

    const isShowing = !!segment && segment.game === game && !isFading;

    return (
        // Full-bleed on phones: the negative margin cancels Home's `px-6` gutter so the field
        // spans the screen.
        <div ref={containerRef} className="relative -mx-6 px-3 py-8 sm:mx-0 sm:w-full sm:px-10">
            {/* Grass backdrop, faded out on all four edges (two gradients intersected) so it
                dissolves into the hero instead of sitting in a box. The padding above keeps the
                content inside the fully opaque middle. Content below is a later positioned
                sibling, so it paints over the image without a negative z-index. */}
            <img
                src="/images/games/Grass Field.jpg"
                alt=""
                className="absolute inset-0 h-full w-full object-cover pointer-events-none select-none"
                style={GRASS_FADE_STYLE}
            />
            {/* The diamond stays put through loading and crossfades; only what's on it changes.
                Offset by the header row and inset like GameField's own field box. */}
            <div aria-hidden className="absolute inset-x-3 top-8 sm:inset-x-10 pointer-events-none">
                <div className={HEADER_ROW} />
                <div className="px-1">
                    <div className="relative aspect-703/369 w-full"><FieldArt /></div>
                </div>
            </div>
            {segment ? (
                <div className="relative transition-opacity ease-out" style={{ opacity: isShowing ? 1 : 0, transitionDuration: `${CROSSFADE_MS}ms` }}>
                    <ReelSegmentPlayer
                        key={segment.game.gamePk}
                        segment={segment}
                        isActive={isOnScreen && isShowing}
                        autoplay={!prefersReducedMotion}
                        onDone={advance}
                        onCardSelect={onCardSelect}
                    />
                </div>
            ) : (
                <div className="relative"><ReelSkeleton /></div>
            )}
        </div>
    );
}

/** Same footprint as the header row + compact field, so nothing shifts when the reel loads. The
 *  field itself is left empty: the persistent `FieldArt` underlay shows through. */
function ReelSkeleton() {
    return (
        <div>
            <div className={`${HEADER_ROW} flex animate-pulse items-center justify-between gap-2`}>
                <div className="h-4 w-40 rounded-plate bg-(--background-tertiary)" />
                <div className="h-4 w-24 rounded-plate bg-(--background-tertiary)" />
            </div>
            <div className="px-1"><div className="aspect-703/369 w-full" /></div>
        </div>
    );
}

function ReelSegmentPlayer({ segment, isActive, autoplay, onDone, onCardSelect }: {
    segment: ReelSegment;
    /** On screen, tab visible, and not mid-crossfade. */
    isActive: boolean;
    /** False under reduced motion — the reel parks on the half-inning's final state instead. */
    autoplay: boolean;
    onDone: () => void;
    onCardSelect?: (card: ShowdownBotCard) => void;
}) {
    const { game, timeline, cardMap } = segment;
    const [state, controls] = useGamePlayback({
        timeline, initialMode: "playback", initialCursor: autoplay ? "start" : "live",
    });

    const controlsRef = useRef(controls);
    controlsRef.current = controls;
    const lastIndex = timeline.frames.length - 1;
    const isAtEnd = state.cursor === lastIndex && state.phase === "idle";

    // The players plop onto the field as the segment mounts; hold the first pitch until they land.
    const [hasLanded, setHasLanded] = useState(!autoplay);
    useEffect(() => {
        if (!autoplay) return;
        const timer = window.setTimeout(() => setHasLanded(true), FIELD_PLOP_MS);
        return () => window.clearTimeout(timer);
    }, [autoplay]);

    // Play only while visible. Pausing interrupts the play in flight, so resuming replays it from
    // its pitch rather than mid-run. No cursor check here: on mount the cursor still reads as the
    // last frame (the hook parks it on frame 0 in its own effect), and playing at the end is a
    // no-op anyway.
    useEffect(() => {
        if (!autoplay) return;
        if (isActive && hasLanded) controlsRef.current.play();
        else controlsRef.current.pause();
    }, [isActive, hasLanded, autoplay]);

    // Hold on the finished half-inning, then hand off to the next game.
    useEffect(() => {
        if (!autoplay || !isAtEnd || !isActive) return;
        const timer = window.setTimeout(onDone, SEGMENT_HOLD_MS);
        return () => window.clearTimeout(timer);
    }, [autoplay, isAtEnd, isActive, onDone]);

    const view = state.frame.view;
    const situation = view.situation;
    const isResultRevealed = state.phase === "result" || state.phase === "runners" || state.phase === "settle";
    const advantage = isResultRevealed ? advantageSideOf(state.pendingPlay) : undefined;
    const handleCardSelect = onCardSelect
        ? (response: ShowdownBotCardAPIResponse) => { if (response.card) onCardSelect(response.card); }
        : undefined;

    return (
        <div>
            <div className={`${HEADER_ROW} flex items-center justify-between gap-3 px-2 ${OVER_GRASS_PANEL}`}>
                <div className="flex min-w-0 items-center gap-3">
                    {([view.away, view.home] as const).map((side) => (
                        <div key={side.team.abbreviation ?? side.team.name} className="flex items-center gap-1.5">
                            <TeamChip team={side.team} size="sm" />
                            <span className="font-display-upright text-[17px] leading-none tabular-nums">{side.score ?? 0}</span>
                        </div>
                    ))}
                    {situation && (
                        <span className="text-[11px] font-bold text-(--secondary) whitespace-nowrap">
                            {situation.isTop ? "▲" : "▼"} {situation.inning}
                        </span>
                    )}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                    <span className="hidden sm:inline text-[11px] font-semibold text-(--secondary) truncate">{game.label}</span>
                    <button
                        type="button"
                        onClick={onDone}
                        aria-label="Next game"
                        className="cursor-pointer rounded-full p-1.5 text-(--secondary) transition-colors hover:bg-(--divider) hover:text-(--primary)"
                    >
                        <FaForward size={11} />
                    </button>
                </div>
            </div>

            <GameField
                game={view}
                cardMap={cardMap}
                onCardSelect={handleCardSelect}
                transition={state.transition}
                pendingPlay={state.pendingPlay}
                phase={state.phase}
                lastPlay={state.frame.play}
                advantage={advantage}
                playbackSpeed={state.effectiveSpeed}
                hideFieldArt
                plopIn={autoplay}
            />

            <div className="mt-2 flex items-center justify-between gap-2">
                <span className={`sm:hidden truncate px-2 py-1 text-[11px] font-semibold text-(--secondary) ${OVER_GRASS_PANEL}`}>{game.label}</span>
                <Link
                    to={`/seasons/game/${game.gamePk}?season=${game.season}`}
                    className={`ml-auto flex shrink-0 cursor-pointer items-center gap-1 px-2 py-1 text-xs font-semibold text-(--primary) hover:brightness-110 ${OVER_GRASS_PANEL}`}
                >
                    Watch full game <FaChevronRight className="text-[10px]" />
                </Link>
            </div>
        </div>
    );
}
