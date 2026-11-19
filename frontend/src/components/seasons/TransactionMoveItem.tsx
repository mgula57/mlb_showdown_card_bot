/**
 * @fileoverview One offseason move (a trade, a signing, a player electing free agency, a waiver
 * claim): its players' cards grouped by where they went, with team chips for each direction.
 * Shared by the Seasons page's Transactions tab and Home's Hot Stove band.
 */
import { FaArrowRight, FaFileSignature, FaHandHolding, FaPersonWalkingArrowRight, FaRightLeft, FaRotate } from "react-icons/fa6";

import type { ShowdownBotCard } from "../../api/showdownBotCard";
import type { TransactionFeedTeam, TransactionMove, TransactionMoveKind, TransactionPlayer } from "../../api/mlbAPI";
import { CardItemCompactFromCard, CardItemCompactSkeleton } from "../cards/CardItemCompact";
import { Plate } from "../shared/Plate";
import { TeamChip } from "../shared/TeamChip";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { KIND_PLATES, feedTeamIdentity, formatMoveDate, moveKindLabel } from "./transactionMoves";

/** The icon for a kind of move, on its badge and on the Transactions tab's filter chips. */
export function MoveKindIcon({ kind, reSigned = false, className = "" }: { kind: TransactionMoveKind; reSigned?: boolean; className?: string }) {
    if (reSigned) return <FaRotate className={className} aria-hidden />;
    switch (kind) {
        case "trade": return <FaRightLeft className={className} aria-hidden />;
        case "signing": return <FaFileSignature className={className} aria-hidden />;
        case "free_agent": return <FaPersonWalkingArrowRight className={className} aria-hidden />;
        case "waiver_claim": return <FaHandHolding className={className} aria-hidden />;
    }
}

type MoveGroup = { key: string; fromTeamId: number | null; toTeamId: number | null; players: TransactionPlayer[] };

/** Players grouped by direction, so a trade reads as "SEA → KC" and "KC → SEA". */
const groupPlayers = (players: TransactionPlayer[]): MoveGroup[] => {
    const groups = new Map<string, MoveGroup>();
    for (const player of players) {
        const fromTeamId = player.from_team_id ?? null;
        const toTeamId = player.to_team_id ?? null;
        const key = `${fromTeamId}-${toTeamId}`;
        const group = groups.get(key) ?? { key, fromTeamId, toTeamId, players: [] };
        group.players.push(player);
        groups.set(key, group);
    }
    return [...groups.values()].map((group) => ({ ...group, players: biggestFirst(group.players) }));
};

/** Big-league cards first by points, then minor-league cards, then players with no card. */
const biggestFirst = (players: TransactionPlayer[]): TransactionPlayer[] => {
    const rank = (player: TransactionPlayer) => (player.points ?? (player.card ? -1 : -2));
    return [...players].sort((a, b) => rank(b) - rank(a));
};

type TeamLookup = { [teamId: string]: TransactionFeedTeam };

/** A club's chip, or a "Free agent" plate when the player came from (or went to) no club. */
function MoveTeamChip({ teamId, teams }: { teamId: number | null; teams: TeamLookup }) {
    const team = teamId !== null ? teams[String(teamId)] : undefined;
    return team
        ? <TeamChip team={feedTeamIdentity(team)} size="sm" />
        : <Plate size="sm" variant="outline">Free agent</Plate>;
}

/** One player in a move: his card (with a MiLB plate for a minor-league card), or a "no card" row. */
function MovePlayer({ player, cardYear, onCardSelect, fromNote }: {
    player: TransactionPlayer;
    cardYear: number;
    onCardSelect?: (card: ShowdownBotCard) => void;
    /** Shown under the player, e.g. "From SEA" in a trade with three or more clubs. */
    fromNote?: string;
}) {
    return (
        <div className="space-y-1">
            {player.card ? (
                <div className="relative">
                    <CardItemCompactFromCard
                        card={player.card}
                        className="w-full"
                        onClick={onCardSelect ? () => onCardSelect(player.card!) : undefined}
                    />
                    {/* A prospect's card is built from his minor-league season */}
                    {player.is_minor_league && (
                        <Plate size="xs" variant="red" className="absolute z-10 -top-1 -right-1" title="Built from minor-league stats">
                            MiLB
                        </Plate>
                    )}
                </div>
            ) : (
                // Wraps rather than truncating: in a narrow trade column the label drops under the name
                <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-0.5 rounded-card bg-(--background-tertiary) px-2.5 py-2">
                    <span className="text-xs font-semibold text-(--text-primary)">{player.name}</span>
                    {/* Short so the name fits a narrow trade column; the year is in the tooltip */}
                    <span className={`${CAPS_LABEL_CLASS} shrink-0 text-(--text-tertiary)`} title={`No ${cardYear} card`}>No card</span>
                </div>
            )}
            {fromNote && <span className={`${CAPS_LABEL_CLASS} block text-(--text-tertiary)`}>{fromNote}</span>}
        </div>
    );
}

/**
 * A trade laid out the way trade trackers do: one column per club, headed "{club} receives" with
 * the big-league card points it took in, listing what it got. Two clubs sit side by side; a narrow
 * tile, a phone, or a trade with three or more clubs stacks the columns instead.
 */
