/**
 * @fileoverview The field: the centerpiece of the game view. Renders the current situation
 * — runners on base, the pitcher/batter confrontation, and (expanded) the full defensive
 * alignment — over the field art.
 *
 * Reads only `GameView`, so a sim game drives it the same way a real one does. Slots the sim
 * can't fill (defense alignment, runner identity) degrade to markers rather than disappearing.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { FaCompress, FaExpand } from "react-icons/fa6";

import type { DefenseAlignment, GameView, PlayerRef } from "../../domain/game";
import { resolveCardKey } from "../../domain/players";
import { runnerKey, type FrameTransition, type RunnerSpot } from "../../domain/timeline";
import type { PlayEntry } from "../../domain/play";
import type { ShowdownBotCardAPIResponse, ShowdownBotCardCompact } from "../../api/showdownBotCard";
import { CardItemCompact, CardItemCompactFromCard } from "../cards/CardItemCompact";
import { defenseAtPosition, IF_POSITIONS, OF_POSITIONS } from "../shared/DefenseUtils";
import { usePresenceList } from "../../hooks/usePresenceList";
import type { PlayPhase } from "../../hooks/useGamePlayback";
import IconButton from "../shared/IconButton";
import { BasesDiamond } from "./BasesDiamond";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

type GameFieldProps = {
    game: GameView;
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    /** Expanded overlays all nine defenders; compact shows only the battery, runners, and batter. */
    expanded?: boolean;
    onToggleExpanded?: () => void;
    /** True while cardMap entries are still being fetched — shows a loading state on markers with a name but no resolved card yet. */
    isLoadingCards?: boolean;
    /** The move set that produced `game`'s current situation — only set during playback. A
     *  scoring or retired runner isn't in `situation.bases` anymore by the time this frame
     *  renders, so their departure has nothing to animate from without this: `transition` is what
     *  lets the field keep them mounted for one beat at "home" or their old base, fading out,
     *  instead of just vanishing. Undefined outside playback (live polling has no transition
     *  object — see the class doc on `GameTimeline`), which degrades fine: departures simply pop
     *  instead of fading, exactly like they do today. */
    transition?: FrameTransition;
    /** The play `transition` belongs to — its `event` (e.g. "Double", "Strikeout") is what the
     *  result flash displays. Undefined outside playback, same as `transition`. */
    pendingPlay?: PlayEntry;
    /** The playback phase machine's current step — drives the result flash's visibility (shown
     *  during "result"/"runners") and nothing else here; the runner animations themselves are
     *  driven purely by `game`/`transition` changing, not by watching `phase`. */
    phase?: PlayPhase;
    className?: string;
};

/**
 * The art (736x800) is mostly transparent padding — the field itself occupies x 17-720,
 * y 274-643. These constants scale and offset the <img> so that opaque region exactly fills
 * its container, letting every coordinate below be a simple percentage of the visible field.
 */
const ART = { width: 736, height: 800, left: 17, top: 274, right: 720, bottom: 643 } as const;
const FIELD_W = ART.right - ART.left;
const FIELD_H = ART.bottom - ART.top;
const ART_STYLE: React.CSSProperties = {
    position: "absolute",
    width: `${(ART.width / FIELD_W) * 100}%`,
    height: `${(ART.height / FIELD_H) * 100}%`,
    left: `${(-ART.left / FIELD_W) * 100}%`,
    top: `${(-ART.top / FIELD_H) * 100}%`,
    maxWidth: "none",
};

/** Percentages of the visible field. Base coordinates are measured from the art's white base
 * markers; fielder spots are placed relative to them. */
const BASES = {
    first: [78.9, 49.9],
    second: [49.9, 18.4],
    third: [20.6, 49.6],
} as const;
const HOME: readonly [number, number] = [49.9, 85.4];

const DEFENSE_SPOTS: Record<keyof DefenseAlignment, readonly [number, number]> = {
    pitcher: [49.9, 53.5],
    catcher: [49.9, 105],
    first: [90, 24],
    second: [70, 12],
    third: [10, 24],
    shortstop: [30, 12],
    left: [19, -10],
    center: [49.9, -15],
    right: [81, -10],
};

