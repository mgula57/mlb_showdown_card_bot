/**
 * @fileoverview Box score for a simulated game.
 *
 * Reads the canonical `TeamBoxscore` rather than the raw MLB shape the real-game tables use, so it
 * is the one place that renders a sim's own batting and pitching lines. Deliberately narrower than
 * `GameDetail`'s MLB tables: the sim has no fielding, no substitutions among position players, and
 * no unearned runs, so columns that would always be empty are left out.
 */
import type { TeamBoxscore } from "../../domain/game";
import { resolveCardKey } from "../../domain/players";
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

const BATTING_COLUMNS = ["AB", "R", "H", "RBI", "BB", "K"] as const;
const PITCHING_COLUMNS = ["IP", "H", "R", "ER", "BB", "K", "HR"] as const;

function NameCell({
    id, name, detail, role, cardMap, onCardSelect,
}: {
    id: number | string;
    name: string;
    detail?: string;
    role: "H" | "P";
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
}) {
    const card = cardMap[resolveCardKey(id, role) ?? ""];
    return (
        <td className="py-1.5 pr-2 text-left">
            <button
                type="button"
                disabled={!card}
                onClick={card ? () => onCardSelect?.(card) : undefined}
                className="max-w-full truncate text-left text-xs font-semibold text-(--primary) enabled:cursor-pointer enabled:hover:underline disabled:cursor-default"
            >
                {name}
                {detail && <span className="ml-1 font-normal text-(--secondary)">{detail}</span>}
            </button>
        </td>
    );
}

export default function SimBoxScoreTable({
    boxscore, cardMap, onCardSelect,
}: {
    boxscore: TeamBoxscore;
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
}) {
    const headerClass = "py-1 px-1 text-right text-[10px] font-bold uppercase tracking-wide text-(--secondary)";
    const cellClass = "py-1.5 px-1 text-right text-xs tabular-nums text-(--primary)";

    return (
        <div className="space-y-4">
            <div className="overflow-x-auto">
                <table className="w-full min-w-[20rem]">
                    <thead>
                        <tr className="border-b border-(--divider)">
                            <th className="py-1 pr-2 text-left text-[10px] font-bold uppercase tracking-wide text-(--secondary)">
                                {boxscore.team.abbreviation} Batting
                            </th>
                            {BATTING_COLUMNS.map((column) => (
                                <th key={column} className={headerClass}>{column}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {boxscore.batting.map((batter) => (
                            <tr key={batter.id} className="border-b border-(--divider)/40">
                                <NameCell
                                    id={batter.id} name={batter.name} detail={batter.position}
                                    role="H" cardMap={cardMap} onCardSelect={onCardSelect}
                                />
                                <td className={cellClass}>{batter.atBats}</td>
                                <td className={cellClass}>{batter.runs}</td>
                                <td className={cellClass}>{batter.hits}</td>
                                <td className={cellClass}>{batter.rbi}</td>
                                <td className={cellClass}>{batter.baseOnBalls}</td>
                                <td className={cellClass}>{batter.strikeOuts}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full min-w-[20rem]">
                    <thead>
                        <tr className="border-b border-(--divider)">
                            <th className="py-1 pr-2 text-left text-[10px] font-bold uppercase tracking-wide text-(--secondary)">
                                {boxscore.team.abbreviation} Pitching
                            </th>
                            {PITCHING_COLUMNS.map((column) => (
                                <th key={column} className={headerClass}>{column}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {boxscore.pitching.map((pitcher) => (
                            <tr key={pitcher.id} className="border-b border-(--divider)/40">
                                <NameCell
                                    id={pitcher.id} name={pitcher.name} detail={pitcher.position}
                                    role="P" cardMap={cardMap} onCardSelect={onCardSelect}
                                />
                                <td className={cellClass}>{pitcher.inningsPitched}</td>
                                <td className={cellClass}>{pitcher.hits}</td>
                                <td className={cellClass}>{pitcher.runs}</td>
                                <td className={cellClass}>{pitcher.earnedRuns}</td>
                                <td className={cellClass}>{pitcher.baseOnBalls}</td>
                                <td className={cellClass}>{pitcher.strikeOuts}</td>
                                <td className={cellClass}>{pitcher.homeRuns}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
