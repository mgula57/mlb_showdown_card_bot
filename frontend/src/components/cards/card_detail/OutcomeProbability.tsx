import { useState, useEffect } from 'react';
import { type ShowdownBotCardChart } from '../../../api/showdownBotCard';

const OUTCOME_ORDER = ['PU', 'SO', 'GB', 'FB', 'BB', '1B', '1B+', '2B', '3B', 'HR'];
const TOTAL = 20;
const LABEL_MIN_PCT = 6;
const SEASON_PA = 600;

const PLACEHOLDER_CHART: ShowdownBotCardChart = {
    command: 8, outs: 14, outs_full: 14, is_pitcher: false, ranges: {}, set: '2005',
    values: { PU: 2, SO: 5, GB: 4, FB: 3, BB: 2, '1B': 2, '2B': 1, HR: 1 },
    opponent: { command: 5, outs: 17, outs_full: 17, is_pitcher: true, ranges: {}, values: { SO: 5, GB: 6, FB: 4, BB: 2, '1B': 2, '2B': 1 }, set: '2005' },
};

function outcomeColor(key: string, primaryColor?: string, secondaryColor?: string): string {
    const k = key.toUpperCase();
    if (['PU','SO','GB','FB'].includes(k)) return primaryColor || 'rgb(239,68,68)';
    if (k === 'HR') return secondaryColor || 'rgb(168,85,247)';
    return 'rgb(70,70,70)';
}

function calcProbabilities(
    playerChart: ShowdownBotCardChart,
    opponentCommand: number,
): { key: string; prob: number }[] {
    const isPitcher = playerChart.is_pitcher;

    const batterOB    = isPitcher ? opponentCommand     : playerChart.command;
    const pitcherCtrl = isPitcher ? playerChart.command : opponentCommand;

    const pBatterChart  = Math.max(0, Math.min(batterOB - pitcherCtrl, TOTAL)) / TOTAL;
    const pPitcherChart = 1 - pBatterChart;

    const batterValues  = isPitcher ? (playerChart.opponent?.values ?? {}) : playerChart.values;
    const pitcherValues = isPitcher ? playerChart.values : (playerChart.opponent?.values ?? {});

    const allKeys = Array.from(new Set([...Object.keys(batterValues), ...Object.keys(pitcherValues)]));

    return allKeys
        .map(key => ({
            key,
            prob: pBatterChart  * ((batterValues[key]  ?? 0) / TOTAL)
                + pPitcherChart * ((pitcherValues[key] ?? 0) / TOTAL),
        }))
        .filter(r => r.prob > 0)
        .sort((a, b) => {
            const ia = OUTCOME_ORDER.indexOf(a.key.toUpperCase());
            const ib = OUTCOME_ORDER.indexOf(b.key.toUpperCase());
            return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
        });
}

// Linear run weights (approximate, based on run expectancy tables)
const RUN_WEIGHTS: Record<string, number> = {
    BB: 0.30, '1B': 0.46, '1B+': 0.50, '2B': 0.76, '3B': 1.04, HR: 1.42,
    PU: -0.09, SO: -0.09, GB: -0.09, FB: -0.09,
};

function calcSeasonStats(results: { key: string; prob: number }[]) {
    const p = (key: string) => results.find(r => r.key === key)?.prob ?? 0;
    const pBB = p('BB');
    const p1B = p('1B') + p('1B+');
    const p2B = p('2B');
    const p3B = p('3B');
    const pHR = p('HR');
    const pH  = p1B + p2B + p3B + pHR;
    const ab  = SEASON_PA - Math.round(pBB * SEASON_PA);

    return {
        h:   Math.round(pH  * SEASON_PA),
        d:   Math.round(p2B * SEASON_PA),
        t:   Math.round(p3B * SEASON_PA),
        hr:  Math.round(pHR * SEASON_PA),
        bb:  Math.round(pBB * SEASON_PA),
        avg: ab > 0 ? pH * SEASON_PA / ab : 0,
        obp: pH + pBB,
        slg: ab > 0 ? (p1B * SEASON_PA + 2 * p2B * SEASON_PA + 3 * p3B * SEASON_PA + 4 * pHR * SEASON_PA) / ab : 0,
    };
}

