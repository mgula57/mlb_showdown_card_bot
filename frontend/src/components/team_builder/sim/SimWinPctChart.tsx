import { useMemo } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine, Tooltip, type DotItemDotProps } from 'recharts';
/** Only the running record is read here, so both a live (streamed) `SimProgressGameLine` and a
 *  finished `SimGameLine` satisfy it. */
type GameRecord = { date: string; is_win: boolean; wins: number; losses: number };

type Point = { game: number; winPct: number; date: string; isWin: boolean; wins: number; losses: number };

function CustomTooltip({ active, payload }: { active?: boolean; payload?: { payload: Point }[] }) {
    if (!active || !payload?.length) return null;
    const point = payload[0].payload;
    return (
        <div className="bg-(--background-secondary) border border-(--divider) rounded-lg px-2.5 py-1.5 text-[11px] shadow-lg">
            <p className="font-bold text-primary">Game {point.game} · {point.date}</p>
            <p className="text-tertiary">
                {point.wins}–{point.losses} ({point.winPct.toFixed(3).replace(/^0\./, '.')})
                <span className={`ml-1.5 font-bold ${point.isWin ? 'text-(--showdown-blue)' : 'text-tertiary'}`}>{point.isWin ? 'W' : 'L'}</span>
            </p>
        </div>
    );
}

type Props = {
    games: GameRecord[];
    /** Win% of the lowest-seeded playoff team that season — the cutoff a team needed to clear to
     * make it in. Omitted when nobody in the league has a playoff seeding (e.g. no postseason). */
    playoffCutlinePct?: number | null;
    /** Fixes the x-axis to the full season length. Pass while streaming a partial season so the
     * axis holds still and the line just extends into it; omit for a finished season (the axis
     * then ends at the last game played). */
    totalGames?: number | null;
};

/** Cumulative win% across the season — a single series, so no legend box (the section title
 * above it already names it). Games already carry a running record, so no server work needed.
 *
 * Colors reference `--divider`/`--tertiary`/`--showdown-blue` directly rather than the
 * `text-(--text-tertiary)`-style Tailwind classes used elsewhere in the app: those alias custom
 * properties (`--text-primary`, `--text-tertiary`, …) that are never actually defined anywhere,
 * so they silently resolve via CSS inheritance for ordinary DOM text — a fallback that doesn't
 * reach into an SVG chart's own stroke/fill attributes, which just stayed static across themes. */
export function SimWinPctChart({ games, playoffCutlinePct, totalGames }: Props) {
    const data: Point[] = useMemo(() => games.map((g, i) => ({
        game: i + 1,
        winPct: g.wins / (g.wins + g.losses),
        date: g.date,
        isWin: g.is_win,
        wins: g.wins,
        losses: g.losses,
    })), [games]);

    // Streaming (`totalGames` set): pin the axis to the full season so the frame is visible (and
    // stays put) from the very first poll, before any games have actually streamed in.
    const streaming = totalGames != null;

    if (data.length === 0 && !streaming) {
        return <p className="text-[13px] text-tertiary py-6 text-center">No games played.</p>;
    }
    const hasGames = data.length > 0;
    const xMax = Math.max(totalGames ?? 0, data.length);

    // Before the first game lands, there's nothing to draw a line between - just a single point
    // pinned to the standard .500 start so the axes aren't empty while waiting.
    const chartData: Point[] = hasGames ? data : [{ game: 1, winPct: 0.5, date: '', isWin: false, wins: 0, losses: 0 }];

    // Pulses the .500 starting dot while waiting for the first game - a "live, standing by" cue.
    // Stops once real games exist: the line itself never animates (each poll would otherwise
    // redraw/animate the whole path, since recharts re-interpolates from a shorter previous
    // array), and a pulsing tip on every poll reads as more distracting than informative there.
    const renderStartDot = ({ key, cx, cy }: DotItemDotProps) => (
        <g key={key}>
            <circle cx={cx} cy={cy} r={6} fill="var(--showdown-blue)" opacity={0.5} className="animate-ping" />
            <circle cx={cx} cy={cy} r={3} fill="var(--showdown-blue)" />
        </g>
    );

    return (
        // Fixed height floor so ResponsiveContainer has a concrete pixel height to resolve
        // against when this card isn't grid-stretched to match Standings (i.e. below `md`,
        // where the two SectionCards stack in a single column instead of sharing a grid row).
        // flex-1/min-h-0 let it grow to fill the stretched row height once `md:grid-cols-2` applies.
        <div className="h-64 min-h-0 flex-1">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--divider)" vertical={false} />
                    <XAxis
                        dataKey="game" type="number" allowDecimals={false}
                        domain={streaming ? [1, xMax] : ['dataMin', 'dataMax']}
                        allowDataOverflow tickLine={false} axisLine={{ stroke: 'var(--divider)' }}
                        tick={{ fill: 'var(--tertiary)', fontSize: 10 }} tickMargin={6}
                    />
                    <YAxis
                        domain={[0, 1]} tickFormatter={(v: number) => v.toFixed(2).replace(/^0\./, '.')}
                        tickLine={false} axisLine={false} tick={{ fill: 'var(--tertiary)', fontSize: 10 }} width={42}
                    />
                    <ReferenceLine y={0.5} stroke="var(--tertiary)" strokeDasharray="4 4" />
                    {playoffCutlinePct != null && (
                        <ReferenceLine
                            y={playoffCutlinePct} stroke="var(--warning)" strokeDasharray="2 3" strokeWidth={1.5}
                            label={{ value: 'Playoff cutoff', position: 'insideBottomLeft', fill: 'var(--warning)', fontSize: 9 }}
                        />
                    )}
                    {hasGames && <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--divider)' }} />}
                    <Line
                        type="monotone" dataKey="winPct" stroke="var(--showdown-blue)" strokeWidth={2}
                        dot={hasGames ? false : renderStartDot} activeDot={hasGames ? { r: 4, fill: 'var(--showdown-blue)' } : false}
                        isAnimationActive={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
