/**
 * @fileoverview Card style settings (Set + Image) shared by the Custom Card Builder and the
 * Release Builder's per-edition style defaults: types, option lists, and section summaries.
 */

import type { SelectOption } from '../shared/CustomSelect';
import { optionSummaryItem } from './FormSectionSummary';
import type { CustomCardFormState } from './CustomCardBuilder';

// ----------------------------------
// MARK: - Types
// ----------------------------------

export type CardStyleSettings = Pick<CustomCardFormState,
    | 'expansion' | 'edition' | 'add_one_to_set_year' | 'show_year_text' | 'disable_display_text_on_card'
    | 'image_parallel' | 'image_coloring' | 'image_glow_multiplier'
    | 'stat_highlights_type' | 'nickname_index' | 'is_bordered' | 'is_dark_mode' | 'hide_team_logo'
>;

export const CARD_STYLE_KEYS: (keyof CardStyleSettings)[] = [
    'expansion', 'edition', 'add_one_to_set_year', 'show_year_text', 'disable_display_text_on_card',
    'image_parallel', 'image_coloring', 'image_glow_multiplier',
    'stat_highlights_type', 'nickname_index', 'is_bordered', 'is_dark_mode', 'hide_team_logo',
];

/** Whether two styles differ on any style field */
export const isCardStyleDifferent = (a: CardStyleSettings, b: CardStyleSettings): boolean =>
    CARD_STYLE_KEYS.some(key => (a[key] ?? null) !== (b[key] ?? null));

/** Hiding the split/date text banner only applies to non-Base Set expansions (Trading Deadline,
 * Pennant Run) or the All-Star Game / Postseason editions. */
export const canHideDisplayText = (expansion: string, edition: string): boolean =>
    expansion !== 'BS' || edition === 'ASG' || edition === 'POST';

// ----------------------------------
// MARK: - Options
// ----------------------------------

const publicImagePath = (imageName: string): string => `/images/card/${imageName}.png`;

// design-ok-start: expansion and edition colors identify the physical card products, like team colors
export const expansionOptions: SelectOption[] = [
    { label: "Base Set", value: "BS", image: publicImagePath('expansion-bs') },
    { label: "Trading Deadline", value: "TD", image: publicImagePath('expansion-td'), 'borderColor': 'border-red-600' },
    { label: "Pennant Run", value: "PR", image: publicImagePath('expansion-pr'), 'borderColor': 'border-blue-900' },
];

export const editionOptions: SelectOption[] = [
    { 'value': 'NONE', 'label': 'None', 'symbol': '―' },
    { 'value': 'CC', 'label': 'Cooperstown Collection', 'image': publicImagePath('edition-cc'), 'borderColor': 'border-amber-800' },
    { 'value': 'SS', 'label': 'Super Season', 'image': publicImagePath('edition-ss'), 'borderColor': 'border-red-500' },
    { 'value': 'ASG', 'label': 'All-Star Game', 'symbol': '⭐', 'borderColor': 'border-yellow-400' },
    { 'value': 'RS', 'label': 'Rookie Season', 'image': publicImagePath('edition-rs'), 'borderColor': 'border-red-800' },
    { 'value': 'HOL', 'label': 'Holiday', 'symbol': '🎄', 'borderColor': 'border-green-600' },
    { 'value': 'NAT', 'label': 'Nationality', 'symbol': '🌍', 'borderColor': 'border-blue-500' },
    { 'value': 'WBC', 'label': 'WBC', 'image': publicImagePath('edition-wbc'), 'borderColor': 'border-red-700' },
    { 'value': 'POST', 'label': 'Postseason', 'image': publicImagePath('edition-post'), 'borderColor': 'border-blue-800' },
];
// design-ok-end

/** Zoomed-in and full-card samples rendered by `mlb_showdown_bot/scripts/parallel_samples.py` (keyed by the backend enum name). */
const parallelSample = (imageName: string) => ({
    image: `/images/parallels/${imageName}.webp`,
    fullImage: `/images/parallels/${imageName}-full.webp`,
});

/** Set the parallel samples were rendered on, since some parallels look different per set. */
export const PARALLEL_SAMPLE_SET = '2001';

/** Every parallel but Base carries a sample and description; Base is the card without one. */
export type ImageParallelOption = SelectOption & { fullImage?: string; description?: string };