/** Position abbreviations for the defense slots, used for the card's defensive rating lookup. */
const DEFENSE_POSITIONS: Record<keyof DefenseAlignment, string> = {
    pitcher: "P", catcher: "C", first: "1B", second: "2B", third: "3B",
    shortstop: "SS", left: "LF", center: "CF", right: "RF",
};

const atPercent = ([x, y]: readonly [number, number]): React.CSSProperties => ({
    left: `${x}%`,
    top: `${y}%`,
});

/** Every spot an offensive occupant (runner or batter) can render at — the three bases plus the
 *  plate, used both as "about to bat" and as "just scored" (a different visual moment, same x/y). */
const SPOTS: Record<RunnerSpot, readonly [number, number]> = {
    first: BASES.first, second: BASES.second, third: BASES.third, plate: HOME, home: HOME,
};

type FieldOccupant = { key: string; player: PlayerRef; spot: RunnerSpot; isOut?: boolean };

/**
 * One offensive occupant per base PLUS the batter, keyed by player identity rather than by base
 * slot. Keying the batter with the exact identity they'll have as a runner (`runnerKey` ignores
 * which spot it's asked about when the player has an id) is what turns a single or a walk into
 * one DOM node whose `left`/`top` changes — the card runs to first — instead of two markers
 * swapping out. `transition` (playback only) adds back a scoring or retired runner for one beat
 * so their departure has something to fade from; without it (live polling) they simply disappear
 * when `situation` stops reporting them, same as today.
 */
function buildFieldOccupants(situation: GameView["situation"], transition: FrameTransition | undefined): FieldOccupant[] {
    if (!situation) return [];
    const occupants = new Map<string, FieldOccupant>();

    (["first", "second", "third"] as const).forEach((slot) => {
        const player = situation.bases[slot];
        if (!player) return;
        const key = runnerKey(player, slot);
        occupants.set(key, { key, player, spot: slot });
    });

    if (situation.batter) {
        const key = runnerKey(situation.batter, "plate");
        occupants.set(key, { key, player: situation.batter, spot: "plate" });
    }

    for (const move of transition?.moves ?? []) {
        if (move.to === "home") {
            occupants.set(move.key, { key: move.key, player: move.player, spot: "home" });
        } else if (move.to === null && move.from) {
            occupants.set(move.key, { key: move.key, player: move.player, spot: move.from, isOut: true });
        }
    }

    return [...occupants.values()];
}

/** The base path in running order — a runner always travels forward along this sequence, never
 *  in a straight line across the infield. `plate` (pre-contact) and `home` (post-score) share
 *  coordinates but are distinct stops: `plate` only ever starts a path, `home` only ever ends one. */
const BASE_PATH_ORDER: RunnerSpot[] = ["plate", "first", "second", "third", "home"];

/** The intermediate bases a runner passes through going from `from` to `to`, INCLUDING `to` but
 *  not `from` — e.g. `first` → `third` is `["second", "third"]`, so a runner taking two bases on a
 *  single still rounds first before angling to third rather than cutting straight across the infield. */
function basePathBetween(from: RunnerSpot, to: RunnerSpot): RunnerSpot[] {
    const fromIndex = BASE_PATH_ORDER.indexOf(from);
    const toIndex = BASE_PATH_ORDER.indexOf(to);
    if (fromIndex === -1 || toIndex === -1 || toIndex <= fromIndex) return [to];
    return BASE_PATH_ORDER.slice(fromIndex + 1, toIndex + 1);
}

/** How long each individual base-to-base hop takes. A HR (plate→home, 4 hops) then takes 4x this,
 *  which is intentional — covering more ground should visibly take longer, not less per hop. */
const BASE_HOP_MS = 220;

/**
 * Steps a multi-base move through its intermediate stops instead of letting the CSS transition
 * interpolate `left`/`top` directly between start and end — a direct interpolation would cut a
 * diagonal line across the infield grass on a double or triple. Returns a per-runner-key override
 * of which stop to render at RIGHT NOW; a single-hop move (the common case — batter to first,
 * runner to the next base over) isn't stepped at all, since one direct CSS transition already
 * looks correct for a single leg.
 */
