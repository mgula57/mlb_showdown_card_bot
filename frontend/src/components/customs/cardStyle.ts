/**
 * @fileoverview Card style settings (Set + Image) shared by the Custom Card Builder and the
 * Release Builder's per-edition style defaults: types, option lists, and section summaries.
 */

import type { SelectOption } from '../shared/CustomSelect';
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

export const imageParallelOptions: SelectOption[] = [
    { "label": "Base", "value": "NONE", 'symbol': '―' },
    { "label": "Rainbow Foil", "value": "RF", 'symbol': '🌈' },
    { "label": "Team Color Blast", "value": "TCB", 'symbol': '💥' },
    { "label": "Galaxy", "value": "GALAXY", 'symbol': '🌌' },
    { "label": "Gold", "value": "GOLD", "borderColor": "border-(--gold)", 'symbol': '🟡' },
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
        const expansionOption = expansionOptions.find(opt => opt.value === values.expansion);
        summaries.push(expansionOption || { label: 'Expansion', value: values.expansion });
    }
    if (values.edition !== defaults.edition) {
        const editionOption = editionOptions.find(opt => opt.value === values.edition);
        summaries.push(editionOption || { label: 'Edition', value: values.edition });
    }
    if (setNumber) summaries.push({ label: 'Set Number', value: setNumber });

    if (values.add_one_to_set_year) summaries.push({ value: "Set Year +1", borderColor: 'border-(--green)' });
    if (values.show_year_text) summaries.push({ value: "Show Year Text", borderColor: 'border-(--green)' });
    if (values.disable_display_text_on_card) summaries.push({ value: "Hide Date Text", borderColor: 'border-(--green)' });
    return summaries;
}

/** Chips shown on the collapsed Image section. Parallel only applies to auto images. */
export function imageStyleSummary(values: CardStyleSettings, defaults: CardStyleSettings, includeParallel: boolean = true): SelectOption[] {
    const summaries: SelectOption[] = [];
    if (includeParallel && values.image_parallel !== defaults.image_parallel) {
        const parallelOption = imageParallelOptions.find(opt => opt.value === values.image_parallel);
        summaries.push(parallelOption || { label: 'Parallel', value: values.image_parallel });
    }
    if (values.image_coloring !== defaults.image_coloring) {
        const coloringOption = imageColoringOptions.find(opt => opt.value === values.image_coloring);
        summaries.push({ ...(coloringOption || { value: values.image_coloring }), label: 'Coloring' });
    }
    if (values.image_glow_multiplier !== defaults.image_glow_multiplier) {
        const glowOption = outerGlowOptions.find(opt => opt.value === values.image_glow_multiplier);
        summaries.push({ ...(glowOption || { value: values.image_glow_multiplier }), label: 'Glow' });
    }
    if (values.stat_highlights_type && values.stat_highlights_type !== defaults.stat_highlights_type) {
        const statsOption = statHighlightsTypeOptions.find(opt => opt.value === values.stat_highlights_type);
        summaries.push({ ...(statsOption || { value: values.stat_highlights_type }), label: 'Real Stats' });
    }
    if (values.nickname_index && values.nickname_index !== defaults.nickname_index) {
        const nicknameOption = nicknameIndexOptions.find(opt => opt.value === values.nickname_index);
        summaries.push({ ...(nicknameOption || { value: values.nickname_index }), label: 'Nickname' });
    }
    if (values.is_bordered !== defaults.is_bordered) summaries.push({ value: 'ADD BORDER', borderColor: 'border-(--green)' });
    if (values.is_dark_mode !== defaults.is_dark_mode) summaries.push({ value: 'DARK MODE', borderColor: 'border-(--green)' });
    if (values.hide_team_logo !== defaults.hide_team_logo) summaries.push({ value: 'REMOVE TEAM BRANDING', borderColor: 'border-(--green)' });
    return summaries;
}
