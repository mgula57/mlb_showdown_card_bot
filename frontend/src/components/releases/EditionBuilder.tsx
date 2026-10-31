import { useState, useMemo, useRef, useEffect, useCallback, memo, type ReactNode, type Ref } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import type { ReleaseEdition, ReleaseCard, AlgorithmPreviewResult, AlgorithmPreviewPlayer, ReleaseCardImageStatus, FoilSuggestion } from '../../api/releases';
import { updateEdition, patchEditionCards, rebuildEditionCard, customEditionCard, StaleEditionError } from '../../api/releases';
import { cardPatchesBetween, mergeCardPatches, type CardPatches } from './cardPatches';
import { SummaryCharts } from './SummaryCharts';
import { AlgorithmBuilder } from './AlgorithmBuilder';
import { parseAlgorithmSettings, allShowdownSets } from './algorithmSettings';
import ShowdownCardSearch from '../cards/ShowdownCardSearch';
import { CardSource } from '../../types/cardSource';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord, CardItemCompactSkeleton } from '../cards/CardItemCompact';
import { CardItemFromCardDatabaseRecord, CardItemSkeleton } from '../cards/CardItem';
import { CardDetail } from '../cards/CardDetail';
import { Modal } from '../shared/Modal';
import CustomSelect from '../shared/CustomSelect';
import { SetBadgeRow } from '../shared/SetBadge';
import type { ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import type { FilterSelections } from '../cards/ShowdownCardSearch';
import FormEnabler from '../customs/FormEnabler';
import CustomCardBuilder, { type CustomCardBuilderEmbed } from '../customs/CustomCardBuilder';
import { formSectionSummary } from '../customs/FormSectionSummary';
import { EditionStyleModal } from './EditionStyleModal';
import { EditionImages } from './EditionImages';
import { FOIL_TAG, ReleaseCardSuggestedTagChip, ReleaseCardTagChips, ReleaseCardTagsEditor } from './ReleaseCardTags';
import { FoilSuggestControl, FoilSuggestionBanner, POOL_TOOLBAR_POPOVER_CLASS } from './FoilSuggestions';
import { foilSuggestionTitle, useFoilSuggestions } from './useFoilSuggestions';
import { PoolPreviewBanner } from './PoolPreviewBanner';
import { ReleaseCardPreviewRankBadge, ReleaseCardPreviewRankPicker } from './ReleaseCardPreviewRank';
import { AlgorithmCutLineSummary, AlgorithmMatchBadge } from './AlgorithmMatch';
import { AlgorithmCutoff } from './AlgorithmCutoff';
import { useMediaQuery } from '../../hooks/useMediaQuery';
import { useStableCallback } from '../../hooks/useStableCallback';
import { useLiveImageMatches } from './useLiveImageMatches';
import { ImageLibrariesButton, ReleaseDriveNotice } from './ReleaseImageLibraries';
import { ConnectDriveButton } from '../account/ImageLibrarySettings';
import { useCopyReleaseLink } from './useCopyReleaseLink';
import { parseManualPicks, manualPickFor, withManualPick, type ManualPicks } from './manualPicks';
import { relativeTime } from '../../functions/formatters';
import { parseEditionStyle, editionStyleSummary, releaseCardStyle, releaseCardOverridesFor } from './editionStyle';
import type { CardStyleSettings } from '../customs/cardStyle';
import type { CardStyleEditorConfig } from '../cards/card_detail/CardStyleEditor';
import type { CardStyleOverrides } from '../cards/cardStyleOverrides';
import {
    groupAndSortCards, takeFromGroups, filterPoolCards, activePoolFilterCount, POOL_GROUP_OPTIONS, POOL_SORT_OPTIONS, POOL_SORT_DEFAULT_DIRECTION,
    type PoolGroupBy, type PoolSortBy, type PoolSortDirection, type PoolFilters,
} from './poolGrouping';
import { PoolFilterPanel } from './PoolFilterPanel';
import { ReleaseTip } from './ReleaseOnboarding';
import { TeamSearchInput } from '../team_builder/TeamSearchInput';
import { FaGripVertical } from 'react-icons/fa';
import { FaCheck, FaLink, FaPlus, FaXmark, FaSpinner, FaWandMagicSparkles, FaCircleCheck, FaMagnifyingGlass, FaArrowsRotate, FaGear, FaArrowUp, FaArrowDown, FaTriangleExclamation, FaTableCellsLarge, FaList, FaAnglesLeft, FaAnglesRight, FaListCheck, FaChartColumn, FaPalette, FaFilter, FaScissors, FaPenRuler } from 'react-icons/fa6';

import { InlineError } from '../shared/InlineError';
import { Plate } from '../shared/Plate';
import { CornerCount } from '../shared/CornerCount';
import { Heading } from '../shared/Heading';
import { headingClass } from '../shared/headingStyles';
import { buttonClass } from '../shared/buttonStyles';
import { choiceClass } from '../shared/choiceStyles';
import { FIELD_LABEL_CLASS, fieldClass } from '../shared/fieldStyles';
import { radixTabTriggerClass, tabListClass } from '../shared/tabStyles';
import { EmptyState } from '../shared/EmptyState';
/** Narrowest the Player Pool panel can get; it takes whatever the Build Method panel leaves. */
const MIN_POOL_PANEL_WIDTH = 280;
/** Narrowest the Build Method panel can be dragged to. */
const MIN_BUILD_PANEL_WIDTH = 320;
/** Default Build Method widths until the user drags the divider — the searches need a bit more room for results. */
const DEFAULT_BUILD_PANEL_WIDTH = { algorithm: 480, manual: 560, custom: 560 } as const;

type EditionBuilderProps = {
    releaseId: string;
    releaseName: string;
    edition: ReleaseEdition;
    readOnly: boolean;
    token?: string;
    defaultShowdownSet?: string | null;
    onEditionUpdated: (edition: ReleaseEdition) => void;
    /** The release-wide Review step (step 3). Owners only: leave `onReviewOpenChange` out when browsing. */
    reviewOpen?: boolean;
    onReviewOpenChange?: (open: boolean) => void;
    /** What step 3 shows; only passed to the edition on screen. */
    review?: ReactNode;
    /** Opens a step from outside (a Review fix link). A new object re-applies the same request. */
    navRequest?: EditionNavRequest | null;
    /** Reports whether an unapplied Algorithm run is showing, for the Review checklist. */
    onUnsavedPreviewChange?: (editionId: string, hasUnsavedPreview: boolean) => void;
    /** A card save found the edition changed elsewhere (another tab or device): reload it fresh. */
    onReloadRequested?: () => void;
    /** A card link's release card id to open on arrival; `onCardLinkOpened` fires once handled. */
    openCardRef?: string | null;
    onCardLinkOpened?: () => void;
    /** Slugs for a card's short link; null hides "Copy card link" (e.g. in a working copy, whose cards aren't live). */
    cardLinkSlugs?: { release: string; edition: string } | null;
};

export type EditionNavRequest = {
    step: 'pool' | 'images' | 'style';
    imageStatus?: ReleaseCardImageStatus | null;
};

const TAB_TRIGGER_CLASS = radixTabTriggerClass('sm');
/** The panels' tab strips: inset to line up with their content, never shrinking out of the column.
 * Chrome (the step bar, panel headers, tab strips, the pool toolbar) sits on the raised surface so
 * it reads apart from the build panel's page background and the card grid's darker tray. */
const CHROME_SURFACE_CLASS = 'bg-(--background-secondary)';
const TAB_LIST_CLASS = tabListClass(true, `px-3 shrink-0 ${CHROME_SURFACE_CLASS}`);

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
    mode: 'auto',
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
        mode: raw.mode === 'manual' || raw.mode === 'none' ? raw.mode : DEFAULT_NUMBERING.mode,
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

type NumberIssue = 'duplicate' | 'unnumbered';

type NumberingIssues = {
    /** Numbers held by more than one card (only possible in data saved before the uniqueness check). */
    duplicates: Set<number>;
    /** Missing numbers between 1 and the highest one, as the Review step counts them. */
    gaps: number[];
    unnumbered: number;
};

/** Mirrors the Review step's numbering checks (release_review.py `_numbering_items`), plus duplicates. */
function findNumberingIssues(cards: ReleaseCard[]): NumberingIssues {
    const counts = new Map<number, number>();
    for (const c of cards) {
        if (c.card_number !== null) counts.set(c.card_number, (counts.get(c.card_number) ?? 0) + 1);
    }
    const max = Math.max(0, ...counts.keys());
    const gaps: number[] = [];
    for (let n = 1; n <= max; n++) if (!counts.has(n)) gaps.push(n);
    return {
        duplicates: new Set([...counts].filter(([, count]) => count > 1).map(([num]) => num)),
        gaps,
        unnumbered: cards.filter(c => c.card_number === null).length,
    };
}

function numberIssueFor(card: ReleaseCard, issues: NumberingIssues | null): NumberIssue | undefined {
    if (!issues) return undefined;
    if (card.card_number === null) return 'unnumbered';
    return issues.duplicates.has(card.card_number) ? 'duplicate' : undefined;
}

/** "2 gaps: #14, #37 · 3 unnumbered", listing at most a few numbers per part. */
function numberingIssuesSummary(issues: NumberingIssues): string {
    const listed = (nums: number[]) => {
        const shown = nums.slice(0, 5).map(n => `#${n}`).join(', ');
        return nums.length > 5 ? `${shown} +${nums.length - 5} more` : shown;
    };
    const plural = (count: number, word: string) => `${count} ${word}${count === 1 ? '' : 's'}`;
    const duplicates = [...issues.duplicates].sort((a, b) => a - b);
    return [
        duplicates.length > 0 && `${plural(duplicates.length, 'duplicate')}: ${listed(duplicates)}`,
        issues.gaps.length > 0 && `${plural(issues.gaps.length, 'gap')}: ${listed(issues.gaps)}`,
        issues.unnumbered > 0 && `${issues.unnumbered} unnumbered`,
    ].filter(Boolean).join(' · ');
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
        tags: [],
        preview_rank: null,
        card_overrides: null,
    }));
}

/** Cards rendered per page in the Selected pool grid. */
const POOL_PAGE_SIZE = 40;
/** Per-viewer preference for full vs. compact card items in the pool grid. */
const POOL_FULL_CARDS_STORAGE_KEY = 'releaseBuilder.poolFullCards';
/** Per-viewer preference for hiding the Build Method panel. */
const BUILD_PANEL_HIDDEN_STORAGE_KEY = 'releaseBuilder.buildPanelHidden';
/** Labels the right panel as an unsaved Algorithm preview or the edition's saved pool. */
function PoolStatusBadge({ isPreview }: { isPreview: boolean }) {
    return isPreview ? (
        <Plate variant="custom" size="sm" className="bg-(--preview-accent)/12 text-(--preview-accent)">
            <FaWandMagicSparkles className="text-[9px]" /> Preview · Unsaved
        </Plate>
    ) : (
        <Plate variant="outline" size="sm">
            <FaCircleCheck className="text-[9px]" /> Saved
        </Plate>
    );
}

/** Per-viewer Build Method panel width, saved once they drag the divider. */
const BUILD_PANEL_WIDTH_STORAGE_KEY = 'releaseBuilder.buildPanelWidth';

