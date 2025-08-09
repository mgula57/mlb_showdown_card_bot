import { useState, useEffect } from 'react';

/** Enum for theme types */
type Theme = 'light' | 'dark' | 'system';

/** Interface for the useTheme hook return type */
interface UseThemeReturn {
    theme: Theme;
    setTheme: (theme: Theme) => void;
    isDark: boolean;
}

/** Custom hook to manage theme state */
export const useTheme = (): UseThemeReturn => {
    const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem('theme') as Theme) || 'system');
    const [isDark, setIsDark] = useState(false);

    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

        const apply = () => {
            const dark = theme === 'system' ? mediaQuery.matches : theme === 'dark';
            setIsDark(dark);
            document.documentElement.classList.toggle('dark', dark);
            localStorage.setItem('theme', theme);
        };

        apply();

        if (theme === 'system') {
            const handler = () => apply();
            mediaQuery.addEventListener('change', handler);
            return () => mediaQuery.removeEventListener('change', handler);
        }
    }, [theme]);

    return { theme, setTheme, isDark };
};