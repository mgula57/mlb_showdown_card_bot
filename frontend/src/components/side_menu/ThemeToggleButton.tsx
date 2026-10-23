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
import { SideMenuRowContent } from "./SideMenuRowContent";
import { sideMenuRowClassName } from "./sideMenuStyles";

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
type ThemeToggleButtonProps = {
    /** Whether the parent side menu is in expanded state */
    isSideMenuOpen: boolean;
};

/** Icon + label for each theme mode, shown with the same row layout as the nav items */
const THEME_OPTIONS = {
    light:  { icon: FaSun,     text: 'Light Mode' },
    dark:   { icon: FaMoon,    text: 'Dark Mode' },
    system: { icon: FaDesktop, text: 'System Theme' },
} as const;

const ThemeToggleButton: React.FC<ThemeToggleButtonProps> = ({ isSideMenuOpen }) => {
    const { theme, setTheme } = useTheme();

    // Only replay the icon pop after the user cycles, not on first render
    const [hasCycled, setHasCycled] = React.useState(false);

    /**
     * Cycles to the next theme in the sequence: light → dark → system → light
     * Uses modulo arithmetic to wrap around to the beginning of the sequence
     */
    const cycleTheme = (): void => {
        const themes = ['light', 'dark', 'system'] as const;
        const currentIndex = themes.indexOf(theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        setTheme(themes[nextIndex]);
        setHasCycled(true);
    };

    const option = THEME_OPTIONS[theme] ?? THEME_OPTIONS.system;

    return (
        <button
            type="button"
            onClick={cycleTheme}
            className={sideMenuRowClassName(false)}
            title={`Current theme: ${theme}. Click to cycle through light/dark/system.`}
            aria-label={`Theme toggle button. Current theme: ${theme}. Click to cycle themes.`}
        >
            <SideMenuRowContent
                icon={option.icon}
                text={option.text}
                isSideMenuOpen={isSideMenuOpen}
                iconKey={hasCycled ? theme : undefined}
            />
        </button>
    );
};

export default ThemeToggleButton;