function TradeSides({ move, teams, cardYear, onCardSelect, compact }: {
    move: TransactionMove;
    teams: TeamLookup;
    cardYear: number;
    onCardSelect?: (card: ShowdownBotCard) => void;
    compact: boolean;
}) {
    const sides = move.team_ids.map((teamId) => {
        const players = biggestFirst(move.players.filter((player) => player.to_team_id === teamId));
        return { teamId, players, points: players.reduce((sum, player) => sum + (player.points ?? 0), 0) };
    });
    const isMultiClub = sides.length > 2;
    const sideBySide = !compact && !isMultiClub;
    const abbreviation = (teamId?: number | null) => {
        const team = teamId != null ? teams[String(teamId)] : undefined;
        return team?.abbreviation || team?.name || "";
    };

    return (
        <div className={`grid ${sideBySide
            ? "grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-(--divider)"
            : "grid-cols-1 divide-y divide-(--divider)"}`}
        >
            {sides.map((side, index) => (
                <section
                    key={side.teamId}
                    className={`space-y-2 ${index === 0 ? "pb-3" : "pt-3 pb-3 last:pb-0"} ${sideBySide ? (index === 0 ? "sm:pb-0 sm:pr-3" : "sm:pt-0 sm:pl-3") : ""}`}
                >
                    <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 min-w-0">
                            <MoveTeamChip teamId={side.teamId} teams={teams} />
                            <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>receives</span>
                        </div>
                        {side.points > 0 && <Plate size="xs">{side.points} PT.</Plate>}
                    </div>
                    {side.players.length > 0 ? (
                        <div className="flex flex-col gap-2">
                            {side.players.map((player) => (
                                <MovePlayer
                                    key={player.mlb_id}
                                    player={player}
                                    cardYear={cardYear}
                                    onCardSelect={onCardSelect}
                                    fromNote={isMultiClub && player.from_team_id ? `From ${abbreviation(player.from_team_id)}` : undefined}
                                />
                            ))}
                        </div>
                    ) : (
                        <p className="text-xs text-(--text-tertiary)">Cash or a player to be named later</p>
                    )}
                </section>
            ))}
        </div>
    );
}

type TransactionMoveItemProps = {
    move: TransactionMove;
    teams: { [teamId: string]: TransactionFeedTeam };
    /** The year the players' cards come from, for the "no card" note. */
    cardYear: number;
    onCardSelect?: (card: ShowdownBotCard) => void;
    /** One card per row and a trade's clubs stacked, for a narrow tile. */
    compact?: boolean;
    /** Leaves off MLB's one-line description of the move (Home's tiles). */
    hideDescription?: boolean;
    /** Leaves off the date, for a move shown under its day's heading. */
    hideDate?: boolean;
    className?: string;
};

export function TransactionMoveItem({ move, teams, cardYear, onCardSelect, compact = false, hideDescription = false, hideDate = false, className = "" }: TransactionMoveItemProps) {
    return (
        <article className={`rounded-card border border-(--divider) bg-(--background-secondary) p-3 flex flex-col gap-3 ${className}`}>
            <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                    <Plate size="sm" variant={KIND_PLATES[move.kind]}>
                        <MoveKindIcon kind={move.kind} reSigned={move.is_re_signing} className="h-2.5 w-2.5 shrink-0" />
                        {moveKindLabel(move)}
                    </Plate>
                    {!hideDate && <span className="text-[11px] tabular-nums text-(--text-tertiary)">{formatMoveDate(move.date)}</span>}
                </div>
                {move.total_points > 0 && <Plate size="sm">{move.total_points} PT.</Plate>}
            </div>

            {move.kind === "trade" ? (
                <TradeSides move={move} teams={teams} cardYear={cardYear} onCardSelect={onCardSelect} compact={compact} />
            ) : (
                groupPlayers(move.players).map((group) => (
                    <div key={group.key} className="space-y-1.5">
                        <div className="flex items-center gap-1.5">
                            <MoveTeamChip teamId={group.fromTeamId} teams={teams} />
                            <FaArrowRight className="h-2.5 w-2.5 shrink-0 text-(--text-tertiary)" aria-hidden />
                            <MoveTeamChip teamId={group.toTeamId} teams={teams} />
                        </div>
                        <div className={`grid gap-2 ${compact ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-2"}`}>
                            {group.players.map((player) => (
                                <MovePlayer key={player.mlb_id} player={player} cardYear={cardYear} onCardSelect={onCardSelect} />
                            ))}
                        </div>
                    </div>
                ))
            )}

            {!hideDescription && move.description && (
                <p className="text-xs leading-snug text-(--text-tertiary)">{move.description}</p>
            )}
        </article>
    );
}

/** Skeleton shaped like a move: kind plate and points plate, a chip row, two compact cards. */
export function TransactionMoveItemSkeleton({ compact = false, className = "" }: { compact?: boolean; className?: string }) {
    return (
        <div className={`rounded-card border border-(--divider) bg-(--background-secondary) p-3 flex flex-col gap-3 animate-pulse ${className}`}>
            <div className="flex items-center justify-between">
                <div className="h-4 w-24 rounded-plate bg-(--background-tertiary)" />
                <div className="h-4 w-12 rounded-plate bg-(--background-tertiary)" />
            </div>
            <div className="h-5 w-28 rounded-plate bg-(--background-tertiary)" />
            <div className={`grid gap-2 ${compact ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-2"}`}>
                <CardItemCompactSkeleton className="w-full" animated={false} />
                {!compact && <CardItemCompactSkeleton className="w-full" animated={false} />}
            </div>
        </div>
    );
}
