/**
 * @fileoverview CustomCardBuilder - Main card creation and customization interface
 * 
 * This is the primary component for the MLB Showdown card builder application,
 * providing a comprehensive interface for creating custom player cards with
 * extensive customization options including player search, set configuration,
 * image customization, and chart settings.
 * 
 * Key Features:
 * - Advanced player search with autocomplete
 * - Real-time card preview and generation
 * - Comprehensive form sections for all card aspects
 * - Live game integration for current players
 * - Local storage persistence of settings
 * - Responsive design for mobile and desktop
 * - File upload and image URL support
 * - Statistical analysis and trend visualization
 * 
 * The component manages complex state for form data, API calls, loading states,
 * and user interactions while providing a smooth, intuitive user experience.
 */

// ----------------------------------
// MARK: - Imports
// ----------------------------------

import { useAuth } from '../auth/AuthContext';
import { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import FormInput from './FormInput';
import FormSection from './FormSection';
import FormDropdown from './FormDropdown';
import FormEnabler from './FormEnabler';
import { PlayerSearchInput } from './PlayerSearchInput';
import CustomSelect from '../shared/CustomSelect';
import type { SelectOption } from '../shared/CustomSelect';
import { useSiteSettings, showdownSets } from '../shared/SiteSettingsContext';
import { hasVariableSpeedSet } from '../../functions/showdownSets';
import { setSelectOption } from '../shared/SetBadge';
import { WhatsNewBanner } from '../shared/WhatsNewBanner';
import { InfoTooltip } from '../shared/InfoTooltip';

// Popovers
import { ToastMessage, type ToastStatus } from '../shared/ToastMessage';
import { Plate } from '../shared/Plate';
import { CardDetail } from '../cards/CardDetail';
import { GalleryTabContent } from '../gallery/GalleryTabContent';

// API
import { buildCustomCard, type ShowdownBotCard, type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import { fetchSplits } from '../../api/mlbAPI';
// Icons
import {
    FaTable, FaImage, FaLayerGroup, FaUser, FaBaseballBall, FaExclamationCircle,
    FaChevronCircleRight, FaChevronCircleLeft, FaChevronCircleUp, FaChevronCircleDown,
    FaImages, FaGoogleDrive, FaListOl
} from 'react-icons/fa';
import {
    FaShuffle, FaXmark, FaRotateLeft, FaCircleCheck, FaArrowDown
} from 'react-icons/fa6';
import CardBuildIcon from './CardBuildIcon';
import ImageLibraryOrderHint from './ImageLibraryOrderHint';
import Set2026Notice from './Set2026Notice';
import { SetStyleFields, ImageStyleFields } from './CardStyleFields';
import { NewBadge } from '../shared/NewBadge';
import { setStyleSummary, imageStyleSummary, chartVersionOptions } from './cardStyle';
import { formSectionSummary } from './FormSectionSummary';
import { formInputsFromCard, type CustomizeCardRouteState } from './customizeCard';

import { Heading } from '../shared/Heading';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { Tabs, type TabItem } from '../shared/Tabs';
import { smoothScrollBehavior } from '../../hooks/usePrefersReducedMotion';
// ----------------------------------
// MARK: - Form Interface
// ----------------------------------

/** State for the custom card form */
export interface CustomCardFormState {
    // Name and Year
    name: string; // ex: "Mike Trout"
    player_id?: string | null; // ex: "troutmi01"
    player_type_override?: string; // ex: "Hitter" or "Pitcher"
    year: string; // ex: "2023"
    stats_period_type: string; // e.g. "REGULAR"
    start_date?: string | null; // e.g. "2023-05-01"
    end_date?: string | null; // e.g. "2023-10-01"
    split?: string | null; // e.g. "First Half"
    league: string; // e.g. "MLB" or "MILB"
    team_selection?: string; // e.g. "GAMES_PLAYED". Only applies to multi-year stats periods (CAREER, ranges, combos)

    // Set
    expansion: string; // e.g. "BS"
    set_number?: string | null; // e.g. "001"
    edition: string; // e.g. "Cooperstown"
    add_one_to_set_year: boolean; // Whether to show the year + 1 in the set section
    show_year_text: boolean; // Whether to show the year text as a label on the card
    disable_display_text_on_card?: boolean; // Whether to hide the stats period display text (e.g. split/date range) banner on the card. Only applicable for non-Base Set expansions or All-Star Game/Postseason editions

    // Image
    image_source: string; // e.g. "Auto"
    image_parallel: string; // e.g. "Rainbow Foil"
    image_coloring: string; // e.g. "Primary"
    image_glow_multiplier: string; // e.g. "Glow 1x"
    image_url?: string | null; // e.g. "https://example.com/image.png"
    image_upload?: File | null; // For file uploads

    // Image Extras
    is_bordered: boolean; // Whether to add a border to the image
    is_dark_mode: boolean; // Whether the card is in dark mode
    hide_team_logo: boolean; // Whether to remove team branding from the image
    stat_highlights_type?: string; // e.g. "ALL", "OLD", "MODERN"
    nickname_index?: string; // e.g. "NICKNAME 1",

    // Chart
    chart_version?: string; // e.g. "1"
    era?: string; // e.g. "Dynamic"
    is_variable_speed_00_01?: boolean; // Whether to use variable speed for 00-01
    regress_small_sample_to_replacement?: boolean; // Whether to regress small sample stats toward replacement level

    // Added in post-processing, not user inputs
    randomize?: boolean; // Tags if user randomly generated the card
    name_original?: string; // Original name inputted by user
}

/** Default values for the custom card form */
export const FORM_DEFAULTS: CustomCardFormState = {
    name: "", 
    player_id: null,
    player_type_override: undefined,
    year: "", 
    stats_period_type: "REGULAR", 
    start_date: null, 
    end_date: null, 
    split: null,
    league: 'MLB',
    team_selection: 'GAMES_PLAYED',

    expansion: "BS", 
    set_number: null, 
    edition: "NONE",
    add_one_to_set_year: false,
    show_year_text: false,
    disable_display_text_on_card: false,

    image_source: "AUTO", 
    image_parallel: "NONE", 
    image_coloring: "PRIMARY", 
    image_glow_multiplier: "1",
    image_url: null, 
    image_upload: null,

    is_bordered: false, 
    is_dark_mode: false, 
    hide_team_logo: false,
    stat_highlights_type: "NONE", 
    nickname_index: "NONE", 
    
    chart_version: "1",
    era: "DYNAMIC",
    is_variable_speed_00_01: false,
    regress_small_sample_to_replacement: false
};

/** Whether a year string spans multiple seasons (CAREER, ranges like "2000-2004", or combos like "2006+2014") */
const isMultiYearInput = (year: string): boolean => {
    const trimmed = year.trim();
    if (!trimmed) return false;
    return trimmed.toUpperCase() === 'CAREER' || trimmed.includes('-') || trimmed.includes('+');
};

// ----------------------------------
// MARK: - Local Storage
// ----------------------------------

const STORAGE_KEY = 'customCardFormSettings-V2';
/** Bump when the 2026 notice content changes so previously dismissed users see it again. */
const SET_2026_NOTICE_KEY = 'customCardBuilder2026Phase4Notice';

/** Save form settings to localStorage */
const saveFormSettings = (formData: CustomCardFormState) => {
    try {
        // Don't save certain fields that shouldn't persist
        const { image_upload, ...settingsToSave } = formData;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settingsToSave));
    } catch (error) {
        console.warn('Failed to save form settings:', error);
    }
};

