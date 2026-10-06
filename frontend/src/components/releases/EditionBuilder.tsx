import { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import type { ReleaseEdition, ReleaseCard, AlgorithmPreviewResult, AlgorithmPreviewPlayer } from '../../api/releases';
import { updateEdition } from '../../api/releases';
import { SummaryCharts } from './SummaryCharts';
import { AlgorithmBuilder } from './AlgorithmBuilder';
import ShowdownCardSearch from '../cards/ShowdownCardSearch';
import { CardSource } from '../../types/cardSource';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { CardItemFromCardDatabaseRecord } from '../cards/CardItem';
import { CardDetail } from '../cards/CardDetail';
import { Modal } from '../shared/Modal';
import CompactSelect from '../shared/CompactSelect';
import { showdownSets, imageForSet } from '../shared/SiteSettingsContext';
import type { ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import FormEnabler from '../customs/FormEnabler';
import {
    groupAndSortCards, takeFromGroups, POOL_GROUP_OPTIONS, POOL_SORT_OPTIONS, POOL_SORT_DEFAULT_DIRECTION,
    type PoolGroupBy, type PoolSortBy, type PoolSortDirection,
} from './poolGrouping';
import { FaGripVertical } from 'react-icons/fa';
import { FaPlus, FaXmark, FaSpinner, FaWandMagicSparkles, FaMagnifyingGlass, FaArrowsRotate, FaGear, FaArrowUp, FaArrowDown, FaTriangleExclamation, FaTableCellsLarge, FaList, FaAnglesLeft, FaAnglesRight, FaListCheck, FaChartColumn } from 'react-icons/fa6';

/** Narrowest the Player Pool panel can get; it takes whatever the Build Method panel leaves. */
const MIN_POOL_PANEL_WIDTH = 280;
/** Narrowest the Build Method panel can be dragged to. */
const MIN_BUILD_PANEL_WIDTH = 320;
/** Default Build Method widths until the user drags the divider — Manual needs a bit more room for search results. */
const DEFAULT_BUILD_PANEL_WIDTH = { algorithm: 480, manual: 560 } as const;

type EditionBuilderProps = {
    releaseId: string;
    edition: ReleaseEdition;
    readOnly: boolean;
    token?: string;
    defaultShowdownSet?: string | null;
    onEditionUpdated: (edition: ReleaseEdition) => void;
};

const TAB_TRIGGER_CLASS =
    'relative flex items-center px-4 py-2 text-sm rounded-lg transition-colors ' +
    'data-[state=active]:bg-(--background-quaternary) data-[state=active]:font-bold ' +
    'data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:font-medium data-[state=inactive]:hover:bg-(--divider)';

// =============================================================================
// MARK: - NUMBERING
// =============================================================================

type NumberingMode = 'manual' | 'auto' | 'none';
type SortCategory = 'team' | 'last_name' | 'points' | 'position';
type SortDirection = 'asc' | 'desc';
type SortLayer = { category: SortCategory; direction: SortDirection };

type NumberingSettings = {
    mode: NumberingMode;
    /** When true, re-run auto numbering every time a card is added/removed, rather than requiring "Renumber Now". */
    autoLive: boolean;
    /** Zero-pad displayed numbers to the width of the current card count (e.g. "001" vs "1"). */
    zeroPad: boolean;
    /** Up to 3 letters prepended to every displayed number (e.g. "AS" -> "AS001"). */
    prefix: string;
    /** Applied in order — e.g. Team asc, then Points desc breaks ties within each team by points. */
    sortLayers: SortLayer[];
};

const DEFAULT_SORT_LAYERS: SortLayer[] = [
    { category: 'team', direction: 'asc' },
    { category: 'last_name', direction: 'asc' },
];

const DEFAULT_NUMBERING: NumberingSettings = {
    mode: 'manual',
    autoLive: true,
    zeroPad: false,
    prefix: '',
    sortLayers: DEFAULT_SORT_LAYERS,
};

function sanitizePrefix(value: unknown): string {
    if (typeof value !== 'string') return '';
    return value.replace(/[^a-zA-Z]/g, '').slice(0, 3).toUpperCase();
}

const NUMBERING_MODE_OPTIONS: { label: string; value: NumberingMode }[] = [
    { label: 'Manual', value: 'manual' },
    { label: 'Auto', value: 'auto' },
    { label: 'None', value: 'none' },
];

const SORT_CATEGORY_OPTIONS: { label: string; value: SortCategory }[] = [
    { label: 'Team', value: 'team' },
    { label: 'Last Name', value: 'last_name' },
    { label: 'Points', value: 'points' },
    { label: 'Position', value: 'position' },
];

const SORT_CATEGORY_VALUES = SORT_CATEGORY_OPTIONS.map(o => o.value);

function parseSortLayers(raw: unknown): SortLayer[] {
    if (!Array.isArray(raw) || raw.length === 0) return DEFAULT_SORT_LAYERS;
    const layers = raw
        .filter((l): l is SortLayer => l && typeof l === 'object' && (SORT_CATEGORY_VALUES as string[]).includes(l.category))
        .map(l => ({ category: l.category, direction: l.direction === 'desc' ? 'desc' as const : 'asc' as const }));
    return layers.length > 0 ? layers : DEFAULT_SORT_LAYERS;
}

function parseNumberingSettings(attributes: Record<string, unknown>): NumberingSettings {
    const raw = attributes.numbering as Partial<NumberingSettings> | undefined;
    if (!raw || typeof raw !== 'object') return DEFAULT_NUMBERING;
    return {
        mode: raw.mode === 'auto' || raw.mode === 'none' ? raw.mode : 'manual',
        autoLive: raw.autoLive ?? true,
        zeroPad: raw.zeroPad ?? false,
        prefix: sanitizePrefix(raw.prefix),
        sortLayers: parseSortLayers(raw.sortLayers),
    };
}

/** Last name for sort purposes — mirrors CardItemCompact's display heuristic (suffix-aware). */
function getLastNameForSort(name: string | undefined): string {
    if (!name) return '';
    const parts = name.trim().split(/\s+/);
    if (parts.length <= 1) return parts[0] ?? '';
    const last = parts[parts.length - 1].replace('.', '').toUpperCase();
    if (['JR', 'SR', 'II', 'III', 'IV', 'V'].includes(last) && parts.length > 1) {
        return parts[parts.length - 2];
    }
    return parts[parts.length - 1];
}

function compareByCategory(a: ReleaseCard, b: ReleaseCard, category: SortCategory): number {
    switch (category) {
        case 'points':
            return (a.card_snapshot.points ?? 0) - (b.card_snapshot.points ?? 0);
        case 'position':
            return (a.card_snapshot.positions_list?.[0] ?? '').localeCompare(b.card_snapshot.positions_list?.[0] ?? '');
        case 'last_name':
            return getLastNameForSort(a.card_snapshot.name).localeCompare(getLastNameForSort(b.card_snapshot.name));
        case 'team':
        default:
            return (a.card_snapshot.team || '').localeCompare(b.card_snapshot.team || '');
    }
}

/** Applies each sort layer in priority order — later layers only break ties left by earlier ones. */
function compareByLayers(a: ReleaseCard, b: ReleaseCard, layers: SortLayer[]): number {
    for (const layer of layers) {
        const factor = layer.direction === 'desc' ? -1 : 1;
        const cmp = factor * compareByCategory(a, b, layer.category);
        if (cmp !== 0) return cmp;
    }
    return 0;
}

function sortForAutoNumbering(cards: ReleaseCard[], layers: SortLayer[]): ReleaseCard[] {
    return [...cards].sort((a, b) => compareByLayers(a, b, layers));
}

function renumberSorted(cards: ReleaseCard[], layers: SortLayer[]): ReleaseCard[] {
    const sorted = sortForAutoNumbering(cards, layers);
    const numbered = sorted.map((c, i) => ({ ...c, card_number: i + 1 }));
    // Preserve the caller's array order — only the numbers change, not the sort-order-on-screen.
    const byId = new Map(numbered.map(c => [c.id, c]));
    return cards.map(c => byId.get(c.id) ?? c);
}

function formatCardNumber(num: number | null, totalCount: number, zeroPad: boolean, prefix?: string): string {
    if (num === null) return prefix ? `${prefix}—` : '—';
    const numStr = zeroPad ? String(num).padStart(String(totalCount).length, '0') : String(num);
    return prefix ? `${prefix}${numStr}` : numStr;
}

/** Maps an algorithm preview result's players into the same `ReleaseCard` shape used by manual
 * add, so the existing grid/SummaryCharts/persist machinery works unmodified against a preview. */
function buildReleaseCardsFromPreview(players: AlgorithmPreviewPlayer[]): ReleaseCard[] {
    return players.map(record => ({
        id: `pending-${record.id}`,
        card_number: record.algorithm_set_number ?? null,
        source_card_id: record.id,
        source_card_type: record.source,
        card_snapshot: record,
    }));
}

/** Cards rendered per page in the Selected pool grid. */
const POOL_PAGE_SIZE = 40;
/** Per-viewer preference for full vs. compact card items in the pool grid. */
const POOL_FULL_CARDS_STORAGE_KEY = 'releaseBuilder.poolFullCards';
/** Per-viewer preference for hiding the Build Method panel. */
const BUILD_PANEL_HIDDEN_STORAGE_KEY = 'releaseBuilder.buildPanelHidden';
/** Per-viewer Build Method panel width, saved once they drag the divider. */
const BUILD_PANEL_WIDTH_STORAGE_KEY = 'releaseBuilder.buildPanelWidth';

function loadSavedBuildPanelWidth(): number | null {
    try {
        const saved = Number(localStorage.getItem(BUILD_PANEL_WIDTH_STORAGE_KEY));
        return Number.isFinite(saved) && saved >= MIN_BUILD_PANEL_WIDTH ? saved : null;
    } catch {
        return null;
    }
}

export function EditionBuilder({ releaseId, edition, readOnly, token, defaultShowdownSet, onEditionUpdated }: EditionBuilderProps) {
    const [cards, setCards] = useState<ReleaseCard[]>(edition.cards);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [previewResult, setPreviewResult] = useState<AlgorithmPreviewResult | null>(null);
    const [numbering, setNumbering] = useState<NumberingSettings>(() => parseNumberingSettings(edition.attributes));
    const [editingNumbers, setEditingNumbers] = useState<Record<string, string>>({});
    const [showNumberingSettings, setShowNumberingSettings] = useState(false);
    const numberingSettingsRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (numberingSettingsRef.current && !numberingSettingsRef.current.contains(event.target as Node)) {
                setShowNumberingSettings(false);
            }
        };
        if (showNumberingSettings) document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showNumberingSettings]);

    // Left/right split resize
    const [buildMethod, setBuildMethod] = useState<'algorithm' | 'manual'>('algorithm');
    const [blueprintSlot, setBlueprintSlot] = useState<HTMLDivElement | null>(null);
    const [buildPanelWidth, setBuildPanelWidth] = useState<number>(() => loadSavedBuildPanelWidth() ?? DEFAULT_BUILD_PANEL_WIDTH.algorithm);
    // Summary mounts lazily on first open, then stays mounted so its filters/WOTC comparison survive tab switches.
    const [summaryMounted, setSummaryMounted] = useState(false);
    const [detailCard, setDetailCard] = useState<CardDatabaseRecord | null>(null);
    const isResizing = useRef(false);
    const hasManuallyResized = useRef(loadSavedBuildPanelWidth() !== null);
    const splitContainerRef = useRef<HTMLDivElement>(null);
    const buildPanelRef = useRef<HTMLDivElement>(null);
    const [buildPanelHidden, setBuildPanelHidden] = useState<boolean>(() => {
        try { return localStorage.getItem(BUILD_PANEL_HIDDEN_STORAGE_KEY) === 'true'; } catch { return false; }
    });
    function toggleBuildPanelHidden() {
        setBuildPanelHidden(prev => {
            try { localStorage.setItem(BUILD_PANEL_HIDDEN_STORAGE_KEY, String(!prev)); } catch { /* storage unavailable */ }
            return !prev;
        });
    }

    useEffect(() => {
        if (hasManuallyResized.current) return;
        setBuildPanelWidth(DEFAULT_BUILD_PANEL_WIDTH[buildMethod]);
    }, [buildMethod]);

    const handleResizeStart = (e: React.MouseEvent) => {
        e.preventDefault();
        isResizing.current = true;
        hasManuallyResized.current = true;
        const startX = e.clientX;
        // Start from the rendered width — the CSS max-width may have clamped the stored value on a narrow screen.
        const startWidth = buildPanelRef.current?.offsetWidth ?? buildPanelWidth;
        const maxWidth = Math.max((splitContainerRef.current?.clientWidth ?? 0) - MIN_POOL_PANEL_WIDTH, MIN_BUILD_PANEL_WIDTH);
        let latestWidth = startWidth;

        const onMouseMove = (ev: MouseEvent) => {
            if (!isResizing.current) return;
            latestWidth = Math.min(Math.max(startWidth + (ev.clientX - startX), MIN_BUILD_PANEL_WIDTH), maxWidth);
            setBuildPanelWidth(latestWidth);
        };
        const onMouseUp = () => {
            isResizing.current = false;
            try { localStorage.setItem(BUILD_PANEL_WIDTH_STORAGE_KEY, String(Math.round(latestWidth))); } catch { /* storage unavailable */ }
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none';
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    };

    const excludeIds = useMemo(
        () => cards.map(c => c.source_card_id).filter((id): id is string => !!id),
        [cards]
    );

    async function persist(nextCards: ReleaseCard[]) {
        if (!token) return;
        const previous = cards;
        setCards(nextCards);
        setSaving(true);
        setError(null);
        try {
            const updated = await updateEdition(releaseId, edition.id, {
                cards: nextCards.map(c => ({
                    card_number: c.card_number,
                    source_card_id: c.source_card_id,
                    source_card_type: c.source_card_type,
                    card_snapshot: c.card_snapshot,
                })),
            }, token);
            setCards(updated.cards);
            onEditionUpdated(updated);
        } catch (err: any) {
            setCards(previous);
            setError(err.message ?? 'Failed to save changes.');
        } finally {
            setSaving(false);
        }
    }

    /** Applies the current numbering mode to a candidate card list, e.g. after an add/remove. */
    function applyNumberingIfNeeded(list: ReleaseCard[]): ReleaseCard[] {
        if (numbering.mode === 'none') return list.map(c => ({ ...c, card_number: null }));
        if (numbering.mode === 'auto' && numbering.autoLive) {
            return renumberSorted(list, numbering.sortLayers);
        }
        return list;
    }

    // While a preview is active, the right panel shows the (unsaved) preview pool instead of the
    // committed `cards` — everything downstream (grid, SummaryCharts) reads `displayCards`.
    const previewCards = useMemo(
        () => previewResult ? buildReleaseCardsFromPreview(previewResult.players) : null,
        [previewResult]
    );
    const displayCards = previewCards ?? cards;

    // The pool can be hundreds of cards, so the grid renders in pages and loads more as the
    // user scrolls to the sentinel below it.
    const [visibleCount, setVisibleCount] = useState(POOL_PAGE_SIZE);
    const [groupBy, setGroupBy] = useState<PoolGroupBy>('none');
    const [sortBy, setSortBy] = useState<PoolSortBy>('set_number');
    const [sortDirection, setSortDirection] = useState<PoolSortDirection>('asc');
    const [showFullCards, setShowFullCards] = useState<boolean>(() => {
        try { return localStorage.getItem(POOL_FULL_CARDS_STORAGE_KEY) === 'true'; } catch { return false; }
    });
    function toggleShowFullCards() {
        setShowFullCards(prev => {
            try { localStorage.setItem(POOL_FULL_CARDS_STORAGE_KEY, String(!prev)); } catch { /* storage unavailable */ }
            return !prev;
        });
    }
    // Distinct Showdown sets in the pool, in the site's set order, for the icons in the pool tab bar.
    const poolSets = useMemo(() => {
        const present = new Set(displayCards.map(c => c.card_snapshot.showdown_set));
        return showdownSets.map(s => s.value).filter(set => present.has(set));
    }, [displayCards]);

    const poolGroups = useMemo(
        () => groupAndSortCards(displayCards, groupBy, sortBy, sortDirection),
        [displayCards, groupBy, sortBy, sortDirection]
    );
    const visibleGroups = useMemo(() => takeFromGroups(poolGroups, visibleCount), [poolGroups, visibleCount]);
    useEffect(() => { setVisibleCount(POOL_PAGE_SIZE); }, [previewResult, groupBy, sortBy, sortDirection]);
    const poolSentinelRef = useCallback((node: HTMLDivElement | null) => {
        if (!node) return;
        const observer = new IntersectionObserver(entries => {
            if (entries[0]?.isIntersecting) setVisibleCount(n => n + POOL_PAGE_SIZE);
        }, { rootMargin: '400px' });
        observer.observe(node);
        return () => observer.disconnect();
    }, []);

    /** Non-destructive save: keeps every currently-persisted card, appends new preview players
     * (deduped by source_card_id) until reaching the configured set size. */
    function handleFillRemainingSlots() {
        if (!previewResult) return;
        const existingSourceIds = new Set(cards.map(c => c.source_card_id).filter(Boolean));
        const remainingSlots = Math.max(0, previewResult.summary.requested_set_size - cards.length);
        const additions = buildReleaseCardsFromPreview(previewResult.players)
            .filter(c => !existingSourceIds.has(c.source_card_id))
            .slice(0, remainingSlots);
        persist(applyNumberingIfNeeded([...cards, ...additions]));
        setPreviewResult(null);
    }

    /** Destructive save: replaces the entire pool with the preview result. Warns if it would drop
     * any currently-persisted card (manual or from a prior algorithm run — provenance isn't tracked). */
    function handleReplaceAllFromPreview() {
        if (!previewResult) return;
        const newCards = buildReleaseCardsFromPreview(previewResult.players);
        const newSourceIds = new Set(newCards.map(c => c.source_card_id));
        const droppedCount = cards.filter(c => !newSourceIds.has(c.source_card_id)).length;
        if (droppedCount > 0) {
            const confirmed = window.confirm(
                `Replacing will remove ${droppedCount} existing card${droppedCount === 1 ? '' : 's'} from the pool. Continue?`
            );
            if (!confirmed) return;
        }
        persist(applyNumberingIfNeeded(newCards));
        setPreviewResult(null);
    }

    function handleAddCard(record: CardDatabaseRecord) {
        const nextNumber = numbering.mode === 'manual'
            ? (cards.length > 0 ? Math.max(0, ...cards.map(c => c.card_number ?? 0)) + 1 : 1)
            : null;
        const newCard: ReleaseCard = {
            id: `pending-${record.id}`,
            card_number: nextNumber,
            source_card_id: record.id,
            source_card_type: record.source,
            card_snapshot: record,
        };
        persist(applyNumberingIfNeeded([...cards, newCard]));
    }

    function handleRemoveCard(cardId: string) {
        persist(applyNumberingIfNeeded(cards.filter(c => c.id !== cardId)));
    }

    function handleNumberInputChange(cardId: string, value: string) {
        setEditingNumbers(prev => ({ ...prev, [cardId]: value }));
    }

    function handleNumberInputBlur(cardId: string) {
        const value = editingNumbers[cardId];
        setEditingNumbers(prev => {
            const next = { ...prev };
            delete next[cardId];
            return next;
        });
        if (value === undefined) return;
        const parsed = value.trim() === '' ? null : parseInt(value, 10);
        if (parsed !== null && Number.isNaN(parsed)) return;
        persist(cards.map(c => c.id === cardId ? { ...c, card_number: parsed } : c));
    }

    function handlePrefixInputChange(value: string) {
        setNumbering(prev => ({ ...prev, prefix: sanitizePrefix(value) }));
    }

    function handlePrefixInputBlur() {
        persistNumberingSettings(numbering);
    }

    async function persistNumberingSettings(next: NumberingSettings) {
        setNumbering(next);
        if (!token) return;
        try {
            const updated = await updateEdition(releaseId, edition.id, {
                attributes: { ...edition.attributes, numbering: next },
            }, token);
            onEditionUpdated(updated);
        } catch (err: any) {
            setError(err.message ?? 'Failed to save numbering settings.');
        }
    }

    function handleNumberingModeChange(mode: NumberingMode) {
        const next = { ...numbering, mode };
        persistNumberingSettings(next);
        if (mode === 'none') {
            persist(cards.map(c => ({ ...c, card_number: null })));
        } else if (mode === 'auto') {
            persist(renumberSorted(cards, next.sortLayers));
        }
    }

    /** Handles Live/Sort-By/Direction changes from the numbering settings popover. Re-numbers
     * immediately when in live auto mode, otherwise just saves the setting for next Renumber/live-trigger. */
    function handleNumberingSettingChange(patch: Partial<NumberingSettings>) {
        const next = { ...numbering, ...patch };
        persistNumberingSettings(next);
        if (next.mode === 'auto' && next.autoLive) {
            persist(renumberSorted(cards, next.sortLayers));
        }
    }

    /** Categories not already claimed by another sort layer (a category can only appear once). */
    function availableCategoriesFor(currentCategory: SortCategory): { label: string; value: SortCategory }[] {
        const usedByOthers = new Set(numbering.sortLayers.filter(l => l.category !== currentCategory).map(l => l.category));
        return SORT_CATEGORY_OPTIONS.filter(o => o.value === currentCategory || !usedByOthers.has(o.value));
    }

    function addSortLayer() {
        const used = new Set(numbering.sortLayers.map(l => l.category));
        const next = SORT_CATEGORY_OPTIONS.find(o => !used.has(o.value));
        if (!next) return;
        handleNumberingSettingChange({ sortLayers: [...numbering.sortLayers, { category: next.value, direction: 'asc' }] });
    }

    function updateSortLayer(index: number, patch: Partial<SortLayer>) {
        handleNumberingSettingChange({
            sortLayers: numbering.sortLayers.map((l, i) => i === index ? { ...l, ...patch } : l),
        });
    }

    function removeSortLayer(index: number) {
        const layers = numbering.sortLayers.filter((_, i) => i !== index);
        handleNumberingSettingChange({ sortLayers: layers.length > 0 ? layers : DEFAULT_SORT_LAYERS });
    }

    function moveSortLayer(index: number, direction: -1 | 1) {
        const target = index + direction;
        if (target < 0 || target >= numbering.sortLayers.length) return;
        const layers = [...numbering.sortLayers];
        [layers[index], layers[target]] = [layers[target], layers[index]];
        handleNumberingSettingChange({ sortLayers: layers });
    }

    return (
        <div className="flex flex-col flex-1 min-h-0">
            {/* Step indicator */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-(--divider) shrink-0">
                <div className="flex items-center gap-2">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-(--secondary) text-(--background-primary) text-[10px] font-black shrink-0">
                        1
                    </span>
                    <span className="flex items-center gap-1.5 text-[13px] font-bold text-(--text-primary)">
                         Player Pool
                    </span>
                </div>

                <div className="w-8 h-px bg-(--divider) shrink-0" />

                <div className="flex items-center gap-2 opacity-50 cursor-not-allowed">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full border border-(--text-tertiary) text-(--text-tertiary) text-[10px] font-black shrink-0">
                        2
                    </span>
                    <span className="flex items-center gap-1.5 text-[13px] font-semibold text-(--text-tertiary)">
                        Images
                    </span>
                </div>

                {saving && (
                    <span className="ml-auto flex items-center gap-1 text-[11px] text-(--text-tertiary)">
                        <FaSpinner className="animate-spin text-[10px]" /> Saving…
                    </span>
                )}
            </div>

            {error && (
                <div className="mx-4 mt-2 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5 shrink-0">
                    {error}
                </div>
            )}

            <div ref={splitContainerRef} className="flex flex-1 min-h-0">
                {/* Collapsed rail for the hidden Build panel */}
                {!readOnly && buildPanelHidden && (
                    <button
                        type="button"
                        onClick={toggleBuildPanelHidden}
                        title="Show build method"
                        className="flex flex-col items-center gap-3 w-9 shrink-0 py-3 border-r border-(--divider) text-(--text-tertiary) hover:text-(--text-primary) hover:bg-(--background-secondary) transition-colors cursor-pointer"
                    >
                        <FaAnglesRight className="text-[12px]" />
                        <span className="text-[10px] font-bold uppercase tracking-wide [writing-mode:vertical-rl]">Build Method</span>
                    </button>
                )}

                {/* Build panel: Algorithm / Manual. Hidden (not unmounted) when collapsed so its state survives. */}
                {!readOnly && (
                    <div
                        ref={buildPanelRef}
                        style={{ width: buildPanelWidth, maxWidth: `calc(100% - ${MIN_POOL_PANEL_WIDTH}px)` }}
                        className={`shrink-0 min-w-0 border-r border-(--divider) flex-col min-h-0 ${buildPanelHidden ? 'hidden' : 'flex'}`}
                    >
                        <div className="px-3 pt-2 pb-1 shrink-0 flex items-center justify-between gap-2">
                            <div className="flex items-center gap-1.5">
                                <button
                                    type="button"
                                    onClick={toggleBuildPanelHidden}
                                    title="Hide build method"
                                    className="flex items-center justify-center w-5 h-5 rounded text-(--text-tertiary) hover:text-(--text-primary) hover:bg-(--divider) transition-colors cursor-pointer"
                                >
                                    <FaAnglesLeft className="text-[11px]" />
                                </button>
                                <span className="text-[10px] font-bold text-(--text-tertiary) uppercase tracking-wide">Build Method</span>
                            </div>
                            <div ref={setBlueprintSlot} />
                        </div>
                        <Tabs.Root
                            value={buildMethod}
                            onValueChange={v => setBuildMethod(v as 'algorithm' | 'manual')}
                            className="flex flex-col flex-1 min-h-0"
                        >
                            <Tabs.List className="flex items-center px-3 border-b border-(--divider) gap-x-1 py-1 shrink-0">
                                <Tabs.Trigger value="algorithm" className={TAB_TRIGGER_CLASS}>
                                    <FaWandMagicSparkles className="text-[10px] mr-1.5" /> Algorithm
                                </Tabs.Trigger>
                                <Tabs.Trigger value="manual" className={TAB_TRIGGER_CLASS}>
                                    <FaMagnifyingGlass className="text-[10px] mr-1.5" /> Manual
                                </Tabs.Trigger>
                            </Tabs.List>
                            <Tabs.Content value="algorithm" className="flex-1 min-h-0 flex flex-col focus:outline-none">
                                <AlgorithmBuilder
                                    releaseId={releaseId}
                                    edition={edition}
                                    token={token}
                                    defaultShowdownSet={defaultShowdownSet}
                                    onPreviewResult={setPreviewResult}
                                    blueprintSlot={blueprintSlot}
                                />
                            </Tabs.Content>
                            <Tabs.Content value="manual" className="flex-1 min-h-0 flex flex-col focus:outline-none">
                                <ShowdownCardSearch
                                    source={CardSource.BOT}
                                    compact={true}
                                    excludeIds={excludeIds}
                                    defaultFilters={defaultShowdownSet ? { showdown_set: [defaultShowdownSet] } : undefined}
                                    actionButton={{
                                        icon: <FaPlus />,
                                        label: 'Add',
                                        bgColorClass: 'bg-(--showdown-red) opacity-95 border p-2 md:p-1 text-white shadow-sm rounded-full',
                                        onClick: handleAddCard,
                                    }}
                                />
                            </Tabs.Content>
                        </Tabs.Root>
                    </div>
                )}

                {/* Drag-to-resize handle */}
                {!readOnly && !buildPanelHidden && (
                    <div
                        onMouseDown={handleResizeStart}
                        className="relative w-1.5 shrink-0 -translate-x-0.5 cursor-ew-resize flex items-center justify-center group hover:bg-(--divider) transition-colors"
                    >
                        <FaGripVertical className="absolute text-[14px] text-(--text-tertiary) group-hover:text-(--text-secondary) transition-colors bg-(--background-primary) rounded-md px-0.5" />
                    </div>
                )}

                {/* Selected Cards / Summary — takes whatever width the Build panel leaves. */}
                <div className="flex-1 min-w-0 flex flex-col min-h-0">
                    <div className="px-3 pt-2 shrink-0">
                        <span className="text-[10px] font-bold text-(--text-tertiary) uppercase tracking-wide">Player Pool</span>
                    </div>
                    <Tabs.Root
                        defaultValue="cards"
                        onValueChange={value => { if (value === 'summary') setSummaryMounted(true); }}
                        className="flex flex-col flex-1 min-h-0"
                    >
                        <Tabs.List className="flex items-center px-3 border-b border-(--divider) gap-x-1 py-1 shrink-0">
                            <Tabs.Trigger value="cards" className={TAB_TRIGGER_CLASS}>
                                <FaListCheck className="text-[10px] mr-1.5" /> Selected <span className="ml-1.5 text-[10px] text-(--text-tertiary) bg-(--background-secondary) py-0.5 px-1 rounded-md">{displayCards.length}</span>
                            </Tabs.Trigger>
                            <Tabs.Trigger value="summary" className={TAB_TRIGGER_CLASS}>
                                <FaChartColumn className="text-[10px] mr-1.5" /> Summary
                            </Tabs.Trigger>
                            {poolSets.length > 0 && (
                                <div className="flex items-center gap-1 ml-auto shrink-0">
                                    {poolSets.map(set => {
                                        const useAbbreviated = poolSets.length >= 2;
                                        const image = imageForSet(set, useAbbreviated);
                                        return image ? (
                                            <img key={set} src={image} alt={set} title={set} className={`${useAbbreviated ? 'h-4.5' : 'h-5.5'} w-auto object-contain`} />
                                        ) : null;
                                    })}
                                </div>
                            )}
                        </Tabs.List>

                        <Tabs.Content value="cards" className="flex-1 min-h-0 flex flex-col focus:outline-none">
                            {previewResult && (
                                <div className="flex flex-col gap-2 px-3 py-2 border-b border-(--divider) shrink-0">
                                    <div className="flex items-center gap-1.5 text-[12px] font-semibold text-(--text-secondary)">
                                        <FaWandMagicSparkles className="text-(--secondary)" />
                                        Previewing {previewResult.summary.actual_count} player{previewResult.summary.actual_count === 1 ? '' : 's'} — not yet saved
                                    </div>
                                    {previewResult.summary.warnings.length > 0 && (
                                        <div className="flex flex-col gap-1">
                                            {previewResult.summary.warnings.map((warning, i) => (
                                                <div key={i} className="flex items-center gap-1.5 text-[11px] text-amber-500">
                                                    <FaTriangleExclamation className="shrink-0" /> {warning}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    <div className="flex flex-wrap gap-2">
                                        <button
                                            type="button"
                                            onClick={handleFillRemainingSlots}
                                            className="min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-bold bg-(--secondary) text-(--background-primary) cursor-pointer"
                                        >
                                            Fill Remaining Slots
                                        </button>
                                        <button
                                            type="button"
                                            onClick={handleReplaceAllFromPreview}
                                            className="min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-bold border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors cursor-pointer"
                                        >
                                            Replace All
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setPreviewResult(null)}
                                            className="min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-semibold text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer"
                                        >
                                            Discard Preview
                                        </button>
                                    </div>
                                </div>
                            )}
                            {((!readOnly && !previewResult) || displayCards.length > 0) && (
                                <div className="flex flex-wrap items-center gap-x-2 gap-y-2 px-3 py-2 border-b border-(--divider) shrink-0">
                                    {displayCards.length > 0 && (
                                        <div className="flex flex-wrap items-center gap-2">
                                            <CompactSelect
                                                label="Group"
                                                options={POOL_GROUP_OPTIONS}
                                                value={groupBy}
                                                onChange={value => setGroupBy(value as PoolGroupBy)}
                                            />
                                            <CompactSelect
                                                label="Sort"
                                                options={POOL_SORT_OPTIONS}
                                                value={sortBy}
                                                onChange={value => {
                                                    setSortBy(value as PoolSortBy);
                                                    setSortDirection(POOL_SORT_DEFAULT_DIRECTION[value as PoolSortBy]);
                                                }}
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setSortDirection(d => d === 'asc' ? 'desc' : 'asc')}
                                                title={sortDirection === 'asc' ? 'Ascending' : 'Descending'}
                                                className="flex items-center justify-center w-9 h-9 rounded-lg border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors shrink-0 cursor-pointer"
                                            >
                                                {sortDirection === 'asc' ? <FaArrowUp className="text-[13px]" /> : <FaArrowDown className="text-[13px]" />}
                                            </button>
                                            <button
                                                type="button"
                                                onClick={toggleShowFullCards}
                                                title={showFullCards ? 'Show compact cards' : 'Show full cards'}
                                                className="flex items-center justify-center w-9 h-9 rounded-lg border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors shrink-0 cursor-pointer"
                                            >
                                                {showFullCards ? <FaList className="text-[13px]" /> : <FaTableCellsLarge className="text-[13px]" />}
                                            </button>
                                        </div>
                                    )}

                                    {!readOnly && !previewResult && (
                                        <div className="flex flex-wrap items-center gap-2 ml-auto">
                                            <span className="text-[10px] font-bold text-(--text-tertiary) uppercase tracking-wide shrink-0">
                                                Numbering
                                            </span>
                                            <div className="flex gap-1.5">
                                                {NUMBERING_MODE_OPTIONS.map(opt => (
                                                    <button
                                                        key={opt.value}
                                                        type="button"
                                                        onClick={() => handleNumberingModeChange(opt.value)}
                                                        className={`min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-bold border transition-colors
                                                            ${numbering.mode === opt.value
                                                                ? 'bg-(--secondary) text-(--background-primary) border-(--secondary)'
                                                                : 'border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary)'}`}
                                                    >
                                                        {opt.label}
                                                    </button>
                                                ))}
                                            </div>
                                            {numbering.mode === 'auto' && !numbering.autoLive && (
                                                <button
                                                    type="button"
                                                    onClick={() => persist(renumberSorted(cards, numbering.sortLayers))}
                                                    className="flex items-center gap-1.5 min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-bold border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors"
                                                >
                                                    <FaArrowsRotate className="text-[12px]" /> Renumber Now
                                                </button>
                                            )}

                                            {numbering.mode !== 'none' && (
                                                <div className="relative shrink-0" ref={numberingSettingsRef}>
                                                    <button
                                                        type="button"
                                                        onClick={() => setShowNumberingSettings(v => !v)}
                                                        className="flex items-center justify-center w-9 h-9 rounded-lg border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors"
                                                        aria-label="Numbering settings"
                                                    >
                                                        <FaGear className="text-[15px]" />
                                                    </button>

                                                    {showNumberingSettings && (
                                                        <div className="absolute right-0 top-full mt-2 w-80 max-w-[calc(100vw-2rem)] p-3 bg-(--background-secondary) border border-(--divider) rounded-lg shadow-xl z-50 flex flex-col gap-4">
                                                            {numbering.mode === 'auto' && (
                                                                <>
                                                                    <div className="flex flex-col gap-2">
                                                                        <span className="text-[10px] font-bold text-(--text-tertiary) uppercase tracking-wide">
                                                                            Sort By (in order)
                                                                        </span>
                                                                        {numbering.sortLayers.map((layer, index) => (
                                                                            <div key={index} className="flex items-center gap-1.5">
                                                                                <span className="text-[11px] font-mono text-(--text-tertiary) w-3 shrink-0">{index + 1}</span>
                                                                                <select
                                                                                    value={layer.category}
                                                                                    onChange={e => updateSortLayer(index, { category: e.target.value as SortCategory })}
                                                                                    className="flex-1 min-w-0 min-h-9 text-[13px] bg-transparent border border-(--divider) rounded-lg px-2 py-2 text-(--text-primary) focus:outline-none focus:border-(--secondary)"
                                                                                >
                                                                                    {availableCategoriesFor(layer.category).map(opt => (
                                                                                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                                                    ))}
                                                                                </select>
                                                                                <button
                                                                                    type="button"
                                                                                    onClick={() => updateSortLayer(index, { direction: layer.direction === 'asc' ? 'desc' : 'asc' })}
                                                                                    title={layer.direction === 'asc' ? 'Ascending' : 'Descending'}
                                                                                    className="flex items-center justify-center w-9 h-9 rounded-lg border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors shrink-0"
                                                                                >
                                                                                    {layer.direction === 'asc' ? <FaArrowUp className="text-[13px]" /> : <FaArrowDown className="text-[13px]" />}
                                                                                </button>
                                                                                <button
                                                                                    type="button"
                                                                                    onClick={() => moveSortLayer(index, -1)}
                                                                                    disabled={index === 0}
                                                                                    className="flex items-center justify-center w-8 h-9 text-[13px] text-(--text-tertiary) hover:text-(--text-primary) disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
                                                                                >
                                                                                    ▲
                                                                                </button>
                                                                                <button
                                                                                    type="button"
                                                                                    onClick={() => moveSortLayer(index, 1)}
                                                                                    disabled={index === numbering.sortLayers.length - 1}
                                                                                    className="flex items-center justify-center w-8 h-9 text-[13px] text-(--text-tertiary) hover:text-(--text-primary) disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
                                                                                >
                                                                                    ▼
                                                                                </button>
                                                                                {numbering.sortLayers.length > 1 && (
                                                                                    <button
                                                                                        type="button"
                                                                                        onClick={() => removeSortLayer(index)}
                                                                                        className="flex items-center justify-center w-8 h-9 text-(--text-tertiary) hover:text-red-400 transition-colors shrink-0"
                                                                                    >
                                                                                        <FaXmark className="text-[13px]" />
                                                                                    </button>
                                                                                )}
                                                                            </div>
                                                                        ))}
                                                                        {numbering.sortLayers.length < SORT_CATEGORY_OPTIONS.length && (
                                                                            <button
                                                                                type="button"
                                                                                onClick={addSortLayer}
                                                                                className="flex items-center gap-1.5 min-h-9 px-2 text-[13px] font-semibold text-secondary hover:bg-(--background-quaternary) rounded-lg transition-colors self-start"
                                                                            >
                                                                                <FaPlus className="text-[11px]" /> Add sort level
                                                                            </button>
                                                                        )}
                                                                    </div>

                                                                    <FormEnabler
                                                                        label="Live"
                                                                        isEnabled={numbering.autoLive}
                                                                        onChange={autoLive => handleNumberingSettingChange({ autoLive })}
                                                                        className="min-h-10 text-[13px]"
                                                                    />
                                                                </>
                                                            )}

                                                            <FormEnabler
                                                                label="Zero-pad"
                                                                isEnabled={numbering.zeroPad}
                                                                onChange={zeroPad => persistNumberingSettings({ ...numbering, zeroPad: !zeroPad })}
                                                                className="min-h-10 text-[13px]"
                                                            />

                                                            <div className="flex flex-col gap-1">
                                                                <span className="text-[10px] font-bold text-(--text-tertiary) uppercase tracking-wide">Prefix</span>
                                                                <input
                                                                    type="text"
                                                                    value={numbering.prefix}
                                                                    onChange={e => handlePrefixInputChange(e.target.value)}
                                                                    onBlur={handlePrefixInputBlur}
                                                                    maxLength={3}
                                                                    placeholder="e.g. AS"
                                                                    className="w-24 min-h-9 text-[13px] font-mono uppercase bg-transparent border border-(--divider) rounded-lg px-2 py-1.5 text-(--text-primary) focus:outline-none focus:border-(--secondary)"
                                                                />
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Card Grid */}
                            <div className="flex-1 min-h-0 overflow-y-auto p-3">
                                {displayCards.length === 0 ? (
                                    <p className="text-[13px] text-(--text-tertiary) py-8 text-center">
                                        {previewResult
                                            ? 'No players matched this configuration.'
                                            : (readOnly ? 'No cards in this edition yet.' : 'No cards yet — use Manual search to build your pool.')}
                                    </p>
                                ) : (
                                    <div className="flex flex-col gap-4">
                                        {visibleGroups.map(group => (
                                            <div key={group.key} className="flex flex-col gap-2">
                                                {groupBy !== 'none' && (
                                                    <div className="flex items-center gap-2 border-t border-(--divider) pt-2">
                                                        <span className="text-[11px] font-bold text-(--text-secondary) uppercase tracking-wide">{group.label}</span>
                                                        <span className="text-[10px] text-(--text-tertiary) bg-(--background-secondary) py-0.5 px-1 rounded-md">
                                                            {poolGroups.find(g => g.key === group.key)?.cards.length}
                                                        </span>
                                                    </div>
                                                )}
                                                <div className={showFullCards ? 'grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-3' : 'grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-1.5'}>
                                                    {group.cards.map(card => {
                                                        const cardProps = {
                                                            card: card.card_snapshot,
                                                            onClick: () => setDetailCard(card.card_snapshot),
                                                        };
                                                        return (
                                                        <div key={card.id} className="group/row flex items-center gap-1.5">
                                                            {/* Set number with the remove button stacked beneath it, to save horizontal space. */}
                                                            <div className="flex flex-col items-end gap-1 shrink-0">
                                                                {!previewResult && numbering.mode === 'manual' && !readOnly ? (
                                                                    <div className="flex items-center gap-1 shrink-0">
                                                                        {numbering.prefix && (
                                                                            <span className="text-[13px] font-mono text-(--text-tertiary)">{numbering.prefix}</span>
                                                                        )}
                                                                        <input
                                                                            type="number"
                                                                            value={editingNumbers[card.id] ?? (card.card_number?.toString() ?? '')}
                                                                            onChange={e => handleNumberInputChange(card.id, e.target.value)}
                                                                            onBlur={() => handleNumberInputBlur(card.id)}
                                                                            placeholder="—"
                                                                            className="w-14 min-h-9 text-[13px] font-mono text-right bg-transparent border border-(--divider) rounded-lg px-2 py-1.5 text-(--text-primary) focus:outline-none focus:border-(--secondary)"
                                                                        />
                                                                    </div>
                                                                ) : (
                                                                    <span className="text-[13px] font-mono text-(--text-tertiary) w-7 text-right shrink-0">
                                                                        {formatCardNumber(card.card_number, displayCards.length, numbering.zeroPad, numbering.prefix)}
                                                                    </span>
                                                                )}
                                                                {!readOnly && !previewResult && (
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => handleRemoveCard(card.id)}
                                                                        title="Remove"
                                                                        aria-label="Remove"
                                                                        data-remove-button
                                                                        className="flex items-center justify-center w-5 h-5 rounded-full text-(--text-tertiary) hover:bg-red-500/90 hover:text-white transition-colors shrink-0 cursor-pointer"
                                                                    >
                                                                        <FaXmark className="text-[11px]" />
                                                                    </button>
                                                                )}
                                                            </div>
                                                            {/* Hovering the remove button outlines the card it removes. */}
                                                            <div className={`flex-1 min-w-0 transition-shadow group-has-[[data-remove-button]:hover]/row:ring-2 group-has-[[data-remove-button]:hover]/row:ring-red-500/80 ${showFullCards ? 'rounded-xl max-w-[400px]' : 'rounded-lg'}`}>
                                                                {showFullCards
                                                                    ? <CardItemFromCardDatabaseRecord {...cardProps} />
                                                                    : <CardItemCompactFromCardDatabaseRecord {...cardProps} />}
                                                            </div>
                                                        </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                {visibleCount < displayCards.length && (
                                    <div key={visibleCount} ref={poolSentinelRef} className="h-8" />
                                )}
                            </div>
                        </Tabs.Content>

                        {summaryMounted && (
                            <Tabs.Content
                                value="summary"
                                forceMount
                                className="flex-1 min-h-0 overflow-y-auto focus:outline-none data-[state=inactive]:hidden"
                            >
                                <SummaryCharts cards={displayCards} editionId={edition.id} />
                            </Tabs.Content>
                        )}
                    </Tabs.Root>
                </div>
            </div>

            {/* Player Pool card detail */}
            <div className={detailCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={() => setDetailCard(null)} isVisible={!!detailCard}>
                    <CardDetail
                        showdownBotCardData={detailCard?.card_data ? { card: detailCard.card_data } as ShowdownBotCardAPIResponse : undefined}
                        cardId={detailCard?.card_id}
                        hideTrendGraphs={true}
                        context="explore"
                        parent="modal"
                    />
                </Modal>
            </div>
        </div>
    );
}