function useBasePathAnimation(transition: FrameTransition | undefined): Record<string, RunnerSpot> {
    // The FIRST waypoint of every multi-hop move is known synchronously from `transition` alone —
    // computed directly during render rather than via an effect, so there's no frame where a
    // runner briefly renders at its old spot before the animation has had a chance to start.
    const initialOverrides = useMemo(() => {
        const initial: Record<string, RunnerSpot> = {};
        for (const move of transition?.moves ?? []) {
            if (!move.from || !move.to) continue; // no path to animate (fresh arrival, or an out — those don't travel)
            const path = basePathBetween(move.from, move.to);
            if (path.length > 1) initial[move.key] = path[0]; // one leg needs no stepping at all
        }
        return initial;
    }, [transition]);

    // Later waypoints land on a delay, which genuinely needs an effect+timers — but every
    // `setState` call here happens inside a `setTimeout` callback, never synchronously in the
    // effect body itself, so a stale-transition guard (comparing `transition` at read time) does
    // the resetting instead of an unconditional `setLaterOverrides({})` at the top of the effect.
    const [laterState, setLaterState] = useState<{ transition: FrameTransition | undefined; overrides: Record<string, RunnerSpot> }>(
        { transition: undefined, overrides: {} },
    );
    const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

    useEffect(() => {
        timersRef.current.forEach(clearTimeout);
        timersRef.current = [];
        if (!transition) return;

        const timers: ReturnType<typeof setTimeout>[] = [];
        for (const move of transition.moves) {
            if (!move.from || !move.to) continue;
            const path = basePathBetween(move.from, move.to);
            if (path.length <= 1) continue;

            path.forEach((stop, i) => {
                if (i === 0) return;
                timers.push(setTimeout(() => {
                    setLaterState((prev) => ({
                        transition,
                        overrides: { ...(prev.transition === transition ? prev.overrides : {}), [move.key]: stop },
                    }));
                }, i * BASE_HOP_MS));
            });
            // Once the full path has played out, drop the override — by then the occupant's own
            // `spot` (computed from the now-current `situation`) already matches the final stop.
            timers.push(setTimeout(() => {
                setLaterState((prev) => {
                    if (prev.transition !== transition) return prev;
                    const next = { ...prev.overrides };
                    delete next[move.key];
                    return { transition, overrides: next };
                });
            }, path.length * BASE_HOP_MS));
        }

        timersRef.current = timers;
        return () => timers.forEach(clearTimeout);
    }, [transition]);

    const laterOverrides = laterState.transition === transition ? laterState.overrides : {};
    return { ...initialOverrides, ...laterOverrides };
}

/** Temporary badge announcing the result of the play that's resolving — "Double", "Home Run",
 *  "Strikeout" — visible for the stretch of the phase machine where the runners are actually
 *  moving, then it fades. Absent entirely outside playback (`phase` stays "idle" when there's
 *  nothing to reveal), so a plain live view never shows it. */
function ResultFlash({ play, phase, severity }: { play: PlayEntry | undefined; phase: PlayPhase; severity?: FrameTransition["severity"] }) {
    if (!play) return null;
    const visible = phase === "result" || phase === "runners";

    const isBig = severity === "big";
    const label = isBig && play.isScoringPlay && !/[!?]$/.test(play.event) ? `${play.event}!` : play.event;

    return (
        <div
            key={play.id}
            aria-hidden={!visible}
            className={`
                absolute left-1/2 top-[6%] z-30 -translate-x-1/2
                pointer-events-none select-none whitespace-nowrap
                rounded-full border font-black uppercase tracking-wide shadow-lg
                transition-[opacity,transform] duration-300 ease-out
                ${visible ? "opacity-100 translate-y-0 result-pop" : "opacity-0 -translate-y-2"}
                ${isBig
                    ? "bg-(--live) border-(--live) text-white text-base px-5 py-2"
                    : "bg-(--background-secondary)/95 border-(--divider) text-(--primary) text-xs px-3.5 py-1.5"}
            `}
        >
            {label}
        </div>
    );
}

/** Border accent distinguishing offense from defense — a translucent version of the same
 * live/divider colors the rest of the field UI already leans on. */
