/**
 * @fileoverview CardStyleEditor - Inline Card Style (Set + Image, optionally Chart) editor for a
 * single card, shown inside CardDetail. Style edits auto-save after a pause; the caller owns
 * persistence and re-renders the card by passing CardDetail updated `styleOverrides`. A chart
 * version change rebuilds the card right away; the caller passes CardDetail the rebuilt card.
 */

import { useEffect, useRef, useState } from 'react';
import { FaTable } from 'react-icons/fa';
import { FaCheck, FaPalette, FaRotateLeft, FaSpinner, FaXmark } from 'react-icons/fa6';
import { CardStyleSections } from '../../customs/CardStyleFields';
import FormDropdown from '../../customs/FormDropdown';
import FormSection from '../../customs/FormSection';
import { formSectionSummary, optionSummaryItem } from '../../customs/FormSectionSummary';
import { useMediaQuery } from '../../../hooks/useMediaQuery';
import { chartVersionOptions, isCardStyleDifferent, type CardStyleSettings } from '../../customs/cardStyle';
import type { SelectOption } from '../../shared/CustomSelect';
import type { ShowdownBotCard } from '../../../api/showdownBotCard';
import { rankChartsByVersion } from './chartVersions';
import { Heading } from '../../shared/Heading';

/** Enables in-place style editing on CardDetail (see its `styleEditor` prop) */
export type CardStyleEditorConfig = {
    /** The card's current style */
    style: CardStyleSettings;
    /** What Revert resets to and what collapsed section summaries compare against, e.g. the
     * edition's default style */
    defaults: CardStyleSettings;
    /** Persists the style — called automatically once edits pause. Throw to show an error (the
     * next edit retries). */
    onSave: (style: CardStyleSettings) => Promise<void> | void;
    /** Revert button tooltip, e.g. "Revert to the edition style" */
    revertTitle?: string;
    /** Adds a Chart section for switching the card's chart version (Bot cards only). Leave out
     * where the card itself can't change. */
    chart?: {
        /** Rebuilds the card at `chartVersion` and persists it — called as soon as the version
         * changes. Throw to show an error. */
        onChange: (chartVersion: number) => Promise<void>;
    };
};

/** How long edits must pause before they're saved — each save re-renders the card image */
const SAVE_DELAY_MS = 800;

type CardStyleEditorProps = CardStyleEditorConfig & {
    /** The card as shown, for its chart version and the versions it has */
    card?: ShowdownBotCard | null;
    onClose: () => void;
};

/** The card's chart versions, each with its command/outs and accuracy. Cards without stored
 * accuracies (older archives) list every version. */
function chartVersionOptionsFor(card: ShowdownBotCard): SelectOption[] {
    const pickedChart = card.command_out_selection ? `${card.command_out_selection.command}-${card.command_out_selection.outs}` : null;
    const ranked = rankChartsByVersion(
        Object.entries(card.command_out_accuracies ?? {}).map(([chart, accuracy]) => ({ chart, accuracy })),
        pickedChart,
    );
    if (ranked.length === 0) return chartVersionOptions;
    return chartVersionOptions.slice(0, ranked.length).map((option, index) => ({
        ...option,
        trailing: (
            <span className="ml-auto pl-3 text-[11px] tabular-nums text-(--text-tertiary)">
                {ranked[index].chart} · {(ranked[index].accuracy * 100).toFixed(1)}%
            </span>
        ),
    }));
}