export const imageParallelOptions: ImageParallelOption[] = [
    // Ungrouped options must come first, or they render under the previous group's header
    { "label": "Base", "value": "NONE", 'symbol': '―' },
    { "label": "Mystery", "value": "MYSTERY", ...parallelSample('mystery'), "description": "Hides the player's name and photo behind a silhouette." },

    // Groups render a header when `group` changes, so keep each group contiguous
    { "label": "Gold", "value": "GOLD", "borderColor": "border-(--gold)", ...parallelSample('gold'), "description": "A solid gold background behind the team logo.", "group": "Gold" },
    { "label": "Gold Rush", "value": "GOLDRUSH", ...parallelSample('gold-rush'), "description": "Gold rays bursting out from behind the player.", "group": "Gold" },
    { "label": "Gold Frame", "value": "GF", ...parallelSample('gold-frame'), "description": "A gold border around a faded vintage photo background.", "group": "Gold" },

    { "label": "Rainbow Foil", "value": "RF", ...parallelSample('rainbow-foil'), "description": "A shifting rainbow foil sheen over the background.", "group": "Shine" },
    { "label": "Sapphire", "value": "SPH", ...parallelSample('sapphire'), "description": "A faceted blue gem texture over the background.", "group": "Shine" },
    { "label": "Galaxy", "value": "GALAXY", ...parallelSample('galaxy'), "description": "Replaces the background with a starfield.", "group": "Shine" },
    { "label": "Moonlight", "value": "MOONLIGHT", ...parallelSample('moonlight'), "description": "A dim, muted wash over the background.", "group": "Shine" },

    { "label": "Team Color Blast", "value": "TCB", ...parallelSample('team-color-blast'), "description": "A white background with a burst of team color behind the player.", "group": "Backgrounds" },
    { "label": "Breakout", "value": "BREAKOUT", ...parallelSample('breakout'), "description": "The player bursts out of a team-color photo frame on concrete with halftone dots.", "group": "Backgrounds" },
    { "label": "Radial", "value": "RAD", ...parallelSample('radial'), "description": "Team-color rays radiating from behind the player.", "group": "Backgrounds" },
    { "label": "White Smoke", "value": "WS", ...parallelSample('white-smoke'), "description": "A clean white, smoky background.", "group": "Backgrounds" },
    { "label": "Flames", "value": "FLAMES", ...parallelSample('flames'), "description": "Replaces the background with fire.", "group": "Backgrounds" },

    { "label": "Comic Book Hero", "value": "CB", ...parallelSample('comic-book-hero'), "description": "Comic-style action lines behind the player.", "group": "Stylized" },
    { "label": "Black and White", "value": "B&W", ...parallelSample('black-and-white'), "description": "The whole image, player included, in black and white.", "group": "Stylized" },
];

export const imageColoringOptions: SelectOption[] = [
    { "label": "Primary Color", "value": "PRIMARY" },
    { "label": "Secondary Color", "value": "SECONDARY" },
    { "label": "Multi-Color", "value": "MULTI" },
];

export const statHighlightsTypeOptions: SelectOption[] = [
    { "label": "None", "value": "NONE" },
    { "label": "Classic", "value": "CLASSIC" },
    { "label": "Modern", "value": "MODERN" },
    { "label": "All", "value": "ALL" },
];

export const nicknameIndexOptions: SelectOption[] = [
    { "label": "None", "value": "NONE" },
    { "label": "Nickname 1", "value": "1" },
    { "label": "Nickname 2", "value": "2" },
    { "label": "Nickname 3", "value": "3" },
];

export const chartVersionOptions: SelectOption[] = [
    { 'value': '1', 'label': 'Version 1' },
    { 'value': '2', 'label': 'Version 2' },
    { 'value': '3', 'label': 'Version 3' },
    { 'value': '4', 'label': 'Version 4' },
    { 'value': '5', 'label': 'Version 5' },
];

export const outerGlowOptions: SelectOption[] = [
    { "label": "Glow 1x", "value": "1" },
    { "label": "Glow 2x", "value": "2" },
    { "label": "Glow 3x", "value": "3" },
];

// ----------------------------------
// MARK: - Section Summaries
// ----------------------------------

/** Chips shown on the collapsed Set section. `setNumber` is a per-card value, so callers without one omit it. */
export function setStyleSummary(values: CardStyleSettings, defaults: CardStyleSettings, setNumber?: string | null): SelectOption[] {
    const summaries: SelectOption[] = [];
    if (values.expansion !== defaults.expansion) {
        summaries.push(optionSummaryItem(expansionOptions, values.expansion));
    }
    if (values.edition !== defaults.edition) {
        summaries.push(optionSummaryItem(editionOptions, values.edition));
    }
    if (setNumber) summaries.push({ label: 'Set Number', value: setNumber });

    if (values.add_one_to_set_year) summaries.push({ value: "Set Year +1" });
    if (values.show_year_text) summaries.push({ value: "Show Year Text" });
    if (values.disable_display_text_on_card) summaries.push({ value: "Hide Date Text" });
    return summaries;
}

/** Chips shown on the collapsed Image section. Parallel only applies to auto images. */
export function imageStyleSummary(values: CardStyleSettings, defaults: CardStyleSettings, includeParallel: boolean = true): SelectOption[] {
    const summaries: SelectOption[] = [];
    if (includeParallel && values.image_parallel !== defaults.image_parallel) {
        // Named rather than pictured: the sample photo is unreadable at chip size
        const parallelOption = imageParallelOptions.find(opt => opt.value === values.image_parallel);
        summaries.push({ label: 'Parallel', value: parallelOption?.label ?? values.image_parallel, borderColor: parallelOption?.borderColor });
    }
    if (values.image_coloring !== defaults.image_coloring) {
        summaries.push(optionSummaryItem(imageColoringOptions, values.image_coloring, 'Coloring'));
    }
    if (values.image_glow_multiplier !== defaults.image_glow_multiplier) {
        summaries.push(optionSummaryItem(outerGlowOptions, values.image_glow_multiplier, 'Glow'));
    }
    if (values.stat_highlights_type && values.stat_highlights_type !== defaults.stat_highlights_type) {
        summaries.push(optionSummaryItem(statHighlightsTypeOptions, values.stat_highlights_type, 'Real Stats'));
    }
    if (values.nickname_index && values.nickname_index !== defaults.nickname_index) {
        summaries.push(optionSummaryItem(nicknameIndexOptions, values.nickname_index, 'Nickname'));
    }
    if (values.is_bordered !== defaults.is_bordered) summaries.push({ value: 'Add Border' });
    if (values.is_dark_mode !== defaults.is_dark_mode) summaries.push({ value: 'Dark Mode' });
    if (values.hide_team_logo !== defaults.hide_team_logo) summaries.push({ value: 'Remove Team Branding' });
    return summaries;
}
