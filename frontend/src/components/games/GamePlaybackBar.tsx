/**
 * @fileoverview The transport strip under the field: play/pause/step/scrub through a
 * `GameTimeline`, plus (live games only) a buffered-plays badge and a jump back to the live edge.
 * Pure controls component — all state lives in `useGamePlayback` / `useGameDetailData`.
 */
import { FaBackwardStep, FaForwardStep, FaPause, FaPlay } from "react-icons/fa6";

import type { GamePlaybackControls, GamePlaybackState, PlaybackSpeed } from "../../hooks/useGamePlayback";
import IconButton from "../shared/IconButton";

const SPEEDS: PlaybackSpeed[] = [0.5, 1, 2, 4];

type GamePlaybackBarProps = {
    state: GamePlaybackState;
    controls: GamePlaybackControls;
    frameCount: number;
    /** Live only — plays that arrived while paused and are waiting to be watched. */
    bufferedCount?: number;
    onSkipToLive?: () => void;
    /** Box score/defense don't change frame-to-frame during playback — shown as a quiet caveat
     *  rather than left unexplained. */
    isBoxscoreFrozen?: boolean;
    className?: string;
};

export default function GamePlaybackBar({
    state, controls, frameCount, bufferedCount, onSkipToLive, isBoxscoreFrozen, className = "",
}: GamePlaybackBarProps) {
    const situation = state.frame.view.situation;
    const inningLabel = situation ? `${situation.isTop ? "Top" : "Bot"} ${situation.inningLabel}` : state.frame.view.detailedState;
    const outsLabel = situation?.outs != null ? ` · ${situation.outs} out${situation.outs !== 1 ? "s" : ""}` : "";

    const cycleSpeed = () => {
        const idx = SPEEDS.indexOf(state.speed);
        controls.setSpeed(SPEEDS[(idx + 1) % SPEEDS.length]);
    };

    const atEnd = state.cursor >= frameCount - 1;
    const atStart = state.cursor <= 0;
    const pct = frameCount > 1 ? (state.cursor / (frameCount - 1)) * 100 : 0;

    return (
        <div className={`rounded-xl border border-(--divider) bg-(--background-secondary)/90 px-3 py-2.5 ${className}`}>
            <div className="flex items-center gap-2">
                <IconButton
                    icon={<FaBackwardStep size={11} />}
                    onClick={controls.stepBack}
                    label="Previous play"
                    disabled={atStart}
                />
                <IconButton
                    icon={state.isPlaying ? <FaPause size={11} /> : <FaPlay size={11} />}
                    onClick={controls.toggle}
                    label={state.isPlaying ? "Pause" : "Play"}
                    disabled={atEnd && !state.isPlaying}
                />
                <IconButton
                    icon={<FaForwardStep size={11} />}
                    onClick={controls.stepForward}
                    label="Next play"
                    disabled={atEnd}
                />

                <div className="relative flex-1 h-2 rounded-full bg-(--background-tertiary) overflow-hidden">
                    <div
                        className="h-full bg-(--showdown-blue) transition-[width] duration-300 ease-out pointer-events-none"
                        style={{ width: `${pct}%` }}
                    />
                    <input
                        type="range"
                        min={0}
                        max={Math.max(0, frameCount - 1)}
                        step={1}
                        value={state.cursor}
                        onChange={(e) => controls.seek(Number(e.target.value))}
                        aria-label="Scrub through the play-by-play"
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                </div>

                <button
                    type="button"
                    onClick={cycleSpeed}
                    className="cursor-pointer rounded-full border border-(--divider) px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-(--secondary) hover:text-(--primary) transition-colors shrink-0"
                    aria-label={`Playback speed: ${state.speed}x`}
                >
                    {state.speed}×
                </button>
            </div>

            <div className="mt-1.5 flex items-center justify-between gap-2 text-[10px] text-(--secondary)">
                <span className="truncate">
                    {inningLabel}{outsLabel}
                    {isBoxscoreFrozen && <span className="ml-1.5 opacity-60">· box score shows current totals</span>}
                </span>
                <span className="flex items-center gap-2 shrink-0">
                    <span className="tabular-nums">{state.cursor + 1} / {frameCount}</span>
                    {!!bufferedCount && bufferedCount > 0 && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-(--background-tertiary) px-2 py-0.5 font-bold text-(--primary)">
                            <span className="live-pulse h-1.5 w-1.5 rounded-full bg-(--live)" />
                            +{bufferedCount} new
                        </span>
                    )}
                    {onSkipToLive && (
                        <button
                            type="button"
                            onClick={onSkipToLive}
                            className="cursor-pointer font-bold text-(--showdown-blue) hover:underline"
                        >
                            Skip to live
                        </button>
                    )}
                </span>
            </div>
        </div>
    );
}
