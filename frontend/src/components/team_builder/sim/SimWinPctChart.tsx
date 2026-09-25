import { Fragment, useMemo } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine, Tooltip, type DotItemDotProps } from 'recharts';
/** Only the running record is read here, so both a live (streamed) `SimProgressGameLine` and a
 *  finished `SimGameLine` satisfy it. */
type GameRecord = { date: string; is_win: boolean; wins: number; losses: number };

type Point = { game: number; winPct: number; date: string; isWin: boolean; wins: number; losses: number; isSeed?: boolean };

// Fallback x-axis length for a genuinely empty chart with no known schedule length yet (e.g. the
// live progress chart before its job has loaded) - a standard MLB season, so the blank frame
// isn't a single degenerate tick.
const DEFAULT_SEASON_GAMES = 162;

function CustomTooltip({ active, payload }: { active?: boolean; payload?: { payload: Point }[] }) {
    if (!active || !payload?.length) return null;
    const point = payload[0].payload;
    if (point.isSeed) {
        return (
            <div className="bg-(--background-secondary) border border-(--divider) rounded-lg px-2.5 py-1.5 text-[11px] shadow-lg">
                <p className="font-bold text-primary">Real record</p>
                <p className="text-tertiary">
                    {point.wins}–{point.losses} ({point.winPct.toFixed(3).replace(/^0\./, '.')})
                    <span className="ml-1.5 font-bold text-(--showdown-gray)">resumed here</span>
                </p>
            </div>
        );
    }
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
    /** The club's real win-loss record as of the resume date, for a "resume from real standings"
     *  run - plotted as a distinct gray landmark point at game 0, ahead of the simulated (blue)
     *  games, so the real-vs-simulated split is visible on the line itself rather than just
     *  folded into the running totals. Omit (or 0-0) for a run that isn't resumed. */
    seedRecord?: { wins: number; losses: number } | null;
    /** A "resume from the real postseason" run simulates no regular-season games at all - there
     *  is nothing meaningful to plot (a lone seed point would just repeat the same real final
     *  record shown elsewhere on the page), so this renders a greyed-out placeholder frame
     *  instead of the normal chart. */
    noRegularSeasonGames?: boolean;
};

/** Cumulative win% across the season — a single series, so no legend box (the section title
 * above it already names it). Games already carry a running record, so no server work needed.
 *
 * Colors reference `--divider`/`--tertiary`/`--showdown-blue` directly rather than the
 * `text-(--text-tertiary)`-style Tailwind classes used elsewhere in the app: those alias custom
 * properties (`--text-primary`, `--text-tertiary`, …) that are never actually defined anywhere,
 * so they silently resolve via CSS inheritance for ordinary DOM text — a fallback that doesn't
 * reach into an SVG chart's own stroke/fill attributes, which just stayed static across themes. */