export function CardStyleEditor({ style: initialStyle, defaults, onSave, revertTitle = 'Revert to the default style', chart, card, onClose }: CardStyleEditorProps) {
    const [style, setStyle] = useState<CardStyleSettings>(initialStyle);
    // On phones the editor sits above the card — start collapsed so the card still peeks out below
    const isDesktop = useMediaQuery('(min-width: 768px)');
    const [saving, setSaving] = useState(false);
    const [hasSaved, setHasSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateStyle = (patch: Partial<CardStyleSettings>) => setStyle(prev => ({ ...prev, ...patch }));

    // Chart version: rebuilds immediately (it changes the card, not just its image). The picked
    // version shows until the rebuilt card arrives.
    const [isRebuilding, setIsRebuilding] = useState(false);
    const [pendingChartVersion, setPendingChartVersion] = useState<number | null>(null);
    const cardChartVersion = card?.chart_version || 1;
    const chartVersion = pendingChartVersion ?? cardChartVersion;
    useEffect(() => {
        if (!isRebuilding && pendingChartVersion === cardChartVersion) setPendingChartVersion(null);
    }, [isRebuilding, pendingChartVersion, cardChartVersion]);
    const showChart = !!chart && !!card && !card.is_wotc;

    async function handleChartVersionChange(value: string) {
        const version = Number(value);
        if (!chart || version === chartVersion) return;
        setPendingChartVersion(version);
        setIsRebuilding(true);
        setError(null);
        try {
            await chart.onChange(version);
        } catch (err) {
            setPendingChartVersion(null);
            setError(err instanceof Error ? err.message : 'Failed to rebuild card.');
        } finally {
            setIsRebuilding(false);
        }
    }

    // Auto-save once edits pause, one save at a time (an edit made mid-save goes out after it).
    // Starts from the card's own style, so opening the editor (or toggling a field back) saves nothing.
    const lastSavedRef = useRef<CardStyleSettings>(initialStyle);
    const styleRef = useRef(style);
    styleRef.current = style;
    const isUnsaved = isCardStyleDifferent(style, lastSavedRef.current);
    useEffect(() => {
        if (saving || !isCardStyleDifferent(style, lastSavedRef.current)) return;
        const timer = setTimeout(async () => {
            setSaving(true);
            setError(null);
            try {
                await onSave(style);
                lastSavedRef.current = style;
                setHasSaved(true);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to save card style.');
            } finally {
                setSaving(false);
            }
        }, SAVE_DELAY_MS);
        return () => clearTimeout(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [style, saving]);

    /** Closing mid-pause still saves the latest edit */
    function handleClose() {
        if (!saving && isCardStyleDifferent(styleRef.current, lastSavedRef.current)) {
            Promise.resolve(onSave(styleRef.current)).catch(err => console.error('Failed to save card style:', err));
        }
        onClose();
    }

    return (
        <div className="flex-1 flex flex-col min-h-0 bg-secondary rounded-card border border-form-element fade-in">
            {/* Header */}
            <div className="flex items-center gap-2 pl-4 pr-2 py-2 border-b border-form-element shrink-0">
                <FaPalette className="text-[12px] text-(--text-tertiary)" />
                <Heading level="panel" as="h3">Card Style</Heading>
                <span className="flex items-center gap-1 text-[11px] text-(--text-tertiary)">
                    {isRebuilding ? (
                        <><FaSpinner className="animate-spin text-[10px]" /> Rebuilding card</>
                    ) : saving ? (
                        <><FaSpinner className="animate-spin text-[10px]" /> Saving</>
                    ) : hasSaved && !isUnsaved && !error ? (
                        <><FaCheck className="text-[10px]" /> Saved</>
                    ) : null}
                </span>
                <div className="ml-auto flex items-center gap-1">
                    <button
                        type="button"
                        onClick={() => setStyle(defaults)}
                        disabled={!isCardStyleDifferent(style, defaults)}
                        title={revertTitle}
                        className="flex items-center gap-1.5 min-h-8 px-2.5 py-1.5 rounded-control text-[13px] font-semibold text-(--text-tertiary) hover:text-(--text-primary) disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
                    >
                        <FaRotateLeft className="text-[11px]" /> Revert
                    </button>
                    <button
                        type="button"
                        onClick={handleClose}
                        title="Close"
                        className="p-2 rounded-control text-(--text-tertiary) hover:text-(--text-primary) hover:bg-(--background-tertiary) transition-colors cursor-pointer"
                    >
                        <FaXmark className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>

            {/* Fields */}
            <div className="flex flex-col gap-3 p-3 min-h-0 overflow-y-auto">
                {error && (
                    <div className="text-[12px] text-(--red) px-3 py-2 rounded-control border border-(--red)/30 bg-(--red)/5">
                        {error}
                    </div>
                )}
                <CardStyleSections values={style} onChange={updateStyle} defaults={defaults} isOpenByDefault={isDesktop} />
                {showChart && card && (
                    <FormSection
                        title='Chart'
                        icon={<FaTable />}
                        isOpenByDefault={isDesktop}
                        childrenWhenClosed={chartVersion !== 1
                            ? formSectionSummary([optionSummaryItem(chartVersionOptions, String(chartVersion), 'Chart Version')])
                            : undefined}
                    >
                        <FormDropdown
                            label="Chart Version"
                            className='col-span-full'
                            options={chartVersionOptionsFor(card)}
                            selectedOption={String(chartVersion)}
                            onChange={handleChartVersionChange}
                            disabled={isRebuilding}
                        />
                        <p className="col-span-full text-[11px] text-(--text-tertiary)">
                            Changes the card's command, outs and points. Versions past 1 re-run the card with the current formulas.
                        </p>
                    </FormSection>
                )}
            </div>
        </div>
    );
}
