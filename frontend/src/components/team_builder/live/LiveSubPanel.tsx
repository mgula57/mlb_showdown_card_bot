/**
 * @fileoverview Picking a substitute in a live game, in a `RightPanel` so the board stays in view:
 * a reliever for a pitching change, or a bench player and the batter he hits for. Picking queues the
 * move; it takes effect at the next point it can (see `core/simulation/live_game.py`).
 */
import { useState } from "react";

import type { LiveAction, LiveSide, LiveSideState } from "../../../api/liveGame";
import type { ShowdownBotCardAPIResponse } from "../../../api/showdownBotCard";
import { CardItemCompactFromCard, CardItemCompactSkeleton } from "../../cards/CardItemCompact";
import { choiceClass } from "../../shared/choiceStyles";
import { EmptyState } from "../../shared/EmptyState";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";
import { RightPanel } from "../../shared/RightPanel";
import type { SubPickerMode } from "./LiveTurnBar";

type Props = {
    mode: SubPickerMode | null;
    side: LiveSide;
    mine: LiveSideState;
    names: Record<string, string>;
    cardMap: Record<string, ShowdownBotCardAPIResponse>;
    onPick: (action: LiveAction) => void;
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

export default function LiveSubPanel({ mode, side, mine, names, cardMap, onPick, onClose }: Props) {
    const [target, setTarget] = useState<string | undefined>(undefined);
    const queued = new Set(mine.queued.map((action) => action.player_id));
    const forId = target && mine.lineup_ids.includes(target) && target !== mine.at_bat_id ? target : defaultTarget(mine);

    const close = () => { setTarget(undefined); onClose(); };
    const pick = (action: LiveAction) => { onPick(action); close(); };

    const relievers = mine.available_reliever_ids.filter((id) => !queued.has(id));
    const bench = mine.bench_ids.filter((id) => !queued.has(id));

    return (
        <RightPanel
            isOpen={mode !== null}
            onClose={close}
            title={mode === "pinch" ? "Pinch hit" : "Pitching change"}
            subtitle={mode === "pinch" ? "He bats when that spot comes up." : `Replaces ${names[mine.pitcher_id] ?? "your pitcher"} before your next pitch.`}
        >
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
        </RightPanel>
    );
}