const TONE_ACCENT: Record<"offense" | "defense", string | undefined> = {
    offense: "color-mix(in srgb, var(--live) 60%, transparent)",
    defense: undefined,
};

/** A player marker on the field, built from the shared compact card so it reads consistently
 * with the rest of the app. Falls back to an unnamed dot for runners the source can only report
 * as "occupied" (the sim tracks base state, not who's standing there), and to a name-only
 * placeholder card while the real one is still being fetched. */
function FieldMarker({
    player, role, cardMap, onCardSelect, isLoadingCards, tone,
    hideCommand = false, hideTeamPoints = hideCommand, detailStat1Category, liveIp, fieldPosition,
}: {
    player: PlayerRef;
    role: "H" | "P";
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
    tone: "offense" | "defense";
    hideCommand?: boolean;
    /** Hide the team/points row, leaving just the name and detail stat. Defaults to whatever hideCommand is, since the two go together on these lean field chips. */
    hideTeamPoints?: boolean;
    detailStat1Category?: "defense" | "speed" | "hr";
    liveIp?: string | number | null;
    fieldPosition?: string;
}) {
    if (!player.name) {
        return <span className="block h-3 w-3 rotate-45 rounded-xs bg-(--live) shadow-sm" />;
    }

    const response = cardMap[resolveCardKey(player.id, role) ?? ""];
    const accentColor = TONE_ACCENT[tone];
    const showDetails = detailStat1Category != null;

    const placeholderCard: ShowdownBotCardCompact = {
        id: `${player.id}-${role}`,
        name: player.name,
        year: "----",
        set: "---",
        points: 0,
        command: 0,
        outs: 0,
        is_pitcher: role === "P",
        color_primary: null,
        color_secondary: null,
        team: null,
        positions_and_defense_string: null,
        positions_and_defense: null,
        ip: null,
        speed: null,
        hand: null,
        hr_range: null,
        source: "BOT",
    };

    return (
        <div className="w-28 @[420px]:w-32">
            {response?.card ? (
                <CardItemCompactFromCard
                    card={response.card}
                    onClick={() => onCardSelect?.(response)}
                    hideCommand={hideCommand}
                    hideTeamPoints={hideTeamPoints}
                    hideDetails={!showDetails}
                    detailStat1Category={detailStat1Category}
                    liveIp={liveIp}
                    fieldPosition={fieldPosition}
                    accentColor={accentColor}
                />
            ) : (
                <CardItemCompact
                    card={placeholderCard}
                    isLoading={isLoadingCards}
                    hideCommand={hideCommand}
                    hideTeamPoints={hideTeamPoints}
                    hideDetails
                    accentColor={accentColor}
                />
            )}
        </div>
    );
}

/** OF / IF / CA totals for the fielding side, as in the mockup's left rail. Null when no
 * alignment is available (pre-first-pitch, or a sim game). */
function DefenseTotals({ defense, cardMap }: { defense: DefenseAlignment; cardMap: CardMap }) {
    const ratingFor = (slot: keyof DefenseAlignment): number | null => {
        const player = defense[slot];
        const card = cardMap[resolveCardKey(player?.id, "H") ?? ""]?.card;
        return defenseAtPosition(card?.positions_and_defense, DEFENSE_POSITIONS[slot]);
    };

    const sumFor = (positions: readonly string[]): number | null => {
        const slots = (Object.keys(DEFENSE_POSITIONS) as (keyof DefenseAlignment)[])
            .filter((slot) => positions.includes(DEFENSE_POSITIONS[slot]));
        const ratings = slots.map(ratingFor).filter((rating): rating is number => rating != null);
        return ratings.length ? ratings.reduce((total, rating) => total + rating, 0) : null;
    };

    const rows: [string, number | null][] = [
        ["OF", sumFor(OF_POSITIONS)],
        ["IF", sumFor(IF_POSITIONS)],
        ["CA", ratingFor("catcher")],
    ];

    if (rows.every(([, value]) => value == null)) return null;

    return (
        <div className="flex-col p-1 items-center gap-1.5">
            {rows.map(([label, value]) => (
                <div
                    key={label}
                    className="flex items-center gap-1.5 rounded-md border border-(--divider) bg-(--background-secondary)/90 px-1.5 py-0.5 text-[10px] font-bold"
                >
                    <span className="text-(--secondary)">{label}</span>
                    <span className="text-(--primary)">{value == null ? "–" : `+${value}`}</span>
                </div>
            ))}
        </div>
    );
}

