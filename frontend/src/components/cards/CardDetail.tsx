import { Plate } from '../shared/Plate';
import { Eyebrow } from '../shared/Eyebrow';
import { buttonClass } from '../shared/buttonStyles';
/**
 * @fileoverview CardDetail - Comprehensive card display and analysis component
 * 
 * This component provides a detailed view of generated MLB Showdown cards including:
 * - Full card visualization with dynamic styling
 * - Statistical analysis tables (real vs projected, accuracy breakdowns)
 * - Performance trends and historical data
 * - Live game integration when applicable
 * - Interactive table switching and customization options
 */

import { useState, useEffect, useRef, useMemo, memo, type CSSProperties } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useTheme, useSiteSettings } from "../shared/SiteSettingsContext";
import { FaPlus, FaWandMagicSparkles } from 'react-icons/fa6';
import { type ShowdownBotCard, type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import { enhanceColorVisibility } from '../../functions/colors';
import { fetchCardData } from '../../api/card_db/cardDatabase';
import { CardSource } from '../../types/cardSource';
import CustomSelect from '../shared/CustomSelect';
import ShowdownBotLogo from '../shared/ShowdownBotLogo';
import { useCustomizeCard } from '../customs/customizeCard';
import { SetBadge, SET_SELECT_OPTIONS } from "../shared/SetBadge";


// Chart accuracy table (kept as table — compact and precise)
import { ChartSelectionBreakdown } from './card_detail/ChartSelectionBreakdown';
import { BaselineOpponentBreakdown } from './card_detail/BaselineOpponentBreakdown';

// API integration
import { generateCardImage, fetchCardById, fetchSeasonStatRanges } from '../../api/showdownBotCard';
import { applyCardStyleOverrides, type CardStyleOverrides } from './cardStyleOverrides';

// Performance visualization
import ChartPlayerPointsTrend from './card_detail/ChartPlayerPointsTrend';

// Live game integration
import GameItem from '../games/GameItem';
import { fromBoxscoreDetail } from '../../domain/adapters/fromMlbApi';

// Visual breakdown panels
import OutcomeProbability from './card_detail/OutcomeProbability';
import RealVsProjectedVisual from './card_detail/RealVsProjectedVisual';
import PointsContributionBars from './card_detail/PointsContributionBars';
import { CardComps } from './card_detail/CardComps';
import { CardStyleEditor, type CardStyleEditorConfig } from './card_detail/CardStyleEditor';
import { isCardStyleDifferent, CARD_STYLE_KEYS } from '../customs/cardStyle';
import ImageSourceBadge from './card_detail/ImageSourceBadge';
import PinnedFooterPortal from '../shared/PinnedFooterPortal';
import { cardImagePublicUrl } from '../../api/supabase';

import { Heading } from '../shared/Heading';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';
/**
 * Props for the CardDetail component
 */
type CardDetailProps = {
    /** Complete card data with statistics and analysis */
    showdownBotCardData?: ShowdownBotCardAPIResponse | null;
    /** Card Id is passed in when loading from search */
    cardId?: string;
    /** Whether to hide trend graphs (optional for mobile/compact views) */
    hideTrendGraphs?: boolean;
    /** Loading state for the main card data */
    isLoading?: boolean;
    /** Usage context: 'custom' for card builder, 'explore' for database browser, 'release' for a
     * Release Builder card */
    context?: 'custom' | 'explore' | 'home' | 'season' | 'roster' | 'game_detail' | 'sim_result' | 'release';
    parent?: string;
    showdownSetForPlaceholder?: string; // Used to determine placeholder image when card image is not available
    /** A simulated season's statline (`SimStatLine.stats`) — adds a SIM column to "Card vs Real
     * Stats" alongside the card's own projection and real-life stat, e.g. for a sim result's
     * award-winner card, where "real" is the player's actual season and this is what they did in
     * the simulated one. */
    simStats?: Record<string, number>;
    /** Optional message shown directly below the player name/set/attributes row, styled like the
     * warnings/errata banner above it — e.g. explaining that `simStats` reflects a simulated
     * season rather than the card's own real one. */
    tooltip?: string;
    /** Team-builder draft/edit mode: when set, renders a "Draft" button pinned to the bottom-right
     * of the modal. Runs the same handler as the compact card item's action button (opens the
     * slot-fill flow for the roster slot this card sits in). */
    onDraft?: () => void;
    /** Greys out the Draft button and blocks clicks — e.g. while a previous pick is still saving. */
    draftDisabled?: boolean;
    /** Text for the `onDraft` button — e.g. "Add to Edition" in the Release Builder. Defaults to "Draft". */
    draftLabel?: string;
    /** Extra controls for the action bar (pinned to the bottom of an enclosing Modal/sidebar), shown left of
     * Customize/Draft — e.g. a release card's tags and preview slot. */
    actionBarContent?: React.ReactNode;
    /** When true, the Set badge next to the player name becomes a dropdown (styled like the
     * header's Showdown Set selector) that swaps the displayed card for the same player/year in
     * a different set. Selecting a new card elsewhere always discards this — it only affects the
     * currently displayed card, not any persisted preference. */
    enableSetSwitcher?: boolean;
    /** Renders the card with this styling instead of its own (e.g. a release edition's style and
     * set number), generating a fresh image unless `storagePath` supplies the already-rendered one.
     * Applies to both `showdownBotCardData` and `cardId` cards. */
    styleOverrides?: CardStyleOverrides;
    /** Enables editing this card's style in place: Customize opens the Card Style fields inline
     * (instead of the Custom Card Builder) and auto-saves edits via `onSave` once they pause. The
     * caller persists them and passes updated `styleOverrides`, which re-renders the card image. */
    styleEditor?: CardStyleEditorConfig;
};

// design-ok: the rendered card art has its own large corner radius; the image clip matches it
const CARD_IMAGE_RADIUS = 'rounded-2xl';

const SectionPanel = ({ title, subtitle, isLoading, children }: { title: string; subtitle?: string; isLoading?: boolean; children: React.ReactNode }) => (
    <div className={`bg-secondary rounded-card p-4 border border-form-element space-y-3 overflow-y-scroll ${isLoading ? 'blur-xs' : ''}`}>
        <div className="flex flex-col gap-1">
            <Eyebrow>{title}</Eyebrow>
            {subtitle && <div className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>{subtitle}</div>}
        </div>
        {children}
    </div>
);

/**
 * CardDetail - Comprehensive card display and analysis component
 *
 * Provides a complete view of generated MLB Showdown cards with interactive
 * analysis tools. Features include:
 * 
 * - **Card Visualization**: Full card display with team colors and styling
 * - **Statistical Analysis**: Multiple comparison tables showing accuracy
 * - **Performance Trends**: Historical and seasonal performance graphs
 * - **Live Integration**: Real-time game data when applicable
 * - **Interactive Tables**: Switchable views for different analysis types
 * 
 * The component adapts its layout and features based on the usage context
 * and available data, providing both casual browsing and deep analysis capabilities.
 * 
 * @param showdownBotCardData - Complete card API response with all data
 * @param hideTrendGraphs - Hide trend charts for compact layouts
 * @param isLoading - Main loading state
 * @param context - Usage context affecting available features
 * 
 * @example
 * ```tsx
 * <CardDetail 
 *   showdownBotCardData={cardResponse}
 *   context="explore"
 *   hideTrendGraphs={isMobile}
 * />
 * ```
 */
export const CardDetail = memo(function CardDetail({ showdownBotCardData: showdownBotCardDataProp, cardId, isLoading, hideTrendGraphs=false, context='custom', parent, showdownSetForPlaceholder, simStats, tooltip, onDraft, draftDisabled=false, draftLabel='Draft', actionBarContent, enableSetSwitcher=false, styleOverrides: styleOverridesProp, styleEditor }: CardDetailProps) {
    // Keyed on content, so a caller handing over an equal overrides object (e.g. after an unrelated
    // save returns fresh objects) doesn't regenerate the image
    const styleOverridesKey = JSON.stringify([
        styleOverridesProp?.style && CARD_STYLE_KEYS.map(key => styleOverridesProp.style?.[key]),
        styleOverridesProp?.setNumber,
        styleOverridesProp?.storagePath,
    ]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    const styleOverrides = useMemo(() => styleOverridesProp, [styleOverridesKey]);
    const withStyleOverrides = (data: ShowdownBotCardAPIResponse | null | undefined) => (
        styleOverrides && data?.card ? { ...data, card: applyCardStyleOverrides(data.card, styleOverrides) } : data
    );
    const showdownBotCardData = useMemo(
        () => withStyleOverrides(showdownBotCardDataProp),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [showdownBotCardDataProp, styleOverrides]
    );
    /** True when a card has no image to show yet. A stored override image counts as one — the card
     * already looks the way the overrides describe, so there's nothing to generate. */
    const isMissingImage = (card: ShowdownBotCard | null | undefined) =>
        !!card && !card.image.output_file_name && !styleOverrides?.storagePath;
    /** URL of a card's rendered image, if it has one */
    const imagePathFor = (card: ShowdownBotCard | null | undefined): string | null => {
        const image = card?.image;
        if (image?.storage_path) return cardImagePublicUrl(image.storage_path);
        if (image?.output_folder_path && image?.output_file_name) return `/${image.output_folder_path}/${image.output_file_name}`.replace(/\/\//, '/');
        return null;
    };


    const { session } = useAuth();
    const customizeCard = useCustomizeCard();

    // =============================================================================
    // MARK: STATES
    // =============================================================================

    /**
     * Internal card data state for handling dynamic updates
     * Allows component to maintain its own copy for features like image regeneration
     */
    const [internalCardData, setInternalCardData] = useState<ShowdownBotCardAPIResponse | null | undefined>(showdownBotCardData);
    // Tracks the last `cardId` PROP value this component has already fetched/synced from —
    // deliberately separate from "the id of the card currently on screen" (which the set
    // switcher below reassigns locally). Comparing against that instead would make Case 2 think
    // the parent handed us a new card every time the parent re-renders after a local set switch
    // (e.g. a background session refresh when the browser tab regains focus), re-fetching the
    // stale prop id and silently reverting the user's chosen set.
    // Mounting with only a `cardId` (no data) must still fetch it, so it starts unhandled then.
    const handledCardIdPropRef = useRef<string | undefined>(showdownBotCardDataProp?.card ? cardId : undefined);
    // The style overrides last rendered, and the unstyled card last fetched by id — so new
    // overrides re-render (and regenerate the image) without refetching.
    const appliedStyleOverridesRef = useRef<CardStyleOverrides | undefined>(undefined);
    const fetchedCardRef = useRef<ShowdownBotCardAPIResponse | null>(null);
    // Whether the shown card came from `showdownBotCardData` (vs fetched by `cardId`)
    const isShowingPropDataRef = useRef(false);
    // While a restyled card's new image generates, keep showing the image it's replacing
    const restyleFromImagePathRef = useRef<string | null>(null);
    // Only the latest image request may land — restyles can fire while an earlier one is in flight
    const latestImageRequestRef = useRef(0);

    // Use internal state when available, fallback to prop
    const activeCardData = internalCardData || showdownBotCardData;

    // Extras when card is loaded - stat ranges for real vs projected table
    const [seasonStatRanges, setSeasonStatRanges] = useState<Record<string, { min: number; max: number }> | null>(null);
    const [isRangesLoading, setIsRangesLoading] = useState(false);

    // Theme and settings
    const { isDark } = useTheme();
    const { userShowdownSet } = useSiteSettings();

    /**
     * Sync internal state with prop changes
     * Ensures component reflects updates from parent while maintaining ability
     * to handle local updates (like image regeneration)
     */
    useEffect(() => {
        const fetchRanges = (card: NonNullable<ShowdownBotCardAPIResponse['card']>) => {
            const yearList = card.stats_period?.year_list || [];
            const playerType = card.player_type.toUpperCase() as "HITTER" | "PITCHER";
            const subType: string | undefined = card.player_sub_type;
            const pitcherRole: 'SP' | 'RP' | undefined =
                playerType === 'PITCHER'
                    ? (subType === 'starting_pitcher' ? 'SP' : 'RP')
                    : undefined;
            setIsRangesLoading(true);
            setSeasonStatRanges(null);
            fetchSeasonStatRanges(yearList, playerType, pitcherRole)
                .then((response) => {
                    console.log("Fetched season stat ranges:", response);
                    setSeasonStatRanges(response?.ranges ?? null);
                })
                .catch((error) => {
                    console.error("Error fetching season stat ranges:", error);
                })
                .finally(() => {
                    setIsRangesLoading(false);
                });
        };

        // Case 1: New data provided via prop
        if (showdownBotCardData && showdownBotCardData.card) {
            // Skip if same card (by bref_id + year + set). With `enableSetSwitcher`, the set is
            // excluded from this check: the same player/year re-arriving from the parent at its
            // default set (e.g. a background search refresh after the browser tab regains focus)
            // must not be treated as a "new" card and clobber a set the user manually switched to
            // — only a genuinely different player/year should do that.
            const isSamePlayer =
                context !== 'custom' &&
                (
                    (internalCardData?.card?.bref_id || internalCardData?.card?.mlb_id) === (showdownBotCardData?.card?.bref_id || showdownBotCardData?.card?.mlb_id) &&
                    internalCardData?.card?.year === showdownBotCardData?.card?.year &&
                    (enableSetSwitcher || internalCardData?.card?.set === showdownBotCardData?.card?.set)
                );
            // A rebuilt chart (e.g. a new chart version) is the same player but a different card
            const isSameCard = isSamePlayer && (internalCardData?.card?.chart_version ?? 1) === (showdownBotCardData?.card?.chart_version ?? 1);
            console.log("CardDetail: Checking for prop data update, isSameCard =", isSameCard);
            // isSameCard is true on mount (internal state starts from the prop). Styled cards never
            // carry a matching image, so new overrides (incl. the first) count as a new card.
            const styleOverridesChanged = styleOverrides !== appliedStyleOverridesRef.current;
            appliedStyleOverridesRef.current = styleOverrides;
            if (!isSameCard || styleOverridesChanged) {
                restyleFromImagePathRef.current = isSamePlayer
                    ? (imagePathFor(internalCardData?.card) ?? restyleFromImagePathRef.current)
                    : null;
                setInternalCardData(showdownBotCardData);
                setSetSwitchError(null);

                // Load image if necessary. A restyle supersedes any render already in flight.
                console.log("Image Output Filename:", showdownBotCardData.card);
                if (isMissingImage(showdownBotCardData.card) && (styleOverridesChanged || !isGeneratingImage)) {
                    console.log("Generating image for new prop data...");
                    handleGenerateImage(showdownBotCardData);
                }
            }

            // Fetch ranges whenever the card changes or on initial mount (isSameCard is true
            // on first render because useState initializes internalCardData from the prop)
            if (!isSamePlayer || seasonStatRanges === null) {
                fetchRanges(showdownBotCardData.card);
            }

            handledCardIdPropRef.current = cardId;
            isShowingPropDataRef.current = true;
            return;
        }

        // Case 2: No data but cardId provided - fetch it from DB. If the prop data was just dropped
        // (e.g. a rebuilt card restored to its archived version), the card it showed is gone too.
        if (isShowingPropDataRef.current) {
            isShowingPropDataRef.current = false;
            handledCardIdPropRef.current = undefined;
        }
        const styleOverridesChanged = styleOverrides !== appliedStyleOverridesRef.current;
        appliedStyleOverridesRef.current = styleOverrides;
        if (cardId && cardId === handledCardIdPropRef.current && styleOverridesChanged && fetchedCardRef.current) {
            // Same card, new styling: restyle the already-fetched card and regenerate its image
            restyleFromImagePathRef.current = imagePathFor(internalCardData?.card) ?? restyleFromImagePathRef.current;
            const cardResponse = withStyleOverrides(fetchedCardRef.current);
            setInternalCardData(cardResponse);
            if (isMissingImage(cardResponse?.card) && cardResponse) handleGenerateImage(cardResponse);
            return;
        }
        if (cardId && cardId !== handledCardIdPropRef.current) {
            handledCardIdPropRef.current = cardId;
            setIsLoadingFromId(true);
            fetchCardById(cardId, 'card-detail')
                .then((data) => {
                    console.log("Fetched single card data by ID:", data);
                    if (data) {
                        fetchedCardRef.current = data as ShowdownBotCardAPIResponse;
                        const cardResponse = withStyleOverrides(fetchedCardRef.current) as ShowdownBotCardAPIResponse;
                        setSetSwitchError(null);

                        // Show chart data immediately; the image (if missing) fills in afterwards
                        setInternalCardData(cardResponse);
                        if (isMissingImage(cardResponse.card) && !isGeneratingImage) {
                            handleGenerateImage(cardResponse);
                        }

                        if (cardResponse.card) {
                            fetchRanges(cardResponse.card);
                        }
                    }
                })
                .catch((error) => {
                    console.error("Error fetching card by ID:", error);
                })
                .finally(() => {
                    setIsLoadingFromId(false);
                });

            return;
        }

    }, [showdownBotCardData, cardId, styleOverrides]);

    // Image Generation State
    const [isGeneratingImage, setIsGeneratingImage] = useState<boolean>(false);
    const [isLoadingFromId, setIsLoadingFromId] = useState<boolean>(false);

    // Set Switcher State (enableSetSwitcher only) — looks up the same player/year in a different
    // set via the existing search + by-id endpoints, no dedicated backend support needed.
    const [isSwitchingSet, setIsSwitchingSet] = useState<boolean>(false);
    const [setSwitchError, setSetSwitchError] = useState<string | null>(null);

    // Inline style editor (styleEditor only) — closes whenever a different card is shown
    const [isStyleEditorOpen, setIsStyleEditorOpen] = useState<boolean>(false);
    const styleEditorCardKey = cardId ?? `${showdownBotCardDataProp?.card?.bref_id}-${showdownBotCardDataProp?.card?.year}-${showdownBotCardDataProp?.card?.set}`;
    const hasStyleEditor = !!styleEditor;
    useEffect(() => { setIsStyleEditorOpen(false); }, [styleEditorCardKey, hasStyleEditor]);
    const showStyleEditor = isStyleEditorOpen && !!styleEditor;
    const isStyleCustomized = !!styleEditor && isCardStyleDifferent(styleEditor.style, styleEditor.defaults);

    // Mark if isLoading or isGeneratingImage
    const isLoadingOverall = isLoading || isGeneratingImage || isLoadingFromId || isSwitchingSet;
    // Panels only blur while chart data itself is loading — not when just the image is generating
    const isLoadingPanels = isLoading || isLoadingFromId || isSwitchingSet || (isGeneratingImage && !activeCardData?.card?.chart);

    // Game
    const showGameBoxscore = (): boolean => {
        if (!activeCardData?.latest_game_box_score) return false;
        
        try {
            // Parse the date string without timezone conversion
            const dateStr = activeCardData.latest_game_box_score.datetime.official_date || "1970-01-01";
            const [year, month, day] = dateStr.split('-').map(Number);
            
            // Create date object in local timezone (no conversion)
            const gameDate = new Date(year, month - 1, day, 12); // month is 0-indexed
            const now = new Date();
            const oneDayAgo = new Date(now.getTime() - (24 * 60 * 60 * 1000)); // 24 hours ago

            return gameDate >= oneDayAgo;
        } catch (error) {
            console.error('Invalid date format:', activeCardData.latest_game_box_score.datetime.official_date);
            return false;
        }
    };

    // --------------------------------
    // MARK: - EFFECTS
    // --------------------------------

    // Card Calcs
    const cardImagePath: string | null = imagePathFor(activeCardData?.card)
        ?? (isGeneratingImage ? restyleFromImagePathRef.current : null);
    const cardAttributes: Record<string, string | number | null> = activeCardData?.card ? {
        points: `${activeCardData.card.points} PTS`,
        year: activeCardData.card.year,
        stats_period_summary: activeCardData.card.stats_period?.type !== "REGULAR" ? activeCardData.card.stats_period?.display_text || null : null,
        expansion: activeCardData.card.image.expansion == "BS" ? null : activeCardData.card.image.expansion,
        edition: activeCardData.card.image.edition == "NONE" || activeCardData.card.image.edition == undefined ? null : activeCardData.card.image.edition,
        chart_version: activeCardData.card.chart_version === 1 || activeCardData.card.chart_version == undefined ? null : `CHART ${activeCardData.card.chart_version}`,
        parallel: activeCardData.card.image.parallel == "NONE" || activeCardData.card.image.parallel == undefined ? null : `PARALLEL: ${activeCardData.card.image.parallel}`,
        is_errata: activeCardData.card.is_errata ? 'ERRATA' : null,
    } : {};
    var weeklyChangePoints = activeCardData?.in_season_trends?.pts_change?.week || null;
    const isThisYearBeforeOct8th = activeCardData?.card?.year === String(new Date().getFullYear()) && (new Date().getMonth() < 9 || (new Date().getMonth() === 9 && new Date().getDate() < 8));
    const isValidStatsPeriodType = activeCardData?.card?.stats_period && ['REGULAR', 'PRESEASON', 'POSTSEASON'].includes(activeCardData.card.stats_period.type);
    if (isThisYearBeforeOct8th === false || !isValidStatsPeriodType) {
        weeklyChangePoints = null; // Only show for current year cards
    }
    const weeklyChangePointsColor = weeklyChangePoints ? (weeklyChangePoints > 0 ? 'text-(--green)' : 'text-(--red)') : '';
    const weeklyChangePointsSymbol = weeklyChangePoints ? (weeklyChangePoints > 0 ? '▲' : '▼') : '';

    // Handle Image Generation
    const handleGenerateImage = (data: ShowdownBotCardAPIResponse) => {
        if (!data?.card || context === 'custom') return;
        
        console.log("Starting image generation...", parent);
        const requestId = ++latestImageRequestRef.current;
        setIsGeneratingImage(true);
        
        generateCardImage(data, session?.access_token)
            .then((data) => {
                console.log("Received card data with image:", data);
                if (data && requestId === latestImageRequestRef.current) {
                    setInternalCardData(data as ShowdownBotCardAPIResponse);
                }
            })
            .catch((error) => {
                console.error("Error generating card image:", error);
            })
            .finally(() => {
                if (requestId !== latestImageRequestRef.current) return;
                restyleFromImagePathRef.current = null;
                setIsGeneratingImage(false);
            });
    };

    // Handle Showdown Set Switching (enableSetSwitcher only)
    const handleSetSwitch = async (newSet: string) => {
        const currentCard = activeCardData?.card;
        if (!currentCard || newSet === currentCard.set || isSwitchingSet) return;

        setIsSwitchingSet(true);
        setSetSwitchError(null);

        try {
            const source = currentCard.is_wotc ? CardSource.WOTC : CardSource.BOT;
            const matches = await fetchCardData(source, {
                bref_id: currentCard.bref_id,
                year: currentCard.year,
                is_pitcher: currentCard.chart?.is_pitcher,
                showdown_set: [newSet],
                limit: 1,
            });

            const match = matches?.[0];
            if (!match?.card_id) {
                setSetSwitchError(`Not available in the ${newSet} set`);
                return;
            }

            // WOTC/WBC search rows embed full card_data; BOT rows don't, so hydrate by id.
            const cardResponse = match.card_data
                ? ({ card: match.card_data, error: null, error_for_user: null } as ShowdownBotCardAPIResponse)
                : await fetchCardById(match.card_id, 'card-detail-set-switch');

            setInternalCardData(cardResponse);

            // This particular set's image may not be pre-rendered yet — generate it on demand,
            // same as the initial-load path does.
            const isDataWithoutImage = !cardResponse.card?.image.output_file_name && !cardResponse.card?.image.storage_path && cardResponse.card;
            if (isDataWithoutImage) {
                handleGenerateImage(cardResponse);
            }
        } catch (error) {
            console.error("Error switching showdown set:", error);
            setSetSwitchError(`Not available in the ${newSet} set`);
        } finally {
            setIsSwitchingSet(false);
        }
    };

    // Changing opacity of color
    const addOpacityToRGB = (rgbColor: string, opacity: number) => {
        // Extract numbers from rgb(r, g, b) format
        const match = rgbColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (match) {
            const [, r, g, b] = match;
            return `rgba(${r}, ${g}, ${b}, ${opacity})`;
        }
        return rgbColor; // fallback if parsing fails
    };

    const teamGlowColor = activeCardData?.card?.image ? (
        ( ['NYM', 'SDP', 'NYY'].includes(activeCardData?.card?.team || '') && isDark && !activeCardData.card.wbc_team)
            ? enhanceColorVisibility(activeCardData?.card?.image?.color_secondary)
            : enhanceColorVisibility(activeCardData?.card?.image?.color_primary)
    ) : 'rgb(0, 0, 0)';

    // Team colors for visual panels (NYM/SDP swap for better contrast)
    const team = activeCardData?.card?.wbc_team || activeCardData?.card?.team;
    const rawPrimary = activeCardData?.card?.image.color_primary || 'rgb(0,0,0)';
    const rawSecondary = activeCardData?.card?.image.color_secondary || 'rgb(0,0,0)';
    const mechPrimaryColor = ['NYM', 'SDP'].includes(team || '') ? rawSecondary : rawPrimary;
    const mechSecondaryColor = ['NYM', 'SDP'].includes(team || '') ? rawPrimary : rawSecondary;

    const getBlankPlayerImageName = (): string => {
        const setName = (showdownSetForPlaceholder || userShowdownSet || '2001').toLowerCase();
        const appearance = isDark ? 'dark' : 'light';
        return `/images/blank_players/blankplayer-${setName}-${appearance}.png`;
    };

    const cardImageMaxHeight = '@xl:max-h-[600px] @xl:overflow-hidden @3xl:max-h-[700px]';

    /** Live game + Card vs Real Stats — beside the card image, or down in the analysis grid while
     * the style editor holds that spot */
    const realStatsPanels = (
        <>
            {/* Game Boxscore — desktop only */}
            {showGameBoxscore() && activeCardData?.latest_game_box_score && (
                <div className='hidden @xl:block'>
                    <GameItem
                        game={fromBoxscoreDetail(activeCardData.latest_game_box_score)}
                        playerIdForLinescoreHighlight={activeCardData?.card?.mlb_id ?? undefined}
                    />
                </div>
            )}

            {/* Card vs Real Stats */}
            <SectionPanel isLoading={isLoadingPanels} title="Card vs Real Stats" subtitle='Compares projected card outcomes vs real stats'>
                
                <RealVsProjectedVisual
                    realVsProjectedData={activeCardData?.card?.real_vs_projected_stats}
                    statRanges={seasonStatRanges}
                    isLoading={isRangesLoading}
                    playerType={activeCardData?.card?.player_type?.toUpperCase() as 'HITTER' | 'PITCHER'}
                    simStats={simStats}
                />
                <div className="flex flex-col text-[10px] opacity-40 space-y-0.5 pt-1">
                    <i>* Real stat is estimated (limited data, adjusted era, etc.)</i>
                    <i>** Projection includes post-processing accuracy correction</i>
                </div>
            </SectionPanel>
        </>
    );

    // MARK: MAIN CONTENT
    return (
        <div 
            className="
                @container
                w-full
                overflow-visible @2xl:overflow-y-auto
                p-4 @6xl:px-8 space-y-4
                h-full
                pb-24
            "
        >

            {/* Warnings */}
            {activeCardData?.card?.warnings && activeCardData.card.warnings.length > 0 && (
                <div className="bg-(--warning)/5 border border-(--warning) text-(--warning) p-2 rounded-card">
                    <Heading level="panel" as="h4">Warnings</Heading>
                    <ul className="list-disc list-inside">
                        {activeCardData.card.warnings.map((warning, index) => (
                            <li key={index}>{warning}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Name and player attributes. Right padding keeps the row clear of the Modal's floating
                close button (most CardDetails render in a Modal). */}
            <div className="
                flex flex-wrap items-center
                gap-1 mb-2 pr-8
            ">
                <a 
                    href={activeCardData?.card?.bref_url || '#'} 
                    className='font-display uppercase text-3xl leading-none text-(--text-primary) hover:text-(--showdown-blue) transition-colors pr-2'
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    {activeCardData?.card?.name.toUpperCase() || ""}
                </a>

                {/* Card Set */}
                {enableSetSwitcher && activeCardData?.card ? (
                    <div className="flex flex-col items-start">
                        <CustomSelect
                            className="w-28"
                            size="sm"
                            value={activeCardData.card.set}
                            onChange={handleSetSwitch}
                            options={SET_SELECT_OPTIONS}
                            showDropdownArrow={true}
                            disabled={isSwitchingSet}
                        />
                        {setSwitchError && (
                            <span className="text-[10px] text-(--showdown-red) font-semibold whitespace-nowrap">{setSwitchError}</span>
                        )}
                    </div>
                ) : (
                    activeCardData?.card?.set && <SetBadge set={activeCardData.card.set} />
                )}

                {/* Iterate through attributes */}
                {Object.entries(cardAttributes)
                    .filter(([, value]) => value != null && value !== '')
                    .map(([key, value]) => (
                    <Plate key={key} size="md">
                        <span>{value}</span>
                        
                        {/* Change in Points Weekly */}
                        { (weeklyChangePoints && key === "points" && String(new Date().getFullYear()) === String(activeCardData?.card?.year || "n/a")) && (
                            <div className={`text-xs ${weeklyChangePointsColor}`}>
                                {weeklyChangePointsSymbol} {Math.abs(weeklyChangePoints)} THIS WEEK
                            </div>
                        )}
                    </Plate>
                ))}

                {/* Player image source (Showdown Bot library, user's Drive library, upload, link) */}
                <ImageSourceBadge source={activeCardData?.card?.image?.source} />
            </div>

            {/* Action bar — caller-supplied controls (`actionBarContent`, e.g. a release card's tags)
                on the left, Customize and the primary `onDraft` action on the right. Inside a Modal or the
                search sidebar (any PinnedFooterScrollArea) it moves to the pinned footer so it stays
                reachable while the detail scrolls; elsewhere it's a row under the header. */}
            {activeCardData?.card && (context !== 'custom' || onDraft || actionBarContent) && (
                <PinnedFooterPortal>
                <div className="flex flex-wrap items-center gap-x-6 gap-y-3 w-full">
                    {actionBarContent && (
                        <div className="flex flex-wrap items-start gap-x-6 gap-y-3 min-w-0">
                            {actionBarContent}
                        </div>
                    )}
                    <div className="ml-auto flex items-center gap-2">
                        {/* Customize — edits this card's style inline (`styleEditor`), otherwise opens the
                            Custom Card Builder prefilled with this card */}
                        {context !== 'custom' && (
                            <button
                                type="button"
                                onClick={() => styleEditor
                                    ? setIsStyleEditorOpen(open => !open)
                                    : activeCardData.card && customizeCard(activeCardData.card)}
                                title={styleEditor ? "Edit this card's style" : 'Open in the Custom Card Builder'}
                                className={buttonClass('secondary', 'sm', `relative ${showStyleEditor ? 'bg-(--background-tertiary)' : ''}`)}
                            >
                                <FaWandMagicSparkles className="w-3.5 h-3.5" />
                                Customize
                                {isStyleCustomized && (
                                    <span title="This card has its own style" className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-(--showdown-blue-fill)" />
                                )}
                            </button>
                        )}

                        {onDraft && (
                            <button
                                type="button"
                                disabled={draftDisabled}
                                title={draftDisabled ? 'Saving your last pick…' : undefined}
                                onClick={onDraft}
                                className={buttonClass('feature', 'sm')}
                            >
                                <FaPlus className="w-3.5 h-3.5" />
                                {draftLabel}
                            </button>
                        )}
                    </div>
                </div>
                </PinnedFooterPortal>
            )}

            {/* Tooltip */}
            {tooltip && (
                <div className="bg-(--showdown-red)/5 border border-(--showdown-red) text-(--showdown-red) p-2 rounded-card text-xs">
                    {tooltip}
                </div>
            )}

            {/* Notes */}
            {activeCardData?.card?.notes && (
                <div className="
                    bg-(--secondary)/50
                    border border-(--form-element)
                    rounded-card
                    p-3
                    text-xs
                ">
                    {activeCardData.card.notes}
                </div>
            )}

            {/* Image and Breakdown Tables. While customizing, the style editor takes the image's spot
                (left, or top on mobile) and the card moves beside/below it so its re-render stays in
                view. Keyed so the image doesn't remount when the editor slots in ahead of it. */}
            <div
                className={`
                    grid grid-cols-1 ${showStyleEditor ? '@xl:grid-cols-[9fr_11fr]' : '@xl:grid-cols-[11fr_9fr]'}
                    gap-4
                    pt-2
                `}
            >
                {/* Card Style editor. Side by side, it's pulled out of flow so the card image alone sets
                    the row height — the editor matches it and scrolls its fields inside. */}
                {showStyleEditor && styleEditor && (
                    <div key="style-editor" className="relative">
                        <div className="flex flex-col @xl:absolute @xl:inset-0">
                            <CardStyleEditor {...styleEditor} card={activeCardData?.card} onClose={() => setIsStyleEditorOpen(false)} />
                        </div>
                    </div>
                )}

                {/* Card Image */}
                <div key="card-image" className={`
                    relative
                    h-auto
                    w-full
                    px-0 @md:px-3 @xl:px-0
                `}>
                    {/* Game Boxscore — on mobile sits above card, hidden here on xl (shown in right col) */}
                    {showGameBoxscore() && activeCardData?.latest_game_box_score && (
                        <div className='@xl:hidden mb-3'>
                            <GameItem
                                game={fromBoxscoreDetail(activeCardData.latest_game_box_score)}
                                playerIdForLinescoreHighlight={activeCardData?.card?.mlb_id ?? undefined}
                            />
                        </div>
                    )}
                    {/* Wrapper shrinks to the rendered image so the processing ring traces the
                        card's actual edges rather than the full grid column. */}
                    <div className="relative w-fit @2xl:mx-auto">
                        <img
                            src={cardImagePath == null ? getBlankPlayerImageName() : cardImagePath}
                            alt="Blank Player"
                            key={activeCardData?.card?.image.output_file_name || (isDark ? 'blank-dark' : 'blank-light')}
                            className={`
                                block
                                @2xl:mx-auto
                                ${cardImageMaxHeight}
                                ${CARD_IMAGE_RADIUS} overflow-hidden
                                object-contain
                                fade-in
                                ${isLoadingOverall ? 'blur-xs' : ''}
                                ${activeCardData?.card?.image ? 'card-glow-pulse' : ''}
                            `}
                            style={activeCardData?.card?.image ? {
                                '--card-glow-lo': addOpacityToRGB(teamGlowColor, 0.52),
                                '--card-glow-md': addOpacityToRGB(teamGlowColor, 0.66),
                                '--card-glow-hi': addOpacityToRGB(teamGlowColor, 0.85),
                            } as CSSProperties : {
                                boxShadow: `0 0 10px color-mix(in srgb, var(--tertiary) 33%, transparent),
                                            0 0 20px color-mix(in srgb, var(--tertiary) 44%, transparent),
                                            0 0 30px color-mix(in srgb, var(--tertiary) 34%, transparent)`
                            }}
                        />

                        {/* Loading Overlay — orbiting border ring + glass status pill */}
                        {isLoadingOverall && (
                            <div
                                className="absolute inset-0 flex items-center justify-center"
                                style={activeCardData?.card?.image ? {
                                    '--ring-a': teamGlowColor,
                                    '--ring-b': teamGlowColor,
                                } as CSSProperties : undefined}
                            >
                                <div className="card-processing-ring card-processing-ring--glow" />
                                <div className="card-processing-ring" />
                                <div className="fade-in flex flex-col items-center gap-4 w-1/2 max-w-56">
                                    <ShowdownBotLogo className="card-processing-logo w-full" />
                                    <div className="
                                        flex items-center gap-2
                                        px-4 py-2
                                        rounded-control whitespace-nowrap
                                        bg-(--background-secondary)
                                        border border-(--divider)
                                        shadow-overlay
                                    ">
                                        <div className="card-processing-spinner" />
                                        <p className="text-xs font-semibold tracking-wide">
                                            {isSwitchingSet ? 'Switching Set' : `Generating ${isGeneratingImage ? 'Image' : 'Card'}`}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right column */}
                {!showStyleEditor && (
                    <div key="right-column" className={`flex flex-col gap-3 ${cardImageMaxHeight}`}>
                        {realStatsPanels}
                    </div>
                )}

            </div>

            {/* Below-fold grid: analysis panels + trend graphs */}
            <div className="w-full grid grid-cols-1 @xl:grid-cols-2 gap-4">

                {/* Card vs Real Stats, moved down while the style editor sits beside the card */}
                {showStyleEditor && realStatsPanels}

                {/* Points Breakdown */}
                {!activeCardData?.card?.is_wotc && (
                    <SectionPanel isLoading={isLoadingPanels} title="Points Breakdown">
                        <PointsContributionBars
                            pointsBreakdownData={activeCardData?.card?.points_breakdown}
                            ip={activeCardData?.card?.ip}
                        />
                        <i className="text-[10px] opacity-40">* Slashlines/HR projections based on Steroid Era opponent.</i>
                    </SectionPanel>
                )}

                {/* Chart Accuracy */}
                {!activeCardData?.card?.is_wotc && (
                    <SectionPanel
                        isLoading={isLoadingPanels}
                        title={`Chart Selection - Version ${activeCardData?.card?.chart_version || '1'}`}
                        subtitle={activeCardData?.card?.command_out_selection ? "Version 1 is hand-curated. Scores shown are each chart's true accuracy" : undefined}
                    >
                        <ChartSelectionBreakdown
                            chartAccuracyData={activeCardData?.card?.command_out_accuracy_breakdowns}
                            commandOutAccuraciesData={activeCardData?.card?.command_out_accuracies}
                            selectedChartVersion={activeCardData?.card?.chart_version || 1}
                            selectedChart={activeCardData?.card?.selected_command_outs}
                            selection={activeCardData?.card?.command_out_selection}
                        />
                    </SectionPanel>
                )}

                {/* Opponent Breakdown */}
                <SectionPanel 
                    isLoading={isLoadingPanels} 
                    title="Baseline Opponent"
                    subtitle={`The avg opposing pitcher/hitter used to create the card. Adjusted to reflect run scoring environment of the ${activeCardData?.card?.era}`}
                >
                    <BaselineOpponentBreakdown
                        chart={activeCardData?.card?.chart?.opponent}
                        primaryColor={mechPrimaryColor}
                        secondaryColor={mechSecondaryColor}
                    />
                </SectionPanel>

                {/* Outcome Distribution */}
                <SectionPanel isLoading={isLoadingPanels} title="Outcome Probabilities" subtitle="Use baseline or search for a specific opponent">
                    <OutcomeProbability
                        chart={activeCardData?.card?.chart}
                        primaryColor={mechPrimaryColor}
                        secondaryColor={mechSecondaryColor}
                        set={activeCardData?.card?.set}
                    />
                </SectionPanel>                

                {/* Trend Graphs */}
                {!hideTrendGraphs && (
                    <>
                        <SectionPanel isLoading={isLoadingPanels} title="Career Trends">
                            <ChartPlayerPointsTrend
                                title="Career Trends"
                                trendData={activeCardData?.historical_season_trends?.yearly_trends || null}
                            />
                        </SectionPanel>
                        <SectionPanel isLoading={isLoadingPanels} title={activeCardData?.in_season_trends && activeCardData?.card?.year ? `${activeCardData?.card?.year} Card Evolution` : "Year Card Evolution (Available 2020+)"}>
                            <ChartPlayerPointsTrend
                                title={activeCardData?.in_season_trends && activeCardData?.card?.year ? `${activeCardData?.card?.year} Card Evolution` : "Year Card Evolution (Available 2020+)"}
                                trendData={activeCardData?.in_season_trends?.cumulative_trends || null}
                            />
                        </SectionPanel>
                    </>
                )}

                {/* Most Similar WOTC Cards */}
                <SectionPanel
                    isLoading={isLoadingPanels}
                    title="Most Similar WOTC Cards"
                    subtitle={`Top matches by chart similarity`}
                >
                    <CardComps
                        card={activeCardData?.card ?? null}
                        isLoading={isLoadingPanels}
                    />
                </SectionPanel>

            </div>

        </div>
    );
});