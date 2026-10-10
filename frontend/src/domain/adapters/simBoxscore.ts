/**
 * @fileoverview Rebuilds a sim's box score one plate appearance at a time, so a game that's still
 * in progress (a replay mid-way through, or eventually a game the user is playing live) can show
 * its batting/pitching lines as of "now" instead of hiding them until the final out.
 *
 * The accounting mirrors the engine exactly (`PlateAppearance.hitter_stats` / `pitcher_stats` /
 * `runner_*_stats_dict` in `core/simulation/plate_appearance.py`, merged in `Game.simulate`), so
 * folding a stored sim's full log lands on the engine's own final box line for line.
 */
import type { BoxscoreBatterLine, BoxscorePitcherLine, TeamBoxscore } from "../game";
import type { SimGameLogEntryJson } from "./fromSim";

/** Mirrors `stats.py`'s `_BUILDER_ID_PREFIX` / `real_card_id` — the log carries the engine's
 *  (possibly builder-prefixed) ids, the box score carries the bare card id. */
const BUILDER_ID_PREFIX = "builder@";
const realCardId = (simId: string): string =>
    simId.startsWith(BUILDER_ID_PREFIX) ? simId.slice(simId.lastIndexOf("@") + 1) : simId;

const HIT_RESULTS = new Set(["1b", "1b+", "2b", "3b", "hr"]);

/** Mirrors `game.py`'s `_ip_string`. */
const ipString = (outs: number): string => `${Math.floor(outs / 3)}.${outs % 3}`;
const outsFromIp = (ip: string): number => {
    const [whole, partial] = ip.split(".");
    return Number(whole || 0) * 3 + Number(partial || 0);
};

/** Mirrors `game.py`'s `_batting_summary`. */
const battingSummary = (line: BoxscoreBatterLine): string => {
    const extras: string[] = [];
    const doubles = line.doubles ?? 0;
    const triples = line.triples ?? 0;
    if (doubles) extras.push(doubles > 1 ? `${doubles} 2B` : "2B");
    if (triples) extras.push(triples > 1 ? `${triples} 3B` : "3B");
    if (line.homeRuns) extras.push(line.homeRuns > 1 ? `${line.homeRuns} HR` : "HR");
    if (line.rbi) extras.push(`${line.rbi} RBI`);
    if (line.baseOnBalls) extras.push(line.baseOnBalls > 1 ? `${line.baseOnBalls} BB` : "BB");
    return `${line.hits}-${line.atBats}${extras.length ? `, ${extras.join(", ")}` : ""}`;
};

/** The counting stats this accumulator owns — everything else on a line (name, position, order)
 *  is roster identity carried through untouched. */
const BATTER_STATS = [
    "atBats", "runs", "hits", "doubles", "triples", "homeRuns", "rbi",
    "baseOnBalls", "strikeOuts", "stolenBases", "caughtStealing", "groundIntoDoublePlay",
] as const;
const PITCHER_STATS = ["hits", "runs", "earnedRuns", "baseOnBalls", "strikeOuts", "homeRuns", "battersFaced"] as const;

type BatterCounts = Record<(typeof BATTER_STATS)[number], number>;
type PitcherCounts = Record<(typeof PITCHER_STATS)[number] | "outs", number>;

const batterCounts = (line?: BoxscoreBatterLine): BatterCounts =>
    Object.fromEntries(BATTER_STATS.map((k) => [k, line ? Number(line[k] ?? 0) : 0])) as BatterCounts;
const pitcherCounts = (line?: BoxscorePitcherLine): PitcherCounts => ({
    ...(Object.fromEntries(PITCHER_STATS.map((k) => [k, line ? Number(line[k] ?? 0) : 0])) as Omit<PitcherCounts, "outs">),
    outs: line ? outsFromIp(line.inningsPitched) : 0,
});

type Side = "away" | "home";
type Rosters = Record<Side, TeamBoxscore>;

export type SimBoxscoreStart = {
    inning: number;
    isTop: boolean;
    outs: number;
    runners: { id: string; base: number; pitcher_id: string }[];
};

type SideState = {
    roster: TeamBoxscore;
    batters: Map<string, BatterCounts>;
    pitchers: Map<string, PitcherCounts>;
    /** Pitchers in the game so far — a reliever's row appears once he enters, not before. */
    pitchersUsed: Set<string>;
};

/**
 * Folds `GameLogEntry`s into per-team box scores on top of a starting line for every player
 * (zero for a game from the first pitch). `apply()` each entry in order; `snapshot()` whenever a
 * frame needs the current lines.
 */
export class SimBoxscoreAccumulator {
    private readonly sides: Record<Side, SideState>;
    /** Runner id → the pitcher charged if they score (`Runner.pitcher_id` in the engine): whoever
     *  was pitching when they reached. Reset each half-inning. */
    private responsiblePitcher = new Map<string, string>();
    /** Base each runner occupied at the end of the previous entry — for spotting stolen bases. */
    private runnerBases = new Map<string, number>();
    private outsBefore = 0;
    private half: { inning: number; isTop: boolean } | null = null;