/** Score, inning, bases and outs — the always-visible state summary, as in the mockup's corner bug. */
function ScoreBug({ game }: { game: GameView }) {
    const situation = game.situation;
    const isLive = game.state === "LIVE";

    return (
        <div className="absolute flex right-0 top-0 w-max overflow-hidden rounded-lg border border-(--divider) bg-(--background-secondary)/90 text-[11px] shadow-sm lg:hidden">
            <div className='flex-col'>
                {[game.away, game.home].map((side, index) => (
                    <div
                        key={side.team.key}
                        className={`flex items-center justify-between gap-3 px-2 py-1 ${index === 0 ? "border-b border-(--divider)" : ""}`}
                    >
                        <span className="font-bold text-(--primary)">{side.team.abbreviation}</span>
                        <span className="font-black tabular-nums text-(--primary)">{side.score ?? 0}</span>
                    </div>
                ))}
            </div>

            {situation && (
                <div className="flex items-center gap-2 px-2 py-1">
                    {isLive && <span className="live-pulse h-1.5 w-1.5 rounded-full bg-(--live)" />}
                    <span className="font-bold text-(--secondary)">
                        {situation.isTop ? "▲" : "▼"} {situation.inningLabel}
                    </span>
                    <BasesDiamond bases={situation.bases} outs={situation.outs} size="sm" />
                </div>
            )}
        </div>
    );
}

