import { FORM_DEFAULTS } from '../customs/CustomCardBuilder';
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
