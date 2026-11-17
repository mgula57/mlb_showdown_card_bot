/**
 * @fileoverview The wide board's panel between the pitcher's and hitter's cards: what the plate
 * appearance comes down to, numbered as the rolls come (`plateAppearanceSteps`): 1 the pitch, 2 the
 * swing, with any throw on a runner (a steal before the pitch, a double-play turn or an extra base
 * after the swing) taking its place in the order. The pitch's meter is the d20's twenty faces, high
 * to low from the pitcher's side to the hitter's, split where Control meets On-Base, with the face
 * rolled lit up. The swing's is each result's chance in this matchup, the one it lands on lit up.
 * Then who bats next. Defense is navy and offense red, as on the strategy cards.
 *
 * While a roll is in the air its meter's marker runs along it and stops where the die lands (the
 * swing's on the result it decides), and the step's header carries a copy of the die
 * (`RollMirrors`), so the roll can be watched here without looking away to the field.
 */
import type { ReactNode } from "react";

import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import type { GameView } from "../../domain/game";
import { DIE_FACES, hitterAdvantageFaces, matchupOutcomeOdds, OUT_RESULTS, pitcherAdvantagePct, type OutcomeOdds } from "../../domain/matchupOdds";
import type { AdvantageSide } from "../../domain/play";
import { useSweptFace } from "../../hooks/useScrambledFace";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { Plate, type PlateVariant } from "../shared/Plate";
import { isDieShown, restingDie, type BoardDie } from "./boardDie";
import { BOARD_PANEL_CLASS } from "./boardStyles";
import { UpNext } from "./GameMatchup";
import type { PlateAppearanceStep, PlateAppearanceStepState } from "./plateAppearanceSteps";
import type { MatchupSideData } from "./resolveMatchup";
import { MiniDie } from "./RollMirrors";

const PITCHER_FILL = "bg-(--showdown-blue-fill)";
const HITTER_FILL = "bg-(--showdown-red-fill)";

/** Faces 20 down to 1, so the pitcher's (the high ones) sit on his card's side. */
const FACES_HIGH_TO_LOW = Array.from({ length: DIE_FACES }, (_, i) => DIE_FACES - i);

const faceRange = (low: number, high: number) => (low > high ? "none" : low === high ? `${low}` : `${low}-${high}`);

const MARKER_CLASS = "outline-2 outline-(--text-primary) -outline-offset-2";

