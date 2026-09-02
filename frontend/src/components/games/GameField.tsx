/**
 * @fileoverview The field: the centerpiece of the game view. Renders the current situation
 * — runners on base, the pitcher/batter confrontation, and (expanded) the full defensive
 * alignment — over the field art.
 *
 * Reads only `GameView`, so a sim game drives it the same way a real one does. Slots the sim
 * can't fill (defense alignment, runner identity) degrade to markers rather than disappearing.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { FaCaretUp, FaCompress, FaExpand } from "react-icons/fa6";

import type { DefenseAlignment, GameView, PlayerRef } from "../../domain/game";
import { resolveCardKey } from "../../domain/players";
import { ordinal } from "../../functions/formatters";
import { basePathBetween, runnerKey, type FrameTransition, type RunnerSpot } from "../../domain/timeline";
import type { PlayEntry } from "../../domain/play";
import type { ShowdownBotCardAPIResponse, ShowdownBotCardCompact } from "../../api/showdownBotCard";
import { CardItemCompact, CardItemCompactFromCard } from "../cards/CardItemCompact";
import { defenseAtPosition, IF_POSITIONS, OF_POSITIONS } from "../shared/DefenseUtils";
import { usePresenceList } from "../../hooks/usePresenceList";
import type { PlayPhase } from "../../hooks/useGamePlayback";

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
    /** The most recent completed play — its text description sits in the field's bottom-right
     *  corner, opposite the defense summary. Undefined before the first play of the game. */
    lastPlay?: PlayEntry;
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
    pitcher: [49.9, 50.5],
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

/** Linear blend between two field coordinates — parks a retiring player a fraction of the way
 *  along the path they were running (toward first on a ground out, toward the next base on a
 *  runner thrown out) before they fade out, instead of teleporting or vanishing on the spot. */
const lerpSpot = (
    [ax, ay]: readonly [number, number],
    [bx, by]: readonly [number, number],
    t: number,
): [number, number] => [ax + (bx - ax) * t, ay + (by - ay) * t];

/** Every spot an offensive occupant (runner or batter) can render at — the three bases plus the
 *  plate, used both as "about to bat" and as "just scored" (a different visual moment, same x/y). */
const SPOTS: Record<RunnerSpot, readonly [number, number]> = {
    first: BASES.first, second: BASES.second, third: BASES.third, plate: HOME, home: HOME,
};

type FieldOccupant = {
    key: string;
    player: PlayerRef;
    spot: RunnerSpot;
    isOut?: boolean;
    /** Playback-only exit choreography for a retirement:
     *   - "poof"  — fade out in place, promptly (a strikeout: the batter just leaves the box).
     *   - "drift" — break a fraction of the way toward `driftTo` while fading (a ball put in
     *               play for an out heads up the first-base line; a runner thrown out
     *               advancing/stealing breaks for the next base).
     *  Undefined = the pre-existing behaviour (the presence list fades them where they stand). */
    exit?: "poof" | "drift";
    /** Destination for `exit: "drift"` — the runner covers part of the way there, then fades. */
    driftTo?: RunnerSpot;
};

const STRIKEOUT_EVENT = /strikeout/;
const IN_PLAY_OUT_EVENT = /(groundout|flyout|lineout|pop\s?out|forceout|force out|field out|fielders? choice|grounded into|double play|triple play|sac fly|sac bunt|bunt)/;

/**
 * One offensive occupant per base PLUS the batter, keyed by player identity rather than by base
 * slot. Keying the batter with the exact identity they'll have as a runner (`runnerKey` ignores
 * which spot it's asked about when the player has an id) is what turns a single or a walk into
 * one DOM node whose `left`/`top` changes — the card runs to first — instead of two markers
 * swapping out. `transition`/`pendingPlay` (playback only) also add back a departing player for a
 * beat so their exit has something to animate:
 *   - a scoring runner sits at "home" and fades;
 *   - a runner retired on the bases starts at `move.from` and, when the base they were breaking
 *     for is known (`move.attemptedTo`), gets `exit: "drift"` toward the next base along that
 *     path — otherwise (stranded at a half-inning's end, or a data gap) they just fade in place;
 *   - the batter's own retirement isn't a `move` at all (they were never on a base to leave), so
 *     it's read straight off `pendingPlay.event`: a strikeout "poof"s in place, anything else put
 *     in play for an out "drift"s toward first.
 * Without a transition (live polling) a departure simply disappears when `situation` stops
 * reporting it, same as today.
 */
