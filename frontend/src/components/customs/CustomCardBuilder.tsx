// ----------------------------------
// MARK: - Imports
// ----------------------------------

import { useEffect, useState, useRef } from 'react';
import FormInput from './FormInput';
import FormSection from './FormSection';
import FormDropdown from './FormDropdown';
import FormEnabler from './FormEnabler';
import { PlayerSearchInput } from './PlayerSearchInput';
import type { SelectOption } from '../shared/CustomSelect';
import { useSiteSettings } from '../shared/SiteSettingsContext';

import { CardDetail } from '../cards/CardDetail';

// API
import { buildCustomCard, type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';

// Image Assets
import expansionBS from '../../assets/expansion-bs.png';
import expansionTD from '../../assets/expansion-td.png';
import expansionPR from '../../assets/expansion-pr.png';

import editionRS from '../../assets/edition-rs.png';
import editionCC from '../../assets/edition-cc.png';
import editionPOST from '../../assets/edition-post.png';
import editionSS from '../../assets/edition-ss.png';

// Icons
import { 
    FaTable, FaImage, FaLayerGroup, FaUser, FaBaseballBall, FaExclamationCircle, 
    FaChevronCircleRight, FaChevronCircleLeft, FaChevronCircleUp, FaChevronCircleDown
} from 'react-icons/fa';
import { FaShuffle, FaXmark, FaRotateLeft } from 'react-icons/fa6';

// ----------------------------------
// MARK: - Form Interface
// ----------------------------------

/** State for the custom card form */
interface CustomCardFormState {
    // Name and Year
    name: string; // ex: "Mike Trout"
    year: string; // ex: "2023"
    stats_period_type: string; // e.g. "REGULAR"
    start_date?: string | null; // e.g. "2023-05-01"
    end_date?: string | null; // e.g. "2023-10-01"
    split?: string | null; // e.g. "First Half"

    // Set
    expansion: string; // e.g. "BS"
    set_number?: string | null; // e.g. "001"
    edition: string; // e.g. "Cooperstown"
    add_one_to_set_year: boolean; // Whether to show the year + 1 in the set section
    show_year_text: boolean; // Whether to show the year text as a label on the card

    // Image
    image_source: string; // e.g. "Auto"
    image_parallel: string; // e.g. "Rainbow Foil"
    image_coloring: string; // e.g. "Primary"
    image_glow_multiplier: string; // e.g. "Glow 1x"
    image_url?: string | null; // e.g. "https://example.com/image.png"
    image_upload?: File | null; // For file uploads

    // Image Extras
    add_image_border: boolean; // Whether to add a border to the image
    is_dark_mode: boolean; // Whether the card is in dark mode
    remove_team_branding: boolean; // Whether to remove team branding from the image
    stat_highlights_type?: string; // e.g. "ALL", "OLD", "MODERN"
    nickname_index?: string; // e.g. "NICKNAME 1",

    // Chart
    chart_version?: string; // e.g. "1"
    era?: string; // e.g. "Dynamic"
    is_variable_speed_00_01?: boolean; // Whether to use variable speed for 00-01

}

/** Default values for the custom card form */
const FORM_DEFAULTS: CustomCardFormState = {
    name: "", 
    year: "", 
    stats_period_type: "REGULAR", 
    start_date: null, 
    end_date: null, 
    split: null,
    expansion: "BS", 
    set_number: null, 
    edition: "NONE",
    image_source: "AUTO", 
    image_parallel: "NONE", 
    image_coloring: "PRIMARY", 
    image_glow_multiplier: "1",
    image_url: null, 
    image_upload: null,
    add_image_border: false, 
    is_dark_mode: false, 
    remove_team_branding: false,
    stat_highlights_type: "NONE", 
    nickname_index: "NONE", 
    add_one_to_set_year: false, 
    show_year_text: false,
    chart_version: "1", 
    era: "DYNAMIC", 
    is_variable_speed_00_01: false
};

// ----------------------------------
// MARK: - Local Storage
// ----------------------------------

const STORAGE_KEY = 'customCardFormSettings';

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

/** 
 * Card Creation Page for users to create and customize their own cards. 
*/
function CustomCardBuilder() {

    // Card States
    const { userShowdownSet } = useSiteSettings();
    const [showdownBotCardData, setShowdownBotCardData] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isProcessingCard, setIsProcessingCard] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [query, _] = useState("");
    const [isFormCollapsed, setIsFormCollapsed] = useState(false);

    // Live update states
    const [isLiveUpdating, setIsLiveUpdating] = useState(false);
    const [isLoadingGameBoxscore, setIsLoadingGameBoxscore] = useState(false);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const lastFormRef = useRef<CustomCardFormState | null>(null);

    // Define the form state
    const [form, setForm] = useState<CustomCardFormState>(loadFormSettings());
    const disableBuildButton = (
        !form.name.trim() 
        || form.year.trim().length < 4 
        || (form.stats_period_type === "SPLIT" && !form.split)
        || isProcessingCard
    )

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

    // Expansion options
    const expansionOptions: SelectOption[] = [
        { label: "Base Set", value: "BS", image: expansionBS },
        { label: "Trading Deadline", value: "TD", image: expansionTD, 'borderColor': 'border-red-600' },
        { label: "Pennant Run", value: "PR", image: expansionPR, 'borderColor': 'border-blue-900' },
    ]

    // Stats Period Options
    const statsPeriodOptions: SelectOption[] = [
        { 'value': 'REGULAR', 'label': 'Regular Season', 'symbol': '⚾' },
        { 'value': 'POST', 'label': 'Postseason', 'symbol': '🏆', 'borderColor': 'border-yellow-500'},
        { 'value': 'DATES', 'label': 'Date Range', 'symbol': '📅', 'borderColor': 'border-red-600' },
        { 'value': 'SPLIT', 'label': 'Split', 'symbol': '🔀', 'borderColor': 'border-blue-700' },
    ]

    // Edition Options
    const editionOptions: SelectOption[] = [
        { 'value': 'NONE', 'label': 'None', 'symbol': '―' },
        { 'value': 'CC', 'label': 'Cooperstown Collection', 'image': editionCC, 'borderColor': 'border-amber-800' },
        { 'value': 'SS', 'label': 'Super Season', 'image': editionSS, 'borderColor': 'border-red-500' },
        { 'value': 'ASG', 'label': 'All-Star Game', 'symbol': '⭐', 'borderColor': 'border-yellow-400' },
        { 'value': 'RS', 'label': 'Rookie Season', 'image': editionRS, 'borderColor': 'border-red-800' },
        { 'value': 'HOL', 'label': 'Holiday', 'symbol': '🎄', 'borderColor': 'border-green-600' },
        { 'value': 'NAT', 'label': 'Nationality', 'symbol': '🌍', 'borderColor': 'border-blue-500' },
        { 'value': 'POST', 'label': 'Postseason', 'image': editionPOST, 'borderColor': 'border-blue-800' },
    ]

    // Image Source Options
    const imageSourceOptions: SelectOption[] = [
        { 'value': 'AUTO', 'label': 'Auto', 'symbol': '⚙️' },
        { 'value': 'LINK', 'label': 'Link', 'symbol': '🔗' },
        { 'value': 'UPLOAD', 'label': 'Upload', 'symbol': '📤' },
    ]

    // Image Parallel Options
    const imageParallelOptions: SelectOption[] = [
        { "label": "Base", "value": "NONE", 'symbol': '―' },
        { "label": "Rainbow Foil", "value": "RF", 'symbol': '🌈' },
        { "label": "Team Color Blast", "value": "TCB", 'symbol': '💥' },
        { "label": "Galaxy", "value": "GALAXY", 'symbol': '🌌' },
        { "label": "Gold", "value": "GOLD", "borderColor": "border-yellow-300", 'symbol': '🟡' },
        { "label": "Gold Rush", "value": "GOLDRUSH", 'symbol': '✨' },
        { "label": "Gold Frame", "value": "GF", 'symbol': '🖼️' },
        { "label": "Sapphire", "value": "SPH", 'symbol': '💎' },
        { "label": "Black and White", "value": "B&W", 'symbol': '📰' },
        { "label": "Radial", "value": "RAD", 'symbol': '☀' },
        { "label": "Comic Book Hero", "value": "CB", 'symbol': '🦸' },
        { "label": "White Smoke", "value": "WS", 'symbol': '💨' },
        { "label": "Flames", "value": "FLAMES", 'symbol': '🔥' },
        { "label": "Mystery", "value": "MYSTERY", 'symbol': '❓' },
        { "label": "Moonlight", "value": "MOONLIGHT", 'symbol': '🌙' },
    ]

    const imageColoringOptions: SelectOption[] = [
        { "label": "Primary Color", "value": "PRIMARY" },
        { "label": "Secondary Color", "value": "SECONDARY" },
        { "label": "Multi-Color", "value": "MULTI" },
    ]

    const chartVersionOptions: SelectOption[] = [
        { 'value': '1', 'label': 'Version 1' },
        { 'value': '2', 'label': 'Version 2' },
        { 'value': '3', 'label': 'Version 3' },
        { 'value': '4', 'label': 'Version 4' },
        { 'value': '5', 'label': 'Version 5' },
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

    const statHighlightsTypeOptions: SelectOption[] = [
        { "label": "None", "value": "NONE" },
        { "label": "Classic", "value": "CLASSIC" },
        { "label": "Modern", "value": "MODERN" },
        { "label": "All", "value": "ALL" },
    ]

    const nicknameIndexOptions: SelectOption[] = [
        { "label": "None", "value": "NONE" },
        { "label": "Nickname 1", "value": "1" },
        { "label": "Nickname 2", "value": "2" },
        { "label": "Nickname 3", "value": "3" },
    ]

    const outerGlowOptions: SelectOption[] = [
        { "label": "Glow 1x", "value": "1" },
        { "label": "Glow 2x", "value": "2" },
        { "label": "Glow 3x", "value": "3" },
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
            'Player': true,
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
                if (form.split) summaries.push({ label: 'Split', value: form.split });
                break;
                
            case 'set':
                if (form.expansion !== FORM_DEFAULTS.expansion) {
                    const expansionOption = expansionOptions.find(opt => opt.value === form.expansion);
                    summaries.push(expansionOption || { label: 'Expansion', value: form.expansion });
                }
                if (form.edition !== FORM_DEFAULTS.edition) {
                    const editionOption = editionOptions.find(opt => opt.value === form.edition);
                    summaries.push(editionOption || { label: 'Edition', value: form.edition });
                }
                if (form.set_number) summaries.push({ label: 'Set Number', value: form.set_number });

                if (form.add_one_to_set_year) summaries.push({ value: "Set Year +1", borderColor: 'border-green-500' });
                if (form.show_year_text) summaries.push({ value: "Show Year Text", borderColor: 'border-green-500' });

                break;
                
            case 'image':
                if (form.image_source !== FORM_DEFAULTS.image_source) {
                    const sourceOption = imageSourceOptions.find(opt => opt.value === form.image_source);
                    summaries.push(sourceOption || { label: 'Source', value: form.image_source });
                }
                if (form.image_source === FORM_DEFAULTS.image_source && form.image_parallel !== FORM_DEFAULTS.image_parallel) {
                    const parallelOption = imageParallelOptions.find(opt => opt.value === form.image_parallel);
                    summaries.push(parallelOption || { label: 'Parallel', value: form.image_parallel });
                }
                if (form.image_coloring !== FORM_DEFAULTS.image_coloring) {
                    const coloringOption = imageColoringOptions.find(opt => opt.value === form.image_coloring);
                    summaries.push({ ...(coloringOption || { value: form.image_coloring }), label: 'Coloring' });
                }
                if (form.image_glow_multiplier !== FORM_DEFAULTS.image_glow_multiplier) {
                    const glowOption = outerGlowOptions.find(opt => opt.value === form.image_glow_multiplier);
                    summaries.push({ ...(glowOption || { value: form.image_glow_multiplier }), label: 'Glow' });
                }
                if (form.stat_highlights_type && form.stat_highlights_type !== FORM_DEFAULTS.stat_highlights_type) {
                    const statsOption = statHighlightsTypeOptions.find(opt => opt.value === form.stat_highlights_type);
                    summaries.push({ ...(statsOption || { value: form.stat_highlights_type }), label: 'Real Stats' });
                }
                if (form.nickname_index && form.nickname_index !== FORM_DEFAULTS.nickname_index) {
                    const nicknameOption = nicknameIndexOptions.find(opt => opt.value === form.nickname_index);
                    summaries.push({ ...(nicknameOption || { value: form.nickname_index }), label: 'Nickname' });
                }
                if (form.add_image_border !== FORM_DEFAULTS.add_image_border) summaries.push({ value: 'ADD BORDER', borderColor: 'border-green-500' });
                if (form.is_dark_mode !== FORM_DEFAULTS.is_dark_mode) summaries.push({ value: 'DARK MODE', borderColor: 'border-green-500' });
                if (form.remove_team_branding !== FORM_DEFAULTS.remove_team_branding) summaries.push({ value: 'REMOVE TEAM BRANDING', borderColor: 'border-green-500' });
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
                if (form.is_variable_speed_00_01 !== FORM_DEFAULTS.is_variable_speed_00_01) summaries.push({ value: 'VARIABLE SPEED', borderColor: 'border-green-500' });
                break;
        }
        
        return summaries;
    };

    const sectionWhenClosed = (sectionName: string) => {

        const summaryItems = getSectionSummary(sectionName);

        if (summaryItems.length === 0) {
            return undefined;
        }
        return (
            <div className="text-sm font-bold flex flex-wrap items-center gap-x-2 gap-y-1 text-[var(--tertiary)]">
                {summaryItems.map(item => (
                    <div key={item.label} className={`flex rounded-lg px-1 border-2 ${item.borderColor || 'border-[var(--tertiary)]/65'}`}>
                        <span className="font-semibold">{item.icon}</span>
                        {(() => {
                            const label = item.label?.toLowerCase()
                            var prefix = "";
                            var suffix = "";
                            var value = item.value || "";
                            if (label === "name") {
                                return <span style={{ textTransform: 'capitalize' }}>{item.value}</span>;
                            }
                            if (item.image) {
                                return <img src={item.image} alt={item.label} className="w-5 h-5" />;
                            }
                            if (item.icon) {
                                return <span className="w-5 h-5" >{item.icon}</span>;
                            }
                            if (item.symbol) {
                                return <span className="w-5 h-5" >{item.symbol}</span>;
                            }
                            switch (label) {
                                case "set number": prefix = "#"; break;
                                case "coloring": suffix = " COLOR"; break;
                                case "glow": suffix = "X"; prefix = "GLOW "; break;
                                case "nickname": prefix = "NICKNAME "; break;
                                case "chart version": prefix = "CHART "; break;
                                case "real stats": prefix = "SHOW "; suffix = " STATS"; break;
                            }
                            return <span className={`${item.borderColor || 'text-[var(--tertiary)]'}`}>{prefix}{value}{suffix}</span>;
                        })()}
                    </div>
                ))}
            </div>
        );
    };

    // MARK: Live Updates

    // Check if there's a live game
    const hasLiveGame = showdownBotCardData?.latest_game_box_score && 
                        !showdownBotCardData.latest_game_box_score.has_game_ended;

    useEffect(() => {

        // Temp Disable Live updates
        console.log(isLiveUpdating);
        return;

        if (hasLiveGame && showdownBotCardData && lastFormRef.current) {
            // Start live updates
            setIsLiveUpdating(true);
            
            intervalRef.current = setInterval(async () => {
                try {
                    console.log('Updating live game data...');
                    setIsLoadingGameBoxscore(true);

                    const { image_upload, image_source, ...payload } = lastFormRef.current!;
                    
                    const updatedCardData = await buildCustomCard({
                        ...payload,
                        set: userShowdownSet,
                        is_running_on_website: true,
                        image_output_folder_path: "static/output",
                        show_historical_points: true,
                        season_trend_date_aggregation: 'WEEK',
                    });
                    
                    setShowdownBotCardData(updatedCardData);
                    
                    // Stop updating if game has ended
                    if (updatedCardData.latest_game_box_score?.has_game_ended) {
                        setIsLiveUpdating(false);
                        if (intervalRef.current) {
                            clearInterval(intervalRef.current);
                            intervalRef.current = null;
                        }
                    }
                    setIsLoadingGameBoxscore(false);
                } catch (error) {
                    console.error('Error updating live game:', error);
                    // Continue trying updates even on error
                    setIsLoadingGameBoxscore(false);
                }
            }, 20000); // 20 seconds
        } else {
            // Stop live updates
            setIsLiveUpdating(false);
            if (intervalRef.current) {
                // clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        }
        
        // Cleanup on unmount
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        };
    }, [hasLiveGame, showdownBotCardData, userShowdownSet]);

    // ---------------------------------
    // MARK: Build Processing
    // ---------------------------------

    const submitCard = async (card_payload: any) => {
        // Implement your submit logic here

        try {

            // Set Is Loading
            setIsProcessingCard(true);

            // TODO: Handle image uploads
            console.log("Building card with form data:", card_payload);

            // Prepare payload based on image source
            let finalPayload = { ...card_payload };
            
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

            const cardData = await buildCustomCard({
                ...finalPayload,

                // Default parameters/settings
                set: userShowdownSet,
                is_running_on_website: true,
                image_output_folder_path: "static/output",
                show_historical_points: true,
                season_trend_date_aggregation: 'WEEK',
            });
            
            // Handle Errors
            setErrorMessage(cardData.error_for_user);
            if (cardData.error_for_user) {
                console.log("Card build error:", cardData);
                setIsProcessingCard(false);
                return;
            }

            // Retrieve response, set state
            setShowdownBotCardData(cardData);
            
            console.log("Card built successfully:", cardData);

            lastFormRef.current = card_payload; // Store form data for live updates
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

        submitCard(form);
    };

    // Handle shuffle
    const handleShuffle = () => {

        // Prevent multiple submissions
        if (isProcessingCard) return; 

        // Use form data but replace name with shuffle key
        const shuffledForm = {
            ...form,
            name: '((RANDOM))'
        };

        submitCard(shuffledForm);
    };

    // Handle reset
    const handleReset = () => {

        // Reset form to initial state
        setForm(FORM_DEFAULTS);
    };

    // Handle Enter key press
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
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
    }, [form]); // Re-bind when form changes so handleBuild has latest state

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

    // Dynamic date management
    useEffect(() => {
        
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
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            saveFormSettings(form);
        }, 1000); // Save 1 second after user stops typing

        return () => clearTimeout(timeoutId);
    }, [form]);

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
            case 'SPLIT':
                return (
                    <FormInput
                        label="Split*"
                        value={form.split || ''}
                        onChange={(value) => setForm({ ...form, split: value })}
                        isClearable={true}
                        className='col-span-full'
                    />
                );
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

            <div className="
                @container flex flex-col @2xl:flex-row 
                @2xl:overflow-hidden 
                @2xl:h-[calc(100vh-3rem)]
            ">

                {/* Form Inputs */}
                <section className={`
                    ${isFormCollapsed ? 'w-auto' : 'w-full @2xl:w-84 @2xl:flex-shrink-0'}
                    border-b-2 @2xl:border-r border-form-element
                    bg-background-secondary
                    flex flex-col 
                    h-full
                `}>

                    {/* Scrollable area */}
                    <div className={`flex-1 overflow-y-auto pt-4 ${isFormCollapsed ? 'px-1' : 'px-4'}`}>

                        {/* Form Inputs */}
                        <div className={`space-y-4 ${isFormCollapsed ? 'pb-2' : 'pb-6'} @2xl:pb-64 justify-center`}>

                            {/* Search Box and Collapse Button */}
                            <div className='flex col-span-full pb-2 gap-2'>
                                <PlayerSearchInput
                                    label=""
                                    value={query}
                                    className={`${isFormCollapsed ? 'hidden' : 'block w-full'}`}
                                    onChange={(selection) => setForm({ ...form, name: selection.name, year: selection.year })}
                                />

                                <button
                                    className={`
                                        text-xl p-2 rounded-lg hover:bg-[var(--background-tertiary)] transition-colors 
                                        ${isFormCollapsed ? 'flex flex-row-reverse @2xl:flex-col items-center gap-2 @2xl:gap-3 px-4 w-full justify-center ' : ''}
                                    `}
                                    onClick={() => setIsFormCollapsed(!isFormCollapsed)}
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
                                            <span className="text-nowrap text-md font-semibold text-[var(--tertiary)] @2xl:hidden">
                                                Card Settings
                                            </span>
                                            {/* Vertical text for large screens */}
                                            <span 
                                                className='text-nowrap text-md font-semibold text-[var(--tertiary)] hidden @2xl:block'
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

                            {!isFormCollapsed && (
                                <>
                                    {/* Display Error (If Applicable) */}
                                    {errorMessage && (
                                        <div className='w-full border-3 bg-red-500/10 text-red-500 border-red-500 rounded-xl p-2'>
                                            <div className='flex flex-row justify-between items-center mb-1 text-xl'>
                                                <div className='font-black flex flex-row gap-2 items-center'> 
                                                    <FaExclamationCircle /> 
                                                    Error
                                                </div>
                                                <button className='text-red-500 underline' onClick={() => setErrorMessage('')}>
                                                    <FaXmark />
                                                </button>
                                            </div>
                                            <div className="text-md font-bold overflow-scroll">
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
                                            onChange={(value) => setForm({ ...form, name: value || '' })}
                                            isClearable={true}
                                            isTitleCase={true}
                                        />

                                        <FormInput
                                            label="Year*"
                                            value={form.year}
                                            onChange={(value) => setForm({ ...form, year: value || '' })}
                                            isClearable={true}
                                        />

                                        <FormDropdown
                                            label="Period"
                                            options={statsPeriodOptions}
                                            selectedOption={form.stats_period_type}
                                            onChange={(value) => setForm({ ...form, stats_period_type: value })}
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

                                        <FormDropdown
                                            label="Expansion"
                                            options={expansionOptions}
                                            selectedOption={form.expansion}
                                            onChange={(value) => setForm({ ...form, expansion: value })}
                                        />

                                        <FormDropdown
                                            label="Edition"
                                            options={editionOptions}
                                            selectedOption={form.edition}
                                            onChange={(value) => setForm({ ...form, edition: value })}
                                        />

                                        <FormInput
                                            label="Set Number"
                                            className='col-span-full'
                                            value={form.set_number || ''}
                                            onChange={(value) => setForm({ ...form, set_number: value || '' })}
                                            isClearable={true}
                                        />

                                        <FormEnabler label='Show Year as Text' isEnabled={form.show_year_text} onChange={(isEnabled) => setForm({ ...form, show_year_text: !isEnabled })} />
                                        <FormEnabler label='Add 1 to Set Year' isEnabled={form.add_one_to_set_year} onChange={(isEnabled) => setForm({ ...form, add_one_to_set_year: !isEnabled })} />

                                    </FormSection>

                                    {/* Image */}
                                    <FormSection 
                                        title='Image' 
                                        icon={<FaImage />} 
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

                                        {/* Source Specific Options */}
                                        <FormDropdown
                                            label="Image Parallel"
                                            className={`col-span-full ${form.image_source === 'AUTO' ? '' : 'hidden'}`}
                                            options={imageParallelOptions}
                                            selectedOption={form.image_parallel}
                                            onChange={(value) => setForm({ ...form, image_parallel: value })}
                                        />
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
                                                    <label className="block text-sm font-medium text-[var(--tertiary)] mb-1">
                                                        Preview
                                                    </label>
                                                    <img
                                                        src={getImagePreview() || ''}
                                                        alt="Invalid Image"
                                                        className="max-w-full h-38 object-contain rounded-lg border-2 border-form-element"
                                                    />
                                                </div>

                                                <button type="button" className="flex flex-col items-center space-x-2 cursor-pointer hover:opacity-50">
                                                    <FaXmark
                                                        className="text-3xl text-red-500 hover:text-red-300 transition-colors"
                                                        onClick={() => handleFileChange(null)}
                                                    />
                                                    <span>Remove Image</span>
                                                </button>
                                            </div>
                                        )}

                                        <FormDropdown
                                            label="Image Coloring"
                                            options={imageColoringOptions}
                                            selectedOption={form.image_coloring}
                                            onChange={(value) => setForm({ ...form, image_coloring: value })}
                                            className='text-nowrap'
                                        />

                                        <FormDropdown
                                            label="Outer Glow"
                                            options={outerGlowOptions}
                                            selectedOption={form.image_glow_multiplier}
                                            onChange={(value) => setForm({ ...form, image_glow_multiplier: value })}
                                        />

                                        {/* Extras */}
                                        <h1 className="col-span-full text-md font-semibold text-secondary mt-2">Extras</h1>
                                        <FormDropdown
                                            label="Show Real Stats?"
                                            options={statHighlightsTypeOptions}
                                            selectedOption={form.stat_highlights_type || 'NONE'}
                                            onChange={(value) => setForm({ ...form, stat_highlights_type: value })}
                                        />
                                        <FormDropdown
                                            label="Show Nickname?"
                                            options={nicknameIndexOptions}
                                            selectedOption={form.nickname_index || 'NONE'}
                                            onChange={(value) => setForm({ ...form, nickname_index: value })}
                                        />
                                        <FormEnabler label='Add Border' isEnabled={form.add_image_border} onChange={(isEnabled) => setForm({ ...form, add_image_border: !isEnabled })} />
                                        <FormEnabler label='Dark Mode' isEnabled={form.is_dark_mode} onChange={(isEnabled) => setForm({ ...form, is_dark_mode: !isEnabled })} />
                                        <FormEnabler label='Remove Team' className='col-span-full' isEnabled={form.remove_team_branding} onChange={(isEnabled) => setForm({ ...form, remove_team_branding: !isEnabled })} />


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

                                        <FormEnabler
                                            label="Variable Speed 00-01"
                                            className="col-span-2"
                                            isEnabled={form.is_variable_speed_00_01 || false}
                                            onChange={(isEnabled) => setForm({ ...form, is_variable_speed_00_01: !isEnabled })}
                                        />

                                    </FormSection>
                                </>
                            )}
                            
                        </div>

                        {/* Form Buttons */}
                        {/* Make sticky at bottom */}
                        <footer className={`
                            fixed bottom-0 left-0 right-0 z-20
                            -mx-4 px-12 py-4 @xl:p-6
                            @2xl:sticky @2xl:bottom-0 @2xl:left-auto @2xl:right-auto @2xl:z-auto
                            bg-background-secondary/95 backdrop-blur
                            border-t border-form-element
                            shadow-md
                            ${isFormCollapsed ? '@2xl:hidden' : ''}
                        `}>

                            <div className="flex flex-col gap-2">
                                {/* Build Card */}
                                <button
                                    type="button"
                                    title={disableBuildButton ? "Please enter player name and year" : ""}
                                    className={`
                                        flex items-center justify-center
                                        w-full rounded-xl py-4
                                        text-white
                                        bg-[var(--showdown-blue)]
                                        ${disableBuildButton
                                            ? 'cursor-not-allowed opacity-25'
                                            : 'hover:bg-[var(--showdown-blue)]/50 cursor-pointer'
                                        }
                                        font-black
                                    `}
                                    onClick={handleBuild}
                                >
                                    <FaBaseballBall className="mr-1" />
                                    Build Card
                                </button>

                                

                                <div className="flex flex-row gap-2 h-10 font-black text-sm">
                                    
                                    {/* Shuffle Button */}
                                    <button
                                        type="button"
                                        className="
                                            flex items-center justify-center
                                            w-1/2
                                            rounded-xl
                                            bg-yellow-500 hover:bg-yellow-300
                                            cursor-pointer
                                        "
                                        onClick={handleShuffle}
                                    >
                                        <FaShuffle className="mr-1" />
                                        <div className='inline'>Shuffle</div>
                                    </button>

                                    {/* Reset Button */}
                                    <button
                                        type="button"
                                        className="
                                            flex items-center justify-center
                                            w-1/2
                                            rounded-xl
                                            text-white
                                            bg-[var(--tertiary)]/50 hover:bg-[var(--tertiary)]
                                            cursor-pointer
                                        "
                                        onClick={handleReset}
                                    >
                                        <FaRotateLeft className="mr-1" />
                                        <div className='inline'>Reset</div>
                                    </button>
                                </div>

                            </div>

                        </footer>
                        
                    </div>

                </section>

                {/* Preview Section */}
                <section className="
                    w-full @2xl:flex-grow
                    pb-64 @2xl:pb-0
                ">
                    <CardDetail 
                        showdownBotCardData={showdownBotCardData} 
                        isLoading={isProcessingCard} 
                        isLoadingGameBoxscore={isLoadingGameBoxscore}
                    />
                </section>
                
            </div>
        </div>
    );
}

export default CustomCardBuilder;