    /**
     * @param rosters  Every player's line as of `start` — their stats are the starting counts.
     * @param inGame   Pitcher ids already in the game at `start`, beyond each side's starter.
     * @param start    A takeover's handoff point (inning, outs, runners on with their charged pitcher).
     */
    constructor(rosters: Rosters, inGame: Iterable<string> = [], start?: SimBoxscoreStart) {
        const used = new Set(inGame);
        this.sides = {
            away: SimBoxscoreAccumulator.sideFrom(rosters.away, used),
            home: SimBoxscoreAccumulator.sideFrom(rosters.home, used),
        };
        if (start) {
            this.half = { inning: start.inning, isTop: start.isTop };
            this.outsBefore = start.outs;
            for (const runner of start.runners) {
                const id = realCardId(runner.id);
                this.runnerBases.set(id, runner.base);
                if (runner.pitcher_id) this.responsiblePitcher.set(id, realCardId(runner.pitcher_id));
            }
        }
    }

    /**
     * For a stored, finished sim: works backward from the engine's final box to each player's line
     * at the start of the log (final minus everything the log adds — all zeros for a game played
     * from the first pitch), so replaying the log forward ends exactly on the final box.
     */
    static fromFinal(final: Rosters, log: SimGameLogEntryJson[], start?: SimBoxscoreStart): SimBoxscoreAccumulator {
        const delta = new SimBoxscoreAccumulator(SimBoxscoreAccumulator.zeroed(final), [], start);
        for (const entry of log) delta.apply(entry);

        const baseline = {} as Rosters;
        const inGame: string[] = [];
        for (const side of ["away", "home"] as const) {
            const state = delta.sides[side];
            // Pitchers ahead of the first one the log shows for this side already pitched before
            // a takeover's handoff — they belong on the staff from the first frame.
            const firstLogOrder = Math.min(...final[side].pitching
                .filter((p) => state.pitchersUsed.has(String(p.id)) && (state.pitchers.get(String(p.id))?.battersFaced ?? 0) > 0)
                .map((p) => p.order ?? 0));
            baseline[side] = {
                team: final[side].team,
                batting: final[side].batting.map((b) => {
                    const added = state.batters.get(String(b.id))!;
                    return { ...b, ...Object.fromEntries(BATTER_STATS.map((k) => [k, Number(b[k] ?? 0) - added[k]])) };
                }),
                pitching: final[side].pitching.map((p) => {
                    const added = state.pitchers.get(String(p.id))!;
                    if ((p.order ?? 0) < firstLogOrder) inGame.push(String(p.id));
                    return {
                        ...p,
                        ...Object.fromEntries(PITCHER_STATS.map((k) => [k, Number(p[k] ?? 0) - added[k]])),
                        inningsPitched: ipString(outsFromIp(p.inningsPitched) - added.outs),
                    };
                }),
            };
        }
        return new SimBoxscoreAccumulator(baseline, inGame, start);
    }

    private static zeroed(rosters: Rosters): Rosters {
        const zero = (box: TeamBoxscore): TeamBoxscore => ({
            team: box.team,
            batting: box.batting.map((b) => ({ ...b, ...batterCounts() })),
            pitching: box.pitching.map((p) => ({ ...p, ...pitcherCounts(), inningsPitched: "0.0" })),
        });
        return { away: zero(rosters.away), home: zero(rosters.home) };
    }

    private static sideFrom(roster: TeamBoxscore, inGame: Set<string>): SideState {
        // The starter is in the game from the first frame even before he's thrown a pitch.
        const used = roster.pitching
            .filter((p) => (p.order ?? 0) === 0 || inGame.has(String(p.id)))
            .map((p) => String(p.id));
        return {
            roster,
            batters: new Map(roster.batting.map((b) => [String(b.id), batterCounts(b)])),
            pitchers: new Map(roster.pitching.map((p) => [String(p.id), pitcherCounts(p)])),
            pitchersUsed: new Set(used),
        };
    }