function buildFieldOccupants(
    situation: GameView["situation"],
    transition: FrameTransition | undefined,
    pendingPlay: PlayEntry | undefined,
): FieldOccupant[] {
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
            const driftTo = move.attemptedTo && move.attemptedTo !== move.from
                ? basePathBetween(move.from, move.attemptedTo)[0]
                : undefined;
            occupants.set(move.key, {
                key: move.key, player: move.player, spot: move.from, isOut: true,
                exit: driftTo ? "drift" : undefined, driftTo,
            });
        }
    }

    // The batter's retirement — classified from the resolving play, since it produces no `move`.
    if (situation.batter && transition && pendingPlay) {
        const key = runnerKey(situation.batter, "plate");
        const batterMoved = transition.moves.some((m) => m.key === key);
        if (!batterMoved) {
            const event = (pendingPlay.event ?? "").toLowerCase();
            if (STRIKEOUT_EVENT.test(event)) {
                occupants.set(key, { key, player: situation.batter, spot: "plate", isOut: true, exit: "poof" });
            } else if (IN_PLAY_OUT_EVENT.test(event)) {
                occupants.set(key, { key, player: situation.batter, spot: "plate", isOut: true, exit: "drift", driftTo: "first" });
            }
        }
    }

    return [...occupants.values()];
}

/** How long each individual base-to-base hop takes. A HR (plate→home, 4 hops) then takes 4x this,
 *  which is intentional — covering more ground should visibly take longer, not less per hop. */
const BASE_HOP_MS = 220;

/**
 * Steps a multi-base ADVANCE through its intermediate stops instead of letting the CSS transition
 * interpolate `left`/`top` directly between start and end — a direct interpolation would cut a
 * diagonal line across the infield grass on a double or triple. Returns a per-runner-key override
 * of which stop to render at RIGHT NOW; a single-hop move (the common case — batter to first,
 * runner to the next base over) isn't stepped at all, since one direct CSS transition already
 * looks correct for a single leg.
 *
 * Only moves with a real `move.to` (advance / arrive / score) are stepped. A runner retired on
 * the bases has `to: null` and is handled by `buildFieldOccupants` + `GameField` instead — they
 * break a short way toward the base they were going for and fade, rather than completing the trip.
 */
function useBasePathAnimation(transition: FrameTransition | undefined): Record<string, RunnerSpot> {
    // The FIRST waypoint of every multi-hop move is known synchronously from `transition` alone —
    // computed directly during render rather than via an effect, so there's no frame where a
    // runner briefly renders at its old spot before the animation has had a chance to start.
    const initialOverrides = useMemo(() => {
        const initial: Record<string, RunnerSpot> = {};
        for (const move of transition?.moves ?? []) {
            const destination = move.to;
            if (!move.from || !destination) continue; // no path to step (fresh arrival, or any out)
            const path = basePathBetween(move.from, destination);
            if (path.length > 1) initial[move.key] = path[0]; // one leg needs no stepping at all
        }
        return initial;
    }, [transition]);

    // Later waypoints land on a delay, which genuinely needs an effect+timers — but every
    // `setState` call here happens inside a `setTimeout` callback, never synchronously in the
    // effect body itself, so a stale-transition guard (comparing `transition` at read time) does
    // the resetting instead of an unconditional reset at the top of the effect.
    //
    // Each waypoint, including the LAST one, is held until `transition` itself changes — i.e.
    // until the frame commits or the next play starts — never cleared on a timer. `buildFieldOccupants`
    // reflects a `home` or an out move on the occupant's own `spot` right away, but an
    // arrive/advance ONTO a base isn't mirrored there until the frame commits and `situation`
    // catches up; dropping the override before then would snap a doubled runner (occupant `spot`
    // still "plate") back to the plate for the rest of the beat.
    const [laterState, setLaterState] = useState<{
        transition: FrameTransition | undefined;
        overrides: Record<string, RunnerSpot>;
    }>({ transition: undefined, overrides: {} });
    const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

    useEffect(() => {
        timersRef.current.forEach(clearTimeout);
        timersRef.current = [];
        if (!transition) return;

        const timers: ReturnType<typeof setTimeout>[] = [];
        for (const move of transition.moves) {
            const destination = move.to;
            if (!move.from || !destination) continue;
            const path = basePathBetween(move.from, destination);
            if (path.length <= 1) continue;

            path.forEach((stop, i) => {
                if (i === 0) return;
                timers.push(setTimeout(() => {
                    setLaterState((prev) => {
                        const base = prev.transition === transition ? prev.overrides : {};
                        return { transition, overrides: { ...base, [move.key]: stop } };
                    });
                }, i * BASE_HOP_MS));
            });
        }

        timersRef.current = timers;
        return () => timers.forEach(clearTimeout);
    }, [transition]);

    // `laterState.overrides` (once it's for this transition) wins over the permanent `path[0]`
    // waypoint from `initialOverrides`, so a completed multi-hop resolves to its final stop and
    // stays there until the frame commits.
    const merged: Record<string, RunnerSpot> = { ...initialOverrides };
    if (laterState.transition === transition) Object.assign(merged, laterState.overrides);
    return merged;
}

