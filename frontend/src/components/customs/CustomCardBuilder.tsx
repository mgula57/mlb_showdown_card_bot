// ----------------------------------
// MARK: - Imports
// ----------------------------------

import { useEffect, useState } from 'react';
import FormInput from './FormInput';
import FormSection from './FormSection';
import FormDropdown from './FormDropdown';
import FormEnabler from './FormEnabler';
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
import { FaTable, FaImage, FaLayerGroup, FaUser } from 'react-icons/fa';

// ----------------------------------
// MARK: - Form Interface
// ----------------------------------

/** State for the custom card form */
interface CustomCardFormState {
    // Name and Year
    name: string; // ex: "Mike Trout"
    year: string; // ex: "2023"
    period: string; // e.g. "REGULAR"
    start_date?: string | null; // e.g. "2023-05-01"
    end_date?: string | null; // e.g. "2023-10-01"
    split?: string | null; // e.g. "First Half"

    // Set
    expansion: string; // e.g. "BS"
    set_number?: string | null; // e.g. "001"
    edition: string; // e.g. "Cooperstown"

    // Image
    image_source: string; // e.g. "Auto"
    image_parallel: string; // e.g. "Rainbow Foil"
    image_coloring: string; // e.g. "Primary"
    image_outer_glow: string; // e.g. "Glow 1x"
    image_url?: string | null; // e.g. "https://example.com/image.png"
    image_upload?: File | null; // For file uploads

    // Image Extras
    add_image_border: boolean; // Whether to add a border to the image
    is_dark_mode: boolean; // Whether the card is in dark mode
    remove_team_branding: boolean; // Whether to remove team branding from the image
    stats_type?: string; // e.g. "ALL", "OLD", "MODERN"
    nickname_index?: string; // e.g. "NICKNAME 1",
    show_year_plus_one?: boolean; // Whether to show the year + 1 in the set section
    show_year_text?: boolean; // Whether to show the year text as a label on the card

    // Chart
    chart_version?: string; // e.g. "1"
    era?: string; // e.g. "Dynamic"
    is_variable_speed_00_01?: boolean; // Whether to use variable speed for 00-01

}

// ----------------------------------
// MARK: - Custom Card Props
// ----------------------------------

type CustomCardBuilderProps = {
    condenseFormInputs?: boolean | null;
}

// ----------------------------------
// MARK: - Custom Card Component
// ----------------------------------

