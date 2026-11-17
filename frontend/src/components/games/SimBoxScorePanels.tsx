/**
 * @fileoverview The box score rail tab for a sim (a Faceoff, a live game, or a sim of a real game):
 * one tab per side, each that side's box score as of the playback frame.
 *
 * A sim's box score renders in the same batting and pitching tables as a real MLB game's (card PTS,
 * defense totals, card identity cells), so its canonical `TeamBoxscore` is reshaped into the MLB
 * feed's shape here (`BoxscoreTableTeam`). Where an MLB game shows season AVG / OPS / ERA, a sim shows the
 * real stats on each player's card; a sim throws no pitches, so it has no P-S column.
 */
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import type { GameView, TeamBoxscore } from "../../domain/game";
import { resolveCardKey } from "../../domain/players";
import GameBoxScoreTabs from "./GameBoxScoreTabs";
import BattingTable from "./detail/BattingTable";
import PitchingTable from "./detail/PitchingTable";
import type { BoxscoreTableTeam } from "./detail/boxscoreTableTypes";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

type SimBoxScoreProps = {
    cardMap: CardMap;
    onCardSelect: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
    /** Whether a card's detail is open, which keeps the tables' hover previews shut. */
    isShowingModal?: boolean;
};

/** A rate stat off a card's real stats, in the MLB feed's format (".285", "3.41"); "-" when the
 *  card doesn't carry it. */
function formatRate(value: unknown, digits: number, dropLeadingZero = false): string {
    const number = typeof value === "number" ? value : typeof value === "string" && value !== "" ? Number(value) : NaN;
    if (!Number.isFinite(number)) return "-";
    const text = number.toFixed(digits);
    return dropLeadingZero ? text.replace(/^0(?=\.)/, "") : text;
}

const outsOf = (inningsPitched: string) => {
    const [whole, partial] = inningsPitched.split(".");
    return Number(whole || 0) * 3 + Number(partial || 0);
};

const sumOf = <T,>(rows: T[], pick: (row: T) => number) => rows.reduce((total, row) => total + pick(row), 0);

/** A sim's side in the MLB feed's shape, so the real-game tables can draw it. */
function toBoxscoreTeamData(box: TeamBoxscore, cardMap: CardMap): BoxscoreTableTeam {
    const cardStats = (id: number | string, role: "H" | "P") => cardMap[resolveCardKey(id, role) ?? ""]?.card?.stats ?? {};
    const outs = sumOf(box.pitching, (p) => outsOf(p.inningsPitched));
    return {
        team: {
            id: typeof box.team.id === "number" ? box.team.id : 0,
            name: box.team.name,
            abbreviation: box.team.abbreviation,
            primary_color: box.team.primaryColor,
            secondary_color: box.team.secondaryColor,
        },
        batting: box.batting.map((batter) => {
            const stats = cardStats(batter.id, "H");
            return {
                id: batter.id,
                name: batter.name,
                jersey_number: "",
                position: batter.position,
                batting_order: String(batter.battingOrder),
                is_substitute: batter.isSubstitute,
                is_in_lineup: batter.isInLineup,
                stats: {
                    at_bats: batter.atBats,
                    runs: batter.runs,
                    hits: batter.hits,
                    doubles: batter.doubles,
                    triples: batter.triples,
                    rbi: batter.rbi,
                    base_on_balls: batter.baseOnBalls,
                    strike_outs: batter.strikeOuts,
                    home_runs: batter.homeRuns,
                    stolen_bases: batter.stolenBases,
                    left_on_base: 0,
                },
                season_stats: {
                    avg: formatRate(stats.batting_avg, 3, true),
                    obp: formatRate(stats.onbase_perc, 3, true),
                    ops: formatRate(stats.onbase_plus_slugging, 3, true),
                },
            };
        }),
        pitching: box.pitching.map((pitcher) => ({
            id: pitcher.id,
            name: pitcher.name,
            jersey_number: "",
            stats: {
                note: pitcher.note,
                innings_pitched: pitcher.inningsPitched,
                hits: pitcher.hits,
                runs: pitcher.runs,
                earned_runs: pitcher.earnedRuns,
                base_on_balls: pitcher.baseOnBalls,
                strike_outs: pitcher.strikeOuts,
                home_runs: pitcher.homeRuns,
                pitches_thrown: 0,
                strikes: 0,
                batters_faced: pitcher.battersFaced ?? 0,
            },
            season_stats: { era: formatRate(cardStats(pitcher.id, "P").earned_run_avg, 2), wins: 0, losses: 0 },
        })),
        batting_totals: {
            at_bats: sumOf(box.batting, (b) => b.atBats),
            runs: sumOf(box.batting, (b) => b.runs),
            hits: sumOf(box.batting, (b) => b.hits),
            rbi: sumOf(box.batting, (b) => b.rbi),
            base_on_balls: sumOf(box.batting, (b) => b.baseOnBalls),
            strike_outs: sumOf(box.batting, (b) => b.strikeOuts),
            home_runs: sumOf(box.batting, (b) => b.homeRuns),
            stolen_bases: sumOf(box.batting, (b) => b.stolenBases),
            left_on_base: 0,
            avg: "",
            ops: "",
        },
        pitching_totals: {
            innings_pitched: `${Math.floor(outs / 3)}.${outs % 3}`,
            hits: sumOf(box.pitching, (p) => p.hits),
            runs: sumOf(box.pitching, (p) => p.runs),
            earned_runs: sumOf(box.pitching, (p) => p.earnedRuns),
            base_on_balls: sumOf(box.pitching, (p) => p.baseOnBalls),
            strike_outs: sumOf(box.pitching, (p) => p.strikeOuts),
            home_runs: sumOf(box.pitching, (p) => p.homeRuns),
            pitches_thrown: 0,
            strikes: 0,
            era: "",
        },
        info: [],
        note: "",
    };
}

/** One side of a sim's box score: its batting and pitching tables. */
export function SimBoxScoreSide({ boxscore, cardMap, onCardSelect, isLoadingCards, isShowingModal }: SimBoxScoreProps & { boxscore: TeamBoxscore }) {
    const team = toBoxscoreTeamData(boxscore, cardMap);
    const tableProps = { team, cardMap, onCardSelect, isLoadingCards, isShowingModal, hasGameStarted: true };
    return (
        <>
            <BattingTable {...tableProps} />
            <PitchingTable {...tableProps} hasPitchCounts={false} />
        </>
    );
}

export default function SimBoxScorePanels({ game, ...props }: SimBoxScoreProps & { game: GameView }) {
    return (
        <div className="@container">
            <GameBoxScoreTabs
                awayLabel={game.away.team.abbreviation}
                homeLabel={game.home.team.abbreviation}
                renderSide={(side) => {
                    const boxscore = game[side].boxscore;
                    return boxscore ? <SimBoxScoreSide boxscore={boxscore} {...props} /> : null;
                }}
            />
        </div>
    );
}