type BuildMethod = 'algorithm' | 'manual' | 'custom';
const BUILD_METHODS: readonly BuildMethod[] = ['algorithm', 'manual', 'custom'];
type EditionStep = 'pool' | 'images';
/** Set once the owner dismisses the "connect Google Drive" notice. */
const DRIVE_NOTICE_DISMISSED_KEY = 'releaseBuilderDriveNoticeDismissed';
/** `build` only exists below md, where the Build Method panel moves from a side column into its own tab.
 * `cutoff` is owners only: it explains an Algorithm run, which browsers never see. */
type PoolTab = 'build' | 'cards' | 'summary' | 'cutoff';
/** Per-viewer, per-edition Algorithm/Manual/Customs tab, so returning to an edition reopens the last-used method. */
const buildMethodStorageKey = (editionId: string) => `releaseBuilder.buildMethod.${editionId}`;

function loadSavedBuildMethod(editionId: string): BuildMethod {
    try {
        const saved = localStorage.getItem(buildMethodStorageKey(editionId)) as BuildMethod | null;
        return saved && BUILD_METHODS.includes(saved) ? saved : 'algorithm';
    } catch {
        return 'algorithm';
    }
}

function loadSavedBuildPanelWidth(): number | null {
    try {
        const saved = Number(localStorage.getItem(BUILD_PANEL_WIDTH_STORAGE_KEY));
        return Number.isFinite(saved) && saved >= MIN_BUILD_PANEL_WIDTH ? saved : null;
    } catch {
        return null;
    }
}

/** The newest card list waiting to save, and every `persist` call it settles. `patches` holds
 *  just the changed fields while every queued edit was a patchable one; null means save it all. */
type PendingCardSave = {
    cards: ReleaseCard[];
    manualPicks?: ManualPicks;
    patches: CardPatches | null;
    waiters: ((saved: boolean) => void)[];
};

