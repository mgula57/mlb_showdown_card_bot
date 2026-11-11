import { FORM_DEFAULTS } from '../customs/CustomCardBuilder';
import type { ReleaseCard, ReleaseCardOverrides } from '../../api/releases';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { cardStyleFromCard } from '../cards/cardStyleOverrides';
import { CARD_STYLE_KEYS, setStyleSummary, imageStyleSummary, type CardStyleSettings } from '../customs/cardStyle';
import { POOL_FILTER_OPTIONS, activePoolFilters, cardMatchesPoolFilters, type PoolFilterBy, type PoolFilters } from './poolGrouping';

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

// ----------------------------------
// MARK: - Style Rules
// ----------------------------------

/** Style fields a rule can set. Edition-wide card settings (border, set year) and per-player
 * ones (nickname) stay out. Mirrored by `RULE_STYLE_KEYS` in `core/set_builder/release_style_rules.py`. */
export const RULE_STYLE_KEYS = [
    'image_parallel', 'image_parallel_coloring', 'edition', 'image_coloring', 'show_year_text', 'is_dark_mode', 'hide_team_logo',
] as const satisfies readonly (keyof CardStyleSettings)[];
export type RuleStyleKey = typeof RULE_STYLE_KEYS[number];
export type RuleStyle = Partial<Pick<CardStyleSettings, RuleStyleKey>>;

/** Pool dimensions a rule can test. Image match is left out since it changes as photos are matched,
 * which would restyle cards on its own. Mirrored by `ReleaseCardDimensions` in Python. */
export const STYLE_RULE_DIMENSIONS = POOL_FILTER_OPTIONS.filter(o => o.value !== 'image_match' && o.value !== 'chart_version');
const STYLE_RULE_DIMENSION_KEYS = new Set<PoolFilterBy>(STYLE_RULE_DIMENSIONS.map(o => o.value));

/** "IF every condition THEN style": conditions use the pool filter's values (OR within a dimension,
 * AND across). Stored in order under the edition's `attributes.style_rules`. */
export type EditionStyleRule = {
    id: string;
    when: PoolFilters;
    style: RuleStyle;
};

export function newStyleRule(): EditionStyleRule {
    return { id: crypto.randomUUID(), when: {}, style: {} };
}

/** Reads the edition's style rules out of its `attributes` blob, dropping anything malformed. */
export function parseEditionStyleRules(attributes: Record<string, unknown>): EditionStyleRule[] {
    const raw = attributes.style_rules;
    if (!Array.isArray(raw)) return [];
    return raw
        .filter((rule): rule is Record<string, unknown> => !!rule && typeof rule === 'object')
        .map(rule => ({
            id: typeof rule.id === 'string' ? rule.id : crypto.randomUUID(),
            when: rule.when && typeof rule.when === 'object' ? rule.when as PoolFilters : {},
            style: rule.style && typeof rule.style === 'object'
                ? Object.fromEntries(RULE_STYLE_KEYS.filter(key => key in (rule.style as object)).map(key => [key, (rule.style as Record<string, unknown>)[key]])) as RuleStyle
                : {},
        }));
}

/** A rule applies once it has a condition and sets something. A condition on a dimension rules
 * can't test (e.g. from a newer version) never matches rather than being skipped. */
export function styleRuleMatches(rule: EditionStyleRule, card: ReleaseCard): boolean {
    const conditions = activePoolFilters(rule.when);
    if (conditions.length === 0 || Object.keys(rule.style).length === 0) return false;
    if (conditions.some(([dimension]) => !STYLE_RULE_DIMENSION_KEYS.has(dimension))) return false;
    return cardMatchesPoolFilters(card, rule.when);
}

/** A release card's style before its own overrides: the edition style with each matching rule on
 * top, in order, so a later rule wins. */
export function releaseCardBaseStyle(editionStyle: CardStyleSettings, rules: EditionStyleRule[], card: ReleaseCard): CardStyleSettings {
    return rules.reduce<CardStyleSettings>(
        (style, rule) => styleRuleMatches(rule, card) ? { ...style, ...rule.style } : style,
        editionStyle
    );
}

/** A release card's style: its base style (edition + rules) with the card's own overrides on top. */
export function releaseCardStyle(editionStyle: CardStyleSettings, rules: EditionStyleRule[], card: ReleaseCard): CardStyleSettings {
    return { ...releaseCardBaseStyle(editionStyle, rules, card), ...card.card_overrides?.style };
}

/** The overrides that give a card `style` on top of its base style — only the fields that differ,
 * or null when there are none. */
export function releaseCardOverridesFor(style: CardStyleSettings, baseStyle: CardStyleSettings): ReleaseCardOverrides | null {
    const changed = CARD_STYLE_KEYS.filter(key => (style[key] ?? null) !== (baseStyle[key] ?? null));
    if (changed.length === 0) return null;
    return { style: Object.fromEntries(changed.map(key => [key, style[key]])) as Partial<CardStyleSettings> };
}

/** The overrides that keep a Card Builder custom's own styling once it joins an edition: whatever
 * it was built with beyond the builder's defaults. Anything left at a default follows the edition. */
export function customCardOverrides(snapshot: CardDatabaseRecord): ReleaseCardOverrides | null {
    if (!snapshot.card_data) return null;
    return releaseCardOverridesFor(cardStyleFromCard(snapshot.card_data, CARD_STYLE_DEFAULTS), CARD_STYLE_DEFAULTS);
}
