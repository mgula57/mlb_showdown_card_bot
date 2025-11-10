/**
 * @fileoverview ShowdownBotLogo Component
 * 
 * A theme-aware logo component that automatically switches between light and dark
 * logo variants based on the current theme setting. Provides consistent branding
 * across the application while maintaining optimal visibility in both light and
 * dark themes.
 * 
 * The component uses conditional rendering with CSS classes to show/hide the
 * appropriate logo variant, ensuring smooth theme transitions without layout shifts.
 * 
 * @component
 * @example
 * ```tsx
 * <ShowdownBotLogo className="w-32 h-16" />
 * ```
 */

import React from "react";
import { useTheme } from "./SiteSettingsContext";

/**
 * Props for the ShowdownBotLogo component
 */
type ShowdownBotLogoProps = {
    /** Optional CSS class name for styling and sizing */
    className?: string;
};

/**
 * Theme-aware Showdown logo component that automatically displays the appropriate
 * logo variant based on the current theme setting.
 * 
 * Features:
 * - Automatic theme detection via SiteSettingsContext
 * - Smooth transitions between light/dark variants
 * - Responsive sizing through className prop
 * - Proper alt text for accessibility
 * - No layout shift during theme changes
 * 
 * The component renders both logo variants but uses CSS classes to show only
 * the appropriate one based on the current theme state.
 * 
 * @param props - Component props
 * @returns A theme-aware logo component with automatic variant switching
 */
const ShowdownBotLogo: React.FC<ShowdownBotLogoProps> = ({ className = "" }) => {

    // Get current theme state from context
    const { isDark } = useTheme();

    return (
        <div className={`relative ${className}`}>
            {/* Light theme logo - hidden in dark mode */}
            <img 
                src={"/images/logos/logo-light.png"} 
                alt="MLB Showdown Bot logo" 
                className={`object-contain ${isDark ? 'hidden' : 'block'}`}
            />
            {/* Dark theme logo - hidden in light mode */}
            <img 
                src={"/images/logos/logo-dark.png"} 
                alt="MLB Showdown Bot logo" 
                className={`object-contain ${isDark ? 'block' : 'hidden'}`}
            />
        </div>
    );
};

export default ShowdownBotLogo;