/** 
 * Card Creation Page for users to create and customize their own cards. 
*/
function CustomCardBuilder({ condenseFormInputs }: CustomCardBuilderProps) {

    // Card States
    const { userShowdownSet } = useSiteSettings();
    const [showdownBotCardData, setShowdownBotCardData] = useState<ShowdownBotCardAPIResponse | null>(null);

    // Define the form state
    const [form, setForm] = useState<CustomCardFormState>({
        name: "", year: "", period: "REGULAR", start_date: null, end_date: null, split: null,
        expansion: "BS", set_number: null, edition: "NONE",
        image_source: "AUTO", image_parallel: "NONE", image_coloring: "PRIMARY", image_outer_glow: "1",
        image_url: null, image_upload: null,
        add_image_border: false, is_dark_mode: false, remove_team_branding: false,
        stats_type: "NONE", nickname_index: "NONE", show_year_plus_one: false, show_year_text: false,
        chart_version: "1", era: "DYNAMIC", is_variable_speed_00_01: false
    });

    // ---------------------------------
    // MARK: Select Option Arrays
    // ---------------------------------

    // Expansion options
    const expansionOptions: SelectOption[] = [
        { label: "Base Set", value: "BS", image: expansionBS },
        { label: "Trading Deadline", value: "TD", image: expansionTD },
        { label: "Pennant Run", value: "PR", image: expansionPR },
    ]

    // Period Options
    const periodOptions: SelectOption[] = [
        { 'value': 'REGULAR', 'label': 'Regular Season', 'symbol': '⚾' },
        { 'value': 'POST', 'label': 'Postseason', 'symbol': '🏆' },
        { 'value': 'DATES', 'label': 'Date Range', 'symbol': '📅' },
        { 'value': 'SPLIT', 'label': 'Split', 'symbol': '🔀' },
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

    const statsTypeOptions: SelectOption[] = [
        { "label": "None", "value": "NONE" },
        { "label": "Old School", "value": "OLD" },
        { "label": "Modern", "value": "MODERN" },
        { "label": "Both", "value": "ALL" },
    ]

    const nicknameIndexOptions: SelectOption[] = [
        { "label": "None", "value": "NONE" },
        { "label": "Nickname 1", "value": "NICK1" },
        { "label": "Nickname 2", "value": "NICK2" },
        { "label": "Nickname 3", "value": "NICK3" },
    ]

    const outerGlowOptions: SelectOption[] = [
        { "label": "Glow 1x", "value": "1" },
        { "label": "Glow 2x", "value": "2" },
        { "label": "Glow 3x", "value": "3" },
    ]

    // ---------------------------------
    // MARK: Build Processing
    // ---------------------------------

    const handleBuild = async () => {
        try {
            // TODO: Handle image uploads
            console.log("Building card with form data:", form);

            var { image_upload, image_source, ...payload } = form; // omit the File

            const cardData = await buildCustomCard({
                ...payload,

                // Default parameters/settings
                set: userShowdownSet,
                is_running_on_website: true,
                image_output_folder_path: "static/output/",
                show_historical_points: true,
                season_trend_date_aggregation: 'WEEK',
            });

            console.log("Card built successfully:", cardData);

            // Retrieve response, set state
            setShowdownBotCardData(cardData);

        } catch (err) {
            console.error(err);
        }
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
    // MARK: Render SubComponents
    // ---------------------------------

    /** 
     * Render the period inputs based on the selected period 
     * This will show different inputs based on the period type selected.
     */
    const renderPeriodInputs = () => {
        switch (form.period) {
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
                        label="Split"
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

    const renderImageSourceInputs = () => {
        switch (form.image_source) {
            case 'AUTO':
                return (
                    <FormDropdown
                        label="Image Parallel"
                        className='col-span-full'
                        options={imageParallelOptions}
                        selectedOption={form.image_parallel}
                        onChange={(value) => setForm({ ...form, image_parallel: value })}
                    />
                );
            case 'LINK':
                return (
                    <FormInput
                        label="Image URL"
                        className='col-span-full'
                        value={form.image_url || ''}
                        onChange={(value) => setForm({ ...form, image_url: value || null })}
                        isClearable={true}
                        placeholder="https://example.com/image.png"
                    />
                );
            case 'UPLOAD':
                return (
                    <FormInput
                        label="Upload Image"
                        className='col-span-full'
                        value={form.image_upload?.name || ''}
                        isClearable={true}
                        placeholder="Select an image file"
                        type="file"
                        onChangeFile={(file) => setForm({ ...form, image_upload: file })}
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
        <div className="
            flex flex-col md:flex-row 
            md:overflow-hidden 
            md:h-[calc(100vh-3rem)]
        ">

            {/* Form Inputs */}
            <section className={`
                ${condenseFormInputs ? 
                      'w-full md:max-w-80 xl:max-w-92 2xl:max-w-112' 
                    : 'w-full md:max-w-96 xl:max-w-108 2xl:max-w-128'
                }
                md:border-r border-r-gray-800
                bg-background-secondary
                flex flex-col 
                h-full
            `}>

                {/* Scrollable area */}
                <div className="flex-1 overflow-y-auto px-4 pt-4">

                    {/* Form Inputs */}
                    <div className="space-y-4 pb-12">
                        {/* Player */}
                        <FormSection title='Player' icon={<FaUser />} isOpenByDefault={true}>

                            <FormInput
                                label="Name"
                                className='col-span-full'
                                value={form.name}
                                onChange={(value) => setForm({ ...form, name: value || '' })}
                                isClearable={true}
                            />

                            <FormInput
                                label="Year"
                                value={form.year}
                                onChange={(value) => setForm({ ...form, year: value || '' })}
                                isClearable={true}
                            />

                            <FormDropdown
                                label="Period"
                                options={periodOptions}
                                selectedOption={form.period}
                                onChange={(value) => setForm({ ...form, period: value })}
                            />

                            {renderPeriodInputs()}

                        </FormSection>

                        {/* Set */}
                        <FormSection title='Set' icon={<FaLayerGroup />} isOpenByDefault={true}>

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
                                value={form.set_number || ''}
                                onChange={(value) => setForm({ ...form, set_number: value || '' })}
                                isClearable={true}
                            />
                        </FormSection>

                        {/* Image */}
                        <FormSection title='Image' icon={<FaImage />} isOpenByDefault={true}>

                            <FormDropdown
                                label="Player Image"
                                className='col-span-full'
                                options={imageSourceOptions}
                                selectedOption={form.image_source}
                                onChange={(value) => setForm({ ...form, image_source: value })}
                            />

                            {renderImageSourceInputs()}

                            <FormDropdown
                                label="Image Coloring"
                                options={imageColoringOptions}
                                selectedOption={form.image_coloring}
                                onChange={(value) => setForm({ ...form, image_coloring: value })}
                            />

                            <FormDropdown
                                label="Outer Glow"
                                options={outerGlowOptions}
                                selectedOption={form.image_outer_glow}
                                onChange={(value) => setForm({ ...form, image_outer_glow: value })}
                            />

                            {/* Extras */}
                            <h1 className="col-span-full text-md font-semibold text-secondary mt-2">Extras</h1>
                            <FormDropdown
                                label="Show Real Stats?"
                                options={statsTypeOptions}
                                selectedOption={form.stats_type || 'NONE'}
                                onChange={(value) => setForm({ ...form, stats_type: value })}
                            />
                            <FormDropdown
                                label="Show Nickname?"
                                options={nicknameIndexOptions}
                                selectedOption={form.nickname_index || 'NONE'}
                                onChange={(value) => setForm({ ...form, nickname_index: value })}
                            />
                            <FormEnabler label='Add Border' isEnabled={form.add_image_border} onChange={(isEnabled) => setForm({ ...form, add_image_border: !isEnabled })} />
                            <FormEnabler label='Dark Mode' isEnabled={form.is_dark_mode} onChange={(isEnabled) => setForm({ ...form, is_dark_mode: !isEnabled })} />
                            <FormEnabler label='Remove Team' isEnabled={form.remove_team_branding} onChange={(isEnabled) => setForm({ ...form, remove_team_branding: !isEnabled })} />


                        </FormSection>

                        {/* Chart */}
                        <FormSection title='Chart' icon={<FaTable />} isOpenByDefault={false}>

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
                    </div>

                    {/* Form Buttons */}
                    {/* Make sticky at bottom */}
                    <footer className="
                        fixed bottom-0 left-0 right-0 z-20
                        md:sticky md:bottom-0 md:left-auto md:right-auto md:z-auto
                        -mx-4 p-6
                        bg-background-secondary/95 backdrop-blur
                        md:border-t border-form-element
                        shadow-md
                    ">
                        <button
                            type="button"
                            className="
                                w-full rounded-lg p-2
                                text-white
                                bg-blue-400 hover:bg-blue-500
                                cursor-pointer
                            "
                            onClick={handleBuild}
                        >
                            Build Card
                            <span className="pl-1 text-xs opacity-75">(Enter)</span>
                        </button>
                    </footer>

                </div>

            </section>

            {/* Preview Section */}
            <section>

                <CardDetail showdownBotCardData={showdownBotCardData} />

            </section>
            
        </div>
    );
}

export default CustomCardBuilder;