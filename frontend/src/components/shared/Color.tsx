
//** Standard function for finding best contrast color */
export const getContrastColor = (backgroundColor: string): string => {
    // Remove 'rgb(' and ')' and split by comma
    const rgbMatch = backgroundColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (!rgbMatch) return '#000000'; // Default to black if can't parse
    
    const [, r, g, b] = rgbMatch.map(Number);
    
    // Calculate luminance using standard formula
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    // Return white for dark backgrounds, black for light backgrounds
    return luminance > 0.5 ? '#000000' : '#FFFFFF';
};