export function SimWinPctChart({ games, playoffCutlinePct, totalGames, seedRecord, noRegularSeasonGames }: Props) {
    const hasSeed = !!seedRecord && seedRecord.wins + seedRecord.losses > 0;
    const seedPoint: Point | null = useMemo(() => (
        hasSeed
            ? { game: 0, winPct: seedRecord!.wins / (seedRecord!.wins + seedRecord!.losses), date: '', isWin: false, wins: seedRecord!.wins, losses: seedRecord!.losses, isSeed: true }
            : null
    ), [hasSeed, seedRecord]);

    const data: Point[] = useMemo(() => games.map((g, i) => ({
        game: i + 1,
        winPct: g.wins / (g.wins + g.losses),
        date: g.date,
        isWin: g.is_win,
        wins: g.wins,
        losses: g.losses,
    })), [games]);

    // No regular-season games to plot at all (a postseason-only resume) - a flat, grayscale frame
    // with no line, same footprint as the real chart so nothing shifts around it.
    if (noRegularSeasonGames) {
        return (
            <div className="relative h-64 grayscale opacity-50">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={[{ game: 1, winPct: 0.5, date: '', isWin: false, wins: 0, losses: 0 }]} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--divider)" vertical={false} />
                        <XAxis
                            dataKey="game" type="number" domain={[1, DEFAULT_SEASON_GAMES]}
                            tickLine={false} axisLine={{ stroke: 'var(--divider)' }}
                            tick={{ fill: 'var(--tertiary)', fontSize: 10 }} tickMargin={6}
                        />
                        <YAxis
                            domain={[0, 1]} tickFormatter={(v: number) => v.toFixed(2).replace(/^0\./, '.')}
                            tickLine={false} axisLine={false} tick={{ fill: 'var(--tertiary)', fontSize: 10 }} width={42}
                        />
                        <ReferenceLine y={0.5} stroke="var(--tertiary)" strokeDasharray="4 4" />
                    </LineChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center px-4">
                    <p className="rounded-md border border-(--divider) bg-(--background-secondary)/90 px-3 py-1.5 text-center text-[12px] font-semibold text-tertiary">
                        No Regular Season Simmed Games
                    </p>
                </div>
            </div>
        );
    }

    // Streaming (`totalGames` set): pin the axis to the full season so the frame is visible (and
    // stays put) from the very first poll, before any games have actually streamed in.
    const streaming = totalGames != null;
    const hasGames = data.length > 0;
    // With games: ends at the last game played for a finished season, or the pinned schedule
    // length while streaming. With none: use the known schedule length if there is one, else
    // assume a standard season, so a blank frame still sits on a realistic full-season axis.
    const xMax = hasGames ? Math.max(totalGames ?? 0, data.length) : (totalGames ?? DEFAULT_SEASON_GAMES);
    // The seed sits at game 0, ahead of the first simulated game - only relevant on a resumed run.
    const xMin = hasSeed ? 0 : 1;

    // Before the first game lands there's nothing to draw a line between, but recharts needs at
    // least one data point to lay out the axes/gridlines at all - an empty array renders nothing,
    // not even a blank frame. A resumed run pins that single point to its real seed record instead
    // of the generic .500 start, since that's real data, not a placeholder - and it still pulses
    // while streaming, as a "live, about to simulate from here" cue. Genuinely no data (no seed,
    // no games) falls back to the plain .500 placeholder, exactly as before.
    const showStartDot = !hasGames && streaming;
    const chartData: Point[] = hasGames
        ? (seedPoint ? [seedPoint, ...data] : data)
        : [seedPoint ?? { game: 1, winPct: 0.5, date: '', isWin: false, wins: 0, losses: 0 }];
    // Tooltip/hover only make sense once there's real data to explain - not for the bare .500
    // placeholder, which represents nothing yet.
    const canInspect = hasGames || hasSeed;

    // Stops pulsing once real games exist: the line itself never animates (each poll would
    // otherwise redraw/animate the whole path, since recharts re-interpolates from a shorter
    // previous array), and a pulsing tip on every poll reads as more distracting than informative.
    const renderStartDot = ({ key, cx, cy }: DotItemDotProps) => (
        <g key={key}>
            <circle cx={cx} cy={cy} r={6} fill="var(--showdown-blue)" opacity={0.5} className="animate-ping" />
            <circle cx={cx} cy={cy} r={3} fill="var(--showdown-blue)" />
        </g>
    );

    // The seed's own marker - a static gray landmark once simulated games exist alongside it, or
    // pulsing (like `renderStartDot`) while it's still the only point on the chart.
    const renderSeedDot = ({ key, cx, cy }: DotItemDotProps) => (
        <g key={key}>
            {!hasGames && streaming && <circle cx={cx} cy={cy} r={6} fill="var(--showdown-gray)" opacity={0.5} className="animate-ping" />}
            <circle cx={cx} cy={cy} r={4} fill="var(--showdown-gray)" stroke="var(--background-secondary)" strokeWidth={1.5} />
        </g>
    );

    const renderDot = (props: DotItemDotProps & { payload?: Point }) => {
        if (props.payload?.isSeed) return renderSeedDot(props);
        if (showStartDot) return renderStartDot(props);
        return <Fragment key={props.key} />;
    };

    return (
        <div>
            {/* Fixed height rather than flex-1: this chart is used both standalone (SimProgress,
                no stretched sibling to grow against) and inside a stretched grid row
                (SimSummaryTab, next to Standings) - `flex-1`'s `flex-basis: 0%` overrides a
                `height` in the first case with nothing to grow into, collapsing it to 0. A plain
                fixed height works in both. */}
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--divider)" vertical={false} />
                        <XAxis
                            dataKey="game" type="number" allowDecimals={false}
                            domain={[xMin, xMax]}
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
                        {canInspect && <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--divider)' }} />}
                        <Line
                            type="monotone" dataKey="winPct" stroke="var(--showdown-blue)" strokeWidth={2}
                            dot={renderDot} activeDot={canInspect ? { r: 4, fill: 'var(--showdown-blue)' } : false}
                            isAnimationActive={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
            {hasSeed && (
                <p className="mt-1 flex items-center justify-end gap-3 text-[10px] text-tertiary">
                    <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-(--showdown-gray)" />Real</span>
                    <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-(--showdown-blue)" />Simulated</span>
                </p>
            )}
        </div>
    );
}