/** Load form settings from localStorage */
const loadFormSettings = (): CustomCardFormState => {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            const parsedSettings = JSON.parse(saved);
            // Merge with defaults to ensure all required fields exist
            return { ...FORM_DEFAULTS, ...parsedSettings };
        }
    } catch (error) {
        console.warn('Failed to load form settings:', error);
    }
    return FORM_DEFAULTS;
};

// ----------------------------------
// MARK: - Custom Card Component
// ----------------------------------

type CustomCardBuilderProps = {
    // Mark as hidden, disables actions
    isHidden?: boolean;
}

type PreviewTab = 'preview' | 'gallery';

/** The preview / gallery switch, shared by the mobile and desktop tab bars. */
const PREVIEW_TABS: TabItem<PreviewTab>[] = [
    { id: 'preview', label: 'Preview', shortLabel: 'Card', icon: <CardBuildIcon size="1.5em" /> },
    { id: 'gallery', label: 'Gallery', icon: <FaImages /> },
];

/** 
 * Card Creation Page for users to create and customize their own cards. 
*/
function CustomCardBuilder({ isHidden }: CustomCardBuilderProps) {

    // Card States
    const { userShowdownSet } = useSiteSettings();
    const [showdownSetOverride, setShowdownSetOverride] = useState<string | null>(null);
    const effectiveShowdownSet = showdownSetOverride ?? userShowdownSet;
    const isSet00_01 = hasVariableSpeedSet([effectiveShowdownSet]);
    const [showdownBotCardData, setShowdownBotCardData] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isProcessingCard, setIsProcessingCard] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [query, _] = useState("");
    const [isFormCollapsed, setIsFormCollapsed] = useState(false);
    // True once the expand transition finishes; panel content is clipped until then
    const [isFormSettled, setIsFormSettled] = useState(true);
    const toggleFormCollapsed = () => {
        setIsFormSettled(false);
        setIsFormCollapsed(!isFormCollapsed);
    };
    const [activePreviewTab, setActivePreviewTab] = useState<PreviewTab>('preview');
    const [galleryRefreshKey, setGalleryRefreshKey] = useState(0);
    const [splitOptions, setSplitOptions] = useState<SelectOption[]>([]);
    const [is2026NoticeDismissed, setIs2026NoticeDismissed] = useState(
        () => localStorage.getItem(SET_2026_NOTICE_KEY) === 'true'
    );
    const previewSectionRef = useRef<HTMLDivElement>(null);

    // User Context
    const { user, session } = useAuth();

    // Routing (used to receive cards handed over via "Customize")
    const location = useLocation();
    const navigate = useNavigate();

    // Loading Status
    const [loadingStatus, setLoadingStatus] = useState<ToastStatus | null>(null);
    const [, setIsLoadingStatusVisible] = useState(false);
    const [isLoadingStatusExiting, setIsLoadingStatusExiting] = useState(false);

    // Animation
    const animationTw = 'transition-all duration-200 ease-in-out';
    const formPanelTransitionTw = 'duration-300 ease-in-out';

    // Define the form state
    const [form, setForm] = useState<CustomCardFormState>(loadFormSettings());
    const disableBuildButton = (
        !form.name.trim()
        || form.year.trim().length < 4
        || (form.stats_period_type === "SPLIT" && !form.split)
        || isProcessingCard
    )
    const isMultiYear = isMultiYearInput(form.year);

    const [imageUploadPreview, setImageUploadPreview] = useState<string | null>(null);
    const getImagePreview = (): string | null => {
        switch (form.image_source) {
            case "UPLOAD":
                return imageUploadPreview;
            case "LINK":
                return form.image_url || null;
            default:
                return null;
        }
    };



    // ---------------------------------
    // MARK: Form Options
    // ---------------------------------

    // Stats Period Options
    const statsPeriodOptions: SelectOption[] = [
        { 'value': 'REGULAR', 'label': 'Regular Season', 'symbol': '⚾' },
        { 'value': 'POST', 'label': 'Postseason', 'symbol': '🏆', 'borderColor': 'border-(--gold)'},
        { 'value': 'DATES', 'label': 'Date Range', 'symbol': '📅', 'borderColor': 'border-(--showdown-red)' },
        { 'value': 'SPLIT', 'label': 'Split', 'symbol': '🔀', 'borderColor': 'border-(--showdown-blue)' },
    ]

    const leagueOptions: SelectOption[] = [
        { 'value': 'MLB', 'label': 'MLB' },
        { 'value': 'MILB', 'label': 'MiLB' }
    ]

    // Team Selection Options (only shown for multi-year stats periods)
    const teamSelectionOptions: SelectOption[] = [
        { 'value': 'GAMES_PLAYED', 'label': 'Most Games Played' },
        { 'value': 'LAST_TEAM', 'label': 'Last Team' },
        { 'value': 'FIRST_TEAM', 'label': 'First Team' },
    ]

    // Image Source Options
    const imageSourceOptions: SelectOption[] = [
        { 'value': 'AUTO', 'label': 'Auto', 'symbol': '⚙️' },
        { 'value': 'LINK', 'label': 'Link', 'symbol': '🔗' },
        { 'value': 'UPLOAD', 'label': 'Upload', 'symbol': '📤' },
    ]

    const eraOptions: SelectOption[] = [
        { "value": "DYNAMIC", "label": "Dynamic" },
        { "value": "PRE 1900 ERA", "label": "Pre-1900 (1800-1899)" },
        { "value": "DEAD BALL ERA", "label": "Dead Ball (1900-1919)" },
        { "value": "LIVE BALL ERA", "label": "Live Ball (1920-1941)" },
        { "value": "INTEGRATION ERA", "label": "Integration (1942-1960)" },
        { "value": "EXPANSION ERA", "label": "Expansion (1961-1976)" },
        { "value": "FREE AGENCY ERA", "label": "Free Agency (1977-1993)" },
        { "value": "STEROID ERA", "label": "Steroid (1994-2009)" },
        { "value": "POST STEROID ERA", "label": "Post-Steroid (2010-2014)" },
        { "value": "STATCAST ERA", "label": "Statcast (2015-2022)" },
        { "value": "PITCH CLOCK ERA", "label": "Pitch Clock (2023+)" },
    ]

    // ----------------------------------
    // MARK: - Sections
    // ----------------------------------

    // Manage open/closed states of form sections, persisted in localStorage
    const [sectionStates, setSectionStates] = useState<Record<string, boolean>>(() => {
        try {
            const saved = localStorage.getItem('customCardSectionStates');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Failed to load section states:', error);
        }
        // Default states - only Player section open by default
        return {
            'Player': false,
            'Set': false,
            'Image': false,
            'Chart': false
        };
    });

    // Save section states to localStorage when they change
    useEffect(() => {
        try {
            localStorage.setItem('customCardSectionStates', JSON.stringify(sectionStates));
        } catch (error) {
            console.warn('Failed to save section states:', error);
        }
    }, [sectionStates]);

    // Helper function to toggle section state
    const toggleSection = (sectionName: string) => {
        setSectionStates(prev => ({
            ...prev,
            [sectionName]: !prev[sectionName]
        }));
    };

    const handleTabChange = (tab: PreviewTab) => {
        setActivePreviewTab(tab);
    };

    const getSectionSummary = (sectionName: string) => {
        const summaries: SelectOption[] = [];

        switch (sectionName.toLowerCase()) {
            case 'player':
                if (form.name) summaries.push({ label: 'Name', value: form.name });
                if (form.year) summaries.push({ label: 'Year', value: form.year });
                if (form.stats_period_type !== FORM_DEFAULTS.stats_period_type) {
                    const periodOption = statsPeriodOptions.find(opt => opt.value === form.stats_period_type);
                    summaries.push(periodOption || { label: 'Period', value: form.stats_period_type });
                }
                if (form.start_date) summaries.push({ label: 'Start', value: form.start_date });
                if (form.end_date) summaries.push({ label: 'End', value: form.end_date });
                if (form.split) {
                    const yearNum = parseInt(form.year, 10);
                    const splitLabel = (!isNaN(yearNum) && yearNum >= 2026)
                        ? (splitOptions.find(o => o.value === form.split)?.label ?? form.split)
                        : form.split;
                    summaries.push({ label: 'Split', value: splitLabel });
                }
                if (form.league !== FORM_DEFAULTS.league) {
                    const leagueOption = leagueOptions.find(opt => opt.value === form.league);
                    summaries.push(leagueOption || { label: 'League', value: form.league });
                }
                if (isMultiYearInput(form.year) && form.team_selection && form.team_selection !== FORM_DEFAULTS.team_selection) {
                    const teamSelectionOption = teamSelectionOptions.find(opt => opt.value === form.team_selection);
                    summaries.push({ ...(teamSelectionOption || { value: form.team_selection }), label: 'Team' });
                }
                break;

            case 'set':
                summaries.push(...setStyleSummary(form, FORM_DEFAULTS, form.set_number));
                break;

            case 'image':
                if (form.image_source !== FORM_DEFAULTS.image_source) {
                    const sourceOption = imageSourceOptions.find(opt => opt.value === form.image_source);
                    summaries.push(sourceOption || { label: 'Source', value: form.image_source });
                }
                summaries.push(...imageStyleSummary(form, FORM_DEFAULTS, form.image_source === FORM_DEFAULTS.image_source));
                break;

            case 'chart':
                if (form.chart_version !== FORM_DEFAULTS.chart_version) {
                    const chartOption = chartVersionOptions.find(opt => opt.value === form.chart_version);
                    summaries.push({ ...(chartOption || { value: form.chart_version || "1" }), label: 'Chart Version' });
                }
                if (form.era !== FORM_DEFAULTS.era) {
                    const eraOption = eraOptions.find(opt => opt.value === form.era);
                    summaries.push({ ...(eraOption || { value: form.era || "DYNAMIC" }), label: 'Era' });

                }
                if (isSet00_01 && form.is_variable_speed_00_01 !== FORM_DEFAULTS.is_variable_speed_00_01) summaries.push({ value: 'VARIABLE SPEED', borderColor: 'border-(--green)' });
                if (form.regress_small_sample_to_replacement !== FORM_DEFAULTS.regress_small_sample_to_replacement) summaries.push({ value: 'REGRESS SMALL SAMPLE', borderColor: 'border-(--green)' });
                break;
        }
        
        return summaries;
    };

    const sectionWhenClosed = (sectionName: string) => formSectionSummary(getSectionSummary(sectionName));

    // ---------------------------------
    // MARK: Build Processing
    // ---------------------------------

    const submitCard = async (card_payload: any) => {
        // Implement your submit logic here

        try {

            // Capture the current subMessage before any state changes
            const currentSubMessage = loadingStatus?.subMessage || "";

            // Set Is Loading
            setIsProcessingCard(true);

            // TODO: Handle image uploads
            console.log("Building card with form data:", card_payload);

            // Prepare payload based on image source
            let finalPayload = { ...card_payload };

            // Team selection only applies to multi-year stats periods. For single-year cards the
            // dropdown is hidden, so default to the player's last team (and force it, so a stale
            // preference from a prior multi-year search can't affect a single-year card).
            if (!isMultiYearInput(finalPayload.year || '')) {
                finalPayload.team_selection = 'LAST_TEAM';
            }

            // Handle image source logic
            if (card_payload.image_source === 'UPLOAD' && card_payload.image_upload) {
                // Keep the file for upload
                finalPayload.image_upload = card_payload.image_upload;
            } else if (card_payload.image_source === 'LINK' && card_payload.image_url) {
                // Remove file, keep URL
                delete finalPayload.image_upload;
                finalPayload.image_url = card_payload.image_url;
            } else {
                // Auto or no image - remove both file and URL
                delete finalPayload.image_upload;
                delete finalPayload.image_url;
            }

            // Define datasource
            // Use MLB API if year has 2026+
            let isMlbApiYear = false;
            if (finalPayload.year) {
                const yearNums = (finalPayload.year as string).match(/\d+/g)?.map(Number) ?? [];
                const maxYear = yearNums.length > 0 ? Math.max(...yearNums) : 0;
                isMlbApiYear = maxYear >= 2026;
                finalPayload.datasource = isMlbApiYear ? 'MLB_API' : 'BREF';
            }

            // For 2026+ splits the stored value is a situation code — resolve to description + code
            if (isMlbApiYear && finalPayload.split) {
                const matched = splitOptions.find(o => o.value === finalPayload.split);
                if (matched) {
                    finalPayload.situation_code = matched.value;
                    finalPayload.split = matched.label;
                }
            }
            const cardData = await buildCustomCard({
                ...finalPayload,

                // Default parameters/settings
                set: effectiveShowdownSet,
                is_running_on_website: true,
                image_output_folder_path: "static/output",
                show_historical_points: true,
                season_trend_date_aggregation: 'WEEK',
                user_id: user?.id,
            }, session?.access_token);
            
            // Handle Errors
            setErrorMessage(cardData.error_for_user);
            if (cardData.error_for_user) {
                console.log("Card build error:", cardData);
                setIsProcessingCard(false);
                setLoadingStatus({
                    message: "Error",
                    subMessage: cardData.error_for_user,
                    icon: <FaExclamationCircle className="text-sm"/>,
                    tone: "error",
                    removeAfterSeconds: 5,
                });
                return;
            }

            // Retrieve response, set state
            setShowdownBotCardData(cardData);
            setActivePreviewTab('preview');
            setGalleryRefreshKey(k => k + 1);
            console.log("Card built successfully:", cardData);
            console.log(currentSubMessage);

            setLoadingStatus(prevStatus => ({
                ...prevStatus, // Keep all existing values
                message: "Card built",
                icon: <FaCircleCheck className="text-sm"/>,
                tone: "success",
                removeAfterSeconds: 2,
            }));
            setIsProcessingCard(false);

        } catch (err) {
            console.error(err);
            setErrorMessage(String(err));
            setIsProcessingCard(false);
        }
    };

    const handleBuild = async () => {

        // Prevent multiple submissions
        if (isProcessingCard) return; 

        // Validate form data
        if (disableBuildButton) {
            console.error("Invalid form data");
            return;
        }

        const subMessage = `${form.name} | ${form.year}`;
        setLoadingStatus({
            message: "Building…",
            subMessage: subMessage,
            icon: <FaBaseballBall
                        className="text-sm animate-bounce"
                        style={{
                            animationDuration: '0.6s',
                            animationIterationCount: 'infinite'
                        }}
                    />,
            tone: "loading",
        });

        // Scroll to preview on mobile after a short delay to allow loading status to appear
        setTimeout(scrollToPreviewOnMobile, 200);

        submitCard(form);
    };

    // Handle shuffle
    const handleShuffle = () => {

        // Prevent multiple submissions
        if (isProcessingCard) return; 

        // Define language shown to user 
        var elements: string[] = [];
        if (form.year.length > 0) {
            elements.push(`${form.year}`);
        }
        if (elements.length < 1 && form.stats_period_type === 'ERA') {
            const eraTitled = form.era?.toLowerCase().split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
            elements.push(`${eraTitled}`);
        }
        if (form.edition == "CC") {
            elements.push("HOF");
        } else if (form.edition == "SS") {
            elements.push("AS or 5+ bWAR");
        } else if (form.edition == "RS") {
            elements.push("Rookie");
        } else if (form.edition == "ASG") {
            elements.push("All-Star");
        }
        const subMessage = elements.join(", ");

        setLoadingStatus({
            message: "Shuffling…",
            subMessage: subMessage,
            icon: <FaShuffle
                        className="text-sm animate-bounce"
                        style={{
                            animationDuration: '0.6s',
                            animationIterationCount: 'infinite'
                        }}
                    />,
            tone: "loading",
        });

        // Use form data but replace name with shuffle key
        const shuffledForm = {
            ...form,
            name: '((RANDOM))',
            player_id: null, // Reset player_id when shuffled
            player_type_override: undefined, // Reset player_type_override when shuffled
        };

        submitCard(shuffledForm);
    };

    // Handle reset
    const handleReset = () => {

        // Reset form to initial state
        setForm(FORM_DEFAULTS);
        setShowdownSetOverride(null);
    };

    // Handle Enter key press
    useEffect(() => {
        // Don't set up the listener if component is hidden
        if (isHidden) return;

        const handleKeyDown = (event: KeyboardEvent) => {
            // Dont run if the tab is not active
            if (document.hidden || isHidden) return;

            if (event.key === 'Enter' && !event.shiftKey) {
                // Don't trigger if user is typing in a textarea or input that should allow Enter
                const target = event.target as HTMLElement;
                if (target.tagName === 'TEXTAREA') return;

                event.preventDefault();
                handleBuild();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [form, isHidden]); // Re-bind when form changes so handleBuild has latest state

    // Handle loading status removal after a delay
    useEffect(() => {
        if (loadingStatus?.removeAfterSeconds) {
            const timer = setTimeout(() => {

                setIsLoadingStatusExiting(true);

                // After exit animation completes, remove the status
                const exitTimer = setTimeout(() => {
                    setLoadingStatus(null);
                    setIsLoadingStatusVisible(false);
                    setIsLoadingStatusExiting(false);
                }, 300); // Match animation duration
                
                return () => clearTimeout(exitTimer);

            }, loadingStatus.removeAfterSeconds * 1000); // Convert seconds to milliseconds

            // Cleanup timer if component unmounts or loadingStatus changes
            return () => clearTimeout(timer);
        }   
    }, [loadingStatus]);

    // Create a helper function to handle name changes
    // Resets the player_id if the name is changed manually
    const handleNameChange = (newName: string | null) => {
        setForm(prevForm => {
            return {
                ...prevForm,
                name: newName || "",
                player_id: null, // Reset player_id when name changes
                player_type_override: undefined // Reset player_type_override when name changes
            };
        });
    };

    // Show the loading status when it appears
    useEffect(() => {
        if (loadingStatus) {
            setIsLoadingStatusVisible(true);
            setIsLoadingStatusExiting(false);
        }
    }, [loadingStatus]);

    const scrollToPreview = () => {
        // First try to find the preview section by ID
        const previewElement = document.getElementById('preview-section');
        if (previewElement) {
            previewElement.scrollIntoView({ behavior: smoothScrollBehavior() });
            return;
        }
        
        // Fallback to ref method
        if (previewSectionRef.current) {
            previewSectionRef.current.scrollIntoView({ behavior: smoothScrollBehavior() });
        }
    };

    const scrollToPreviewOnMobile = () => {
        // Only scroll on mobile/tablet screens
        if (window.innerWidth >= 1024) return; // @2xl breakpoint
        scrollToPreview();
    };

    // ---------------------------------
    // MARK: Image Uploads
    // ---------------------------------
    // File input handler
    const handleFileChange = (file: File | null) => {
        
        // Create preview
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                setImageUploadPreview(e.target?.result as string);
            };
            reader.readAsDataURL(file);
        } else {
            setImageUploadPreview(null);
        }
        
        // Update form
        setForm({ ...form, image_upload: file });
    };

    // Dynamic stats period handling
    useEffect(() => {

        // Remove split value if not in SPLIT mode to prevent invalid combinations
        if (form.stats_period_type !== 'SPLIT' && form.split) {
            setForm(prevForm => ({
                ...prevForm,
                split: null
            }));
        }

        // Date Management
        if (form.year && form.stats_period_type === 'DATES') {
            const year = parseInt(form.year);
            
            if (!isNaN(year)) {
                // MLB season dates
                const startDate = `${year}-03-01`;

                // Calculate end date based on conditions
                const today = new Date();
                const currentYear = today.getFullYear();
                const seasonEndDate = new Date(year, 9, 5); // October 5th of the season year
                const seasonStartDate = new Date(year, 2, 1); // March 1st of the season year
                
                let endDate: string;
                if (year === currentYear && today >= seasonStartDate && today <= seasonEndDate) {
                    // Use today's date if we're in the current season and between start and end dates
                    endDate = today.toISOString().split('T')[0]; // Format as YYYY-MM-DD
                } else {
                    // Use default season end date
                    endDate = `${year}-10-05`;
                }
                
                setForm(prevForm => ({
                    ...prevForm,
                    start_date: startDate,
                    end_date: endDate
                }));
            }
        } else if (form.stats_period_type !== 'DATES') {
            // Clear dates when not using date range
            setForm(prevForm => ({
                ...prevForm,
                start_date: null,
                end_date: null
            }));
        }
    }, [form.year, form.stats_period_type]);


    // Save settings whenever form changes (debounced)
    // localStorage is always saved; API is only called when logged in
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            saveFormSettings(form);
        }, 1500);
        return () => clearTimeout(timeoutId);
    }, [form]);

    const handleSelectHistoryCard = (userInputs: CustomCardFormState, cardResult: ShowdownBotCard | null, statusMessage: string = 'Card inputs updated') => {

        // If name_original is present, replace "name" with "name_original" to preserve original name in form
        if (userInputs.name_original) {
            userInputs.name = userInputs.name_original;
        }
        // Merge in default values for any missing fields to ensure form is fully populated
        userInputs = { ...FORM_DEFAULTS, ...userInputs };
        
        // Remove `randomize` and `name_original` from the form state as they are not actual form fields
        delete userInputs.randomize;
        delete userInputs.name_original;

        // Remove all keys that arent in CustomCardFormState to prevent errors and ensure only form fields are set
        const allowedKeys = Object.keys(FORM_DEFAULTS);
        userInputs = Object.fromEntries(
            Object.entries(userInputs).filter(([key]) => allowedKeys.includes(key))
        ) as CustomCardFormState;

        setForm(userInputs);
        setShowdownBotCardData(cardResult ? { card: cardResult } as ShowdownBotCardAPIResponse : null);
        setActivePreviewTab('preview');

        setLoadingStatus({
            message: statusMessage,
            subMessage: `${userInputs.name} | ${userInputs.year}`,
            icon: <FaRotateLeft className="text-sm" />,
            tone: "success",
            removeAfterSeconds: 3,
        });
    };

    const handleGalleryReload = (userInputs: Record<string, unknown>, cardResult: ShowdownBotCard) => {
        handleSelectHistoryCard(userInputs as unknown as CustomCardFormState, cardResult);
    };

    // Prefill from a card handed over via the "Customize" button on CardDetail. The builder stays
    // mounted (hidden) between visits, so this watches location state rather than reading it on mount.
    useEffect(() => {
        const customizeCard = (location.state as CustomizeCardRouteState | null)?.customizeCard;
        if (!customizeCard) return;

        // WOTC cards prefill the form only — the bot's own version needs to be built
        const previewCard = customizeCard.is_wotc ? null : customizeCard;
        handleSelectHistoryCard(formInputsFromCard(customizeCard) as CustomCardFormState, previewCard, 'Card ready for editing');
        setShowdownSetOverride(customizeCard.set === userShowdownSet ? null : customizeCard.set);

        // Clear the state so a refresh or back/forward doesn't re-apply it over later edits
        navigate(location.pathname, { replace: true, state: null });
    }, [location.state]);

    // Fetch MLB situation codes when the user is in SPLIT mode for 2026+ seasons
    useEffect(() => {
        if (form.stats_period_type !== 'SPLIT') return;
        const yearNum = parseInt(form.year, 10);
        if (isNaN(yearNum) || yearNum < 2026) return;

        fetchSplits(form.year)
            .then((codes) =>
                setSplitOptions(codes.map((c) => ({
                    value: c.code,
                    label: c.description,
                    group: c.navigation_menu,
                    trailing: (c.batting || c.pitching) ? (
                        <span className="flex gap-1 shrink-0">
                            {c.batting  && <Plate variant="navy" size="sm">Hitting</Plate>}
                            {c.pitching && <Plate variant="red" size="sm">Pitching</Plate>}
                        </span>
                    ) : undefined,
                })))
            )
            .catch(console.error);
    }, [form.stats_period_type, form.year]);


    // ---------------------------------
    // MARK: Render SubComponents
    // ---------------------------------

    /** 
     * Render the period inputs based on the selected period 
     * This will show different inputs based on the period type selected.
     */
    const renderStatsPeriodInputs = () => {
        switch (form.stats_period_type) {
            case 'DATES':
                return (
                    <>
                        <FormInput
                            label="Start Date"
                            value={form.start_date || ''}
                            type="date"
                            onChange={(value) => setForm({ ...form, start_date: value || null })}
                        />
                        <FormInput
                            label="End Date"
                            value={form.end_date || ''}
                            type="date"
                            onChange={(value) => setForm({ ...form, end_date: value })}
                        />
                    </>
                );
            case 'SPLIT': {
                const yearNum = parseInt(form.year, 10);
                const isMlbApiYear = !isNaN(yearNum) && yearNum >= 2026;
                if (isMlbApiYear) {
                    return (
                        <FormDropdown
                            label="Split*"
                            options={splitOptions}
                            selectedOption={form.split || ''}
                            onChange={(value) => setForm({ ...form, split: value || null })}
                            className='col-span-full'
                            disabled={splitOptions.length === 0}
                            placeholder={splitOptions.length === 0 ? 'Loading…' : 'Select a split'}
                        />
                    );
                }
                return (
                    <FormInput
                        label="Split*"
                        value={form.split || ''}
                        onChange={(value) => setForm({ ...form, split: value })}
                        isClearable={true}
                        className='col-span-full'
                    />
                );
            }
            default:
                return null;
        }
    }

    // ---------------------------------
    // MARK: Main Layout
    // ---------------------------------

    /** Render the main form layout */
    return (
        // Main layout container
        // In small screens, the form will take full width
        // In larger screens, it will be split into two sections
        <div className='@container'>

            <WhatsNewBanner
                storageKey="customCardBuilderWhatsNew_v4.42"
                version="4.42"
                features={[
                    { icon: <FaGoogleDrive />, text: 'Image Libraries: connect your own Google Drive folder of player images' },
                    { icon: <FaListOl />, text: 'Choose whether Auto images check your folders or Showdown Bot first in Account settings' },
                    { icon: <FaImage />, text: "Cards now show where their player image came from" },
                ]}
            />

            {/* Mobile tab bar — fixed below the app header, hidden on @2xl */}
            <div className="flex @2xl:hidden fixed top-10 inset-x-0 z-30 px-2 bg-(--background-secondary)">
                <Tabs tabs={PREVIEW_TABS} value={activePreviewTab} onChange={handleTabChange} fullWidth className="w-full" />
            </div>

            <div className="
                @container flex flex-col @2xl:flex-row
                @2xl:overflow-hidden
                @2xl:h-[calc(100dvh-2.5rem)]
                pt-11 @2xl:pt-0
            ">
                {/* Loading Indicator */}
                <ToastMessage
                    loadingStatus={loadingStatus}
                    isExiting={isLoadingStatusExiting}
                />

                {/* Form Inputs */}
                <section className={`
                    w-full @2xl:shrink-0
                    ${isFormCollapsed ? '@2xl:w-16' : '@2xl:w-84'}
                    ${isFormSettled ? '' : '@2xl:overflow-hidden'}
                    border-b-2 @2xl:border-r border-form-element
                    bg-(--background-secondary)
                    ${activePreviewTab === 'gallery' ? 'hidden @2xl:flex @2xl:flex-col' : 'flex flex-col'}
                    h-full
                    ${formPanelTransitionTw} transition-[width]
                `}>

                    {/* Header */}
                    <div className={`flex items-center justify-between @2xl:justify-start p-2 ${isFormCollapsed ? 'px-2' : 'px-4'}`}>
                        
                        {/* Reset and collapse buttons */}
                        <div className='flex gap-1 text-lg items-center'>

                            <Heading level="section" className={`mr-2 ${isFormCollapsed ? 'hidden' : 'block'}`}>
                                Card Settings
                            </Heading>

                            {/* Reset and shuffle buttons */}
                            <div className={`flex items-center gap-1 text-xl ${isFormCollapsed ? 'hidden' : 'flex'}`}>
                                <button
                                    type="button"
                                    className={`
                                        p-2 rounded-control hover:bg-(--background-tertiary) transition-colors cursor-pointer
                                    `}
                                    title="Reset Form"
                                    onClick={handleReset}
                                >
                                    <FaRotateLeft />
                                </button>

                                <button
                                    type="button"
                                    className={`
                                        p-2 rounded-control hover:bg-(--background-tertiary) transition-colors cursor-pointer
                                    `}
                                    title='Shuffle'
                                    onClick={handleShuffle}
                                >
                                    <FaShuffle />
                                </button>
                            </div>

                        </div>

                        <button
                            className={`
                                text-lg p-2 rounded-control hover:bg-(--background-tertiary) transition-colors cursor-pointer
                                @2xl:order-first @2xl:mr-1
                                ${isFormCollapsed ? 'flex flex-row-reverse @2xl:flex-col items-center gap-2 @2xl:gap-3 px-4 @2xl:px-2 @2xl:mr-0 w-full justify-center ' : ''}
                            `}
                            title='Collapse/Expand Form'
                            onClick={toggleFormCollapsed}
                        >
                            {isFormCollapsed ? (
                                <>
                                    <FaChevronCircleDown className="@2xl:hidden" />
                                    <FaChevronCircleRight className="hidden @2xl:block" />
                                </>
                            ) : (
                                <>
                                    <FaChevronCircleUp className="@2xl:hidden" />
                                    <FaChevronCircleLeft className="hidden @2xl:block" />
                                </>
                            )}
                            {isFormCollapsed && (
                                <>
                                    {/* Normal horizontal text for small screens */}
                                    <span className="text-nowrap font-display uppercase text-sm leading-none text-(--text-tertiary) @2xl:hidden">
                                        Card Settings
                                    </span>
                                    {/* Vertical text for large screens */}
                                    <span 
                                        className='text-nowrap font-display uppercase text-sm leading-none text-(--text-tertiary) hidden @2xl:block'
                                        style={{ 
                                            writingMode: 'vertical-lr',
                                            textOrientation: 'sideways',
                                        }}
                                    >
                                        Card Settings
                                    </span>
                                </>
                            )}
                            
                        </button>
                    </div>

                    {/* Scrollable area */}
                    <div className={`flex-1 px-4 scrollbar-hide
                        ${isFormCollapsed ? 'overflow-hidden' : 'overflow-visible @2xl:overflow-y-auto'}
                    `}>

                        {/* Search and Form Inputs. Collapses height (0fr <-> 1fr) on mobile; on desktop the section width animates instead, so only fade here. */}
                        <div
                            className={`
                                grid ${formPanelTransitionTw} transition-[grid-template-rows,opacity]
                                ${isFormCollapsed
                                    ? 'grid-rows-[0fr] @2xl:grid-rows-[1fr] opacity-0'
                                    : 'grid-rows-[1fr] opacity-100'
                                }
                            `}
                            inert={isFormCollapsed}
                            onTransitionEnd={(e) => {
                                if (e.target === e.currentTarget && !isFormCollapsed) setIsFormSettled(true);
                            }}
                        >

                            {/* Clip only while collapsed/animating so focus rings and popovers aren't cut off when open */}
                            <div className={`min-h-0 ${isFormSettled ? '' : 'overflow-hidden'}`}>

                                <div className="space-y-4 pb-6 @2xl:pb-96 @2xl:w-76">
                                    <>
                                        {!is2026NoticeDismissed && (
                                            <Set2026Notice
                                                onDismiss={() => {
                                                    localStorage.setItem(SET_2026_NOTICE_KEY, 'true');
                                                    setIs2026NoticeDismissed(true);
                                                }}
                                            />
                                        )}

                                        <div className="@container flex flex-row items-end gap-1">
                                            <PlayerSearchInput
                                                label=""
                                                value={query}
                                                className={`flex-1 min-w-0 ${animationTw}`}
                                                onChange={(selection) => setForm({ 
                                                    ...form, 
                                                    name: selection.name, 
                                                    year: selection.year,
                                                    player_id: selection.player_id,
                                                    player_type_override: selection.player_type_override,
                                                })}
                                            />

                                            {/* Showdown Set (default managed via top right corner) */}
                                            <div className="@container shrink-0 w-18">
                                                <CustomSelect
                                                    className="text-sm"
                                                    // design-ok: set-badge picker, not a form field
                                                    buttonClassName="w-full pl-1 py-2 flex items-center hover:bg-(--background-secondary) cursor-pointer rounded-control"
                                                    value={showdownSetOverride ?? ''}
                                                    align="right"
                                                    onChange={(v) => setShowdownSetOverride(v === '' ? null : v)}
                                                    options={[
                                                        { ...setSelectOption(userShowdownSet, { compact: true, size: 'lg' }), value: '' },
                                                        ...showdownSets.map(set => setSelectOption(set.value, { compact: true, size: 'lg' })),
                                                    ]}
                                                    showDropdownArrow={true}
                                                />
                                            </div>
                                        </div>

                                        {/* Display Error (If Applicable) */}
                                        {errorMessage && (
                                            <div className='w-full border-2 bg-(--red)/10 text-(--red) border-(--red) rounded-card p-2'>
                                                <div className='flex flex-row justify-between items-center mb-1 text-xl'>
                                                    <div className='font-display uppercase leading-none flex flex-row gap-2 items-center'> 
                                                        <FaExclamationCircle /> 
                                                        Error
                                                    </div>
                                                    <button className='text-(--red) cursor-pointer hover:opacity-70' aria-label='Dismiss error' onClick={() => setErrorMessage('')}>
                                                        <FaXmark />
                                                    </button>
                                                </div>
                                                <div className="text-sm font-bold overflow-scroll scrollbar-hide">
                                                    {errorMessage}
                                                </div>
                                            </div>
                                        )}

                                        {/* Player */}
                                        <FormSection
                                            title='Player'
                                            icon={<FaUser />}
                                            isOpenByDefault={sectionStates['Player']}
                                            onToggle={() => toggleSection('Player')}
                                            childrenWhenClosed={sectionWhenClosed('Player')}
                                        >

                                            <FormInput
                                                label="Name*"
                                                className='col-span-full'
                                                value={form.name}
                                                onChange={handleNameChange}
                                                isClearable={true}
                                                isTitleCase={true}
                                            />

                                            <FormInput
                                                label="Year*"
                                                value={form.year}
                                                className='col-span-full'
                                                onChange={(value) => setForm({ ...form, year: value || '' })}
                                                isClearable={true}
                                            />

                                            {isMultiYear && (
                                                <FormDropdown
                                                    label="Team Selection"
                                                    options={teamSelectionOptions}
                                                    selectedOption={form.team_selection || 'GAMES_PLAYED'}
                                                    onChange={(value) => setForm({ ...form, team_selection: value })}
                                                    className='col-span-full'
                                                />
                                            )}

                                            <FormDropdown
                                                label="Period"
                                                options={statsPeriodOptions}
                                                selectedOption={form.stats_period_type}
                                                onChange={(value) => setForm({ ...form, stats_period_type: value })}
                                                disabled={form.league === 'MILB'}
                                            />

                                            <FormDropdown
                                                label="League"
                                                options={leagueOptions}
                                                selectedOption={form.league}
                                                onChange={(value) => {
                                                    const isMiLB = value === 'MILB';
                                                    setForm({
                                                        ...form,
                                                        league: value,
                                                        ...(isMiLB && ['POST', 'DATES', 'SPLIT'].includes(form.stats_period_type) && {
                                                            stats_period_type: 'REGULAR',
                                                            start_date: null,
                                                            end_date: null,
                                                            split: null,
                                                        }),
                                                    });
                                                }}
                                            />

                                            {renderStatsPeriodInputs()}

                                        </FormSection>

                                        {/* Set */}
                                        <FormSection 
                                            title='Set' 
                                            icon={<FaLayerGroup />} 
                                            isOpenByDefault={sectionStates['Set']}
                                            onToggle={() => toggleSection('Set')}
                                            childrenWhenClosed={sectionWhenClosed('Set')}
                                        >
                                            <SetStyleFields
                                                values={form}
                                                onChange={(patch) => setForm({ ...form, ...patch })}
                                                afterEdition={
                                                    <FormInput
                                                        label="Set Number"
                                                        className='col-span-full'
                                                        value={form.set_number || ''}
                                                        onChange={(value) => setForm({ ...form, set_number: value || '' })}
                                                        isClearable={true}
                                                    />
                                                }
                                            />

                                        </FormSection>

                                        {/* Image */}
                                        <FormSection 
                                            title='Image' 
                                            icon={<FaImage />} 
                                            isNew={true}
                                            isOpenByDefault={sectionStates['Image']}
                                            onToggle={() => toggleSection('Image')}
                                            childrenWhenClosed={sectionWhenClosed('Image')}
                                        >

                                            <FormDropdown
                                                label="Player Image"
                                                className='col-span-full'
                                                options={imageSourceOptions}
                                                selectedOption={form.image_source}
                                                onChange={(value) => setForm({ ...form, image_source: value })}
                                            />
                                            {form.image_source === 'AUTO' && <ImageLibraryOrderHint className="col-span-full -mt-1" />}

                                            {/* Source Specific Options */}
                                            <FormInput
                                                label="Image URL"
                                                className={`col-span-full ${form.image_source === 'LINK' ? '' : 'hidden'}`}
                                                value={form.image_url || ''}
                                                onChange={(value) => setForm({ ...form, image_url: value || null })}
                                                isClearable={true}
                                                placeholder="https://example.com/image.png"
                                            />
                                            <FormInput
                                                label="Upload Image"
                                                className={`col-span-full ${form.image_source === 'UPLOAD' ? '' : 'hidden'}`}
                                                value={form.image_upload?.name || ''}
                                                isClearable={true}
                                                placeholder="Select an image file"
                                                type="file"
                                                onChangeFile={handleFileChange}
                                            />

                                            {/* Image Preview (Link) */}
                                            {getImagePreview() && (
                                                <div className="col-span-full grid grid-cols-[12fr_8fr] gap-2 items-center">
                                                    <div>
                                                        <label className={`${FIELD_LABEL_CLASS} mb-1`}>
                                                            Preview
                                                        </label>
                                                        <img
                                                            src={getImagePreview() || ''}
                                                            alt="Invalid Image"
                                                            // design-ok: card art keeps its printed corner radius
                                                            className="max-w-full h-38 object-contain rounded-lg border-2 border-form-element"
                                                        />
                                                    </div>

                                                    <button type="button" className="flex flex-col items-center space-x-2 cursor-pointer hover:opacity-50">
                                                        <FaXmark
                                                            className="text-3xl text-(--red) hover:opacity-70 transition-opacity"
                                                            onClick={() => handleFileChange(null)}
                                                        />
                                                        <span>Remove Image</span>
                                                    </button>
                                                </div>
                                            )}

                                            <ImageStyleFields
                                                values={form}
                                                onChange={(patch) => setForm({ ...form, ...patch })}
                                                hideParallel={form.image_source !== 'AUTO'}
                                            />

                                        </FormSection>

                                        {/* Chart */}
                                        <FormSection 
                                            title='Chart' 
                                            icon={<FaTable />} 
                                            isOpenByDefault={sectionStates['Chart']}
                                            onToggle={() => toggleSection('Chart')}
                                            childrenWhenClosed={sectionWhenClosed('Chart')}
                                        >

                                            <FormDropdown
                                                label="Chart Version"
                                                options={chartVersionOptions}
                                                selectedOption={form.chart_version || '1'}
                                                onChange={(value) => setForm({ ...form, chart_version: value })}
                                            />

                                            <FormDropdown
                                                label="Era"
                                                options={eraOptions}
                                                selectedOption={form.era || 'DYNAMIC'}
                                                onChange={(value) => setForm({ ...form, era: value })}
                                            />

                                            {isSet00_01 && (
                                                <FormEnabler
                                                    label="Variable Speed"
                                                    className="col-span-2"
                                                    isEnabled={form.is_variable_speed_00_01 || false}
                                                    onChange={(isEnabled) => setForm({ ...form, is_variable_speed_00_01: !isEnabled })}
                                                />
                                            )}

                                            <div className="col-span-2 flex items-center gap-1.5">
                                                <FormEnabler
                                                    label={<span className="inline-flex items-center gap-1.5">Regress to Replacement Level <NewBadge /></span>}
                                                    className="flex-1"
                                                    isEnabled={form.regress_small_sample_to_replacement || false}
                                                    onChange={(isEnabled) => setForm({ ...form, regress_small_sample_to_replacement: !isEnabled })}
                                                />
                                                <InfoTooltip iconSize="text-[16px]" text="Blends a player's real stats toward that year's replacement level, weighted by how few plate appearances/innings they actually have. A callup's hot 40-PA stretch gets pulled toward replacement level instead of standing in as his true talent; players with a full season are unaffected." />
                                            </div>

                                        </FormSection>
                                    </>
                                </div>

                            </div>

                        </div>

                        {/* Mobile: floating circular CTA pinned bottom-right (Jump to Card pins itself bottom-left). Desktop (@2xl): full-width sticky bar. */}
                        <footer className={`
                            fixed bottom-0 right-0 z-30
                            p-4 pb-[calc(0.5rem+var(--safe-bottom))]
                            pointer-events-none
                            @2xl:sticky @2xl:inset-x-0 @2xl:bottom-0 @2xl:z-20
                            @2xl:-mx-4 @2xl:px-10 @2xl:py-3 @2xl:pb-3
                            @2xl:pointer-events-auto
                            @2xl:bg-(--background-secondary)
                            @2xl:border-t @2xl:border-(--divider)
                            ${isFormCollapsed ? '@2xl:hidden' : ''}
                        `}>

                            <div className="flex justify-end @2xl:block">

                                {/* Jump to Card Detail (mobile only). Pinned on its own rather than via a
                                    full-width footer — iOS Safari tints its toolbar to match full-width fixed
                                    bars along the bottom edge. Bottom offset centers it on the Build button. */}
                                <button
                                    type="button"
                                    aria-label="Jump to Card"
                                    title="Jump to Card"
                                    className="
                                        fixed left-4 bottom-[calc(1rem+var(--safe-bottom))]
                                        pointer-events-auto @2xl:hidden
                                        flex items-center justify-center
                                        h-12 w-12 rounded-full shadow-overlay
                                        bg-(--background-secondary) border border-form-element text-(--primary) text-lg
                                        cursor-pointer hover:brightness-110 active:scale-95 transition-transform
                                    "
                                    onClick={scrollToPreview}
                                >
                                    <FaArrowDown />
                                </button>

                                {/* Build Card */}
                                <button
                                    type="button"
                                    aria-label="Build Card"
                                    title={disableBuildButton ? "Enter a player name and year" : "Build Card"}
                                    className={`
                                        pointer-events-auto
                                        bg-(--showdown-blue-fill)
                                        flex items-center justify-center gap-x-2
                                        text-white
                                        h-16 w-16 rounded-full shadow-feature-float active:translate-y-0.5 active:shadow-overlay
                                        @2xl:h-auto @2xl:w-full @2xl:flex-1 @2xl:gap-x-1.5
                                        @2xl:rounded-control @2xl:py-3.5 @2xl:shadow-feature @2xl:active:shadow-none
                                        transition-transform
                                        ${disableBuildButton
                                            ? 'cursor-not-allowed opacity-25'
                                            : 'cursor-pointer hover:brightness-110 active:scale-95'
                                        }
                                    `}
                                    onClick={handleBuild}
                                >
                                    <CardBuildIcon size="2rem" className='mr-0.5' />
                                    <span className="hidden @2xl:inline font-display uppercase text-2xl leading-none">Build Card</span>
                                </button>

                            </div>

                        </footer>
                        
                    </div>

                </section>

                {/* Preview Section */}
                <section
                    id="preview-section"
                    ref={previewSectionRef}
                    className={`
                        w-full @2xl:grow
                        ${activePreviewTab === 'gallery' ? 'pb-0 min-h-[calc(100dvh-2.75rem)]' : 'pb-64'} @2xl:pb-0 @2xl:min-h-0
                        scroll-mt-21
                        @2xl:scroll-mt-0
                        bg-(--background-primary)
                    `}
                >
                    <div className="flex flex-col h-full">

                        {/* Tab bar — desktop only */}
                        <div className="hidden @2xl:block shrink-0 px-2 bg-(--background-secondary) sticky top-0 z-10">
                            <Tabs tabs={PREVIEW_TABS} value={activePreviewTab} onChange={handleTabChange} fullWidth />
                        </div>

                        {/* Tab content */}
                        <div className="flex-1 @2xl:overflow-y-auto scrollbar-hide">
                            <div className={activePreviewTab === 'preview' ? 'block' : 'hidden'}>
                                <CardDetail
                                    showdownBotCardData={showdownBotCardData}
                                    showdownSetForPlaceholder={showdownSetOverride || undefined}
                                    isLoading={isProcessingCard}
                                />
                            </div>
                            <div className={activePreviewTab === 'gallery' ? 'block h-full' : 'hidden'}>
                                <GalleryTabContent
                                    user={user}
                                    token={session?.access_token ?? null}
                                    onReload={user ? handleGalleryReload : undefined}
                                    refreshKey={galleryRefreshKey}
                                />
                            </div>
                        </div>

                    </div>
                </section>                    
            </div>
        </div>
    );
}

export default CustomCardBuilder;