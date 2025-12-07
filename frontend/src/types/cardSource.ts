/**
 * @fileoverview Card Source Types - Defines the different sources of MLB Showdown card data
 */

/**
 * Card source constants
 */
export const CardSource = {
    /** Showdown Bot generated cards */
    BOT: 'BOT',
    /** Original WOTC cards */
    WOTC: 'WOTC'
} as const;

/**
 * Type for CardSource values
 */
export type CardSource = typeof CardSource[keyof typeof CardSource];

/**
 * Type alias for CardSource values (alternative)
 */
export type CardSourceType = CardSource;

/**
 * Human-readable labels for each card source
 */
export const CardSourceLabels = {
    [CardSource.BOT]: 'Showdown Bot Cards',
    [CardSource.WOTC]: 'WOTC Cards'
} as const;

/**
 * Get the human-readable label for a card source
 * @param source - The card source value
 * @returns The human-readable label
 */
export const getCardSourceLabel = (source: CardSource): string => {
    return CardSourceLabels[source];
};

/**
 * Check if a string value is a valid CardSource
 * @param value - The string to validate
 * @returns True if the value is a valid CardSource
 */
export const isValidCardSource = (value: string): value is CardSource => {
    return Object.values(CardSource).includes(value as CardSource);
};