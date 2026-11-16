/** A faint plate over the board's grass. It's too sheer to hold quiet ink, so everything on one
 *  reads in `--text-primary`. See "Game board" in DESIGN.md. */
export const BOARD_PANEL_CLASS = 'rounded-card border border-(--divider) bg-(--background-secondary)/30';

/** The surface for what's laid over the top of the field: the scoreboard and the tabs that grow out
 *  of it (`ScoreboardIsland`). Mostly filled, with the field blurred behind it, so the score and
 *  the turn read cleanly over the outfield art while still sitting on the field. The board's one
 *  exception to "no glass" (see "Game board" in DESIGN.md). */
export const BOARD_OVERLAY_SURFACE_CLASS = 'bg-(--background-primary)/80 backdrop-blur-md'; // design-ok: scoreboard over the field art
export const BOARD_OVERLAY_CLASS = `rounded-card border border-(--divider) ${BOARD_OVERLAY_SURFACE_CLASS}`;
