import type { ReactNode } from "react";

/** What a host hands `GameStage` to put strategy cards on the board, each in its own zone:
 *  - `hand`: the field's bottom-left corner (`StrategyHandStack`);
 *  - `tray`: laid over the bottom of the field while the hand is open (`StrategyHandTray`);
 *  - `played`: the cards on the table, on the pitcher's and the hitter's card (`PlayedStrategyCards`).
 *  Whose call it is goes in the host's `boardTurn`, in the scoreboard's island. */
export type StrategyBoardSlots = {
    hand?: ReactNode;
    tray?: ReactNode;
    played?: { pitcher?: ReactNode; hitter?: ReactNode };
};
