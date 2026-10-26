import { useState, useEffect, useRef, type ReactNode } from 'react';
import { type ShowdownBotCardChart, type ShowdownBotCard, fetchCardById } from '../../../api/showdownBotCard';
import { PlayerSearchInput, type PlayerSearchSelection } from '../../customs/PlayerSearchInput';
import { CardItemFromCard } from '../CardItem';
import { buildChartRangesFromValues } from '../card_elements/CardChart';
import { FaMinus } from 'react-icons/fa';
import { FaMagnifyingGlass } from 'react-icons/fa6';
import { CAPS_LABEL_CLASS } from '../../shared/fieldStyles';
import { choiceClass } from '../../shared/choiceStyles';
import { StatTile } from '../../shared/StatTile';

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
    if (['PU','SO','GB','FB'].includes(k)) return primaryColor || 'var(--showdown-red)';
    if (k === 'HR') return secondaryColor || 'var(--showdown-blue)';
    return 'var(--field-ink)';
}

function calcProbabilities(
    playerChart: ShowdownBotCardChart,
    opponentCommand: number,
    opponentValuesOverride?: Record<string, number>,
): { key: string; prob: number }[] {
    const isPitcher = playerChart.is_pitcher;

    const batterOB    = isPitcher ? opponentCommand     : playerChart.command;
    const pitcherCtrl = isPitcher ? playerChart.command : opponentCommand;

    const pBatterChart  = Math.max(0, Math.min(batterOB - pitcherCtrl, TOTAL)) / TOTAL;
    const pPitcherChart = 1 - pBatterChart;

    const batterValues  = isPitcher ? (opponentValuesOverride ?? playerChart.opponent?.values ?? {}) : playerChart.values;
    const pitcherValues = isPitcher ? playerChart.values : (opponentValuesOverride ?? playerChart.opponent?.values ?? {});

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

type OpponentMode = 'slider' | 'search';
type OpponentModeOption = { label: string; value: OpponentMode, symbol: ReactNode };

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

    const [opponentMode, setOpponentMode] = useState<OpponentMode>('slider');
    const [opponentCard, setOpponentCard] = useState<ShowdownBotCard | null>(null);
    const [opponentLoading, setOpponentLoading] = useState(false);
    const [searchKey, setSearchKey] = useState(0);

    const searchQueryRef = useRef('');

    const baselineOpponentCard: ShowdownBotCard | undefined = isEmpty ? undefined : {
        bref_id: 'opp01',
        bref_url: '',
        name: 'Baseline Opponent',
        year: '',
        team: '',
        set: set ?? '2001',
        era: '',
        points: 0,
        ip: null,
        chart_version: 1,
        speed: { speed: 0, letter: '' },
        icons: [],
        hand: '',
        player_type: data.opponent?.is_pitcher ? 'Pitcher' : 'Hitter',
        positions_and_defense_string: chart.is_pitcher ? 'HITTER' : 'PITCHER',
        positions_and_defense: {},
        chart: {
            ...data.opponent!,
            command: opponentCommand,
            ranges: buildChartRangesFromValues(data.opponent?.values ?? {}, set ?? '2005', data.opponent?.is_pitcher ?? false),
        },
        image: {
            expansion: null,
            edition: null,
            parallel: null,
            is_multi_colored: false,
            color_primary: 'rgb(0,0,0)',
            color_secondary: 'rgb(0,0,0)',
            stat_highlights_list: [
                "**APPROXIMATE: rounded to whole numbers. Actual values used are decimals**"
            ]
        },
        real_vs_projected_stats: [],
        command_out_accuracy_breakdowns: {},
        points_breakdown: {
            allow_negatives: false,
            breakdowns: {},
            command_out_multiplier: 1,
            decay_rate: 0,
            decay_start: 0,
            ip_multiplier: 1,
        },
        stats: {},
        stats_period: { type: 'REGULAR', year: '' },
        warnings: [],
    };


    useEffect(() => {
        setOpponentCommand(defaultOpponentCommand);
        setOpponentCard(null);
        setSearchKey(k => k + 1);
    }, [chart, set]);

    const handleOpponentSelect = async (selection: PlayerSearchSelection) => {
        const suffix = selection.player_type_override ? `-(${selection.player_type_override.toLowerCase()})` : '';
        const cardId = `${selection.year}-${selection.player_id}${suffix}-${set ?? '2005'}`;
        setOpponentLoading(true);
        try {
            const result = await fetchCardById(cardId, 'outcome-opponent');
            if (result.card) {
                setOpponentCard(result.card);
                setOpponentCommand(result.card.chart.command);
            }
        } finally {
            setOpponentLoading(false);
        }
    };

    const handleClearOpponent = () => {
        setOpponentCard(null);
        setOpponentCommand(defaultOpponentCommand);
        setSearchKey(k => k + 1);
        searchQueryRef.current = '';
    };

    const isExpanded = !['2000', '2001', 'CLASSIC'].includes(set ?? '2005');
    const opponentCommandMin = data.is_pitcher ? (isExpanded ? 7 : 4) : (isExpanded ? 1 : 0);
    const opponentCommandMax = data.is_pitcher ? (isExpanded ? 16 : 12) : 6;
    const opponentLabel = data.is_pitcher ? 'Opp. Onbase' : 'Opp. Control';

    const opponentValues = opponentCard ? opponentCard.chart.values as Record<string, number> : undefined;
    const results = calcProbabilities(data, opponentCommand, opponentValues);
    const total = results.reduce((s, r) => s + r.prob, 0) || 1;
    const isPitcher = data.is_pitcher;
    const stats  = isPitcher ? null : calcSeasonStats(results);
    const pStats = isPitcher ? calcPitcherStats(results) : null;

    const fmtRate = (n: number) => n.toFixed(3).replace('0.', '.');

    const resultsAreBaseline = opponentMode === 'search' && !opponentCard && !opponentLoading;

    return (
        <div className={`space-y-3 ${isEmpty ? 'opacity-25 pointer-events-none select-none' : ''}`}>

            {/* Mode toggle */}
            <div className="flex items-center gap-1.5 self-start">
                {(
                    [
                        { label: 'Baseline', value: 'slider', symbol: <FaMinus /> },
                        { label: 'Search Opponent', value: 'search', symbol: <FaMagnifyingGlass /> },
                    ] as OpponentModeOption[]
                ).map(mode => (
                    <button
                        key={mode.value}
                        onClick={() => {
                            setOpponentMode(mode.value);
                            if (mode.value === 'slider') handleClearOpponent();
                        }}
                        className={choiceClass(opponentMode === mode.value, 'sm')}
                    >
                        {mode.symbol}
                        {mode.label}
                    </button>
                ))}
            </div>

            {/* Opponent control */}
            {opponentMode === 'slider' ? (
                <>
                    <div className="flex items-center gap-3">
                        <span className={`opacity-50 shrink-0 w-24 ${CAPS_LABEL_CLASS}`}>{opponentLabel}</span>
                        <input
                            type="range"
                            min={opponentCommandMin}
                            max={opponentCommandMax}
                            step={1}
                            value={opponentCommand}
                            onChange={e => setOpponentCommand(Number(e.target.value))}
                            className="flex-1 accent-current"
                        />
                        <span className="text-sm font-bold w-5 text-right tabular-nums opacity-80">{opponentCommand}</span>
                    </div>

                    <div className="flex items-center gap-2">
                        <CardItemFromCard
                            card={opponentCard || baselineOpponentCard}
                            className="max-w-full"
                        />
                    </div>

                </>
            ) : (
                <div className="space-y-1">
                    <div className="flex flex-1 items-center gap-1">
                        {/* Player search */}
                        <PlayerSearchInput
                            key={searchKey}
                            label=""
                            value={searchQueryRef.current}
                            onChange={handleOpponentSelect}
                            searchOptions={{ exclude_multi_year: true, exclude_career: true }}
                            className="flex-1"
                        />

                        {/* Loading indicator */}
                        {opponentLoading && (
                            <div className="flex items-center gap-2 px-3 py-2 text-[10px] opacity-50">
                                <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
                                <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
                                <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                        )}
                    </div>

                    {/* Selected opponent card */}
                    <div className="flex items-center gap-2">
                        <CardItemFromCard
                            card={opponentCard}
                            className="flex-1"
                        />
                    </div>
                </div>
            )}

            {/* Stacked area bar */}
            <div className={`flex h-10 rounded-card overflow-hidden gap-px transition-opacity duration-300 ${resultsAreBaseline ? 'opacity-20 pointer-events-none' : ''}`}>
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
                                    {/* design-ok: drop-shadow keeps white labels legible on light team colors */}
                                    <span className="text-[10px] font-bold text-white drop-shadow">{key}</span>
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
            <div className={`flex flex-wrap gap-x-3 gap-y-1 transition-opacity duration-300 ${resultsAreBaseline ? 'opacity-20 pointer-events-none' : ''}`}>
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
            <div className={`rounded-card p-3 space-y-2.5 transition-opacity duration-300 ${resultsAreBaseline ? 'opacity-20 pointer-events-none' : ''}`} style={{ background: 'color-mix(in srgb, var(--form-element) 20%, transparent)' }}>
                {isPitcher && pStats ? (
                    <>
                        <div className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Est. per 9 inn.</div>
                        <div className="flex justify-around">
                            <StatTile size="inline" label="ERA"  value={pStats.era.toFixed(2)}  />
                            <StatTile size="inline" label="WHIP" value={pStats.whip.toFixed(2)} />
                            <StatTile size="inline" label="K/9"  value={pStats.kPer9.toFixed(1)}  />
                            <StatTile size="inline" label="BB/9" value={pStats.bbPer9.toFixed(1)} />
                        </div>
                        <div className="h-px opacity-10" style={{ background: 'currentColor' }} />
                        <div className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Against per 9 inn.</div>
                        <div className="flex justify-around">
                            <StatTile size="inline" label="BAA" value={fmtRate(pStats.avg)} />
                            <StatTile size="inline" label="H"   value={pStats.h}  />
                            <StatTile size="inline" label="2B"  value={pStats.d}  />
                            <StatTile size="inline" label="3B"  value={pStats.t}  />
                            <StatTile size="inline" label="HR"  value={pStats.hr} />
                        </div>
                    </>
                ) : stats ? (
                    <>
                        <div className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Est. over {SEASON_PA} PA</div>
                        <div className="flex justify-around">
                            <StatTile size="inline" label="AVG" value={fmtRate(stats.avg)} />
                            <StatTile size="inline" label="OBP" value={fmtRate(stats.obp)} />
                            <StatTile size="inline" label="SLG" value={fmtRate(stats.slg)} />
                            <StatTile size="inline" label="OPS" value={fmtRate(stats.obp + stats.slg)} />
                        </div>
                        <div className="h-px opacity-10" style={{ background: 'currentColor' }} />
                        <div className="flex justify-around">
                            <StatTile size="inline" label="H"  value={stats.h}  />
                            <StatTile size="inline" label="2B" value={stats.d}  />
                            <StatTile size="inline" label="3B" value={stats.t}  />
                            <StatTile size="inline" label="HR" value={stats.hr} />
                            <StatTile size="inline" label="BB" value={stats.bb} />
                        </div>
                    </>
                ) : null}
            </div>

        </div>
    );
}
