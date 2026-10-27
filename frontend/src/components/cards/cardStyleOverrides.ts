/**
 * @fileoverview Style overrides any screen can inject into CardDetail, e.g. a Release Builder
 * edition's default style + set number. Kept free of runtime imports so CardDetail can use it
 * without a circular dependency (CustomCardBuilder renders CardDetail).
 */

import type { ShowdownBotCard } from '../../api/showdownBotCard';
import type { CardStyleSettings } from '../customs/cardStyle';

/** Card styling to render a card with instead of its own. Omitted keys keep the card's value. */
export type CardStyleOverrides = {
    /** Custom Card Builder style fields (Set + Image sections) */
    style?: Partial<CardStyleSettings>;
    /** Set number printed on the card. `null` clears it; omit to keep the card's own. */
    setNumber?: string | null;
    /** Already-rendered image of the card with these overrides (a `card_images` storage path, e.g. a
     * release edition's stored render) — shown as-is instead of generating a fresh image. */
    storagePath?: string | null;
};

/** Custom Card Builder form field -> `card.image` field, mirroring the backend's `image_` prefix strip,
 * with converters each way (form value -> image value, image value -> form value).
 * `disable_display_text_on_card` is the exception: it lives on the stats period. */
const IMAGE_FIELD_CONVERTERS: { [K in Exclude<keyof CardStyleSettings, 'disable_display_text_on_card'>]: [string, (value: CardStyleSettings[K]) => unknown, (value: unknown) => CardStyleSettings[K] | undefined] } = {
    expansion: ['expansion', v => v, v => (v as string | null) ?? undefined],
    edition: ['edition', v => v, v => (v as string | null) ?? undefined],
    add_one_to_set_year: ['add_one_to_set_year', v => v, v => (v as boolean | null) ?? undefined],
    show_year_text: ['show_year_text', v => v, v => (v as boolean | null) ?? undefined],
    image_parallel: ['parallel', v => v, v => (v as string | null) ?? undefined],
    image_coloring: ['coloring', v => v, v => (v as string | null) ?? undefined],
    image_glow_multiplier: ['glow_multiplier', v => parseFloat(v) || 1, v => (v == null ? undefined : String(v))],
    stat_highlights_type: ['stat_highlights_type', v => v ?? 'NONE', v => (v as string | null) ?? 'NONE'],
    nickname_index: ['nickname_index', v => (v && v !== 'NONE' ? parseInt(v, 10) : null), v => (v == null ? 'NONE' : String(v))],
    is_bordered: ['is_bordered', v => v, v => (v as boolean | null) ?? undefined],
    is_dark_mode: ['is_dark_mode', v => v, v => (v as boolean | null) ?? undefined],
    hide_team_logo: ['hide_team_logo', v => v, v => (v as boolean | null) ?? undefined],
};

/** A card's current style as Custom Card Builder style fields — the inverse of `applyCardStyleOverrides`.
 * Fields the card doesn't carry fall back to `fallback` (e.g. the builder's form defaults). */
export function cardStyleFromCard(card: ShowdownBotCard, fallback: CardStyleSettings): CardStyleSettings {
    const image = card.image as unknown as Record<string, unknown>;
    const style: Record<string, unknown> = { ...fallback };
    for (const [key, [imageKey, , fromImage]] of Object.entries(IMAGE_FIELD_CONVERTERS)) {
        const value = fromImage(image?.[imageKey]);
        if (value !== undefined) style[key] = value;
    }
    const hideDisplayText = card.stats_period?.disable_display_text_on_card;
    if (hideDisplayText != null) style.disable_display_text_on_card = hideDisplayText;
    return style as CardStyleSettings;
}

/** Applies style overrides to a card and clears its rendered image so a fresh one is generated
 * (or swaps in `storagePath` when the styled image already exists). */
export function applyCardStyleOverrides(card: ShowdownBotCard, overrides: CardStyleOverrides): ShowdownBotCard {
    const { style = {}, setNumber, storagePath } = overrides;
    const image: Record<string, unknown> = { ...card.image };
    for (const [key, [imageKey, convert]] of Object.entries(IMAGE_FIELD_CONVERTERS)) {
        const value = style[key as keyof CardStyleSettings];
        if (value !== undefined) image[imageKey] = (convert as (v: unknown) => unknown)(value);
    }
    if (setNumber !== undefined) image.set_number = setNumber;
    Object.assign(image, {
        // Re-derived from edition/parallel when the image is generated
        special_edition: 'NONE',
        output_file_name: null,
        output_folder_path: null,
        storage_path: storagePath ?? null,
        thumbnail_storage_path: null,
    });

    const hideDisplayText = style.disable_display_text_on_card;
    return {
        ...card,
        image: image as unknown as ShowdownBotCard['image'],
        stats_period: card.stats_period && hideDisplayText !== undefined
            ? { ...card.stats_period, disable_display_text_on_card: hideDisplayText }
            : card.stats_period,
    };
}