function calcPitcherStats(results: { key: string; prob: number }[]) {
    const p = (key: string) => results.find(r => r.key === key)?.prob ?? 0;
    const pBB  = p('BB');
    const p1B  = p('1B') + p('1B+');
    const p2B  = p('2B');
    const p3B  = p('3B');
    const pHR  = p('HR');
    const pH   = p1B + p2B + p3B + pHR;
    const pSO  = p('SO');
    const pOut = p('PU') + p('SO') + p('GB') + p('FB');

    if (pOut <= 0) return null;

    const bfPer9 = 27 / pOut;
    const runsPerPA = results.reduce((sum, { key, prob }) => sum + prob * (RUN_WEIGHTS[key] ?? -0.09), 0);
    const ab = bfPer9 - pBB * bfPer9;

    return {
        era:  Math.max(0, runsPerPA * bfPer9),
        whip: (pH + pBB) * bfPer9 / 9,
        kPer9:  pSO  * bfPer9,
        bbPer9: pBB  * bfPer9,
        h:   Math.round(pH  * bfPer9),
        d:   Math.round(p2B * bfPer9),
        t:   Math.round(p3B * bfPer9),
        hr:  Math.round(pHR * bfPer9),
        bb:  Math.round(pBB * bfPer9),
        avg: ab > 0 ? pH * bfPer9 / ab : 0,
    };
}

function StatCell({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="flex flex-col items-center gap-0.5">
            <span className="text-sm font-black tabular-nums leading-none">{value}</span>
            <span className="text-[9px] font-semibold uppercase tracking-wide opacity-40">{label}</span>
        </div>
    );
}

type OutcomeProbabilityProps = {
    chart?: ShowdownBotCardChart;
    primaryColor?: string;
    secondaryColor?: string;
    set?: string;
};

