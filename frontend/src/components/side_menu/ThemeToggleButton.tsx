import React from "react"
import { FaSun, FaMoon, FaDesktop } from "react-icons/fa";
import { useTheme } from "../../hooks/useTheme";

/** Button to toggle between light, dark, and system themes */
const ThemeToggleButton: React.FC = () => {
    const { theme, setTheme } = useTheme();

    const cycleTheme = (): void => {
        const themes = ['light', 'dark', 'system'] as const;
        const currentIndex = themes.indexOf(theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        setTheme(themes[nextIndex]);
    };

    const getIcon = () => {
        switch (theme) {
            case 'light':
                return <FaSun className="w-4 h-4" />;
            case 'dark':
                return <FaMoon className="w-4 h-4" />;
            case 'system':
                return <FaDesktop className="w-4 h-4" />;
            default:
                return <FaDesktop className="w-4 h-4" />;
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
        >
            { getIcon() }
        </button>
    );
};

export default ThemeToggleButton;