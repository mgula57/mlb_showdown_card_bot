/**
 * @fileoverview ThemeToggleButton Component
 * 
 * A cycling theme toggle button that allows users to switch between three theme modes:
 * - Light: Force light theme regardless of system preference
 * - Dark: Force dark theme regardless of system preference  
 * - System: Follow the user's system/OS theme preference automatically
 * 
 * Features:
 * - Visual icons that clearly represent each theme state
 * - Smooth hover effects and transitions
 * - Accessible design with descriptive tooltips
 * - Integration with global theme context
 * - Cycling behavior for easy theme switching
 * - Compact design suitable for side menu footer placement
 * 
 * The button integrates with the SiteSettingsContext to provide consistent
 * theme management across the entire application.
 * 
 * @component
 * @example
 * ```tsx
 * <ThemeToggleButton />
 * ```
 */

import React from "react"
import { FaSun, FaMoon, FaDesktop } from "react-icons/fa";
import { useTheme } from "../shared/SiteSettingsContext";

/**
 * Cycling theme toggle button with visual feedback
 * 
 * Provides a simple interface for users to cycle through all available
 * theme options in a logical progression:
 * 1. Light theme (sun icon)
 * 2. Dark theme (moon icon)  
 * 3. System theme (desktop icon)
 * 
 * Features:
 * - **Visual Clarity**: Each theme has a distinct, recognizable icon
 * - **Cycling Logic**: Click to advance through themes in order
 * - **Accessibility**: Descriptive tooltips explain current state and action
 * - **Responsive**: Consistent sizing and hover effects
 * - **Context Integration**: Automatically syncs with global theme state
 * 
 * The component handles the theme cycling logic internally and delegates
 * actual theme application to the SiteSettingsContext.
 * 
 * @returns A clickable button that cycles through available themes
 */
const ThemeToggleButton: React.FC = () => {
    const { theme, setTheme } = useTheme();

    /**
     * Cycles to the next theme in the sequence: light → dark → system → light
     * Uses modulo arithmetic to wrap around to the beginning of the sequence
     */
    const cycleTheme = (): void => {
        const themes = ['light', 'dark', 'system'] as const;
        const currentIndex = themes.indexOf(theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        setTheme(themes[nextIndex]);
    };

    /**
     * Returns the appropriate icon component for the current theme state
     * Each icon provides clear visual feedback about the active theme mode
     * 
     * @returns React icon component representing the current theme
     */
    const getIcon = () => {
        switch (theme) {
            case 'light':
                return <FaSun className="w-4 h-4" />;      // Sun represents light theme
            case 'dark':
                return <FaMoon className="w-4 h-4" />;     // Moon represents dark theme
            case 'system':
                return <FaDesktop className="w-4 h-4" />;  // Desktop represents system theme
            default:
                return <FaDesktop className="w-4 h-4" />;  // Fallback to system icon
        }
    };

    return (
        <button
            onClick={cycleTheme}
            className={`
                p-2 rounded-md hover:bg-secondary/20 transition-colors duration-200
                flex items-center justify-center
            `}
            title={`Current theme: ${theme}. Click to cycle through light/dark/system.`}
            aria-label={`Theme toggle button. Current theme: ${theme}. Click to cycle themes.`}
        >
            {getIcon()}
        </button>
    );
};

export default ThemeToggleButton;