const FLASH_SHELL = `
    absolute left-1/2 top-[6%] z-30 -translate-x-1/2
    pointer-events-none select-none whitespace-nowrap
    rounded-full border font-black uppercase tracking-wide shadow-lg
    transition-[opacity,transform] duration-300 ease-out
`;

/** The half-inning changeover, shown on the play-less break frame: a caret + inning number that
 *  flips from the half just finished to the half about to start as the bases clear. `▲` = top
 *  (visitors bat), `▼` = bottom (home bats); when the inning number itself changes (a bottom half
 *  ending) the digit rolls up to the next one. Driven by `phase` so it tracks playback speed —
 *  the outgoing half holds through "result", then flips on "runners" as the bases clear. */
function HalfInningFlash({ brk, phase, visible }: {
    brk: NonNullable<FrameTransition["halfInningBreak"]>;
    phase: PlayPhase;
    visible: boolean;
}) {
    const flipped = phase === "runners" || phase === "settle";
    const isTop = flipped ? brk.toIsTop : brk.fromIsTop;
    const inningChanges = brk.fromInning !== brk.toInning;

    return (
        <div
            key={`brk-${brk.toInning}-${brk.toIsTop}`}
            aria-hidden={!visible}
            className={`
                ${FLASH_SHELL}
                flex items-center gap-2 px-4 py-1.5 text-sm
                bg-(--background-secondary)/95 border-(--divider) text-(--primary)
                ${visible ? "opacity-100 translate-y-0 result-pop" : "opacity-0 -translate-y-2"}
            `}
        >
            <FaCaretUp
                className="text-(--live) transition-transform duration-500 ease-out"
                style={{ transform: isTop ? "rotate(0deg)" : "rotate(180deg)" }}
            />
            <span className="inline-block h-[1.15em] overflow-hidden tabular-nums">
                <span
                    className="block transition-transform duration-500 ease-out"
                    style={{ transform: flipped && inningChanges ? "translateY(-50%)" : "translateY(0)" }}
                >
                    <span className="block h-[1.15em] leading-[1.15em]">{ordinal(brk.fromInning)}</span>
                    <span className="block h-[1.15em] leading-[1.15em]">{ordinal(brk.toInning)}</span>
                </span>
            </span>
        </div>
    );
}

/** Temporary badge announcing what's resolving — a play result ("Double", "Home Run",
 *  "Strikeout"), or the inning changeover on the half-inning break (see `HalfInningFlash`).
 *  Visible for the stretch of the phase machine where the field is actually animating, then it
 *  fades. Absent entirely outside playback (`phase` stays "idle" when there's nothing to reveal),
 *  so a plain live view never shows it. */
