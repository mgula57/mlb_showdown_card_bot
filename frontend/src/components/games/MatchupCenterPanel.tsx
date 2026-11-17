/**
 * @fileoverview The wide board's panel between the pitcher's and hitter's cards: what the plate
 * appearance comes down to. The pitch meter is the d20's twenty faces, high to low from the
 * pitcher's side to the hitter's, split where Control meets On-Base, with the face rolled lit up.
 * Under it, each result's chance in this matchup, the one the swing lands on lit up, and then who
 * bats next. Defense is navy and offense red, as on the strategy cards.
 */
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import type { GameView } from "../../domain/game";
import { DIE_FACES, hitterAdvantageFaces, matchupOutcomeOdds, OUT_RESULTS, pitcherAdvantagePct, type OutcomeOdds } from "../../domain/matchupOdds";
import type { AdvantageSide } from "../../domain/play";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { BOARD_PANEL_CLASS } from "./boardStyles";
import { UpNext } from "./GameMatchup";
import type { MatchupSideData } from "./resolveMatchup";

const PITCHER_FILL = "bg-(--showdown-blue-fill)";
const HITTER_FILL = "bg-(--showdown-red-fill)";

/** Faces 20 down to 1, so the pitcher's (the high ones) sit on his card's side. */
const FACES_HIGH_TO_LOW = Array.from({ length: DIE_FACES }, (_, i) => DIE_FACES - i);

const faceRange = (low: number, high: number) => (low > high ? "none" : low === high ? `${low}` : `${low}-${high}`);

function PitchMeter({ control, onbase, advantage, pitchRoll }: {
    control: number;
    onbase: number;
    advantage?: AdvantageSide;
    pitchRoll?: number;
}) {
    const hitterFaces = hitterAdvantageFaces(control, onbase);
    const pitcherPct = pitcherAdvantagePct(control, onbase);
    const sideClass = (side: AdvantageSide) => (advantage == null || advantage === side ? "text-(--text-primary)" : "text-(--text-tertiary)");

    return (
        <div className="space-y-1">
            <div className="flex items-baseline justify-between gap-2 text-[11px] tabular-nums">
                <span className={sideClass("pitcher")}><span className="font-semibold">Control {control}</span> · {pitcherPct}%</span>
                {pitchRoll != null && <span className={`${CAPS_LABEL_CLASS} text-(--text-primary)`}>Rolled {pitchRoll}</span>}
                <span className={sideClass("hitter")}>{100 - pitcherPct}% · <span className="font-semibold">On-Base {onbase}</span></span>
            </div>
            <div className="flex h-3 gap-px overflow-hidden rounded-plate">
                {FACES_HIGH_TO_LOW.map((face) => {
                    const side: AdvantageSide = face > hitterFaces ? "pitcher" : "hitter";
                    const isRolled = face === pitchRoll;
                    return (
                        <div
                            key={face}
                            title={`${face}: ${side === "pitcher" ? "pitcher's" : "hitter's"} advantage`}
                            className={`flex-1 transition-opacity duration-300 ${side === "pitcher" ? PITCHER_FILL : HITTER_FILL} ${advantage != null && advantage !== side ? "opacity-30" : ""} ${isRolled ? "outline-2 outline-(--text-primary) -outline-offset-2" : ""}`}
                        />
                    );
                })}
            </div>
            <div className="flex justify-between text-[10px] tabular-nums text-(--text-tertiary)">
                <span>{faceRange(hitterFaces + 1, DIE_FACES)}</span>
                <span>{faceRange(1, hitterFaces)}</span>
            </div>
        </div>
    );
}

/** The outs are one share; each on-base result its own, shaded up from a walk to a home run. */
const ON_BASE_SHADES: Record<string, string> = { BB: "opacity-45", "1B": "opacity-60", "1B+": "opacity-70", "2B": "opacity-80", "3B": "opacity-90", HR: "" };

function OutcomeBar({ odds, swingResult }: { odds: OutcomeOdds[]; swingResult?: string }) {
    const outProb = odds.filter((o) => OUT_RESULTS.has(o.key.toUpperCase())).reduce((sum, o) => sum + o.prob, 0);
    const groups = [
        { key: "OUT", prob: outProb, isOut: true },
        ...odds.filter((o) => !OUT_RESULTS.has(o.key.toUpperCase())).map((o) => ({ key: o.key.toUpperCase(), prob: o.prob, isOut: false })),
    ].filter((group) => group.prob > 0);
    const landed = swingResult?.toUpperCase();
    const landedGroup = landed == null ? undefined : OUT_RESULTS.has(landed) ? "OUT" : landed;
    const isLit = (key: string) => landedGroup == null || landedGroup === key;

    return (
        <div className="space-y-1">
            <div className="flex h-2 gap-px overflow-hidden rounded-plate">
                {groups.map((group) => (
                    <div
                        key={group.key}
                        className={`transition-opacity duration-300 ${group.isOut ? PITCHER_FILL : HITTER_FILL} ${!isLit(group.key) ? "opacity-20" : group.isOut ? "" : ON_BASE_SHADES[group.key] ?? ""}`}
                        style={{ width: `${group.prob * 100}%` }}
                    />
                ))}
            </div>
            <div className="flex flex-wrap gap-x-2 text-[10px] tabular-nums">
                {groups.map((group) => (
                    <span key={group.key} className={landedGroup === group.key ? "font-semibold text-(--text-primary)" : "text-(--text-tertiary)"}>
                        {group.key} {Math.round(group.prob * 100)}%
                    </span>
                ))}
            </div>
        </div>
    );
}

type MatchupCenterPanelProps = {
    matchup: Record<AdvantageSide, MatchupSideData>;
    game: GameView;
    cardMap: Record<string, ShowdownBotCardAPIResponse>;
    isLoadingCards?: boolean;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    /** Who won the pitch, once it's known. */
    advantage?: AdvantageSide;
    pitchRoll?: number;
    /** The chart result the swing landed on. */
    swingResult?: string;
};

export default function MatchupCenterPanel({ matchup, game, cardMap, isLoadingCards, onCardSelect, advantage, pitchRoll, swingResult }: MatchupCenterPanelProps) {
    const pitcherChart = matchup.pitcher.response?.card?.chart;
    const hitterChart = matchup.hitter.response?.card?.chart;
    const odds = pitcherChart && hitterChart
        ? matchupOutcomeOdds({ control: pitcherChart.command, onbase: hitterChart.command, pitcherValues: pitcherChart.values, hitterValues: hitterChart.values })
        : null;

    return (
        <div className={`${BOARD_PANEL_CLASS} flex h-full flex-col gap-2.5 overflow-hidden p-2`}>
            {pitcherChart && hitterChart && odds ? (
                <>
                    <PitchMeter control={pitcherChart.command} onbase={hitterChart.command} advantage={advantage} pitchRoll={pitchRoll} />
                    <OutcomeBar odds={odds} swingResult={swingResult} />
                </>
            ) : (
                <div aria-hidden className="h-16 shrink-0 animate-pulse rounded-control bg-(--background-tertiary)" />
            )}
            {/* Takes what height is left, the furthest hitters cut off first */}
            <div className="min-h-0 flex-1 overflow-hidden">
                <UpNext game={game} cardMap={cardMap} isLoadingCards={isLoadingCards} onCardSelect={onCardSelect} variant="rows" />
            </div>
        </div>
    );
}