    /** Folds one plate appearance (including any pre-pitch steal and post-hit send) in. */
    apply(entry: SimGameLogEntryJson): void {
        if (!this.half || this.half.inning !== entry.inning || this.half.isTop !== entry.is_top) {
            this.half = { inning: entry.inning, isTop: entry.is_top };
            this.outsBefore = 0;
            this.responsiblePitcher = new Map();
            this.runnerBases = new Map();
        }

        const batting = this.sides[entry.is_top ? "away" : "home"];
        const pitching = this.sides[entry.is_top ? "home" : "away"];
        const hitterId = realCardId(entry.hitter_id ?? "");
        const pitcherId = realCardId(entry.pitcher_id ?? "");
        const swing = entry.swing_result.toLowerCase();
        const paOuts = Math.max(0, entry.outs - this.outsBefore);
        const runs = entry.runs_scored ?? 0;
        const isHit = HIT_RESULTS.has(swing);
        const retired = entry.retired ?? [];
        const scored = entry.scored ?? [];

        // ---- HITTER (`hitter_stats`) ----
        const batter = batting.batters.get(hitterId);
        if (batter) {
            batter.atBats += swing !== "bb" && swing !== "na" ? 1 : 0;
            batter.hits += isHit ? 1 : 0;
            if (swing === "2b") batter.doubles += 1;
            if (swing === "3b") batter.triples += 1;
            if (swing === "hr") batter.homeRuns += 1;
            if (swing === "bb") batter.baseOnBalls += 1;
            if (swing === "so") batter.strikeOuts += 1;
            // The engine credits no RBI on a play that records two or more outs (a DP).
            batter.rbi += paOuts > 1 ? 0 : runs;
            // `double_play_stats_dict`: the DP roll retires the hitter provisionally placed on
            // first — a ground ball whose swing itself produced two outs.
            const swingOuts = paOuts - retired.filter((r) => r.reason === "steal" || r.reason === "advance").length;
            if (swing === "gb" && swingOuts >= 2) batter.groundIntoDoublePlay += 1;
        }

        // ---- RUNNERS (`runner_steals_stats_dict` / `runner_advances_stats_dict`) ----
        // A steal is any runner who moved up between the previous entry and the post-steal
        // snapshot — that also catches the 1B+ automatic steal, which has no roll and so never
        // appears in `steal_rolls`.
        for (const runner of entry.bases_after_steal ?? []) {
            const id = realCardId(runner.id);
            const before = this.runnerBases.get(id);
            const line = batting.batters.get(id);
            if (line && before != null && runner.base > before) line.stolenBases += 1;
        }
        for (const runner of retired.filter((r) => r.reason === "steal")) {
            const line = batting.batters.get(realCardId(runner.id));
            if (line) line.caughtStealing += 1;
        }
        for (const runner of scored) {
            const line = batting.batters.get(realCardId(runner.id));
            if (line) line.runs += 1;
        }

        // ---- PITCHER (`pitcher_stats` + `prior_pitcher_stats_dict`) ----
        const pitcher = pitching.pitchers.get(pitcherId);
        if (pitcher) {
            pitching.pitchersUsed.add(pitcherId);
            pitcher.battersFaced += 1;
            pitcher.hits += isHit ? 1 : 0;
            if (swing === "hr") pitcher.homeRuns += 1;
            if (swing === "bb") pitcher.baseOnBalls += 1;
            if (swing === "so") pitcher.strikeOuts += 1;
            pitcher.outs += paOuts;
        }
        // Each run is charged to whoever put that runner on base — inherited runners land on the
        // reliever's predecessor. A runner with no record (the hitter scoring on his own HR, or
        // reaching and coming around on the same play) is the current pitcher's.
        for (const runner of scored) {
            const charged = pitching.pitchers.get(this.responsiblePitcher.get(realCardId(runner.id)) ?? pitcherId);
            if (charged) {
                charged.runs += 1;
                charged.earnedRuns += 1; // the sim doesn't distinguish unearned runs
            }
        }

        // ---- CARRY STATE TO THE NEXT ENTRY ----
        const onBase = entry.bases_detail ?? [];
        const nextResponsible = new Map<string, string>();
        for (const runner of onBase) {
            const id = realCardId(runner.id);
            nextResponsible.set(id, this.responsiblePitcher.get(id) ?? pitcherId);
        }
        this.responsiblePitcher = nextResponsible;
        this.runnerBases = new Map(onBase.map((r) => [realCardId(r.id), r.base]));
        this.outsBefore = entry.outs;
    }

    /** Independent point-in-time copies, safe to stash on a frame while folding continues. */
    snapshot(): Rosters {
        return { away: this.snapshotSide(this.sides.away), home: this.snapshotSide(this.sides.home) };
    }

    private snapshotSide(side: SideState): TeamBoxscore {
        return {
            team: side.roster.team,
            batting: side.roster.batting.map((b) => {
                const line: BoxscoreBatterLine = { ...b, ...side.batters.get(String(b.id))! };
                return { ...line, summary: battingSummary(line) };
            }),
            pitching: side.roster.pitching
                .filter((p) => side.pitchersUsed.has(String(p.id)))
                .map((p): BoxscorePitcherLine => {
                    const { outs, ...counts } = side.pitchers.get(String(p.id))!;
                    // `Stats.stat(IP)` rounds to one decimal before `Stats.era` divides by it.
                    const ip = Math.round((outs / 3) * 10) / 10;
                    return {
                        ...p,
                        ...counts,
                        inningsPitched: ipString(outs),
                        era: ip > 0 ? Math.round((9 * counts.earnedRuns / ip) * 100) / 100 : 0,
                        summary: `${ipString(outs)} IP, ${counts.earnedRuns} ER, ${counts.strikeOuts} K`,
                        // W / L / SV are the result — only the final box carries them.
                        note: undefined,
                    };
                }),
        };
    }
}
