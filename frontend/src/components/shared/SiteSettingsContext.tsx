import React, { createContext, useContext, useState, useEffect } from "react";

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

export const imageForSet = (set: string): string | undefined => {
    const found = showdownSets.find(s => s.value === set);
    return found?.image;
}

type Theme = 'light' | 'dark' | 'system';

/** Props for the SiteSettingsContext */
type SiteSettings = {
    userShowdownSet: string;
    setUserShowdownSet: (v: string) => void;
    theme: Theme;
    setTheme: (theme: Theme) => void;
    isDark: boolean;
};

/** Context for site settings */
const SiteSettingsContext = createContext<SiteSettings | undefined>(undefined);

export const SiteSettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {

    // State to hold the user's MLB Showdown Set of choice
    const [userShowdownSet, setUserShowdownSetState] = useState("2000");

    // State to hold the theme
    const [theme, setThemeState] = useState<Theme>(() => {
        return (localStorage.getItem('theme') as Theme) || 'system';
    });

    const [isDark, setIsDark] = useState<boolean>(() => {
        const savedTheme = localStorage.getItem('theme') as Theme;
        if (savedTheme === 'dark') return true;
        if (savedTheme === 'light') return false;
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });

    // Load from localStorage on mount
    useEffect(() => {
        const stored = localStorage.getItem("userShowdownSet");
        if (stored) setUserShowdownSetState(stored);
    }, []);

    // Save to localStorage on change
    const setUserShowdownSet = (v: string) => {
        setUserShowdownSetState(v);
        localStorage.setItem("userShowdownSet", v);
    };

    // Handle theme changes
    useEffect(() => {
        const root = document.documentElement;

        // Determine if we should be in dark mode
        const shouldBeDark = theme === 'dark' ||
            (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

        // Update state
        setIsDark(shouldBeDark);

        // Update DOM
        root.classList.remove('light', 'dark');
        root.classList.add(shouldBeDark ? 'dark' : 'light');

        // Save to localStorage
        localStorage.setItem('theme', theme);
    }, [theme]);

    // Listen for system theme changes
    useEffect(() => {
        if (theme !== 'system') return;

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handleChange = () => {
            const shouldBeDark = mediaQuery.matches;
            setIsDark(shouldBeDark);

            const root = document.documentElement;
            root.classList.remove('light', 'dark');
            root.classList.add(shouldBeDark ? 'dark' : 'light');
        };

        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, [theme]);

    const setTheme = (newTheme: Theme) => {
        setThemeState(newTheme);
    };

    return (
        <SiteSettingsContext.Provider value={{ userShowdownSet, setUserShowdownSet, theme, setTheme, isDark }}>
            {children}
        </SiteSettingsContext.Provider>
    );
};

export const useSiteSettings = () => {
    const ctx = useContext(SiteSettingsContext);
    if (!ctx) throw new Error("useSiteSettings must be used within SiteSettingsProvider");
    return ctx;
};

export const useTheme = () => {
   const { theme, setTheme, isDark } = useSiteSettings();
   return { theme, setTheme, isDark };
};