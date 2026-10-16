/**
 * @fileoverview `userTeams.Team` is already the canonical roster on both sides of this app —
 * `fetchShowdownTeam` returns it for a real MLB/WBC roster, persisted user teams round-trip it,
 * and the sim's `SimTeam.from_builder_team` consumes the same shape for tournament mode. This
 * file does not invent a new roster type; it just gives that type a domain-facing name and a
 * `TeamIdentity` projection so a roster and an MLB team can render through the same `TeamChip`.
 */
import type { Team } from "../api/userTeams";
import { ROTATION_ROLES, MAX_STARTERS } from "../api/userTeams";
import type { CardDatabaseRecord } from "../api/card_db/cardDatabase";
import type { TeamIdentity } from "./team";

export type RosterView = Team;

export const toTeamIdentity = (team: RosterView): TeamIdentity => ({
    key: team.team_id,
    id: team.team_id,
    abbreviation: team.abbreviation,
    name: team.name,
    primaryColor: team.primary_color,
    secondaryColor: team.secondary_color,
});

const LINEUP_SLOTS = 9;

/**
 * roster_size may exceed the fixed minimums (9 lineup + num_starters + min_bench +
 * min_bullpen); autofill fills that slack as extra bench/bullpen spots, split in the same
 * ratio as their configured minimums. Mirrors `_split_extra_roster_slots` in
 * mlb_showdown_bot/core/card/team_builder/autofill.py — keep the two in sync.
 */
export function effectiveBenchBullpenMinimums(team: {
    roster_size: number;
    num_starters: number;
    min_bench: number;
    min_bullpen: number;
}): { bench: number; bullpen: number } {
    const baseMin = LINEUP_SLOTS + team.num_starters + team.min_bench + team.min_bullpen;
    const extra = Math.max(0, team.roster_size - baseMin);
    if (extra === 0) return { bench: team.min_bench, bullpen: team.min_bullpen };

    const total = team.min_bench + team.min_bullpen;
    const bullpenExtra = total > 0
        ? Math.min(extra, Math.round((extra * team.min_bullpen) / total))
        : Math.floor(extra / 2);
    const benchExtra = extra - bullpenExtra;

    return { bench: team.min_bench + benchExtra, bullpen: team.min_bullpen + bullpenExtra };
}

type BucketFill = { filled: number; target: number };

/**
 * How many bench / bullpen rows the draft UI should render (filled cards + trailing empty
 * "add" placeholders). Placeholders are shown up to each bucket's displayed target; once
 * every displayed slot is filled, one extra "add another" row appears — but only while the
 * roster still has room for it after reserving every other bucket's unmet need.
 *
 * "Need" for lineup/rotation is the full target (`lineup` = 9, `rotation` = `num_starters`).
 * For the sibling free-form bucket it's only the *hard* configured minimum (`benchMin` /
 * `bullpenMin`), not its `effectiveBenchBullpenMinimums` target — so roster slack beyond the
 * hard minimums is offered to bench AND bullpen, and the drafter decides where the last man
 * goes. Once one bucket claims that slot the other's "add" row retracts.
 */
export function benchBullpenSlotCounts(args: {
    rosterSize: number;
    /** Total roster.length (every drafted slot, all buckets). */
    rosterCount: number;
    lineup: BucketFill;
    rotation: BucketFill;
    /** `target` is the displayed (effective) minimum from `effectiveBenchBullpenMinimums`. */
    bench: BucketFill;
    bullpen: BucketFill;
    /** Hard configured `min_bench` / `min_bullpen` — what the sibling bucket must reserve. */
    benchMin: number;
    bullpenMin: number;
}): { bench: number; bullpen: number } {
    const deficit = (target: number, filled: number) => Math.max(0, target - filled);
    const fixedDeficit =
        deficit(args.lineup.target, args.lineup.filled) +
        deficit(args.rotation.target, args.rotation.filled);

    const rowsFor = (self: BucketFill, selfMin: number, otherReserved: number): number => {
        const floor = Math.max(selfMin, self.filled);
        const free = args.rosterSize - args.rosterCount - otherReserved;
        if (free <= 0) return floor;
        const target = Math.max(self.target, floor);
        const withAdd = self.filled >= self.target ? target + 1 : target;
        return Math.min(withAdd, floor + free);
    };

    return {
        bench: rowsFor(args.bench, args.benchMin,
            fixedDeficit + deficit(args.bullpenMin, args.bullpen.filled)),
        bullpen: rowsFor(args.bullpen, args.bullpenMin,
            fixedDeficit + deficit(args.benchMin, args.bench.filled)),
    };
}

/**
 * Every roster position `card` could be drafted into, in roster-slot notation (C, not CA):
 * the field spots its positions cover plus DH and bench for hitters; the rotation roles for a
 * starter; the generic 'RP' for any other pitcher.
 */
export function getEligiblePositions(card: CardDatabaseRecord, numStarters: number): string[] {
    if (card.is_pitcher) {
        if ('STARTER' in card.positions_and_defense) return ROTATION_ROLES.slice(0, Math.min(numStarters, MAX_STARTERS));
        // The bullpen is free-form — every reliever is a generic 'RP', no closer slot.
        return ['RP'];
    }
    const positions = Object.keys(card.positions_and_defense);
    const expanded = positions.flatMap(pos => {
        if (pos === 'CA') return ['C'];  // showdown notation → roster/lineup slot key
        if (pos === 'LF/RF') return ['LF', 'RF'];
        if (pos === 'IF') return ['1B', '2B', '3B', 'SS'];
        if (pos === 'OF') return ['LF', 'CF', 'RF'];
        return [pos];
    });
    return [...new Set([...expanded, 'DH', 'BE'])];
}
