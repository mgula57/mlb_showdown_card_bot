import { FORM_DEFAULTS } from '../customs/CustomCardBuilder';
import type { ReleaseCardOverrides } from '../../api/releases';
import { CARD_STYLE_KEYS, setStyleSummary, imageStyleSummary, type CardStyleSettings } from '../customs/cardStyle';

export const CARD_STYLE_DEFAULTS = Object.fromEntries(
    CARD_STYLE_KEYS.map(key => [key, FORM_DEFAULTS[key]])
) as CardStyleSettings;

/** Reads the edition's default card style out of its `attributes` blob, falling back to the
 * Custom Card Builder defaults for anything unset. */
export function parseEditionStyle(attributes: Record<string, unknown>): CardStyleSettings {
    const raw = attributes.style;
    if (!raw || typeof raw !== 'object') return CARD_STYLE_DEFAULTS;
    const saved = Object.fromEntries(
        CARD_STYLE_KEYS.filter(key => key in raw).map(key => [key, (raw as Record<string, unknown>)[key]])
    );
    return { ...CARD_STYLE_DEFAULTS, ...saved };
}

/** Chips summarizing an edition's non-default style, e.g. for the button that opens this modal. */
export function editionStyleSummary(style: CardStyleSettings) {
    return [...setStyleSummary(style, CARD_STYLE_DEFAULTS), ...imageStyleSummary(style, CARD_STYLE_DEFAULTS)];
}

/** A release card's style: the edition style with the card's own overrides on top. */
export function releaseCardStyle(editionStyle: CardStyleSettings, overrides: ReleaseCardOverrides | null | undefined): CardStyleSettings {
    return { ...editionStyle, ...overrides?.style };
}

/** The overrides that give a card `style` within an edition — only the fields that differ from the
 * edition style, or null when there are none. */
export function releaseCardOverridesFor(style: CardStyleSettings, editionStyle: CardStyleSettings): ReleaseCardOverrides | null {
    const changed = CARD_STYLE_KEYS.filter(key => (style[key] ?? null) !== (editionStyle[key] ?? null));
    if (changed.length === 0) return null;
    return { style: Object.fromEntries(changed.map(key => [key, style[key]])) as Partial<CardStyleSettings> };
}
