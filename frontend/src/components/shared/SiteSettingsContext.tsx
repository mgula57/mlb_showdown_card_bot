/**
 * @fileoverview Site Settings Context and Theme Management
 * 
 * Provides global state management for application-wide settings including:
 * - MLB Showdown set preferences with visual assets
 * - Theme management (light/dark/system) with localStorage persistence
 * - System theme detection and automatic switching
 * - CSS class management for theme application
 * - Centralized configuration for Showdown sets and imagery
 * 
 * The context handles complex theme logic including:
 * - Initial theme detection from localStorage and system preferences
 * - DOM manipulation for CSS class updates
 * - Media query listening for system theme changes
 * - Proper cleanup of event listeners
 * 
 * @module SiteSettingsContext
 */

import React, { createContext, useContext, useState, useEffect } from "react";

/**
 * Available MLB Showdown sets with their visual assets and styling
 * Each set includes value identifier, display label, image path, and optional text color
 */
export const showdownSets: Array<{ value: string; label: string; image?: string | undefined; textColor?: string | undefined; }> = [
    { value: "2000", label: "", textColor: "text-blue", image: "/images/sets/set-2000.png" },
    { value: "2001", label: "", image: "/images/sets/set-2001.png" },
    { value: "CLASSIC", label: "", image: "/images/sets/set-classic.png" },
    { value: "2002", label: "", image: "/images/sets/set-2002.png" },
    { value: "2003", label: "", image: "/images/sets/set-2003.png" },
    { value: "2004", label: "", image: "/images/sets/set-2004.png" },
    { value: "2005", label: "", image: "/images/sets/set-2005.png" },
    { value: "EXPANDED", label: "", image: "/images/sets/set-expanded.png" },
];

/**
 * Utility function to retrieve the image path for a specific Showdown set
 * @param set - The set identifier to look up
 * @returns The image path for the set, or undefined if not found
 */
export const imageForSet = (set: string): string | undefined => {
    const found = showdownSets.find(s => s.value === set);
    return found?.image;
}

/** Available theme options for the application */
type Theme = 'light' | 'dark' | 'system';

/**
 * Site settings interface defining all globally available settings and their updaters
 */
type SiteSettings = {
    /** Currently selected MLB Showdown set identifier */
    userShowdownSet: string;
    /** Function to update the selected Showdown set */
    setUserShowdownSet: (v: string) => void;
    /** Current theme setting (light/dark/system) */
    theme: Theme;
    /** Function to update the theme setting */
    setTheme: (theme: Theme) => void;
    /** Computed boolean indicating if dark theme is currently active */
    isDark: boolean;
};

/** React context for sharing site settings across the application */
const SiteSettingsContext = createContext<SiteSettings | undefined>(undefined);

/**
 * Provider component that manages and distributes site settings throughout the application
 * 
 * Handles:
 * - MLB Showdown set preference with localStorage persistence
 * - Complex theme management with system preference detection
 * - DOM manipulation for CSS theme classes
 * - Media query monitoring for system theme changes
 * - Proper initialization and cleanup of theme-related effects
 * 
 * @param props - Provider props
 * @returns Context provider wrapping children with site settings
 */
export const SiteSettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {

    // MLB Showdown set preference state (defaults to 2001 set)
    const [userShowdownSet, setUserShowdownSetState] = useState("2001");

    // Theme preference state with localStorage initialization
    const [theme, setThemeState] = useState<Theme>(() => {
        return (localStorage.getItem('theme') as Theme) || 'system';
    });

    // Computed dark mode state based on theme preference and system settings
    const [isDark, setIsDark] = useState<boolean>(() => {
        const savedTheme = localStorage.getItem('theme') as Theme;
        if (savedTheme === 'dark') return true;
        if (savedTheme === 'light') return false;
        // Default to system preference if no saved theme or theme is 'system'
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });

    /**
     * Effect: Load user's Showdown set preference from localStorage on mount
     * Restores previously saved set selection for consistent user experience
     */
    useEffect(() => {
        const stored = localStorage.getItem("userShowdownSet");
        if (stored) setUserShowdownSetState(stored);
    }, []);

    /**
     * Updates the selected Showdown set and persists it to localStorage
     * @param v - The new Showdown set identifier
     */
    const setUserShowdownSet = (v: string) => {
        setUserShowdownSetState(v);
        localStorage.setItem("userShowdownSet", v);
    };

    /**
     * Effect: Main theme management logic
     * 
     * Handles:
     * - Determining actual theme state (light/dark) from preference and system
     * - Updating component state for React re-renders
     * - Manipulating DOM classes for CSS theme application
     * - Persisting theme preference to localStorage
     * 
     * Runs whenever theme preference changes
     */
    useEffect(() => {
        const root = document.documentElement;

        // Calculate effective theme based on preference and system settings
        const shouldBeDark = theme === 'dark' ||
            (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

        // Update React state for component re-renders
        setIsDark(shouldBeDark);

        // Update DOM classes for CSS theme application
        root.classList.remove('light', 'dark');
        root.classList.add(shouldBeDark ? 'dark' : 'light');

        // Persist theme preference to localStorage
        localStorage.setItem('theme', theme);
    }, [theme]);

    /**
     * Effect: System theme change monitoring
     * 
     * When theme is set to 'system', listens for OS-level theme changes
     * and updates the application theme accordingly. This provides seamless
     * integration with system-wide dark/light mode switching.
     * 
     * Only active when theme preference is 'system'
     */
    useEffect(() => {
        if (theme !== 'system') return;

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        /**
         * Handles system theme change events
         * Updates both React state and DOM classes when system theme changes
         */
        const handleChange = () => {
            const shouldBeDark = mediaQuery.matches;
            setIsDark(shouldBeDark);

            const root = document.documentElement;
            root.classList.remove('light', 'dark');
            root.classList.add(shouldBeDark ? 'dark' : 'light');
        };

        // Listen for system theme changes
        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, [theme]);

    /**
     * Updates the theme preference and triggers theme application logic
     * @param newTheme - The new theme preference (light/dark/system)
     */
    const setTheme = (newTheme: Theme) => {
        setThemeState(newTheme);
    };

    return (
        <SiteSettingsContext.Provider value={{ userShowdownSet, setUserShowdownSet, theme, setTheme, isDark }}>
            {children}
        </SiteSettingsContext.Provider>
    );
};

/**
 * Hook to access all site settings from the context
 * 
 * Provides access to:
 * - Current Showdown set preference and setter
 * - Theme preference and setter  
 * - Computed dark mode state
 * 
 * @throws Error if used outside of SiteSettingsProvider
 * @returns All site settings and their updater functions
 */
export const useSiteSettings = () => {
    const ctx = useContext(SiteSettingsContext);
    if (!ctx) throw new Error("useSiteSettings must be used within SiteSettingsProvider");
    return ctx;
};

/**
 * Convenience hook to access only theme-related settings
 * 
 * Provides a focused interface for components that only need theme functionality:
 * - Current theme preference (light/dark/system)
 * - Theme setter function
 * - Computed dark mode boolean
 * 
 * @throws Error if used outside of SiteSettingsProvider
 * @returns Theme settings and updater function
 */
export const useTheme = () => {
   const { theme, setTheme, isDark } = useSiteSettings();
   return { theme, setTheme, isDark };
};