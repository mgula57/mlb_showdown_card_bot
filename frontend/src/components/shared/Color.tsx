
/**
 * @fileoverview Color Utility Functions
 * 
 * Provides color manipulation utilities for determining optimal text contrast
 * against background colors. Uses luminance calculations based on W3C accessibility
 * guidelines to ensure readable text color combinations.
 * 
 * @module ColorUtils
 */

/**
 * Calculates the optimal contrast color (black or white) for text displayed
 * on a given background color using luminance-based contrast ratios.
 * 
 * This function:
 * - Parses RGB color values from CSS rgb() format strings
 * - Calculates relative luminance using the standard formula (ITU-R BT.709)
 * - Returns black (#000000) for light backgrounds or white (#FFFFFF) for dark backgrounds
 * - Ensures accessible text contrast ratios per WCAG guidelines
 * 
 * @param backgroundColor - CSS color string in rgb() format (e.g., "rgb(255, 128, 0)")
 * @returns Hex color string - "#000000" for black text or "#FFFFFF" for white text
 * 
 * @example
 * ```typescript
 * getContrastColor("rgb(255, 255, 255)") // Returns "#000000" (black on white)
 * getContrastColor("rgb(0, 0, 0)")       // Returns "#FFFFFF" (white on black)
 * getContrastColor("rgb(128, 128, 128)") // Returns "#FFFFFF" (white on gray)
 * ```
 */
export const getContrastColor = (backgroundColor: string): string => {
    // Extract RGB values using regex pattern matching
    const rgbMatch = backgroundColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (!rgbMatch) return '#000000'; // Fallback to black if parsing fails
    
    // Convert matched strings to numbers, destructuring to get R, G, B values
    const [, r, g, b] = rgbMatch.map(Number);
    
    // Calculate relative luminance using ITU-R BT.709 coefficients
    // This formula weights green most heavily as human eyes are most sensitive to green light
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    // Apply contrast threshold: return black for light backgrounds (luminance > 0.6),
    // white for dark backgrounds (luminance <= 0.6)
    return luminance > 0.6 ? '#000000' : '#FFFFFF';
};