function PitchMeter({ control, onbase, advantage, pitchRoll, die }: {
    control: number;
    onbase: number;
    advantage?: AdvantageSide;
    /** Lit on the meter; the step's header says it. */
    pitchRoll?: number;
    /** The pitch die: the marker runs along the faces while it's in the air and stops on its roll. */
    die?: BoardDie;
}) {
    const sweptFace = useSweptFace(!!die?.isTumbling, die?.speed);
    const markedFace = die?.isTumbling ? sweptFace : isDieShown(die) ? die.value : pitchRoll;
    const hitterFaces = hitterAdvantageFaces(control, onbase);
    const pitcherPct = pitcherAdvantagePct(control, onbase);
    const sideClass = (side: AdvantageSide) => (advantage == null || advantage === side ? "text-(--text-primary)" : "text-(--text-tertiary)");

    return (
        <div className="space-y-1">
            <div className="flex items-baseline justify-between gap-2 text-[11px] tabular-nums">
                <span className={sideClass("pitcher")}><span className="font-semibold">Control {control}</span> · {pitcherPct}%</span>
                <span className={sideClass("hitter")}>{100 - pitcherPct}% · <span className="font-semibold">On-Base {onbase}</span></span>
            </div>
            <div className="flex h-3 gap-px overflow-hidden rounded-plate">
                {FACES_HIGH_TO_LOW.map((face) => {
                    const side: AdvantageSide = face > hitterFaces ? "pitcher" : "hitter";
                    const isRolled = face === markedFace;
                    return (
                        <div
                            key={face}
                            title={`${face}: ${side === "pitcher" ? "pitcher's" : "hitter's"} advantage`}
                            className={`flex-1 transition-opacity duration-300 ${side === "pitcher" ? PITCHER_FILL : HITTER_FILL} ${advantage != null && advantage !== side ? "opacity-30" : ""} ${isRolled ? MARKER_CLASS : ""}`}
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

function OutcomeBar({ odds, swingResult, die }: {
    odds: OutcomeOdds[];
    swingResult?: string;
    /** The swing die: the marker runs along the results until the one it decides is known. */
    die?: BoardDie;
}) {
    const outProb = odds.filter((o) => OUT_RESULTS.has(o.key.toUpperCase())).reduce((sum, o) => sum + o.prob, 0);
    const groups = [
        { key: "OUT", prob: outProb, isOut: true },
        ...odds.filter((o) => !OUT_RESULTS.has(o.key.toUpperCase())).map((o) => ({ key: o.key.toUpperCase(), prob: o.prob, isOut: false })),
    ].filter((group) => group.prob > 0);
    const landed = swingResult?.toUpperCase();
    const landedGroup = landed == null ? undefined : OUT_RESULTS.has(landed) ? "OUT" : landed;
    const isLit = (key: string) => landedGroup == null || landedGroup === key;
    const isSweeping = !!die && landedGroup == null && groups.length > 0;
    const sweptFace = useSweptFace(isSweeping, die?.speed);
    const markedGroup = isSweeping ? groups[(DIE_FACES - sweptFace) % groups.length].key : landedGroup;

    return (
        <div className="space-y-1">
            <div className="flex h-2 gap-px overflow-hidden rounded-plate">
                {groups.map((group) => (
                    <div
                        key={group.key}
                        className={`transition-opacity duration-300 ${group.isOut ? PITCHER_FILL : HITTER_FILL} ${!isLit(group.key) ? "opacity-20" : group.isOut ? "" : ON_BASE_SHADES[group.key] ?? ""} ${markedGroup === group.key ? MARKER_CLASS : ""}`}
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

const STEP_NUMBER_VARIANT: Record<PlateAppearanceStepState, PlateVariant> = { done: "ink", current: "navy", upcoming: "outline" };

/** What a step came to, beside its name. Its roll is on the die beside it. */
function stepOutcome(step: PlateAppearanceStep): ReactNode {
    if (step.state !== "done") return null;
    switch (step.kind) {
        case "pitch":
            return <>{step.advantage === "pitcher" ? "Pitcher" : "Hitter"} adv</>;
        case "swing":
            return step.swingResult?.toUpperCase();
        default:
            return <span className={step.isSafe ? "text-(--green)" : "text-(--red)"}>{step.isSafe ? "Safe" : "Out"}</span>;
    }
}

/** One roll of the plate appearance: its number and name, its die, what it came to, and its meter. */
function StepRow({ number, step, die, children }: { number: number; step: PlateAppearanceStep; die?: BoardDie; children?: ReactNode }) {
    const outcome = stepOutcome(step);
    return (
        <li className="space-y-1">
            <div className={`flex items-center gap-1.5 transition-opacity duration-300 ${step.state === "upcoming" ? "opacity-50" : ""}`}>
                <Plate size="xs" variant={STEP_NUMBER_VARIANT[step.state]} className="min-w-3.5 justify-center tabular-nums">{number}</Plate>
                <span className={`${CAPS_LABEL_CLASS} text-(--text-primary)`}>{step.label}</span>
                {step.state === "current" && !die && <span className="live-pulse h-1.5 w-1.5 shrink-0 rounded-full bg-(--live)" aria-hidden />}
                <span className="ml-auto flex items-center gap-1 text-[11px] font-semibold text-(--text-primary)">
                    {die && <MiniDie die={die} />}
                    {outcome}
                </span>
            </div>
            {children}
        </li>
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
    /** The plate appearance's rolls in order (`plateAppearanceSteps`). */
    steps: PlateAppearanceStep[];
    /** The pitch and swing dice while they're in play (`RollMirrors`). */
    dice?: { pitch?: BoardDie; swing?: BoardDie };
};

/** A step's die: the pitch's or swing's while it's in play, else the roll it came to. */
function stepDie(step: PlateAppearanceStep, dice: MatchupCenterPanelProps["dice"]): BoardDie | undefined {
    switch (step.kind) {
        case "pitch":
            return dice?.pitch ?? (step.pitchRoll != null ? restingDie(step.key, step.pitchRoll) : undefined);
        case "swing":
            return dice?.swing;
        default:
            return step.roll != null && step.roll > 0 ? restingDie(step.key, step.roll) : undefined;
    }
}

export default function MatchupCenterPanel({ matchup, game, cardMap, isLoadingCards, onCardSelect, advantage, pitchRoll, swingResult, steps, dice }: MatchupCenterPanelProps) {
    const pitcherChart = matchup.pitcher.response?.card?.chart;
    const hitterChart = matchup.hitter.response?.card?.chart;
    const odds = pitcherChart && hitterChart
        ? matchupOutcomeOdds({ control: pitcherChart.command, onbase: hitterChart.command, pitcherValues: pitcherChart.values, hitterValues: hitterChart.values })
        : null;

    return (
        <div className={`${BOARD_PANEL_CLASS} flex h-full flex-col gap-2.5 overflow-hidden p-2`}>
            {pitcherChart && hitterChart && odds ? (
                <ol className="space-y-2">
                    {steps.map((step, i) => (
                        <StepRow key={step.key} number={i + 1} step={step} die={stepDie(step, dice)}>
                            {step.kind === "pitch" && <PitchMeter control={pitcherChart.command} onbase={hitterChart.command} advantage={advantage} pitchRoll={pitchRoll} die={dice?.pitch} />}
                            {step.kind === "swing" && <OutcomeBar odds={odds} swingResult={swingResult} die={dice?.swing} />}
                        </StepRow>
                    ))}
                </ol>
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
