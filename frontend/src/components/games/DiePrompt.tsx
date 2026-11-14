/**
 * @fileoverview The dice of a game people play, before they're thrown. `DiePrompt` is the die
 * the player whose turn it is taps to roll, sitting where it will land (beside the pitcher or at the
 * plate). `HeldDie` keeps a roll already made face-up, e.g. the pitch while the swing is waited on.
 * Both match `RollDie`'s size and label so nothing shifts when the toss takes over.
 */
import { D20Face } from "../team_builder/sim/SimDiceRoll";

const DIE_BOX = "relative h-9 w-9 @md:h-11 @md:w-11";
const DIE_LABEL = "text-[8px] font-bold uppercase tracking-[0.12em] text-(--tertiary)";

export function DiePrompt({ label, onRoll, isBusy = false }: {
    label: string;
    onRoll: () => void;
    /** The roll is on its way to the server: no second tap. */
    isBusy?: boolean;
}) {
    return (
        <button
            type="button"
            onClick={onRoll}
            disabled={isBusy}
            aria-label={`Roll ${label.toLowerCase()}`}
            className="group pointer-events-auto flex cursor-pointer flex-col items-center gap-0.5 disabled:cursor-wait"
        >
            <span className={DIE_BOX}>
                {!isBusy && <span className="absolute inset-0 animate-ping rounded-full bg-(--showdown-blue-fill) opacity-40" />}
                <span className={`absolute inset-0 drop-shadow-[0_2px_0_rgb(0_0_0/0.25)] transition-transform duration-150 group-hover:scale-110 group-active:scale-95 ${isBusy ? "animate-spin" : ""}`}>
                    <D20Face value="?" accent="var(--die-body)" ink="var(--die-ink)" />
                </span>
            </span>
            <span className={DIE_LABEL}>Roll</span>
        </button>
    );
}

export function HeldDie({ value, label }: { value: number; label: string }) {
    return (
        <div aria-label={`${label} roll ${value}`} className="pointer-events-none flex flex-col items-center gap-0.5">
            <div className={`${DIE_BOX} drop-shadow-[0_2px_0_rgb(0_0_0/0.25)]`}>
                <D20Face value={value} accent="var(--die-body)" ink="var(--die-ink)" />
            </div>
            <span className={DIE_LABEL}>{label}</span>
        </div>
    );
}
