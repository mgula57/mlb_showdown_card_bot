/**
 * @fileoverview The field: the centerpiece of the game view. Renders the current situation
 * — runners on base, the pitcher/batter confrontation, and (expanded) the full defensive
 * alignment — over the field art.
 *
 * Reads only `GameView`, so a sim game drives it the same way a real one does. Slots the sim
 * can't fill (defense alignment, runner identity) degrade to markers rather than disappearing.
 */
import { FaCompress, FaExpand } from "react-icons/fa6";

import type { DefenseAlignment, GameView, PlayerRef } from "../../domain/game";
import { resolveCardKey } from "../../domain/players";
import type { ShowdownBotCardAPIResponse, ShowdownBotCardCompact } from "../../api/showdownBotCard";
import { CardItemCompact, CardItemCompactFromCard } from "../cards/CardItemCompact";
import { defenseAtPosition, IF_POSITIONS, OF_POSITIONS } from "../shared/DefenseUtils";
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
    catcher: [49.9, 97],
    first: [83, 44],
    second: [65, 31],
    third: [17, 44],
    shortstop: [34, 31],
    left: [19, 13],
    center: [49.9, 5],
    right: [81, 13],
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
    hideCommand = false, detailStat1Category, liveIp, fieldPosition,
}: {
    player: PlayerRef;
    role: "H" | "P";
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
    tone: "offense" | "defense";
    hideCommand?: boolean;
    detailStat1Category?: "defense" | "speed";
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
        <div className="absolute left-0 top-1/2 -translate-y-1/2 space-y-0.5">
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
        <div className="absolute right-0 top-0 w-max overflow-hidden rounded-lg border border-(--divider) bg-(--background-secondary)/95 text-[11px] shadow-sm lg:hidden">
            {[game.away, game.home].map((side, index) => (
                <div
                    key={side.team.key}
                    className={`flex items-center justify-between gap-3 px-2 py-0.5 ${index === 0 ? "border-b border-(--divider)" : ""}`}
                >
                    <span className="font-bold text-(--primary)">{side.team.abbreviation}</span>
                    <span className="font-black tabular-nums text-(--primary)">{side.score ?? 0}</span>
                </div>
            ))}

            {situation && (
                <div className="flex items-center gap-2 border-t border-(--divider) px-2 py-1">
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

export default function GameField({ game, cardMap, onCardSelect, expanded = false, onToggleExpanded, isLoadingCards, className = "" }: GameFieldProps) {
    const situation = game.situation;
    if (!situation) return null;

    // The fielding side is whichever team isn't batting — used for the pitcher's line score.
    const fieldingSide = situation.isTop ? game.home : game.away;
    const pitcherLine = fieldingSide.boxscore?.pitching.find((line) => line.id === situation.pitcher?.id);
    const defense = situation.defense;

    return (
        <div className={`@container relative w-full ${className}`}>
            {/* Padded so outfielder chips and the score bug can sit above the field art. */}
            <div className="relative px-1 pb-0 pt-8">
                <div className="relative aspect-703/369 w-full overflow-visible">
                    <div className="absolute inset-0 overflow-hidden rounded-lg">
                        <img src="/images/teams/Field No BG.png" alt="" style={ART_STYLE} className="pointer-events-none select-none" />
                    </div>

                    {/* Defense — full alignment when expanded, otherwise just the battery. */}
                    {defense && (Object.keys(DEFENSE_SPOTS) as (keyof DefenseAlignment)[])
                        .filter((slot) => expanded || slot === "pitcher")
                        .map((slot) => {
                            const player = defense[slot];
                            if (!player) return null;
                            return (
                                <div key={slot} className="absolute -translate-x-1/2 -translate-y-1/2" style={atPercent(DEFENSE_SPOTS[slot])}>
                                    <FieldMarker
                                        player={player}
                                        role={slot === "pitcher" ? "P" : "H"}
                                        cardMap={cardMap}
                                        onCardSelect={onCardSelect}
                                        isLoadingCards={isLoadingCards}
                                        tone="defense"
                                        hideCommand={slot !== "pitcher"}
                                        detailStat1Category={slot === "pitcher" ? "defense" : undefined}
                                        liveIp={slot === "pitcher" ? pitcherLine?.inningsPitched : undefined}
                                    />
                                </div>
                            );
                        })}

                    {/* Pitcher without an alignment (sim, or a defense the feed hasn't set yet). */}
                    {!defense && situation.pitcher && (
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

                    {/* Runners */}
                    {(["first", "second", "third"] as const).map((base) => {
                        const runner = situation.bases[base];
                        if (!runner) return null;
                        return (
                            <div key={base} className="absolute -translate-x-1/2 -translate-y-1/2" style={atPercent(BASES[base])}>
                                <FieldMarker
                                    player={runner}
                                    role="H"
                                    cardMap={cardMap}
                                    onCardSelect={onCardSelect}
                                    isLoadingCards={isLoadingCards}
                                    tone="offense"
                                    hideCommand
                                    detailStat1Category="speed"
                                />
                            </div>
                        );
                    })}

                    {/* Batter at the plate */}
                    {situation.batter && (
                        <div className="absolute -translate-x-1/2 -translate-y-1/2" style={atPercent(HOME)}>
                            <FieldMarker
                                player={situation.batter}
                                role="H"
                                cardMap={cardMap}
                                onCardSelect={onCardSelect}
                                isLoadingCards={isLoadingCards}
                                tone="offense"
                            />
                        </div>
                    )}
                </div>

                {defense && <DefenseTotals defense={defense} cardMap={cardMap} />}
                <ScoreBug game={game} />

                {defense && onToggleExpanded && (
                    <button
                        type="button"
                        onClick={onToggleExpanded}
                        aria-label={expanded ? "Show battery only" : "Show all fielders"}
                        className="absolute bottom-0 right-0 cursor-pointer rounded-md border border-(--divider) bg-(--background-secondary)/90 p-1.5 text-(--secondary) hover:text-(--primary)"
                    >
                        {expanded ? <FaCompress size={12} /> : <FaExpand size={12} />}
                    </button>
                )}
            </div>
        </div>
    );
}
