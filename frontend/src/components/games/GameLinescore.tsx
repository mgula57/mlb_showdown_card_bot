/**
 * @fileoverview Inning-by-inning line score with R/H/E totals. Extracted from GameDetail and
 * converted to domain types so a sim game's line score renders through the same component.
 */
import type { GameView } from "../../domain/game";
import { getReadableTextColor } from "../../functions/colors";

type GameLinescoreProps = {
    game: GameView;
    className?: string;
};

export default function GameLinescore({ game, className = "" }: GameLinescoreProps) {
    const linescore = game.linescore;
    if (!linescore) return null;

    // Pad out to the scheduled length so an early game still shows a full nine columns.
    const innings = [...linescore.innings];
    for (let num = innings.length + 1; num <= linescore.scheduledInnings; num++) {
        innings.push({ num, ordinalNum: "", awayRuns: null, homeRuns: null });
    }

    const isLive = game.state === "LIVE";
    const currentInning = game.situation?.inning;
    const isCurrent = (num: number) => isLive && currentInning != null && num === currentInning;
    const isFuture = (num: number) => isLive && currentInning != null && num > currentInning;

    const rows = ([
        { side: game.away, totals: linescore.away, runsFor: (n: (typeof innings)[number]) => n.awayRuns },
        { side: game.home, totals: linescore.home, runsFor: (n: (typeof innings)[number]) => n.homeRuns },
    ]);

    return (
        <div className={`rounded-xl border border-(--divider) bg-(--background-secondary) overflow-x-auto ${className}`}>
            <table className="w-full text-xs text-center">
                <thead>
                    <tr className="border-b border-(--divider) text-(--secondary)">
                        <th className="pl-3 pr-2 py-2 text-left w-16" />
                        {innings.map((inning) => (
                            <th
                                key={inning.num}
                                className={`px-1.5 py-2 min-w-7 text-[10px] tracking-[0.5px] font-semibold ${isCurrent(inning.num) ? "text-(--primary)" : ""}`}
                            >
                                {inning.num}
                            </th>
                        ))}
                        <th className="px-2 py-2 text-[10px] tracking-[0.5px] font-semibold text-(--primary) border-l border-(--divider)">R</th>
                        <th className="px-2 py-2 text-[10px] tracking-[0.5px] font-semibold text-(--primary)">H</th>
                        <th className="px-2 py-2 text-[10px] tracking-[0.5px] font-semibold text-(--primary)">E</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map(({ side, totals, runsFor }, rowIndex) => {
                        const badgeBg = side.team.primaryColor ?? "#374151";
                        return (
                            <tr key={side.team.key} className={rowIndex < rows.length - 1 ? "border-b border-(--divider)" : ""}>
                                <td className="pl-3 pr-2 py-2 text-left">
                                    <span
                                        className="inline-flex items-center justify-center rounded font-bold text-[10px] px-1 py-0.5 leading-none"
                                        style={{ backgroundColor: badgeBg, color: getReadableTextColor(badgeBg, "#ffffff"), minWidth: "22px" }}
                                    >
                                        {side.team.abbreviation}
                                    </span>
                                </td>
                                {innings.map((inning) => (
                                    <td
                                        key={inning.num}
                                        className={`px-1.5 py-2 text-[13px] ${
                                            isCurrent(inning.num) ? "bg-(--background-quaternary) text-(--primary)"
                                            : isFuture(inning.num) ? "text-(--secondary) opacity-30"
                                            : "text-(--secondary)"
                                        }`}
                                    >
                                        {isFuture(inning.num) ? "" : (runsFor(inning) ?? "-")}
                                    </td>
                                ))}
                                <td className="px-2 py-2 font-semibold text-(--primary) border-l border-(--divider)">{totals.runs}</td>
                                <td className="px-2 py-2 font-semibold text-(--primary)">{totals.hits}</td>
                                <td className="px-2 py-2 font-semibold text-(--primary)">{totals.errors}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