export default function OutcomeProbability({ chart, primaryColor, secondaryColor, set }: OutcomeProbabilityProps) {
    const isEmpty = !chart;
    const data = isEmpty ? PLACEHOLDER_CHART : chart!;

    const defaultOpponentCommand = Math.round(data.opponent?.command ?? (data.is_pitcher ? 7 : 5));
    const [opponentCommand, setOpponentCommand] = useState<number>(defaultOpponentCommand);

    useEffect(() => {
        setOpponentCommand(defaultOpponentCommand);
    }, [chart, set]);

    const isExpanded = !['2000', '2001', 'CLASSIC'].includes(set ?? '2005');
    const opponentCommandMin = data.is_pitcher ? (isExpanded ? 7 : 4) : (isExpanded ? 1 : 0);
    const opponentCommandMax = data.is_pitcher ? (isExpanded ? 16 : 12) : 6;
    const opponentLabel = data.is_pitcher ? 'Opp. Onbase' : 'Opp. Control';

    const results = calcProbabilities(data, opponentCommand);
    const total = results.reduce((s, r) => s + r.prob, 0) || 1;
    const isPitcher = data.is_pitcher;
    const stats     = isPitcher ? null : calcSeasonStats(results);
    const pStats    = isPitcher ? calcPitcherStats(results) : null;

    const fmtRate = (n: number) => n.toFixed(3).replace('0.', '.');

    return (
        <div className={`space-y-3 ${isEmpty ? 'opacity-25 pointer-events-none select-none' : ''}`}>

            {/* Opponent command slider */}
            <div className="flex items-center gap-3">
                <span className="text-[10px] font-semibold uppercase tracking-wide opacity-50 shrink-0 w-24">{opponentLabel}</span>
                <input
                    type="range"
                    min={opponentCommandMin}
                    max={opponentCommandMax}
                    step={1}
                    value={opponentCommand}
                    onChange={e => setOpponentCommand(Number(e.target.value))}
                    className="flex-1 accent-current"
                />
                <span className="text-sm font-black w-5 text-right tabular-nums opacity-80">{opponentCommand}</span>
            </div>

            {/* Stacked area bar */}
            <div className="flex h-10 rounded-lg overflow-hidden gap-px">
                {results.map(({ key, prob }) => {
                    const pct = (prob / total) * 100;
                    const color = outcomeColor(key, primaryColor, secondaryColor);
                    const showLabel = pct >= LABEL_MIN_PCT;
                    return (
                        <div
                            key={key}
                            className="relative flex items-center justify-center transition-all duration-300 overflow-hidden shrink-0"
                            style={{ width: `${pct}%`, backgroundColor: color, opacity: 0.88 }}
                            title={`${key}: ${(prob * 100).toFixed(1)}%`}
                        >
                            {showLabel && (
                                <div className="flex flex-col items-center leading-none gap-0.5">
                                    <span className="text-[10px] font-black text-white drop-shadow">{key}</span>
                                    <span className="text-[9px] font-semibold text-white/80 drop-shadow tabular-nums">
                                        {(prob * 100).toFixed(1)}%
                                    </span>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-x-3 gap-y-1">
                {results.map(({ key, prob }) => {
                    const pct = (prob / total) * 100;
                    const color = outcomeColor(key, primaryColor);
                    return (
                        <div key={key} className="flex items-center gap-1">
                            <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
                            <span className="text-[10px] font-semibold opacity-60 tabular-nums">
                                {key} {pct.toFixed(1)}%
                            </span>
                        </div>
                    );
                })}
            </div>

            {/* Estimated season stats */}
            <div className="rounded-lg p-3 space-y-2.5" style={{ background: 'color-mix(in srgb, var(--form-element) 20%, transparent)' }}>
                {isPitcher && pStats ? (
                    <>
                        <div className="text-[9px] font-semibold uppercase tracking-widest opacity-40">Est. per 9 inn.</div>
                        <div className="flex justify-around">
                            <StatCell label="ERA"  value={pStats.era.toFixed(2)}  />
                            <StatCell label="WHIP" value={pStats.whip.toFixed(2)} />
                            <StatCell label="K/9"  value={pStats.kPer9.toFixed(1)}  />
                            <StatCell label="BB/9" value={pStats.bbPer9.toFixed(1)} />
                        </div>
                        <div className="h-px opacity-10" style={{ background: 'currentColor' }} />
                        <div className="text-[9px] font-semibold uppercase tracking-widest opacity-40">Against per 9 inn.</div>
                        <div className="flex justify-around">
                            <StatCell label="BAA" value={fmtRate(pStats.avg)} />
                            <StatCell label="H"   value={pStats.h}  />
                            <StatCell label="2B"  value={pStats.d}  />
                            <StatCell label="3B"  value={pStats.t}  />
                            <StatCell label="HR"  value={pStats.hr} />
                        </div>
                    </>
                ) : stats ? (
                    <>
                        <div className="text-[9px] font-semibold uppercase tracking-widest opacity-40">Est. over {SEASON_PA} PA</div>
                        <div className="flex justify-around">
                            <StatCell label="AVG" value={fmtRate(stats.avg)} />
                            <StatCell label="OBP" value={fmtRate(stats.obp)} />
                            <StatCell label="SLG" value={fmtRate(stats.slg)} />
                        </div>
                        <div className="h-px opacity-10" style={{ background: 'currentColor' }} />
                        <div className="flex justify-around">
                            <StatCell label="H"  value={stats.h}  />
                            <StatCell label="2B" value={stats.d}  />
                            <StatCell label="3B" value={stats.t}  />
                            <StatCell label="HR" value={stats.hr} />
                            <StatCell label="BB" value={stats.bb} />
                        </div>
                    </>
                ) : null}
            </div>

        </div>
    );
}
