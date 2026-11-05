/**
 * @fileoverview Inning-by-inning line score with R/H/E totals. Extracted from GameDetail and
 * converted to domain types so a sim game's line score renders through the same component.
 */
import type { GameView } from "../../domain/game";
import { getReadableTextColor, NEUTRAL_TEAM_COLOR } from '../../functions/colors';
import { Plate } from "../shared/Plate";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";

type GameLinescoreProps = {
    game: GameView;
    className?: string;
};

export default function GameLinescore({ game, className = "" }: GameLinescoreProps) {
    const linescore = game.linescore;
    if (!linescore) return null;

    // Pad out to the scheduled length so an early game still shows a full nine columns. Keyed off
    // the highest inning number actually present, not the array's length - a takeover's line
    // score can start mid-array (e.g. only innings 6-9 populated so far), and padding by index
    // there would relabel and duplicate columns instead of extending past the last real one.
    const innings = [...linescore.innings].sort((a, b) => a.num - b.num);
    const highestInning = innings.length > 0 ? innings[innings.length - 1].num : 0;
    for (let num = highestInning + 1; num <= linescore.scheduledInnings; num++) {
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

    const headerClass = `py-2 ${CAPS_LABEL_CLASS}`;
    const totalClass = "px-2 py-2 font-semibold text-(--text-primary)";

    return (
        <div className={`rounded-card border border-(--divider) bg-(--background-secondary) overflow-x-auto scrollbar-hide ${className}`}>
            <table className="w-full text-[13px] text-center tabular-nums">
                <thead>
                    <tr className="border-b border-(--divider) text-(--text-tertiary)">
                        <th className="pl-3 pr-2 py-2 text-left w-16" />
                        {innings.map((inning) => (
                            <th
                                key={inning.num}
                                className={`px-1.5 min-w-7 ${headerClass} ${isCurrent(inning.num) ? "text-(--text-primary)" : ""}`}
                            >
                                {inning.num}
                            </th>
                        ))}
                        <th className={`px-2 ${headerClass} text-(--text-primary) border-l border-(--divider)`}>R</th>
                        <th className={`px-2 ${headerClass} text-(--text-primary)`}>H</th>
                        <th className={`px-2 ${headerClass} text-(--text-primary)`}>E</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map(({ side, totals, runsFor }, rowIndex) => {
                        const badgeBg = side.team.primaryColor ?? NEUTRAL_TEAM_COLOR;
                        return (
                            <tr key={side.team.key} className={rowIndex < rows.length - 1 ? "border-b border-(--divider)" : ""}>
                                <td className="pl-3 pr-2 py-2 text-left">
                                    <Plate variant="custom" size="sm" style={{ backgroundColor: badgeBg, color: getReadableTextColor(badgeBg, "#ffffff") }}>
                                        {side.team.abbreviation}
                                    </Plate>
                                </td>
                                {innings.map((inning) => (
                                    <td
                                        key={inning.num}
                                        className={`px-1.5 py-2 ${
                                            isCurrent(inning.num) ? "bg-(--background-tertiary) font-semibold text-(--text-primary)"
                                            : isFuture(inning.num) ? "text-(--text-tertiary) opacity-30"
                                            : "text-(--text-secondary)"
                                        }`}
                                    >
                                        {isFuture(inning.num) ? "" : (runsFor(inning) ?? "-")}
                                    </td>
                                ))}
                                <td className={`${totalClass} border-l border-(--divider)`}>{totals.runs}</td>
                                <td className={totalClass}>{totals.hits}</td>
                                <td className={totalClass}>{totals.errors}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