function ResultFlash({ play, phase, transition }: { play: PlayEntry | undefined; phase: PlayPhase; transition?: FrameTransition }) {
    const visible = phase === "result" || phase === "runners";

    // The half-inning-break frame carries no `play` — flip the inning arrow instead.
    if (!play && transition?.halfInningBreak) {
        return <HalfInningFlash brk={transition.halfInningBreak} phase={phase} visible={visible} />;
    }

    if (!play) return null;

    const isBig = transition?.severity === "big";
    const label = isBig && play.isScoringPlay && !/[!?]$/.test(play.event) ? `${play.event}!` : play.event;

    return (
        <div
            key={play.id}
            aria-hidden={!visible}
            className={`
                ${FLASH_SHELL}
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
    hideCommand = false, hideTeamPoints = false, detailStat1Category, liveIp, fieldPosition,
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
        <div className="w-18 @[380px]:w-28 @[520px]:w-32 @[650px]:w-40">
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

/** OF / IF / CA totals for the fielding side plus the expand/collapse toggle, gathered into one
 * container in the field's bottom-left corner. Null when no alignment is available
 * (pre-first-pitch, or a sim game). */
function DefenseSummary({
    defense, cardMap, expanded, onToggleExpanded,
}: {
    defense: DefenseAlignment;
    cardMap: CardMap;
    expanded: boolean;
    onToggleExpanded?: () => void;
}) {
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

    // OF / IF / CA totals plus the toggle, packed into a 2x2 block so the summary claims a
    // compact corner instead of a wide strip. Borders are drawn per grid position: a right edge
    // on the left column, a bottom edge on the top row.
    const cells: { key: string; content: React.ReactNode; onClick?: () => void; label?: string }[] = [
        ...rows.map(([label, value]) => ({
            key: label,
            content: (
                <>
                    <span className="text-(--secondary)">{label}</span>
                    <span className="text-(--primary)">{value == null ? "–" : `+${value}`}</span>
                </>
            ),
        })),
    ];
    if (onToggleExpanded) {
        cells.push({
            key: "toggle",
            content: expanded ? <FaCompress size={12} /> : <FaExpand size={12} />,
            onClick: onToggleExpanded,
            label: expanded ? "Show battery only" : "Show all fielders",
        });
    }

    return (
        <div className="inline-grid grid-cols-2 overflow-hidden rounded-md border border-(--divider) bg-(--background-secondary)/30 text-[10px] font-bold">
            {cells.map((cell, i) => {
                const edges = `${i % 2 === 0 ? "border-r " : ""}${i < 2 ? "border-b " : ""}border-(--divider)`;
                const base = `flex items-center justify-center gap-1 px-1.5 py-1 ${edges}`;
                return cell.onClick ? (
                    <button
                        key={cell.key}
                        type="button"
                        onClick={cell.onClick}
                        aria-label={cell.label}
                        className={`${base} cursor-pointer text-(--secondary) transition-colors hover:text-(--primary)`}
                    >
                        {cell.content}
                    </button>
                ) : (
                    <div key={cell.key} className={base}>
                        {cell.content}
                    </div>
                );
            })}
        </div>
    );
}

/** Plain-text recap of the most recent completed play, tucked into the field's bottom-right
 * corner opposite the defense summary. Clamped to two lines so a wordy description never pushes
 * into the field art. */
function LastPlaySummary({ play }: { play: PlayEntry }) {
    const description = play.description?.trim();
    if (!description && !play.event) return null;

    return (
        <div className="max-w-[35%] rounded-md border border-(--divider) bg-(--background-secondary)/30 px-1.5 py-1 text-right text-[10px] leading-snug text-(--primary)">
            <p className="line-clamp-3 w-full">
                {play.event && <span className="font-extrabold text-(--primary)">{play.event}</span>}
                {description && description !== play.event && <span className="ml-0.5">{description}</span>}
            </p>
        </div>
    );
}

export default function GameField({ game, cardMap, onCardSelect, expanded = false, onToggleExpanded, isLoadingCards, transition, pendingPlay, phase = "idle", lastPlay, className = "" }: GameFieldProps) {
    const situation = game.situation;
    // if (!situation) return null;

    // The fielding side is whichever team isn't batting — used for the pitcher's line score.
    const fieldingSide = situation?.isTop ? game.home : game.away;
    const pitcherLine = fieldingSide.boxscore?.pitching.find((line) => line.id === situation?.pitcher?.id);
    const defense = situation?.defense;

    const occupants = useMemo(
        () => buildFieldOccupants(situation, transition, pendingPlay),
        [situation, transition, pendingPlay],
    );
    // Exit hold covers the longest possible base-running path (plate→home, 4 hops) plus a fade
    // tail, so a runner scoring or getting thrown out has time to finish the whole trip and fade
    // before `usePresenceList` drops them — this is a JS-side mirror of that timing, not a second
    // source of truth for how long the actual CSS transitions run.
    const presentOccupants = usePresenceList(occupants, BASE_HOP_MS * 4 + 300);
    const pathOverrides = useBasePathAnimation(transition);

    return (
        <div className={`@container relative w-full ${className}`}>
            {/* Padded so outfielder/catcher cards have room to sit above and
                below the field art without overlapping whatever follows in the DOM. Expanded
                needs noticeably more of both — the fielder cards carry a defense-rating row, and
                the catcher/corner outfielders sit right at the edges with nothing to spare
                otherwise. The padding transition is what makes the expand/collapse feel like the
                field is growing rather than snapping to a new size. */}
            <div className={`relative px-1 transition-[padding] duration-300 ease-out ${expanded ? "pt-28 pb-12" : "pt-0 pb-0"}`}>
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
                                        hideTeamPoints={!isBattery}
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
                        // Still stepping through `pathOverrides` = still mid-run on a real advance.
                        const isMidPath = pathOverrides[occ.key] !== undefined;
                        const renderSpot = pathOverrides[occ.key] ?? occ.spot;

                        // A retirement's exit choreography ("poof" / "drift", set in
                        // `buildFieldOccupants`) only plays once the result has been revealed —
                        // through the "pitch" beat everyone still stands where they were at first
                        // pitch. After the frame commits the occupant is "leaving" and we keep
                        // playing it out until the presence list drops it.
                        const exiting = !!occ.exit
                            && (phase === "result" || phase === "runners" || phase === "settle" || occ.presence === "leaving");

                        let [x, y] = SPOTS[renderSpot];
                        if (exiting && occ.exit === "drift" && occ.driftTo) {
                            // Batter grounds/flies out → a step up the first-base line. Runner
                            // gunned down advancing → a break toward the next base. Then they fade.
                            [x, y] = lerpSpot(SPOTS[occ.spot], SPOTS[occ.driftTo], occ.spot === "plate" ? 0.4 : 0.45);
                        }

                        // The next hitter walks in from the third-base side rather than fading in
                        // on the spot — paired with the outgoing batter's prompt exit above.
                        const walkingIn = occ.presence === "entering" && occ.spot === "plate";
                        if (walkingIn) x -= 16;

                        // A retired runner with no exit of their own (stranded at inning's end)
                        // still reads as "tagged" where they stood.
                        const taggedOut = occ.isOut && !occ.exit && occ.presence === "present" && !isMidPath;

                        const posDur = walkingIn ? 450 : occ.exit === "drift" ? 600 : BASE_HOP_MS;
                        const opacityDur = occ.exit === "poof" ? 200 : occ.exit === "drift" ? 520 : 300;

                        const stateClass = occ.presence === "entering"
                            ? (walkingIn ? "opacity-0" : "opacity-0 scale-90")
                            : exiting
                                ? (occ.exit === "poof" ? "opacity-0 scale-95"
                                    : occ.spot === "plate" ? "opacity-0 scale-90"
                                    : "opacity-0 scale-90 grayscale")
                                : occ.presence === "leaving"
                                    ? (occ.isOut ? "opacity-0 scale-75 grayscale" : "opacity-0 scale-110")
                                    : taggedOut ? "opacity-50 scale-90 grayscale"
                                    : "opacity-100 scale-100";

                        return (
                            <div
                                key={occ.key}
                                style={{
                                    left: `${x}%`,
                                    top: `${y}%`,
                                    zIndex: renderSpot === "plate" ? 2 : 1,
                                    transitionDuration: `${posDur}ms, ${posDur}ms, ${opacityDur}ms, 300ms`,
                                }}
                                className={`
                                    absolute -translate-x-1/2 -translate-y-1/2
                                    transition-[left,top,opacity,transform] ease-in-out
                                    ${stateClass}
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
                                    hideTeamPoints={occ.spot !== "plate"}
                                    detailStat1Category={occ.spot === "plate" ? "hr" : "hr"}
                                />
                            </div>
                        );
                    })}

                    <ResultFlash play={pendingPlay} phase={phase} transition={transition} />
                </div>

                {defense && (
                    <div className="absolute bottom-0 left-0">
                        <DefenseSummary
                            defense={defense}
                            cardMap={cardMap}
                            expanded={expanded}
                            onToggleExpanded={onToggleExpanded}
                        />
                    </div>
                )}

                {lastPlay && (
                    <div className="absolute bottom-0 right-0 flex justify-end">
                        <LastPlaySummary play={lastPlay} />
                    </div>
                )}
            </div>
        </div>
    );
}
