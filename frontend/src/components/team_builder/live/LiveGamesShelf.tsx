/**
 * @fileoverview The signed-in user's live games on the My Teams tab, the ones waiting on them first.
 * Renders nothing until there's at least one, so it never flashes an empty section (in dev it always
 * renders, with a shortcut into a test game).
 */
import { useEffect, useState } from "react";

import { fetchMyLiveGames, type LiveGameListItem } from "../../../api/liveGame";
import { relativeTime } from "../../../functions/formatters";
import { Heading } from "../../shared/Heading";
import { Plate } from "../../shared/Plate";
import { DevQuickLiveGame } from "./DevQuickLiveGame";
import { LIVE_SIDES } from "./liveGameState";

const STATUS_LABEL: Record<string, string> = { invited: "Invite open", active: "In progress", final: "Final" };

function TeamLine({ name, color, note }: { name: string; color?: string | null; note?: string }) {
    return (
        <span className="flex min-w-0 items-center gap-1.5">
            <span className="h-3 w-1.5 shrink-0 rounded-full" style={{ backgroundColor: color ?? "var(--divider)" }} />
            <span className="truncate text-[13px] text-(--text-primary)">{name}</span>
            {note && <span className="shrink-0 text-[11px] text-(--text-tertiary)">{note}</span>}
        </span>
    );
}

export function LiveGamesShelf({ token, onOpenGame }: { token: string; onOpenGame: (liveGameId: string) => void }) {
    const [games, setGames] = useState<LiveGameListItem[]>([]);

    useEffect(() => {
        let stale = false;
        fetchMyLiveGames(token)
            .then((data) => { if (!stale) setGames([...data].sort((a, b) => Number(b.is_my_turn) - Number(a.is_my_turn))); })
            .catch(() => { if (!stale) setGames([]); });
        return () => { stale = true; };
    }, [token]);

    const showDevShortcut = import.meta.env.DEV;
    if (games.length === 0 && !showDevShortcut) return null;

    return (
        <div className="flex flex-col gap-2">
            <Heading level="panel">Live Games</Heading>
            {showDevShortcut && <DevQuickLiveGame token={token} onOpenGame={onOpenGame} />}
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
                {games.map((game) => (
                    <button
                        key={game.live_game_id}
                        type="button"
                        onClick={() => onOpenGame(game.live_game_id)}
                        className="flex w-full cursor-pointer items-center gap-3 rounded-control bg-(--background-tertiary) px-3 py-2 text-left transition-colors hover:bg-(--divider)"
                    >
                        <span className="min-w-0 flex-1 space-y-0.5">
                            {LIVE_SIDES.map((side) => (
                                <TeamLine
                                    key={side}
                                    name={game.identities[side]?.name ?? "Waiting for an opponent"}
                                    color={game.identities[side]?.primary_color}
                                    note={game.controllers[side] === "sim" ? "Sim" : undefined}
                                />
                            ))}
                        </span>
                        <span className="flex shrink-0 flex-col items-end gap-1">
                            {game.is_my_turn
                                ? <Plate variant="ink" size="sm">Your turn</Plate>
                                : <span className="text-[11px] font-semibold text-(--text-secondary)">{STATUS_LABEL[game.status] ?? game.status}</span>}
                            {game.last_action_at && <span className="text-[11px] text-(--text-tertiary)">{relativeTime(game.last_action_at)}</span>}
                        </span>
                    </button>
                ))}
            </div>
        </div>
    );
}
