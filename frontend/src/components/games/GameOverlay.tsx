import type { ReactNode } from "react";
import { createPortal } from "react-dom";

import { useBodyScrollLock } from "../../hooks/useBodyScrollLock";
import { UnderToolbarFill } from "../shared/UnderToolbarFill";

/**
 * Every game page (real game, replay, sim, Faceoff, live game) as a full-screen layer covering the
 * app's nav, like the league draft room. Portaled to `<body>` since the app's `<main>` is its own
 * stacking context; locks the page behind it and fills under mobile Safari's toolbar (see
 * frontend/DESIGN.md). `--app-nav-offset` zeroes the nav allowance the stage heights normally leave.
 */
export default function GameOverlay({ children }: { children: ReactNode }) {
    useBodyScrollLock(true);
    return createPortal(
        <>
            <UnderToolbarFill zIndex={55} className="left-0 w-full bg-(--background-primary)" />
            <div className="fixed inset-0 z-[55] flex flex-col overflow-y-auto bg-(--background-primary) text-(--text-primary) [--app-nav-offset:0rem]">
                {children}
            </div>
        </>,
        document.body,
    );
}
