/**
 * @fileoverview Display helpers for offseason moves, shared by `TransactionMoveItem`, the
 * Transactions tab and Home's Hot Stove band.
 */
import type { TransactionFeedTeam, TransactionMove, TransactionMoveKind } from "../../api/mlbAPI";
import type { TeamIdentity } from "../../domain/team";
import type { PlateVariant } from "../shared/Plate";

const KIND_LABELS: Record<TransactionMoveKind, string> = {
    trade: "Trade",
    signing: "Signing",
    free_agent: "Free agent",
    waiver_claim: "Waiver claim",
};

export const KIND_PLATES: Record<TransactionMoveKind, PlateVariant> = {
    trade: "navy",
    signing: "ink",
    free_agent: "outline",
    waiver_claim: "outline",
};

export const moveKindLabel = (move: TransactionMove): string => (move.is_re_signing ? "Re-signed" : KIND_LABELS[move.kind]);

/** A feed team as a `TeamChip` identity. */
export const feedTeamIdentity = (team: TransactionFeedTeam): TeamIdentity => ({
    key: String(team.id),
    id: team.id,
    abbreviation: team.abbreviation || team.name || String(team.id),
    name: team.name || team.abbreviation || String(team.id),
    primaryColor: team.primary_color ?? undefined,
    secondaryColor: team.secondary_color ?? undefined,
});

export const formatMoveDate = (date?: string | null): string => {
    if (!date) return "";
    const parsed = new Date(`${date}T00:00:00`);
    return Number.isNaN(parsed.getTime()) ? date : new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(parsed);
};

/** A day heading for a feed of moves: "Today", "Yesterday", or "Mon, Nov 17". */
export const formatMoveDay = (date?: string | null): string => {
    if (!date) return "";
    const parsed = new Date(`${date}T00:00:00`);
    if (Number.isNaN(parsed.getTime())) return date;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const daysAgo = Math.round((today.getTime() - parsed.getTime()) / 86_400_000);
    if (daysAgo === 0) return "Today";
    if (daysAgo === 1) return "Yesterday";
    return new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric" }).format(parsed);
};

/** Consecutive moves on the same date, in feed order (newest first). */
export const groupByDay = (moves: TransactionMove[]): { date: string; moves: TransactionMove[] }[] => {
    const days: { date: string; moves: TransactionMove[] }[] = [];
    for (const move of moves) {
        const date = move.date ?? "";
        const last = days[days.length - 1];
        if (last && last.date === date) last.moves.push(move);
        else days.push({ date, moves: [move] });
    }
    return days;
};
