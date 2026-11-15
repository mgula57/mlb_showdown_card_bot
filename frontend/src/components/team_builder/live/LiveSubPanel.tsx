/**
 * @fileoverview The Manager panel: a live game's club moves, in a `RightPanel` so the board stays
 * in view. Autopilot, how the pitcher is holding up and what's queued sit on top; under them, tabs
 * for a pitching change (a reliever) and a pinch hitter (a bench player and the batter he hits for).
 * Picking queues the move; it takes effect at the next point it can (see
 * `core/simulation/live_game.py`).
 */
import { useState } from "react";
import { FaRobot } from "react-icons/fa6";

import type { LiveAction, LiveSide, LiveSideState } from "../../../api/liveGame";
import type { ShowdownBotCardAPIResponse } from "../../../api/showdownBotCard";
import { CardItemCompactFromCard, CardItemCompactSkeleton } from "../../cards/CardItemCompact";
import { choiceClass } from "../../shared/choiceStyles";
import { EmptyState } from "../../shared/EmptyState";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";
import { RightPanel } from "../../shared/RightPanel";
import { Tabs } from "../../shared/Tabs";
import { describeQueued } from "./liveGameState";
import type { SubPickerMode } from "./LiveTurnControls";

const MODE_TABS: { id: SubPickerMode; label: string }[] = [
    { id: "pitcher", label: "Pitching change" },
    { id: "pinch", label: "Pinch hit" },
];

type Props = {
    /** Null keeps the panel closed. */
    mode: SubPickerMode | null;
    onModeChange: (mode: SubPickerMode) => void;
    side: LiveSide;
    mine: LiveSideState;
    names: Record<string, string>;
    cardMap: Record<string, ShowdownBotCardAPIResponse>;
    /** This club is in the field, so its pitcher's fatigue is worth a note. */
    isFielding: boolean;
    isSubmitting: boolean;
    onPick: (action: LiveAction) => void;
    onToggleAutopilot: (enabled: boolean) => void;
    onClose: () => void;
};

/** The batter a pinch hitter goes in for by default: the one due up, unless he's already at the
 *  plate, in which case the one after him. */
function defaultTarget(mine: LiveSideState): string | undefined {
    if (mine.at_bat_id !== mine.due_up_id) return mine.due_up_id;
    const index = mine.lineup_ids.indexOf(mine.due_up_id);
    return mine.lineup_ids[(index + 1) % mine.lineup_ids.length];
}

function PlayerList({ ids, cardMap, onPick }: { ids: string[]; cardMap: Props["cardMap"]; onPick: (id: string) => void }) {
    return (
        <div className="@container flex flex-col gap-2">
            {ids.map((id) => {
                const card = cardMap[id]?.card;
                return card
                    ? <CardItemCompactFromCard key={id} card={card} onClick={() => onPick(id)} />
                    : <CardItemCompactSkeleton key={id} />;
            })}
        </div>
    );
}

export default function LiveSubPanel({ mode, onModeChange, side, mine, names, cardMap, isFielding, isSubmitting, onPick, onToggleAutopilot, onClose }: Props) {
    const [target, setTarget] = useState<string | undefined>(undefined);
    const queued = new Set(mine.queued.map((action) => action.player_id));
    const forId = target && mine.lineup_ids.includes(target) && target !== mine.at_bat_id ? target : defaultTarget(mine);

    const close = () => { setTarget(undefined); onClose(); };
    const pick = (action: LiveAction) => { onPick(action); close(); };

    const relievers = mine.available_reliever_ids.filter((id) => !queued.has(id));
    const bench = mine.bench_ids.filter((id) => !queued.has(id));
    const pitcherName = names[mine.pitcher_id] ?? "Your pitcher";
    const fatigueNote = isFielding && (mine.pitcher_fatigue > 0
        ? `${pitcherName} is past his IP: −${mine.pitcher_fatigue} Control`
        : mine.pitcher_is_tired ? `${pitcherName} is tiring` : null);

    return (
        <RightPanel
            isOpen={mode !== null}
            onClose={close}
            title="Manager"
            subtitle={mode === "pinch" ? "He bats when that spot comes up." : `Replaces ${pitcherName} before your next pitch.`}
        >
            <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                    <button
                        type="button"
                        onClick={() => onToggleAutopilot(!mine.autopilot)}
                        disabled={isSubmitting}
                        aria-pressed={mine.autopilot}
                        title="Let the sim's manager roll and decide for your club until you switch it off"
                        className={choiceClass(mine.autopilot, "sm", "self-start")}
                    >
                        <FaRobot /> Autopilot {mine.autopilot ? "on" : "off"}
                    </button>
                    {fatigueNote && <p className="text-[12px] text-(--text-secondary)">{fatigueNote}</p>}
                    {mine.queued.length > 0 && (
                        <ul className="space-y-0.5 text-[12px] text-(--text-secondary)">
                            {mine.queued.map((action, i) => <li key={i}>Up next: {describeQueued(action, names)}</li>)}
                        </ul>
                    )}
                </div>

                {mode && <Tabs tabs={MODE_TABS} value={mode} onChange={onModeChange} fullWidth />}

                {mode === "pitcher" && (
                    relievers.length === 0
                        ? <EmptyState size="inline">No one left in the bullpen.</EmptyState>
                        : <PlayerList ids={relievers} cardMap={cardMap} onPick={(id) => pick({ side, kind: "pitching_change", player_id: id })} />
                )}
                {mode === "pinch" && (
                    <div className="flex flex-col gap-4">
                        <div className="flex flex-col gap-2">
                            <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Bat for</span>
                            <div className="flex flex-wrap gap-1.5">
                                {mine.lineup_ids.map((id) => (
                                    <button
                                        key={id}
                                        type="button"
                                        disabled={id === mine.at_bat_id}
                                        onClick={() => setTarget(id)}
                                        className={choiceClass(id === forId, "sm")}
                                    >
                                        {names[id] ?? "Player"}
                                    </button>
                                ))}
                            </div>
                        </div>
                        {bench.length === 0
                            ? <EmptyState size="inline">No one left on the bench.</EmptyState>
                            : <PlayerList ids={bench} cardMap={cardMap} onPick={(id) => forId && pick({ side, kind: "pinch_hit", player_id: id, for_player_id: forId })} />}
                    </div>
                )}
            </div>
        </RightPanel>
    );
}
