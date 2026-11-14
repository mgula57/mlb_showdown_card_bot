/**
 * @fileoverview Dev-only shortcut into a live game: two random clubs from history, no saved team or
 * second account needed. "Both sides" seats you on each side (hot seat); "Vs sim" gives the sim the
 * home side. Never rendered in a production build.
 */
import { useState } from "react";
import { FaSpinner } from "react-icons/fa6";

import { createLiveGame, type OpponentController } from "../../../api/liveGame";
import { buttonClass } from "../../shared/buttonStyles";
import { InlineError } from "../../shared/InlineError";
import { useSiteSettings } from "../../shared/SiteSettingsContext";

const MODES: { controller: OpponentController; label: string }[] = [
    { controller: "me", label: "Test game: both sides" },
    { controller: "sim", label: "Test game: vs sim" },
];

export function DevQuickLiveGame({ token, onOpenGame }: { token: string; onOpenGame: (liveGameId: string) => void }) {
    const { userShowdownSet } = useSiteSettings();
    const [starting, setStarting] = useState<OpponentController | null>(null);
    const [error, setError] = useState<string | null>(null);

    const start = async (controller: OpponentController) => {
        setStarting(controller);
        setError(null);
        try {
            const { live_game_id } = await createLiveGame({
                team: { kind: "random_historical" },
                my_side: "away",
                opponent: { controller, team: { kind: "random_historical" } },
                idle_autopilot_minutes: null,
                showdown_set: userShowdownSet,
            }, token);
            onOpenGame(live_game_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Couldn't start a test game.");
            setStarting(null);
        }
    };

    return (
        <div className="flex flex-wrap items-center gap-2">
            {MODES.map(({ controller, label }) => (
                <button key={controller} type="button" disabled={starting !== null} onClick={() => start(controller)} className={buttonClass("secondary", "sm")}>
                    {starting === controller && <FaSpinner className="animate-spin" />}
                    {label}
                </button>
            ))}
            {error && <InlineError>{error}</InlineError>}
        </div>
    );
}
