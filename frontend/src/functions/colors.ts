
/** Enhance the visibility of colors based on the theme */
export const enhanceColorVisibility = (color: string) => {
    const isDarkMode = document.documentElement.classList.contains('dark');
    
    // Simple brightness adjustment
    if (isDarkMode) {
        // Add some brightness and saturation for dark mode
        return `color-mix(in srgb, ${color} 70%, white 30%)`;
    } else {
        // Slightly darken for light mode
        return `color-mix(in srgb, ${color} 85%, black 15%)`;
    }
};