export default function GameField({ game, cardMap, onCardSelect, expanded = false, onToggleExpanded, isLoadingCards, transition, pendingPlay, phase = "idle", className = "" }: GameFieldProps) {
    const situation = game.situation;
    // if (!situation) return null;

    // The fielding side is whichever team isn't batting — used for the pitcher's line score.
    const fieldingSide = situation?.isTop ? game.home : game.away;
    const pitcherLine = fieldingSide.boxscore?.pitching.find((line) => line.id === situation?.pitcher?.id);
    const defense = situation?.defense;

    const occupants = useMemo(() => buildFieldOccupants(situation, transition), [situation, transition]);
    // Exit hold covers the longest possible base-running path (plate→home, 4 hops) plus a fade
    // tail, so a runner scoring or getting thrown out has time to finish the whole trip and fade
    // before `usePresenceList` drops them — this is a JS-side mirror of that timing, not a second
    // source of truth for how long the actual CSS transitions run.
    const presentOccupants = usePresenceList(occupants, BASE_HOP_MS * 4 + 300);
    const pathOverrides = useBasePathAnimation(transition);

    return (
        <div className={`@container relative w-full ${className}`}>
            {/* Padded so outfielder/catcher cards and the score bug have room to sit above and
                below the field art without overlapping whatever follows in the DOM. Expanded
                needs noticeably more of both — the fielder cards carry a defense-rating row, and
                the catcher/corner outfielders sit right at the edges with nothing to spare
                otherwise. The padding transition is what makes the expand/collapse feel like the
                field is growing rather than snapping to a new size. */}
            <div className={`relative px-1 transition-[padding] duration-300 ease-out ${expanded ? "pt-28 pb-12" : "pt-4 pb-0"}`}>
                <div className="relative aspect-703/369 w-full overflow-visible">
                    <div className="absolute inset-0 overflow-hidden rounded-lg">
                        <img src="/images/teams/Field No BG.png" alt="" style={ART_STYLE} className="pointer-events-none select-none" />
                    </div>

                    {/* Defense — the battery is always mounted; the rest of the alignment stays
                        mounted too (so it can fade/scale in instead of popping in) but is hidden
                        and inert until expanded. */}
                    {defense && (Object.keys(DEFENSE_SPOTS) as (keyof DefenseAlignment)[])
                        .map((slot) => {
                            const player = defense[slot];
                            if (!player) return null;
                            const isBattery = slot === "pitcher";
                            const isVisible = expanded || isBattery;
                            return (
                                <div
                                    key={slot}
                                    aria-hidden={!isVisible}
                                    className={`absolute -translate-x-1/2 -translate-y-1/2 transition-[opacity,transform] duration-300 ease-out ${
                                        isVisible ? "opacity-100 scale-100" : "pointer-events-none scale-75 opacity-0"
                                    }`}
                                    style={atPercent(DEFENSE_SPOTS[slot])}
                                >
                                    <FieldMarker
                                        player={player}
                                        role={isBattery ? "P" : "H"}
                                        cardMap={cardMap}
                                        onCardSelect={onCardSelect}
                                        isLoadingCards={isLoadingCards}
                                        tone="defense"
                                        hideCommand={!isBattery}
                                        detailStat1Category="defense"
                                        fieldPosition={DEFENSE_POSITIONS[slot]}
                                        liveIp={isBattery ? pitcherLine?.inningsPitched : undefined}
                                    />
                                </div>
                            );
                        })}

                    {/* Pitcher without an alignment (sim, or a defense the feed hasn't set yet). */}
                    {!defense && situation?.pitcher && (
                        <div className="absolute -translate-x-1/2 -translate-y-1/2" style={atPercent(DEFENSE_SPOTS.pitcher)}>
                            <FieldMarker
                                player={situation.pitcher}
                                role="P"
                                cardMap={cardMap}
                                onCardSelect={onCardSelect}
                                isLoadingCards={isLoadingCards}
                                tone="defense"
                                detailStat1Category="defense"
                                liveIp={pitcherLine?.inningsPitched}
                            />
                        </div>
                    )}

                    {/* Runners + batter, one identity-keyed list. A player keeps the same DOM node
                        (and so animates via `left`/`top` rather than unmount/remount) whenever
                        they're the same person across renders — most valuably, the batter card
                        already sitting at the plate IS the runner card that slides to first on a
                        single or walk, because both use the same `runnerKey`. A multi-base move
                        (double, triple, scoring from first) is stepped through its intermediate
                        bases by `pathOverrides` rather than left to a straight-line CSS
                        interpolation, so the card visibly rounds each base instead of cutting
                        across the infield — the position transition duration matches one hop
                        (`BASE_HOP_MS`) so each leg of a multi-base run reads as a distinct step. */}
                    {presentOccupants.map((occ) => {
                        const renderSpot = pathOverrides[occ.key] ?? occ.spot;
                        return (
                            <div
                                key={occ.key}
                                style={{
                                    ...atPercent(SPOTS[renderSpot]),
                                    zIndex: renderSpot === "plate" ? 2 : 1,
                                    transitionDuration: `${BASE_HOP_MS}ms, ${BASE_HOP_MS}ms, 300ms, 300ms`,
                                }}
                                className={`
                                    absolute -translate-x-1/2 -translate-y-1/2
                                    transition-[left,top,opacity,transform] ease-in-out
                                    ${occ.presence === "present" ? "opacity-100 scale-100"
                                        : occ.presence === "entering" ? "opacity-0 scale-90"
                                        : occ.isOut ? "opacity-0 scale-75 grayscale"
                                        : "opacity-0 scale-110"}
                                `}
                            >
                                <FieldMarker
                                    player={occ.player}
                                    role="H"
                                    cardMap={cardMap}
                                    onCardSelect={onCardSelect}
                                    isLoadingCards={isLoadingCards}
                                    tone="offense"
                                    hideCommand={occ.spot !== "plate"}
                                    detailStat1Category={occ.spot === "plate" ? "hr" : "speed"}
                                />
                            </div>
                        );
                    })}

                    <ResultFlash play={pendingPlay} phase={phase} severity={transition?.severity} />
                </div>

                <ScoreBug game={game} />

                {defense && (
                    <div className="absolute bottom-0 left-0 flex items-center gap-2">
                        <DefenseTotals defense={defense} cardMap={cardMap} />
                        {onToggleExpanded && (
                            <IconButton
                                icon={expanded ? <FaCompress size={12} /> : <FaExpand size={12} />}
                                onClick={onToggleExpanded}
                                label={expanded ? "Show battery only" : "Show all fielders"}
                            />
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