export function EditionBuilder({ releaseId, releaseName, edition, readOnly, token, defaultShowdownSet, onEditionUpdated, reviewOpen = false, onReviewOpenChange, review, navRequest, onUnsavedPreviewChange, onReloadRequested, openCardRef, onCardLinkOpened, cardLinkSlugs }: EditionBuilderProps) {
    const [cards, setCards] = useState<ReleaseCard[]>(edition.cards);
    // Latest cards, for saves that land after an await (e.g. a chart rebuild)
    const cardsRef = useRef(cards);
    cardsRef.current = cards;
    const [saving, setSaving] = useState(false);
    // Card list saves (see `persist`): the last state the server confirmed (what a failed save
    // reverts to, and the `cards_version` the next save is based on), the newest unsent state, and
    // whether a save is in flight
    const editionRef = useRef(edition);
    editionRef.current = edition;
    const confirmedRef = useRef<{ cards: ReleaseCard[]; manualPicks: ManualPicks; cardsVersion: number }>({
        cards: edition.cards, manualPicks: parseManualPicks(edition.attributes), cardsVersion: edition.cards_version,
    });
    /** A save was refused because the edition changed elsewhere, so only a reload can continue. */
    const [isStale, setIsStale] = useState(false);
    const pendingSaveRef = useRef<PendingCardSave | null>(null);
    const isSavingRef = useRef(false);
    const [error, setError] = useState<string | null>(null);
    const [previewResult, setPreviewResult] = useState<AlgorithmPreviewResult | null>(null);
    // The latest run's summary outlives saving its preview, so the Cutoff tab can still explain the saved picks
    const [lastRunSummary, setLastRunSummary] = useState<AlgorithmPreviewResult['summary'] | null>(null);
    const [isAlgorithmRunning, setIsAlgorithmRunning] = useState(false);
    const [algorithmEstimateSeconds, setAlgorithmEstimateSeconds] = useState<number | null>(null);
    const [numbering, setNumbering] = useState<NumberingSettings>(() => parseNumberingSettings(edition.attributes));
    const [manualPicks, setManualPicks] = useState<ManualPicks>(() => parseManualPicks(edition.attributes));
    const [editingNumbers, setEditingNumbers] = useState<Record<string, string>>({});
    const [showNumberingSettings, setShowNumberingSettings] = useState(false);
    const [showStyleModal, setShowStyleModal] = useState(false);
    const [isDriveNoticeDismissed, setIsDriveNoticeDismissed] = useState(() => {
        try { return localStorage.getItem(DRIVE_NOTICE_DISMISSED_KEY) === 'true'; } catch { return false; }
    });
    function dismissDriveNotice() {
        try { localStorage.setItem(DRIVE_NOTICE_DISMISSED_KEY, 'true'); } catch { /* storage unavailable */ }
        setIsDriveNoticeDismissed(true);
    }
    const [step, setStep] = useState<EditionStep>('pool');
    // Images mount lazily on first open, then stay mounted so a running render keeps polling
    const [imagesMounted, setImagesMounted] = useState(false);
    function handleOpenImagesStep() {
        setImagesMounted(true);
        setStep('images');
        onReviewOpenChange?.(false);
    }
    function handleOpenPoolStep() {
        setStep('pool');
        onReviewOpenChange?.(false);
    }
    const [imagesStatusRequest, setImagesStatusRequest] = useState<{ status: ReleaseCardImageStatus } | null>(null);
    const editionStyle = useMemo(() => parseEditionStyle(edition.attributes), [edition.attributes]);
    const styleSummary = useMemo(() => editionStyleSummary(editionStyle), [editionStyle]);
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
    const [buildMethod, setBuildMethod] = useState<BuildMethod>(() => loadSavedBuildMethod(edition.id));
    function handleBuildMethodChange(method: BuildMethod) {
        setBuildMethod(method);
        try { localStorage.setItem(buildMethodStorageKey(edition.id), method); } catch { /* storage unavailable */ }
    }
    const [buildPanelWidth, setBuildPanelWidth] = useState<number>(() => loadSavedBuildPanelWidth() ?? DEFAULT_BUILD_PANEL_WIDTH[buildMethod]);
    // Summary mounts lazily on first open, then stays mounted so its filters/WOTC comparison survive tab switches.
    const [summaryMounted, setSummaryMounted] = useState(false);
    const [poolTab, setPoolTab] = useState<PoolTab>('cards');
    const isDesktop = useMediaQuery('(min-width: 768px)');
    // The Build tab has nothing to show on desktop (the panel sits beside the pool) or when browsing
    const activePoolTab: PoolTab = (poolTab === 'build' && (isDesktop || readOnly)) || (poolTab === 'cutoff' && readOnly) ? 'cards' : poolTab;
    function handlePoolTabChange(tab: PoolTab) {
        setPoolTab(tab);
        if (tab === 'summary') setSummaryMounted(true);
    }
    const [detailCard, setDetailCard] = useState<ReleaseCard | null>(null);
    // A card link (`/r/<slug>/<edition>/<release card id>`) opens its card once
    function openCardFromLink(releaseCardId: string) {
        const card = cards.find(c => c.id === releaseCardId);
        if (card) {
            handleOpenPoolStep();
            setDetailCard(card);
        } else {
            setError("That card isn't in this edition any more. It may have been removed.");
        }
        onCardLinkOpened?.();
    }
    useEffect(() => {
        if (openCardRef) openCardFromLink(openCardRef);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [openCardRef]);
    const cardLink = useCopyReleaseLink(cardLinkSlugs?.release ?? '', cardLinkSlugs?.edition, detailCard?.id ?? null);
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

    // Pointer events (with capture on the handle) so dragging works with touch and pens as well as a mouse
    const handleResizeStart = (e: React.PointerEvent<HTMLDivElement>) => {
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        e.preventDefault();
        const handle = e.currentTarget;
        const pointerId = e.pointerId;
        handle.setPointerCapture(pointerId);
        isResizing.current = true;
        hasManuallyResized.current = true;
        const startX = e.clientX;
        // Start from the rendered width — the CSS max-width may have clamped the stored value on a narrow screen.
        const startWidth = buildPanelRef.current?.offsetWidth ?? buildPanelWidth;
        const maxWidth = Math.max((splitContainerRef.current?.clientWidth ?? 0) - MIN_POOL_PANEL_WIDTH, MIN_BUILD_PANEL_WIDTH);
        let latestWidth = startWidth;

        const onPointerMove = (ev: PointerEvent) => {
            if (!isResizing.current || ev.pointerId !== pointerId) return;
            latestWidth = Math.min(Math.max(startWidth + (ev.clientX - startX), MIN_BUILD_PANEL_WIDTH), maxWidth);
            setBuildPanelWidth(latestWidth);
        };
        const onPointerUp = (ev: PointerEvent) => {
            if (ev.pointerId !== pointerId) return;
            isResizing.current = false;
            try { localStorage.setItem(BUILD_PANEL_WIDTH_STORAGE_KEY, String(Math.round(latestWidth))); } catch { /* storage unavailable */ }
            if (handle.hasPointerCapture(pointerId)) handle.releasePointerCapture(pointerId);
            handle.removeEventListener('pointermove', onPointerMove);
            handle.removeEventListener('pointerup', onPointerUp);
            handle.removeEventListener('pointercancel', onPointerUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none';
        handle.addEventListener('pointermove', onPointerMove);
        handle.addEventListener('pointerup', onPointerUp);
        handle.addEventListener('pointercancel', onPointerUp);
    };

    // Manual search starts from the saved Algorithm settings' seasons, so manual adds (which become
    // inclusions) are cards the Algorithm can use. Games/IP minimums aren't applied: skipping them is
    // what an inclusion is for.
    const algorithmSettings = useMemo(() => parseAlgorithmSettings(edition.attributes, defaultShowdownSet), [edition.attributes, defaultShowdownSet]);
    // Keyed on content: every save returns a new edition, and new defaults would re-seed (and undo
    // the user clearing) the search's filters.
    const algorithmShowdownSetsKey = allShowdownSets(algorithmSettings).join(',');
    const algorithmAllStarsOnly = algorithmSettings.all_stars_only ?? false;
    const algorithmVariableSpeed = algorithmSettings.variable_speed ?? false;
    // Different sets for pitchers: hold each player type to its own sets, so a manual add is a card the Algorithm could pick
    const algorithmHitterSetsKey = algorithmSettings.showdown_sets.join(',');
    const algorithmPitcherSetsKey = algorithmSettings.pitcher_showdown_sets?.length ? algorithmSettings.pitcher_showdown_sets.join(',') : null;
    const manualSearchScope = useMemo(() => algorithmPitcherSetsKey ? {
        showdown_set_hitters: algorithmHitterSetsKey.split(','),
        showdown_set_pitchers: algorithmPitcherSetsKey.split(','),
    } : undefined, [algorithmHitterSetsKey, algorithmPitcherSetsKey]);
    // Manual adds match the Algorithm's speed mode, so the edition's 2000/2001 cards stay consistent
    const manualSearchDefaults = useMemo<Partial<FilterSelections>>(() => ({
        showdown_set: algorithmShowdownSetsKey ? algorithmShowdownSetsKey.split(',') : undefined,
        awards: algorithmAllStarsOnly ? ['AS'] : undefined,
        // Explicit false overrides the search's variable speed default
        variable_speed: algorithmVariableSpeed,
    }), [algorithmShowdownSetsKey, algorithmAllStarsOnly, algorithmVariableSpeed]);

    const excludeIds = useMemo(
        () => cards.map(c => c.source_card_id).filter((id): id is string => !!id),
        [cards]
    );

    /** Saves the edition's card list (optimistically), plus the Algorithm's manual picks when they
     * changed with it. Resolves false if the save failed.
     *
     * Saves run one at a time, so responses can't land out of order. Each sends the whole list, so
     * edits made while one is in flight coalesce into a single follow-up save of the newest state. */
    function persist(nextCards: ReleaseCard[], nextManualPicks?: ManualPicks): Promise<boolean> {
        if (!token) return Promise.resolve(false);
        // Numbers, tags, cover picks and style tweaks save as just those fields
        const patches = nextManualPicks ? null : cardPatchesBetween(cardsRef.current, nextCards);
        // Ahead of the re-render, so a second edit in the same tick diffs against this one
        cardsRef.current = nextCards;
        setCards(nextCards);
        if (nextManualPicks) setManualPicks(nextManualPicks);
        setError(null);
        return new Promise(resolve => {
            const queued = pendingSaveRef.current;
            pendingSaveRef.current = {
                cards: nextCards,
                manualPicks: nextManualPicks ?? queued?.manualPicks,
                patches: patches && (!queued ? patches : queued.patches && mergeCardPatches(queued.patches, patches)),
                waiters: [...(queued?.waiters ?? []), resolve],
            };
            if (!isSavingRef.current) drainSaves(token);
        });
    }

    async function drainSaves(token: string) {
        isSavingRef.current = true;
        setSaving(true);
        while (pendingSaveRef.current) {
            const save = pendingSaveRef.current;
            pendingSaveRef.current = null;
            try {
                if (save.patches) {
                    const cardsVersion = save.patches.size > 0
                        ? await patchEditionCards(releaseId, edition.id, [...save.patches.values()], confirmedRef.current.cardsVersion, token)
                        : confirmedRef.current.cardsVersion;
                    confirmedRef.current = { ...confirmedRef.current, cards: save.cards, cardsVersion };
                    // The edition's other fields may have saved since this save was queued, so build on the latest
                    onEditionUpdated({ ...editionRef.current, cards: save.cards, cards_version: cardsVersion });
                    save.waiters.forEach(resolve => resolve(true));
                    continue;
                }
                const updated = await updateEdition(releaseId, edition.id, {
                    cards: save.cards.map(c => ({
                        card_number: c.card_number,
                        source_card_id: c.source_card_id,
                        source_card_type: c.source_card_type,
                        card_snapshot: c.card_snapshot,
                        tags: c.tags,
                        preview_rank: c.preview_rank,
                        card_overrides: c.card_overrides,
                    })),
                    ...(save.manualPicks ? { attributes: { manual_picks: save.manualPicks } } : {}),
                    expected_cards_version: confirmedRef.current.cardsVersion,
                }, token);
                confirmedRef.current = {
                    cards: updated.cards,
                    manualPicks: save.manualPicks ?? confirmedRef.current.manualPicks,
                    cardsVersion: updated.cards_version,
                };
                onEditionUpdated(updated);
                // Newer edits are already on screen, and their save's response replaces this one
                if (!pendingSaveRef.current) setCards(updated.cards);
                save.waiters.forEach(resolve => resolve(true));
            } catch (err) {
                // Queued edits were made on top of the failed one, so they go with it. (A cast: TS
                // keeps the `= null` narrowing above across the await, but persist() may have queued more.)
                const dropped = (pendingSaveRef.current as PendingCardSave | null)?.waiters ?? [];
                pendingSaveRef.current = null;
                setCards(confirmedRef.current.cards);
                setManualPicks(confirmedRef.current.manualPicks);
                setError(err instanceof Error ? err.message : 'Failed to save changes.');
                if (err instanceof StaleEditionError) setIsStale(true);
                [...save.waiters, ...dropped].forEach(resolve => resolve(false));
            }
        }
        isSavingRef.current = false;
        setSaving(false);
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
    // Browsing (or previewing the published view) never shows an unsaved algorithm run.
    const activePreview = readOnly ? null : previewResult;
    const previewCards = useMemo(
        () => activePreview ? buildReleaseCardsFromPreview(activePreview.players) : null,
        [activePreview]
    );
    const liveImageMatches = useLiveImageMatches(releaseId, edition.id, previewCards ?? cards, token, !readOnly);

    const hasUnsavedPreview = !!activePreview;
    useEffect(() => {
        onUnsavedPreviewChange?.(edition.id, hasUnsavedPreview);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [edition.id, hasUnsavedPreview]);

    useEffect(() => {
        if (!navRequest) return;
        if (navRequest.step === 'style') {
            setShowStyleModal(true);
        } else if (navRequest.step === 'images') {
            handleOpenImagesStep();
            if (navRequest.imageStatus) setImagesStatusRequest({ status: navRequest.imageStatus });
        } else {
            handleOpenPoolStep();
            handlePoolTabChange('cards');
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [navRequest]);
    const displayCards = liveImageMatches.cards;

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

    // Filters only narrow what the grid shows — numbering, the Summary tab, and saves always use the full pool.
    const [poolFilters, setPoolFilters] = useState<PoolFilters>({});
    const [poolSearch, setPoolSearch] = useState('');
    const [showPoolFilters, setShowPoolFilters] = useState(false);
    const activeFilterCount = activePoolFilterCount(poolFilters);
    // The live image match control only shows while it affects the grid
    const isImageMatchActive = groupBy === 'image_match' || (poolFilters.image_match?.length ?? 0) > 0;
    // Match scores only show while sorting by them, so the grid stays quiet otherwise
    const isMatchSortActive = sortBy === 'match_score' || sortBy === 'match_margin';
    // Foil picks waiting to be applied, by source card id: saved cards not already tagged FOIL. Null
    // when none are showing (browsing, or an Algorithm preview is on screen instead).
    const foils = useFoilSuggestions(releaseId, edition.id, token);
    const pendingFoils = useMemo(() => {
        if (readOnly || activePreview || !foils.result) return null;
        const pending = new Map<string, FoilSuggestion>();
        for (const card of cards) {
            const suggestion = card.source_card_id ? foils.suggestions.get(card.source_card_id) : undefined;
            if (suggestion && !card.tags.includes(FOIL_TAG)) pending.set(suggestion.source_card_id, suggestion);
        }
        return pending;
    }, [readOnly, activePreview, foils.result, foils.suggestions, cards]);
    const showOnlyFoilSuggestions = !!pendingFoils && foils.onlySuggested;
    const filteredCards = useMemo(
        () => filterPoolCards(displayCards, poolFilters, poolSearch)
            .filter(card => !showOnlyFoilSuggestions || (!!card.source_card_id && !!pendingFoils?.has(card.source_card_id))),
        [displayCards, poolFilters, poolSearch, showOnlyFoilSuggestions, pendingFoils]
    );
    const isPoolFiltered = filteredCards.length !== displayCards.length;
    function clearPoolFilters() {
        setPoolFilters({});
        setPoolSearch('');
        foils.setOnlySuggested(false);
    }

    function handleApplyFoilSuggestions() {
        if (!pendingFoils) return;
        persist(cards.map(c => c.source_card_id && pendingFoils.has(c.source_card_id) ? { ...c, tags: [...c.tags, FOIL_TAG] } : c));
        foils.clear();
    }

    const poolGroups = useMemo(
        () => groupAndSortCards(filteredCards, groupBy, sortBy, sortDirection),
        [filteredCards, groupBy, sortBy, sortDirection]
    );
    const visibleGroups = useMemo(() => takeFromGroups(poolGroups, visibleCount), [poolGroups, visibleCount]);
    // Can exceed the pool size when a card sits in several groups (e.g. grouping by tag)
    const poolGroupedCardCount = useMemo(() => poolGroups.reduce((sum, g) => sum + g.cards.length, 0), [poolGroups]);
    useEffect(() => { setVisibleCount(POOL_PAGE_SIZE); }, [previewResult, groupBy, sortBy, sortDirection, poolFilters, poolSearch]);
    const poolSentinelRef = useCallback((node: HTMLDivElement | null) => {
        if (!node) return;
        const observer = new IntersectionObserver(entries => {
            if (entries[0]?.isIntersecting) setVisibleCount(n => n + POOL_PAGE_SIZE);
        }, { rootMargin: '400px' });
        observer.observe(node);
        return () => observer.disconnect();
    }, []);

    /** What each way of saving the preview would do to the saved pool — drives both the handlers
     * and the counts shown on the preview's save buttons. */
    const previewSavePlan = useMemo(() => {
        if (!previewCards || !activePreview) return null;
        // Fill: keeps every saved card, appends new preview players (deduped by source_card_id) up to the set size
        const existingSourceIds = new Set(cards.map(c => c.source_card_id).filter(Boolean));
        const remainingSlots = Math.max(0, activePreview.summary.requested_set_size - cards.length);
        const additions = previewCards.filter(c => !existingSourceIds.has(c.source_card_id)).slice(0, remainingSlots);
        // Replace: the pool becomes the preview; cards that survive keep their tags, preview rank, and overrides
        const existingCards = new Map(cards.map(c => [c.source_card_id, c]));
        const replacement = previewCards.map(c => {
            const existing = existingCards.get(c.source_card_id);
            return existing ? { ...c, tags: existing.tags, preview_rank: existing.preview_rank, card_overrides: existing.card_overrides } : c;
        });
        const newSourceIds = new Set(replacement.map(c => c.source_card_id));
        const droppedCount = cards.filter(c => !newSourceIds.has(c.source_card_id)).length;
        return { additions, replacement, droppedCount };
    }, [previewCards, activePreview, cards]);

    /** Non-destructive save: keeps every currently-persisted card and adds the plan's new players. */
    function handleFillRemainingSlots() {
        if (!previewSavePlan) return;
        persist(applyNumberingIfNeeded([...cards, ...previewSavePlan.additions]));
        setPreviewResult(null);
    }

    /** Destructive save: replaces the entire pool with the preview result. Warns if it would drop
     * any currently-persisted card (manual or from a prior algorithm run — provenance isn't tracked). */
    function handleReplaceAllFromPreview() {
        if (!previewSavePlan) return;
        const { replacement, droppedCount } = previewSavePlan;
        if (droppedCount > 0) {
            const confirmed = window.confirm(
                `Replacing will remove ${droppedCount} existing card${droppedCount === 1 ? '' : 's'} from the pool. Continue?`
            );
            if (!confirmed) return;
        }
        persist(applyNumberingIfNeeded(replacement));
        setPreviewResult(null);
    }

    /** `manualPicks` with the card's player-year moved into `list`. */
    function manualPicksWith(record: CardDatabaseRecord, list: keyof ManualPicks): ManualPicks {
        return withManualPick(manualPicks, manualPickFor(record), list);
    }

    /** Saves the Algorithm's manual picks on their own (e.g. edited from the Algorithm tab). */
    async function persistManualPicks(next: ManualPicks) {
        const previous = manualPicks;
        setManualPicks(next);
        if (!token) return;
        try {
            const updated = await updateEdition(releaseId, edition.id, { attributes: { manual_picks: next } }, token);
            confirmedRef.current = { ...confirmedRef.current, manualPicks: next };
            onEditionUpdated(updated);
        } catch (err: any) {
            setManualPicks(previous);
            setError(err.message ?? 'Failed to save manual picks.');
        }
    }

    /** Adds `snapshot` as the edition's next card. `manualPicks` are saved with it when given. */
    function addCardSnapshot(snapshot: CardDatabaseRecord, nextManualPicks?: ManualPicks) {
        const currentCards = cardsRef.current;
        const nextNumber = numbering.mode === 'manual'
            ? (currentCards.length > 0 ? Math.max(0, ...currentCards.map(c => c.card_number ?? 0)) + 1 : 1)
            : null;
        const newCard: ReleaseCard = {
            id: `pending-${snapshot.id}`,
            card_number: nextNumber,
            source_card_id: snapshot.id,
            source_card_type: snapshot.source,
            card_snapshot: snapshot,
            tags: [],
            preview_rank: null,
            card_overrides: null,
        };
        persist(applyNumberingIfNeeded([...currentCards, newCard]), nextManualPicks);
    }

    function handleAddCard(record: CardDatabaseRecord) {
        addCardSnapshot(record, manualPicksWith(record, 'included'));
    }

    /** A Card Builder custom (date range, multi-year...) has no archived card, so the backend builds
     * its snapshot from the card itself. It isn't a player-year, so it never touches manual picks. */
    async function addCustomCard(customCardId: string) {
        if (!token) return;
        addCardSnapshot(await customEditionCard(releaseId, edition.id, customCardId, token));
    }

    async function handleAddCustomCard(record: CardDatabaseRecord) {
        setError(null);
        try {
            await addCustomCard(record.id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to add custom card.');
        }
    }

    // The Card Builder, in a modal, for building a custom without leaving the edition. Closing it
    // remounts the Customs search so cards built (but not added) show up there.
    const [customBuilderOpen, setCustomBuilderOpen] = useState(false);
    const [customSearchKey, setCustomSearchKey] = useState(0);
    function closeCustomBuilder() {
        setCustomBuilderOpen(false);
        setCustomSearchKey(k => k + 1);
    }
    const customBuilderEmbed = useMemo<CustomCardBuilderEmbed>(() => ({
        showdownSet: algorithmShowdownSetsKey ? algorithmShowdownSetsKey.split(',')[0] : defaultShowdownSet,
        actionLabel: 'Add to Edition',
        completedIds: excludeIds,
        onAction: addCustomCard,
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }), [algorithmShowdownSetsKey, defaultShowdownSet, excludeIds, numbering, token]);

    /** Removing a card also excludes that player-year from future Algorithm runs (not a custom card,
     * which isn't one). In a preview, it just drops the card from the (unsaved) preview. */
    function handleRemoveCard(card: ReleaseCard) {
        const nextManualPicks = card.source_card_type === CardSource.CUSTOM ? undefined : manualPicksWith(card.card_snapshot, 'excluded');
        if (activePreview) {
            setPreviewResult(prev => {
                if (!prev) return prev;
                const players = prev.players.filter(p => p.id !== card.source_card_id);
                return { ...prev, players, summary: { ...prev.summary, actual_count: players.length } };
            });
            if (nextManualPicks) persistManualPicks(nextManualPicks);
            return;
        }
        persist(applyNumberingIfNeeded(cards.filter(c => c.id !== card.id)), nextManualPicks);
    }

    // Saves replace every card row (new ids), so the open detail card is matched by its source card.
    const detailCardCurrent = detailCard
        ? (cards.find(c => c.source_card_id === detailCard.source_card_id) ?? detailCard)
        : null;
    const detailCardTags = detailCardCurrent?.tags ?? [];
    const detailCardPreviewRank = detailCardCurrent?.preview_rank ?? null;
    const editionTags = useMemo(() => [...new Set(cards.flatMap(c => c.tags))].sort(), [cards]);

    // The detail modal renders the release card as it will print: edition style (plus the card's
    // own overrides) + formatted set number. BOT snapshots don't embed card_data, so CardDetail
    // hydrates those by card_id. Keyed on the overrides' content: every save returns fresh card
    // objects, and a new style object would regenerate the image.
    const detailCardOverridesKey = JSON.stringify(detailCardCurrent?.card_overrides?.style ?? null);
    const detailCardStyle = useMemo<CardStyleSettings>(
        () => releaseCardStyle(editionStyle, detailCardCurrent?.card_overrides),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [editionStyle, detailCardOverridesKey]
    );
    /** The set number as it prints on the card, or null when the edition isn't numbered. */
    function printedSetNumber(card: ReleaseCard): string | null {
        return numbering.mode === 'none' || card.card_number === null
            ? null
            : formatCardNumber(card.card_number, displayCards.length, numbering.zeroPad, numbering.prefix);
    }
    const detailStyleOverrides = useMemo<CardStyleOverrides | undefined>(
        () => detailCard ? { style: detailCardStyle, setNumber: printedSetNumber(detailCard) } : undefined,
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [detailCard, detailCardStyle, numbering, displayCards.length]
    );

    // Per-card style edits, saved as overrides on top of the edition style. Not while browsing or
    // viewing an unsaved algorithm preview (same as tags).
    const detailStyleEditor = useMemo<CardStyleEditorConfig | undefined>(() => {
        if (!detailCard || readOnly || activePreview) return undefined;
        const sourceCardId = detailCard.source_card_id;
        return {
            style: detailCardStyle,
            defaults: editionStyle,
            revertTitle: 'Revert to the edition style',
            onSave: async (style) => {
                const card_overrides = releaseCardOverridesFor(style, editionStyle);
                const saved = await persist(cards.map(c => c.source_card_id === sourceCardId ? { ...c, card_overrides } : c));
                if (!saved) throw new Error('Failed to save card style.');
            },
            // A new chart version replaces the card's snapshot (command, outs, points...), so it
            // re-numbers under live auto numbering
            chart: detailCard.source_card_type === CardSource.BOT && sourceCardId && token ? {
                onChange: async (chartVersion) => {
                    const card_snapshot = await rebuildEditionCard(releaseId, edition.id, sourceCardId, chartVersion, token);
                    const nextCards = applyNumberingIfNeeded(cardsRef.current.map(c => c.source_card_id === sourceCardId ? { ...c, card_snapshot } : c));
                    const saved = await persist(nextCards);
                    if (!saved) throw new Error('Failed to save the rebuilt card.');
                    const rebuiltCard = nextCards.find(c => c.source_card_id === sourceCardId);
                    setDetailCard(prev => prev?.source_card_id === sourceCardId && rebuiltCard ? rebuiltCard : prev);
                },
            } : undefined,
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [detailCard, readOnly, activePreview, detailCardStyle, editionStyle, cards, numbering, token]);

    function handleDetailCardTagsChange(tags: string[]) {
        if (!detailCard) return;
        persist(cards.map(c => c.source_card_id === detailCard.source_card_id ? { ...c, tags } : c));
    }

    /** Each slot belongs to one card per edition, so taking one clears it from whichever card held it. */
    function handlePreviewRankChange(sourceCardId: string | null, previewRank: number | null) {
        persist(cards.map(c => {
            if (c.source_card_id === sourceCardId) return { ...c, preview_rank: previewRank };
            return previewRank !== null && c.preview_rank === previewRank ? { ...c, preview_rank: null } : c;
        }));
    }
    const previewRanks = useMemo(
        () => new Map(cards.flatMap(c => c.source_card_id && c.preview_rank ? [[c.source_card_id, c.preview_rank] as const] : [])),
        [cards]
    );

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
        // Numbers are unique per edition; the server would refuse the whole save
        const holder = parsed !== null && cards.find(c => c.id !== cardId && c.card_number === parsed);
        if (holder) {
            setError(`#${parsed} is already ${holder.card_snapshot.name}'s number. Clear that card's number first.`);
            return;
        }
        persist(cards.map(c => c.id === cardId ? { ...c, card_number: parsed } : c));
    }

    // Stable identities so memoized pool rows only re-render when their own card changes
    const handleRemoveCardStable = useStableCallback(handleRemoveCard);
    const handleNumberInputChangeStable = useStableCallback(handleNumberInputChange);
    const handleNumberInputBlurStable = useStableCallback(handleNumberInputBlur);
    const handleSkipFoilSuggestionStable = useStableCallback(foils.skip);
    const isManualNumberingEditable = !activePreview && numbering.mode === 'manual' && !readOnly;
    // Flagged in the pool as you edit, so problems don't wait for the Review step. Null when there's nothing to flag.
    const numberingIssues = useMemo(() => {
        if (readOnly || activePreview || numbering.mode === 'none') return null;
        const issues = findNumberingIssues(cards);
        return issues.duplicates.size > 0 || issues.gaps.length > 0 || issues.unnumbered > 0 ? issues : null;
    }, [cards, readOnly, activePreview, numbering.mode]);

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
                attributes: { numbering: next },
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

    /** On phones the Build panel is its own tab, so jump to the pool once a run produces results. */
    function handlePreviewResult(result: AlgorithmPreviewResult | null) {
        setPreviewResult(result);
        if (result) {
            setLastRunSummary(result.summary);
            setPoolTab(tab => tab === 'build' ? 'cards' : tab);
        }
    }

    /** A discarded run no longer explains anything in the pool, so its cutoff goes with it. */
    function handleDiscardPreview() {
        setPreviewResult(null);
        setLastRunSummary(null);
    }

    const cutoffSummary = activePreview?.summary ?? lastRunSummary;
    const poolSourceIds = useMemo(() => new Set(displayCards.map(c => c.source_card_id).filter((id): id is string => !!id)), [displayCards]);
    function handleOpenCutoffPick(sourceCardId: string) {
        const card = displayCards.find(c => c.source_card_id === sourceCardId);
        if (card) setDetailCard(card);
    }

    // First-build tour anchors (see ReleaseOnboarding)
    const [buildMethodTabs, setBuildMethodTabs] = useState<HTMLDivElement | null>(null);
    const [buildPanelRail, setBuildPanelRail] = useState<HTMLButtonElement | null>(null);
    const [phoneBuildTab, setPhoneBuildTab] = useState<HTMLButtonElement | null>(null);
    const [previewSaveActions, setPreviewSaveActions] = useState<HTMLDivElement | null>(null);
    const [styleButton, setStyleButton] = useState<HTMLButtonElement | null>(null);
    const [imagesStepButton, setImagesStepButton] = useState<HTMLButtonElement | null>(null);
    const buildMethodAnchor = isDesktop
        ? (buildPanelHidden ? buildPanelRail : buildMethodTabs)
        : (activePoolTab === 'build' ? buildMethodTabs : phoneBuildTab);

    // Shared by the desktop pool tab strip and the phone strip (which adds Build in front)
    const poolTabTriggers = (
        <>
            <Tabs.Trigger value="cards" className={TAB_TRIGGER_CLASS}>
                {activePreview ? <FaWandMagicSparkles className="text-[10px] text-(--preview-accent)" /> : <FaListCheck className="text-[10px]" />}
                {readOnly ? 'List' : activePreview ? 'Preview' : 'Selected'}
                <Plate variant={activePreview ? 'custom' : 'ink'} size="sm" className={activePreview ? 'bg-(--preview-accent)/12 text-(--preview-accent)' : ''}>{displayCards.length}</Plate>
            </Tabs.Trigger>
            <Tabs.Trigger value="summary" className={TAB_TRIGGER_CLASS}>
                <FaChartColumn className="text-[10px]" /> Summary
            </Tabs.Trigger>
            {!readOnly && (
                <Tabs.Trigger value="cutoff" className={TAB_TRIGGER_CLASS}>
                    <FaScissors className="text-[10px]" /> Cutoff
                </Tabs.Trigger>
            )}
        </>
    );

    return (
        <div className="flex flex-col flex-1 min-h-0">
            {/* Step indicator */}
            <div className={`flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3 border-b border-(--divider) shrink-0 ${CHROME_SURFACE_CLASS}`}>
                {/* Numbered as a workflow while editing; plain views while browsing */}
                <StepButton number={readOnly ? undefined : 1} label={readOnly ? 'Cards' : 'Player Pool'} mobileLabel={readOnly ? undefined : 'Pool'} isActive={!reviewOpen && step === 'pool'} onClick={handleOpenPoolStep} />
                <div className={`${readOnly ? 'w-3' : 'w-4 sm:w-8'} h-px bg-(--divider) shrink-0`} />
                <StepButton ref={setImagesStepButton} number={readOnly ? undefined : 2} label="Images" isActive={!reviewOpen && step === 'images'} onClick={handleOpenImagesStep} />
                {onReviewOpenChange && (
                    <>
                        <div className="w-4 sm:w-8 h-px bg-(--divider) shrink-0" />
                        <StepButton number={3} label="Review" isActive={reviewOpen} onClick={() => onReviewOpenChange(true)} />
                    </>
                )}

                {!readOnly && (
                    <div className="flex items-center gap-2 ml-auto">
                        <ImageLibrariesButton onClose={liveImageMatches.refresh} tipMoment={!reviewOpen && step === 'images' && cards.length > 0} />
                        <button
                            ref={setStyleButton}
                            type="button"
                            onClick={() => setShowStyleModal(true)}
                            title="Default card style for this edition"
                            className={buttonClass('secondary', 'sm', 'min-h-5')}
                        >
                            <FaPalette className="text-[12px] shrink-0" />
                            <span><span className="hidden sm:inline">Card </span>Style</span>
                            <span className="hidden sm:contents">{formSectionSummary(styleSummary)}</span>
                        </button>
                    </div>
                )}

                {saving && (
                    <span className={`${readOnly ? 'ml-auto' : ''} flex items-center gap-1 text-[11px] text-(--text-tertiary)`}>
                        <FaSpinner className="animate-spin text-[10px]" /> Saving…
                    </span>
                )}
            </div>

            <ReleaseTip id="buildMethod" show={cards.length === 0 && !activePreview && !isAlgorithmRunning} anchor={buildMethodAnchor} placement={isDesktop ? 'right-start' : 'bottom-start'} />
            <ReleaseTip id="savePreview" show={!!activePreview && !isAlgorithmRunning} anchor={previewSaveActions} placement="bottom-start" />
            <ReleaseTip id="cardStyle" show={cards.length > 0 && !showStyleModal} anchor={styleButton} placement="bottom-end" />
            <ReleaseTip id="imagesStep" show={cards.length > 0 && step === 'pool'} anchor={imagesStepButton} placement="bottom-start" />

            {!readOnly && !isDriveNoticeDismissed && (
                <ReleaseDriveNotice
                    className="mx-4 mt-2 shrink-0"
                    action={<ConnectDriveButton size="sm" />}
                    onDismiss={dismissDriveNotice}
                />
            )}

            {error && (
                <InlineError size="md" className="mx-4 mt-2 shrink-0">
                    <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
                        {error}
                        {isStale && onReloadRequested && (
                            <button type="button" onClick={onReloadRequested} className={buttonClass('secondary', 'sm')}>
                                <FaArrowsRotate className="text-[10px]" /> Reload edition
                            </button>
                        )}
                    </span>
                </InlineError>
            )}

            {/* Images step: mounts on first open, then stays mounted (hidden) so a running render keeps reporting */}
            {/* Review step: release-wide, so its content comes from ReleaseDetail */}
            {reviewOpen && review}

            {imagesMounted && (
                <div className={`flex-col flex-1 min-h-0 ${!reviewOpen && step === 'images' ? 'flex' : 'hidden'}`}>
                    <EditionImages
                        releaseId={releaseId}
                        releaseName={releaseName}
                        edition={edition}
                        readOnly={readOnly}
                        token={token}
                        previewRanks={previewRanks}
                        onPreviewRankChange={handlePreviewRankChange}
                        statusFilterRequest={imagesStatusRequest}
                    />
                </div>
            )}

            {/* Player Pool step. Hidden (not unmounted) so the build panel's state survives step switches.
                One Tabs.Root spans the split so the phone-only tab strip can also switch to the Build panel. */}
            <Tabs.Root
                value={activePoolTab}
                onValueChange={value => handlePoolTabChange(value as PoolTab)}
                className={`flex-col flex-1 min-h-0 ${!reviewOpen && step === 'pool' ? 'flex' : 'hidden'}`}
            >
            {!readOnly && (
                <Tabs.List className={`md:hidden ${TAB_LIST_CLASS}`}>
                    <Tabs.Trigger ref={setPhoneBuildTab} value="build" className={TAB_TRIGGER_CLASS}>
                        <FaWandMagicSparkles className="text-[10px]" /> Build
                    </Tabs.Trigger>
                    {poolTabTriggers}
                </Tabs.List>
            )}
            <div ref={splitContainerRef} className="flex flex-1 min-h-0">
                {/* Collapsed rail for the hidden Build panel */}
                {!readOnly && buildPanelHidden && (
                    <button
                        ref={setBuildPanelRail}
                        type="button"
                        onClick={toggleBuildPanelHidden}
                        title="Show build method"
                        className="hidden md:flex flex-col items-center gap-3 w-9 shrink-0 py-3 border-r border-(--divider) text-(--text-tertiary) hover:text-(--text-primary) hover:bg-(--background-secondary) transition-colors cursor-pointer"
                    >
                        <FaAnglesRight className="text-[12px]" />
                        <span className={`${FIELD_LABEL_CLASS} text-inherit! [writing-mode:vertical-rl]`}>Build Method</span>
                    </button>
                )}

                {/* Build panel: Algorithm / Manual. Hidden (not unmounted) when collapsed so its state survives. */}
                {!readOnly && (
                    <div
                        ref={buildPanelRef}
                        style={{
                            '--build-panel-width': `${buildPanelWidth}px`,
                            '--build-panel-max-width': `calc(100% - ${MIN_POOL_PANEL_WIDTH}px)`,
                        } as React.CSSProperties}
                        // Phones: full width, shown only on the Build tab. Desktop: the resizable side column.
                        className={`flex-1 min-w-0 flex-col min-h-0 ${activePoolTab === 'build' ? 'flex' : 'hidden'}
                            md:flex-none md:shrink-0 md:w-(--build-panel-width) md:max-w-(--build-panel-max-width) md:border-r md:border-(--divider)
                            ${buildPanelHidden ? 'md:hidden' : 'md:flex'}`}
                    >
                        <div className={`px-3 pt-2 pb-1 shrink-0 flex items-center justify-between gap-2 ${CHROME_SURFACE_CLASS}`}>
                            <div className="flex items-center gap-1.5">
                                <button
                                    type="button"
                                    onClick={toggleBuildPanelHidden}
                                    title="Hide build method"
                                    className="hidden md:flex items-center justify-center w-5 h-5 rounded-control text-(--text-tertiary) hover:text-(--text-primary) hover:bg-(--divider) transition-colors cursor-pointer"
                                >
                                    <FaAnglesLeft className="text-[11px]" />
                                </button>
                                <span className={FIELD_LABEL_CLASS}>Build Method</span>
                            </div>
                        </div>
                        <Tabs.Root
                            value={buildMethod}
                            onValueChange={v => handleBuildMethodChange(v as BuildMethod)}
                            className="flex flex-col flex-1 min-h-0"
                        >
                            <Tabs.List ref={setBuildMethodTabs} className={TAB_LIST_CLASS}>
                                <Tabs.Trigger value="algorithm" className={TAB_TRIGGER_CLASS}>
                                    <FaWandMagicSparkles className="text-[10px]" /> Algorithm
                                </Tabs.Trigger>
                                <Tabs.Trigger value="manual" className={TAB_TRIGGER_CLASS}>
                                    <FaMagnifyingGlass className="text-[10px]" /> Manual
                                </Tabs.Trigger>
                                <Tabs.Trigger value="custom" className={TAB_TRIGGER_CLASS}>
                                    <FaPenRuler className="text-[10px]" /> Customs
                                </Tabs.Trigger>
                            </Tabs.List>
                            <Tabs.Content value="algorithm" className="flex-1 min-h-0 flex flex-col focus:outline-none">
                                <AlgorithmBuilder
                                    releaseId={releaseId}
                                    edition={edition}
                                    token={token}
                                    defaultShowdownSet={defaultShowdownSet}
                                    manualPicks={manualPicks}
                                    onManualPicksChange={persistManualPicks}
                                    onPreviewResult={handlePreviewResult}
                                    onRunningChange={(running, estimatedSeconds) => { setIsAlgorithmRunning(running); setAlgorithmEstimateSeconds(estimatedSeconds ?? null); }}
                                    onEditionUpdated={onEditionUpdated}
                                />
                            </Tabs.Content>
                            <Tabs.Content value="manual" className="flex-1 min-h-0 flex flex-col focus:outline-none">
                                <ShowdownCardSearch
                                    source={CardSource.BOT}
                                    compact={true}
                                    excludeIds={excludeIds}
                                    defaultFilters={manualSearchDefaults}
                                    scopeFilters={manualSearchScope}
                                    defaultYears={algorithmSettings.years}
                                    enableVariableSpeedToggle
                                    actionButton={{
                                        icon: <FaPlus />,
                                        label: 'Add',
                                        detailLabel: 'Add to Edition',
                                        emphasis: 'primary',
                                        onClick: handleAddCard,
                                    }}
                                />
                            </Tabs.Content>
                            <Tabs.Content value="custom" className="flex-1 min-h-0 flex flex-col focus:outline-none">
                                <div className={`flex items-center gap-3 px-3 py-2 border-b border-(--divider) ${CHROME_SURFACE_CLASS}`}>
                                    <p className="flex-1 text-[12px] leading-snug text-(--text-tertiary)">
                                        Cards you made in the Card Builder: date ranges, multi-year, splits and more.
                                    </p>
                                    <button type="button" onClick={() => setCustomBuilderOpen(true)} className={buttonClass('secondary', 'sm')}>
                                        <FaPlus className="text-[10px]" /> Build New
                                    </button>
                                </div>
                                <ShowdownCardSearch
                                    key={customSearchKey}
                                    source={CardSource.CUSTOM}
                                    compact={true}
                                    excludeIds={excludeIds}
                                    actionButton={{
                                        icon: <FaPlus />,
                                        label: 'Add',
                                        detailLabel: 'Add to Edition',
                                        emphasis: 'primary',
                                        onClick: handleAddCustomCard,
                                    }}
                                />
                            </Tabs.Content>
                        </Tabs.Root>
                    </div>
                )}

                {/* Drag-to-resize handle. `touch-none` keeps a touch drag from scrolling the page; the
                    invisible strip widens the hit area for fingers beyond the thin visible bar. */}
                {!readOnly && !buildPanelHidden && (
                    <div
                        onPointerDown={handleResizeStart}
                        className="relative z-10 w-1.5 shrink-0 -translate-x-0.5 cursor-ew-resize touch-none select-none hidden md:flex items-center justify-center group hover:bg-(--divider) transition-colors"
                    >
                        <div aria-hidden className="absolute inset-y-0 -left-2.5 -right-2.5" />
                        {/* Touch screens get a bigger, bordered grip — it's the only cue the bar drags, and a finger covers it */}
                        <FaGripVertical className="absolute text-[14px] text-(--text-tertiary) group-hover:text-(--text-secondary) transition-colors bg-(--background-primary) rounded-control px-0.5
                            pointer-coarse:text-[22px] pointer-coarse:py-1 pointer-coarse:border pointer-coarse:border-(--divider) pointer-coarse:text-(--text-secondary)" />
                    </div>
                )}

                {/* Selected Cards / Summary — takes whatever width the Build panel leaves. */}
                <div className={`flex-1 min-w-0 flex-col min-h-0 ${activePoolTab === 'build' ? 'hidden md:flex' : 'flex'}`}>
                    {!readOnly && (
                        <div className={`hidden md:flex items-center gap-2 px-3 pt-2 shrink-0 ${CHROME_SURFACE_CLASS}`}>
                            <span className={FIELD_LABEL_CLASS}>Player Pool</span>
                            <PoolStatusBadge isPreview={!!activePreview} />
                        </div>
                    )}
                    <div className="flex flex-col flex-1 min-h-0">
                        {/* Phones get the strip above the split instead (it includes Build) — except when browsing */}
                        <Tabs.List className={`${readOnly ? '' : 'hidden! md:flex!'} ${TAB_LIST_CLASS}`}>
                            {poolTabTriggers}
                            <SetBadgeRow
                                sets={displayCards.map(c => c.card_snapshot.showdown_set)}
                                size="md"
                                className="hidden sm:flex items-center gap-1 ml-auto shrink-0"
                            />
                        </Tabs.List>

                        <Tabs.Content value="cards" className="flex-1 min-h-0 flex flex-col focus:outline-none">
                            {isAlgorithmRunning && <AlgorithmRunningBanner estimatedSeconds={algorithmEstimateSeconds} />}
                            {activePreview && !isAlgorithmRunning && (
                                <PoolPreviewBanner
                                    title={`Algorithm Preview — ${activePreview.summary.actual_count} player${activePreview.summary.actual_count === 1 ? '' : 's'}`}
                                    description={cards.length === 0
                                        ? 'Not saved yet. Save it as this edition\'s pool, or discard it.'
                                        : `Not saved yet. Your saved pool has ${cards.length} card${cards.length === 1 ? '' : 's'} — choose how the preview should change it.`}
                                >
                                    {activePreview.summary.warnings.length > 0 && (
                                        <div className="flex flex-col gap-1">
                                            {activePreview.summary.warnings.map((warning, i) => (
                                                <div key={i} className="flex items-center gap-1.5 text-[11px] text-(--gold)">
                                                    <FaTriangleExclamation className="shrink-0" /> {warning}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    <AlgorithmCutLineSummary cutLines={activePreview.summary.cut_lines ?? []} />
                                    {previewSavePlan && cards.length > 0 && (
                                        <ul className="flex flex-col gap-0.5 text-[11px] text-(--text-secondary)">
                                            <li>
                                                <span className="font-semibold text-(--text-primary)">Add to saved</span> — keeps all {cards.length} saved, adds {previewSavePlan.additions.length} new player{previewSavePlan.additions.length === 1 ? '' : 's'} from the preview{previewSavePlan.additions.length === 0 ? ' (pool is already full or has them all)' : ''}.
                                            </li>
                                            <li>
                                                <span className="font-semibold text-(--text-primary)">Replace saved</span> — pool becomes these {previewSavePlan.replacement.length}{previewSavePlan.droppedCount > 0 ? `, removing ${previewSavePlan.droppedCount} saved card${previewSavePlan.droppedCount === 1 ? '' : 's'}` : ''}.
                                            </li>
                                        </ul>
                                    )}
                                    <div ref={setPreviewSaveActions} className="flex flex-wrap gap-2">
                                        {cards.length === 0 ? (
                                            <button
                                                type="button"
                                                onClick={handleReplaceAllFromPreview}
                                                className={buttonClass('primary', 'sm')}
                                            >
                                                Save {previewSavePlan?.replacement.length ?? 0} card{previewSavePlan?.replacement.length === 1 ? '' : 's'}
                                            </button>
                                        ) : (
                                            <>
                                                <button
                                                    type="button"
                                                    onClick={handleFillRemainingSlots}
                                                    disabled={!previewSavePlan?.additions.length}
                                                    className={buttonClass('primary', 'sm')}
                                                >
                                                    Add {previewSavePlan?.additions.length ?? 0} to saved
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={handleReplaceAllFromPreview}
                                                    className={buttonClass('secondary', 'sm')}
                                                >
                                                    Replace saved
                                                </button>
                                            </>
                                        )}
                                        <button
                                            type="button"
                                            onClick={handleDiscardPreview}
                                            className={buttonClass('ghost', 'sm')}
                                        >
                                            Discard preview
                                        </button>
                                    </div>
                                </PoolPreviewBanner>
                            )}
                            {pendingFoils && (
                                <FoilSuggestionBanner foils={foils} count={pendingFoils.size} onApply={handleApplyFoilSuggestions} />
                            )}
                            {((!readOnly && !activePreview) || displayCards.length > 0) && (
                                // Sized by the pool panel (which resizes), not the window: one row when it's wide,
                                // else view controls over edition tools, each row left-aligned. The container is its
                                // own stacking context, so z-20 keeps its popovers over the grid's tags and headers.
                                <div className={`@container relative z-20 px-3 py-2 border-b border-(--divider) shrink-0 ${CHROME_SURFACE_CLASS}`}>
                                    <div className="flex flex-col gap-2 @7xl:flex-row @7xl:items-center">
                                        {displayCards.length > 0 && (
                                            <div className="flex flex-wrap items-center gap-2 @7xl:flex-1 @7xl:min-w-0">
                                                <CustomSelect
                                                    size="sm"
                                                    prefix="Group"
                                                    options={POOL_GROUP_OPTIONS}
                                                    value={groupBy}
                                                    onChange={value => setGroupBy(value as PoolGroupBy)}
                                                />
                                                <CustomSelect
                                                    size="sm"
                                                    prefix="Sort"
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
                                                    className="flex items-center justify-center w-9 h-9 rounded-control border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors shrink-0 cursor-pointer"
                                                >
                                                    {sortDirection === 'asc' ? <FaArrowUp className="text-[13px]" /> : <FaArrowDown className="text-[13px]" />}
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => setShowPoolFilters(v => !v)}
                                                    title={showPoolFilters ? 'Hide filters' : 'Show filters'}
                                                    className={`relative flex items-center justify-center w-9 h-9 rounded-control border transition-colors shrink-0 cursor-pointer
                                                        ${showPoolFilters || activeFilterCount > 0
                                                            ? 'border-(--showdown-blue) ring-1 ring-(--showdown-blue) text-(--text-primary)'
                                                            : 'border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary)'}`}
                                                >
                                                    <FaFilter className="text-[13px]" />
                                                    <CornerCount count={activeFilterCount} />
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={toggleShowFullCards}
                                                    title={showFullCards ? 'Show compact cards' : 'Show full cards'}
                                                    className="flex items-center justify-center w-9 h-9 rounded-control border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors shrink-0 cursor-pointer"
                                                >
                                                    {showFullCards ? <FaList className="text-[13px]" /> : <FaTableCellsLarge className="text-[13px]" />}
                                                </button>
                                                <TeamSearchInput
                                                    value={poolSearch}
                                                    onChange={setPoolSearch}
                                                    placeholder="Search players…"
                                                    className="grow basis-48 min-w-0"
                                                />
                                                {isPoolFiltered && (
                                                    <span className="flex items-center gap-1.5 text-[12px] text-(--text-tertiary)">
                                                        {filteredCards.length} of {displayCards.length}
                                                        <button
                                                            type="button"
                                                            onClick={clearPoolFilters}
                                                            className="font-semibold text-(--text-secondary) hover:text-(--text-primary) transition-colors cursor-pointer"
                                                        >
                                                            Clear
                                                        </button>
                                                    </span>
                                                )}
                                                {isImageMatchActive && !readOnly && (
                                                    <button
                                                        type="button"
                                                        onClick={liveImageMatches.refresh}
                                                        disabled={liveImageMatches.loading}
                                                        title={liveImageMatches.error
                                                            ?? (liveImageMatches.libraryNames.length > 0
                                                                ? `Matched against: ${liveImageMatches.libraryNames.join(', ')}. Click to re-check your image libraries.`
                                                                : 'Re-check your image libraries')}
                                                        className={`flex items-center gap-1.5 min-h-9 px-3 py-2 rounded-control text-[12px] font-semibold border transition-colors shrink-0 cursor-pointer disabled:cursor-wait
                                                            ${liveImageMatches.error ? 'border-(--red)/40 text-(--red)' : 'border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary)'}`}
                                                    >
                                                        <FaArrowsRotate className={`text-[11px] ${liveImageMatches.loading ? 'animate-spin' : ''}`} />
                                                        {liveImageMatches.loading
                                                            ? 'Checking images…'
                                                            : liveImageMatches.error
                                                                ? 'Image check failed'
                                                                : liveImageMatches.checkedAt ? `Images checked ${relativeTime(liveImageMatches.checkedAt)}` : 'Check images'}
                                                    </button>
                                                )}
                                            </div>
                                        )}

                                        {!readOnly && !activePreview && (
                                            <div className={`flex flex-wrap items-center gap-2 @7xl:ml-auto @7xl:shrink-0 ${displayCards.length > 0 ? 'border-t border-(--divider) pt-2 @7xl:border-t-0 @7xl:pt-0' : ''}`}>
                                                {/* The label stays with its choices when the row wraps */}
                                                <div className="flex items-center gap-2 shrink-0">
                                                    <span className={FIELD_LABEL_CLASS}>
                                                        Numbering
                                                    </span>
                                                    <div className="flex gap-1.5">
                                                        {NUMBERING_MODE_OPTIONS.map(opt => (
                                                            <button
                                                                key={opt.value}
                                                                type="button"
                                                                onClick={() => handleNumberingModeChange(opt.value)}
                                                                className={choiceClass(numbering.mode === opt.value)}
                                                            >
                                                                {opt.label}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                                {numbering.mode === 'auto' && !numbering.autoLive && (
                                                    <button
                                                        type="button"
                                                        onClick={() => persist(renumberSorted(cards, numbering.sortLayers))}
                                                        className={buttonClass('secondary', 'sm', 'min-h-9')}
                                                    >
                                                        <FaArrowsRotate className="text-[12px]" /> Renumber now
                                                    </button>
                                                )}
                                                {numberingIssues && (
                                                    <div className="flex items-center gap-2 min-w-0">
                                                        <span className="flex items-center gap-1.5 min-w-0 text-[12px] font-semibold text-(--warning)">
                                                            <FaTriangleExclamation className="text-[11px] shrink-0" />
                                                            {numberingIssuesSummary(numberingIssues)}
                                                        </span>
                                                        {/* Auto (not live) already shows "Renumber now" beside it */}
                                                        {!(numbering.mode === 'auto' && !numbering.autoLive) && (
                                                            <button
                                                                type="button"
                                                                onClick={() => persist(renumberSorted(cards, numbering.sortLayers))}
                                                                title="Number every card 1 to N, using the auto-numbering sort order"
                                                                className={buttonClass('secondary', 'sm', 'min-h-9 shrink-0')}
                                                            >
                                                                <FaArrowsRotate className="text-[12px]" /> Renumber
                                                            </button>
                                                        )}
                                                    </div>
                                                )}

                                                {numbering.mode !== 'none' && (
                                                    <div className="relative shrink-0" ref={numberingSettingsRef}>
                                                        <button
                                                            type="button"
                                                            onClick={() => setShowNumberingSettings(v => !v)}
                                                            className="flex items-center justify-center w-9 h-9 rounded-control border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors cursor-pointer"
                                                            aria-label="Numbering settings"
                                                        >
                                                            <FaGear className="text-[15px]" />
                                                        </button>

                                                        {showNumberingSettings && (
                                                            <div className={`${POOL_TOOLBAR_POPOVER_CLASS} right-0`}>
                                                                {numbering.mode === 'auto' && (
                                                                    <>
                                                                        <div className="flex flex-col gap-2">
                                                                            <span className={FIELD_LABEL_CLASS}>
                                                                                Sort By (in order)
                                                                            </span>
                                                                            {numbering.sortLayers.map((layer, index) => (
                                                                                <div key={index} className="flex items-center gap-1.5">
                                                                                    <span className="text-[11px] font-mono text-(--text-tertiary) w-3 shrink-0">{index + 1}</span>
                                                                                    <CustomSelect
                                                                                        size="md"
                                                                                        className="flex-1 min-w-0"
                                                                                        value={layer.category}
                                                                                        onChange={value => updateSortLayer(index, { category: value as SortCategory })}
                                                                                        options={availableCategoriesFor(layer.category)}
                                                                                    />
                                                                                    <button
                                                                                        type="button"
                                                                                        onClick={() => updateSortLayer(index, { direction: layer.direction === 'asc' ? 'desc' : 'asc' })}
                                                                                        title={layer.direction === 'asc' ? 'Ascending' : 'Descending'}
                                                                                        className="flex items-center justify-center w-10 h-10 rounded-control border border-(--divider) text-(--text-secondary) hover:border-(--rule-strong) transition-colors shrink-0 cursor-pointer"
                                                                                    >
                                                                                        {layer.direction === 'asc' ? <FaArrowUp className="text-[13px]" /> : <FaArrowDown className="text-[13px]" />}
                                                                                    </button>
                                                                                    <button
                                                                                        type="button"
                                                                                        onClick={() => moveSortLayer(index, -1)}
                                                                                        disabled={index === 0}
                                                                                        className="flex items-center justify-center w-8 h-10 text-[13px] text-(--text-tertiary) hover:text-(--text-primary) cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
                                                                                    >
                                                                                        ▲
                                                                                    </button>
                                                                                    <button
                                                                                        type="button"
                                                                                        onClick={() => moveSortLayer(index, 1)}
                                                                                        disabled={index === numbering.sortLayers.length - 1}
                                                                                        className="flex items-center justify-center w-8 h-10 text-[13px] text-(--text-tertiary) hover:text-(--text-primary) cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
                                                                                    >
                                                                                        ▼
                                                                                    </button>
                                                                                    {numbering.sortLayers.length > 1 && (
                                                                                        <button
                                                                                            type="button"
                                                                                            onClick={() => removeSortLayer(index)}
                                                                                            aria-label="Remove sort level"
                                                                                            className="flex items-center justify-center w-8 h-10 text-(--text-tertiary) hover:text-(--red) transition-colors shrink-0 cursor-pointer"
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
                                                                                    className={buttonClass('ghost', 'sm', 'self-start')}
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
                                                                    <span className={FIELD_LABEL_CLASS}>Prefix</span>
                                                                    <input
                                                                        type="text"
                                                                        value={numbering.prefix}
                                                                        onChange={e => handlePrefixInputChange(e.target.value)}
                                                                        onBlur={handlePrefixInputBlur}
                                                                        maxLength={3}
                                                                        placeholder="e.g. AS"
                                                                        className={fieldClass('md', 'w-24 font-mono uppercase focus:outline-none')}
                                                                    />
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                                {cards.length > 0 && <FoilSuggestControl foils={foils} disabled={saving} />}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {showPoolFilters && displayCards.length > 0 && (
                                <PoolFilterPanel cards={displayCards} filters={poolFilters} onChange={setPoolFilters} />
                            )}

                            {/* Card Grid */}
                            <div className={`flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-3 ${activePreview ? 'bg-(--preview-accent)/4' : 'bg-(--background-tertiary)'}`}>
                                {isAlgorithmRunning ? (
                                    <PoolGridSkeleton showFullCards={showFullCards} />
                                ) : displayCards.length > 0 && filteredCards.length === 0 ? (
                                    <div className="flex flex-col items-center gap-2 py-8">
                                        <EmptyState size="inline">No cards match these filters.</EmptyState>
                                        <button
                                            type="button"
                                            onClick={clearPoolFilters}
                                            className={buttonClass('secondary', 'sm')}
                                        >
                                            Clear filters
                                        </button>
                                    </div>
                                ) : displayCards.length === 0 ? (
                                    activePreview
                                        ? <EmptyState size="inline">No players matched this configuration.</EmptyState>
                                        : (
                                            // Still placeholders hint at the grid the pool will fill
                                            <div className="relative h-full overflow-hidden">
                                                <PoolGridSkeleton showFullCards={showFullCards} animated={false} className="opacity-60" />
                                                <div className="absolute inset-0 flex items-start justify-center pt-12 px-3">
                                                    <EmptyState size="panel" title="No cards yet." className="rounded-card border border-(--divider) bg-(--background-secondary)">
                                                        {readOnly ? 'This edition has no cards yet.' : 'Run an Algorithmic Pool or Manual search to build your player list.'}
                                                    </EmptyState>
                                                </div>
                                            </div>
                                        )
                                ) : (
                                    <div className="flex flex-col gap-4">
                                        {visibleGroups.map(group => (
                                            <div key={group.key} className="flex flex-col gap-2">
                                                {groupBy !== 'none' && (
                                                    // Sticks to the top of the scrolling grid while its group is in view; -top-3/-mx-3 offset the container's p-3.
                                                    <div className="sticky -top-3 z-10 -mx-3 px-3 py-2 flex items-center gap-2 border-t border-b border-(--divider) bg-(--background-secondary)">
                                                        <Heading level="panel" as="span">{group.label}</Heading>
                                                        <Plate size="sm">
                                                            {poolGroups.find(g => g.key === group.key)?.cards.length}
                                                        </Plate>
                                                    </div>
                                                )}
                                                <div className={poolGridClass(showFullCards)}>
                                                    {group.cards.map(card => (
                                                        <PoolCardRow
                                                            key={card.id}
                                                            card={card}
                                                            showFullCards={showFullCards}
                                                            editionStyle={editionStyle}
                                                            numberLabel={formatCardNumber(card.card_number, displayCards.length, numbering.zeroPad, numbering.prefix)}
                                                            setNumber={printedSetNumber(card)}
                                                            numberInputValue={isManualNumberingEditable ? (editingNumbers[card.id] ?? (card.card_number?.toString() ?? '')) : undefined}
                                                            numberPrefix={numbering.prefix}
                                                            numberIssue={numberIssueFor(card, numberingIssues)}
                                                            showMatchBadge={isMatchSortActive}
                                                            onOpen={setDetailCard}
                                                            onRemove={readOnly ? undefined : handleRemoveCardStable}
                                                            onNumberChange={handleNumberInputChangeStable}
                                                            onNumberBlur={handleNumberInputBlurStable}
                                                            foilSuggestion={card.source_card_id ? pendingFoils?.get(card.source_card_id) : undefined}
                                                            onSkipFoilSuggestion={handleSkipFoilSuggestionStable}
                                                        />
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                {visibleCount < poolGroupedCardCount && (
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

                        {!readOnly && (
                            <Tabs.Content value="cutoff" className="flex-1 min-h-0 overflow-y-auto focus:outline-none">
                                <AlgorithmCutoff
                                    cutLines={cutoffSummary?.cut_lines ?? []}
                                    isPreview={!!activePreview}
                                    isRunning={isAlgorithmRunning}
                                    openablePickIds={poolSourceIds}
                                    onOpenPick={handleOpenCutoffPick}
                                />
                            </Tabs.Content>
                        )}
                    </div>
                </div>
            </div>
            </Tabs.Root>

            {showStyleModal && (
                <EditionStyleModal
                    releaseId={releaseId}
                    edition={edition}
                    token={token}
                    onClose={() => setShowStyleModal(false)}
                    onEditionUpdated={onEditionUpdated}
                />
            )}

            {/* Card Builder for the Customs tab. Mounted only while open, so it starts from the saved form each time. */}
            {customBuilderOpen && (
                <Modal
                    onClose={closeCustomBuilder}
                    title="Build a Custom Card"
                    subtitle="Date ranges, multi-year, splits and more. Add each card you build to this edition."
                    size="xl"
                >
                    <CustomCardBuilder embed={customBuilderEmbed} />
                </Modal>
            )}

            {/* Player Pool card detail */}
            <div className={detailCard ? '' : 'hidden pointer-events-none'}>
                <Modal
                    onClose={() => setDetailCard(null)}
                    isVisible={!!detailCard}
                >
                    <CardDetail
                        showdownBotCardData={detailCard?.card_snapshot.card_data ? { card: detailCard.card_snapshot.card_data } as ShowdownBotCardAPIResponse : undefined}
                        cardId={detailCard?.card_snapshot.card_id}
                        variableSpeed={!!detailCard?.card_snapshot.is_variable_speed_00_01}
                        styleOverrides={detailStyleOverrides}
                        styleEditor={detailStyleEditor}
                        hideTrendGraphs={true}
                        context="release"
                        parent="modal"
                        actionBarContent={detailCard && (cardLinkSlugs || detailCardTags.length > 0 || detailCardPreviewRank || detailCardCurrent?.card_snapshot.algorithm_match_score != null || (!readOnly && !activePreview)) ? (
                            <>
                                {cardLinkSlugs && (
                                    <button type="button" onClick={cardLink.copy} title={cardLink.error ?? cardLink.url} className={buttonClass('secondary', 'sm')}>
                                        {cardLink.copied ? <FaCheck className="text-[10px]" /> : <FaLink className="text-[10px]" />}
                                        {cardLink.copied ? 'Copied' : 'Copy card link'}
                                    </button>
                                )}
                                <ReleaseCardTagsEditor
                                    tags={detailCardTags}
                                    editionTags={editionTags}
                                    readOnly={readOnly || !!activePreview}
                                    onChange={handleDetailCardTagsChange}
                                />
                                <ReleaseCardPreviewRankPicker
                                    rank={detailCardPreviewRank}
                                    readOnly={readOnly || !!activePreview}
                                    onChange={rank => detailCard && handlePreviewRankChange(detailCard.source_card_id, rank)}
                                />
                                {detailCardCurrent && <AlgorithmMatchBadge card={detailCardCurrent} labeled />}
                            </>
                        ) : undefined}
                    />
                </Modal>
            </div>
        </div>
    );
}

function StepButton({ number, label, mobileLabel, isActive, onClick, ref }: { number?: number; label: string; mobileLabel?: string; isActive: boolean; onClick: () => void; ref?: Ref<HTMLButtonElement> }) {
    return (
        <button ref={ref} type="button" onClick={onClick} className="group flex items-center gap-2 cursor-pointer">
            {number !== undefined && <span className={`flex items-center justify-center w-5 h-5 rounded-full text-[11px] font-semibold tabular-nums shrink-0 transition-colors
                ${isActive ? 'bg-(--showdown-blue-fill) text-white' : 'border border-(--text-tertiary) text-(--text-tertiary) group-hover:border-(--text-secondary) group-hover:text-(--text-secondary)'}`}>
                {number}
            </span>}
            <span className={`${headingClass('panel')} transition-colors ${isActive ? '' : 'text-(--text-tertiary)! group-hover:text-(--text-secondary)!'}`}>
                {mobileLabel ? <><span className="sm:hidden">{mobileLabel}</span><span className="hidden sm:inline">{label}</span></> : label}
            </span>
        </button>
    );
}

/** Placeholder shaped like the edition builder (toolbar, build-method panel, player pool) while an
 *  edition's cards load. */
/** Shown over the pool while an algorithm run is in flight: a sweeping bar and elapsed time, so a long run still reads as alive. */
function AlgorithmRunningBanner({ estimatedSeconds }: { estimatedSeconds: number | null }) {
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    useEffect(() => {
        const startedAt = Date.now();
        const interval = setInterval(() => setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000)), 1000);
        return () => clearInterval(interval);
    }, []);
    return (
        <div role="status" className="relative flex items-center gap-1.5 px-3 py-2.5 border-b border-(--preview-accent)/30 bg-(--preview-accent)/10 shrink-0 overflow-hidden">
            <FaWandMagicSparkles className="text-(--preview-accent) live-pulse" />
            <span className={`${headingClass('panel')} text-(--preview-accent)!`}>Running algorithm…</span>
            <span className="ml-auto text-[11px] tabular-nums text-(--text-secondary)">{elapsedSeconds}s{estimatedSeconds !== null && ` / ~${estimatedSeconds}s`}</span>
            <div aria-hidden className="absolute bottom-0 inset-x-0 h-0.5 bg-(--preview-accent)/15">
                <div className="indeterminate-sweep h-full w-2/5 bg-(--preview-accent)" />
            </div>
        </div>
    );
}

type PoolCardRowProps = {
    card: ReleaseCard;
    showFullCards: boolean;
    editionStyle: CardStyleSettings;
    /** Number shown beside the card. */
    numberLabel: string;
    /** Set number printed on full cards; null when the edition isn't numbered. */
    setNumber: string | null;
    /** Manual numbering input value; undefined shows the read-only label instead. */
    numberInputValue?: string;
    numberPrefix?: string;
    /** Flags the number as shared with another card, or missing. */
    numberIssue?: NumberIssue;
    showMatchBadge: boolean;
    onOpen: (card: ReleaseCard) => void;
    /** Undefined hides the remove button. */
    onRemove?: (card: ReleaseCard) => void;
    onNumberChange: (cardId: string, value: string) => void;
    onNumberBlur: (cardId: string) => void;
    /** An unapplied foil pick for this card, shown as a dashed FOIL? tag. */
    foilSuggestion?: FoilSuggestion;
    onSkipFoilSuggestion?: (sourceCardId: string) => void;
};

/** One pool grid card. Memoized (with stable callbacks from the builder) because the pool can be
 * hundreds of cards, and loading another page or opening a card shouldn't re-render all of them. */
const PoolCardRow = memo(function PoolCardRow({ card, showFullCards, editionStyle, numberLabel, setNumber, numberInputValue, numberPrefix, numberIssue, showMatchBadge, onOpen, onRemove, onNumberChange, onNumberBlur, foilSuggestion, onSkipFoilSuggestion }: PoolCardRowProps) {
    // Full cards show the edition style and set number they'll print with
    const styleOverrides = useMemo<CardStyleOverrides>(
        () => ({ style: releaseCardStyle(editionStyle, card.card_overrides), setNumber }),
        [editionStyle, card.card_overrides, setNumber]
    );
    const handleOpen = useCallback(() => onOpen(card), [onOpen, card]);
    const issueTitle = numberIssue === 'duplicate'
        ? `Another card is also #${card.card_number}`
        : numberIssue === 'unnumbered' ? 'No number yet' : undefined;
    return (
        // Offscreen rows skip layout and paint, so repaints (opening a card, images loading) don't
        // re-process the whole pool. That clips the row to its padding box, so -m-4/p-4 extends it into
        // the grid gap (same layout) to keep the edge tags, corner icons, and hover ring visible.
        // Heights are the measured row heights, until a row has rendered once.
        <div className={`group/row flex items-center gap-1.5 -m-4 p-4 [content-visibility:auto] [contain-intrinsic-width:auto_0px] ${showFullCards ? '[contain-intrinsic-height:auto_124px]' : '[contain-intrinsic-height:auto_58px]'}`}>
            {/* Set number with the remove button stacked beneath it, to save horizontal space. */}
            <div className="flex flex-col items-end gap-1 shrink-0">
                {numberInputValue !== undefined ? (
                    <div className="flex items-center gap-1 shrink-0">
                        {numberPrefix && (
                            <span className="text-[13px] font-mono text-(--text-tertiary)">{numberPrefix}</span>
                        )}
                        <input
                            type="number"
                            value={numberInputValue}
                            onChange={e => onNumberChange(card.id, e.target.value)}
                            onBlur={() => onNumberBlur(card.id)}
                            placeholder="—"
                            title={issueTitle}
                            aria-invalid={numberIssue === 'duplicate' || undefined}
                            className={fieldClass('md', `w-14 font-mono text-right tabular-nums focus:outline-none ${numberIssue === 'duplicate' ? 'border-(--red)! text-(--red)' : numberIssue === 'unnumbered' ? 'border-(--warning)!' : ''}`)}
                        />
                    </div>
                ) : (
                    <span
                        title={issueTitle}
                        className={`text-[13px] font-mono w-7 text-right shrink-0 ${numberIssue === 'duplicate' ? 'font-semibold text-(--red)' : numberIssue === 'unnumbered' ? 'text-(--warning)' : 'text-(--text-tertiary)'}`}
                    >
                        {numberLabel}
                    </span>
                )}
                {onRemove && (
                    <button
                        type="button"
                        onClick={() => onRemove(card)}
                        title="Remove and exclude from Algorithm runs"
                        aria-label="Remove"
                        data-remove-button
                        className="flex items-center justify-center w-5 h-5 rounded-full text-(--text-tertiary) hover:bg-(--red)/90 hover:text-white transition-colors shrink-0 cursor-pointer"
                    >
                        <FaXmark className="text-[11px]" />
                    </button>
                )}
            </div>
            {/* Hovering the remove button outlines the card it removes. */}
            <div className={`relative flex-1 min-w-0 transition-shadow group-has-[[data-remove-button]:hover]/row:ring-2 group-has-[[data-remove-button]:hover]/row:ring-(--red)/80 ${showFullCards ? 'rounded-card max-w-100' : 'rounded-card'}`}>
                {showFullCards
                    ? <CardItemFromCardDatabaseRecord card={card.card_snapshot} onClick={handleOpen} styleOverrides={styleOverrides} />
                    : <CardItemCompactFromCardDatabaseRecord card={card.card_snapshot} onClick={handleOpen} />}
                {(card.tags.length > 0 || card.preview_rank || foilSuggestion) && (
                    // Overlaid on the bottom edge (like the top-edge badges) so tags don't change row height
                    <div className="absolute -bottom-1 left-1 translate-y-1/2 z-10 pointer-events-none flex items-center gap-1">
                        {card.preview_rank && <ReleaseCardPreviewRankBadge rank={card.preview_rank} />}
                        <ReleaseCardTagChips tags={card.tags} />
                        {foilSuggestion && (
                            <ReleaseCardSuggestedTagChip
                                tag={FOIL_TAG}
                                title={foilSuggestionTitle(foilSuggestion)}
                                onDismiss={onSkipFoilSuggestion && (() => onSkipFoilSuggestion(foilSuggestion.source_card_id))}
                            />
                        )}
                    </div>
                )}
                {showMatchBadge && (
                    <div className="absolute -bottom-1 right-1 translate-y-1/2 z-10">
                        <AlgorithmMatchBadge card={card} />
                    </div>
                )}
            </div>
        </div>
    );
});

/** The pool grid's columns: full cards get wider tracks than compact rows. */
function poolGridClass(showFullCards: boolean) {
    return showFullCards
        ? 'grid grid-cols-[repeat(auto-fill,minmax(min(300px,100%),1fr))] gap-6'
        : 'grid grid-cols-2 sm:grid-cols-[repeat(auto-fit,minmax(min(200px,100%),1fr))] gap-4';
}

/** Placeholder pool grid: pulses while the algorithm runs, sits still behind the empty state. */
function PoolGridSkeleton({ showFullCards, animated = true, className = '' }: { showFullCards: boolean; animated?: boolean; className?: string }) {
    return (
        <div aria-label={animated ? 'Loading cards' : undefined} className={`${poolGridClass(showFullCards)} ${className}`}>
            {Array.from({ length: showFullCards ? 6 : 24 }, (_, i) => showFullCards
                ? <CardItemSkeleton key={i} className="h-28 max-w-100" animated={animated} />
                : <CardItemCompactSkeleton key={i} animated={animated} />)}
        </div>
    );
}

export function EditionBuilderSkeleton() {
    return (
        <div aria-label="Loading edition" className="flex-1 min-h-0 flex flex-col animate-pulse">
            <div className="flex items-center gap-2 px-3 py-2 border-b border-(--divider)">
                <div className="h-8 w-40 rounded-control bg-(--background-tertiary)" />
                <div className="h-8 w-28 rounded-control bg-(--background-tertiary)" />
            </div>
            <div className="flex-1 min-h-0 flex gap-3 p-3">
                <div className="hidden md:block w-80 shrink-0 rounded-card bg-(--background-tertiary)" />
                <div className="flex-1 flex flex-col gap-1.5">
                    {Array.from({ length: 8 }, (_, i) => <div key={i} className="h-16 rounded-card bg-(--background-tertiary)" />)}
                </div>
            </div>
        </div>
    );
}
