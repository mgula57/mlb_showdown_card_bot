import React, { type ReactNode, useState, useEffect } from "react";
import SideMenu from "./side_menu/SideMenu";
import ShowdownBotLogo from "./shared/ShowdownBotLogo";
import { useLocation } from "react-router-dom";
import { useSiteSettings, showdownSets } from "./shared/SiteSettingsContext";
import CustomSelect from "./shared/CustomSelect";
import { FiMenu } from "react-icons/fi";

// *********************************
// App Layout
// *********************************

type AppLayoutProps = {
    children: ReactNode;
};

const TITLE_MAP: Record<string, string> = {
    home: "Home",
    customs: "Custom Card",
    explore: "Explore",
};

// Local storage key for side menu state
const SIDE_MENU_STORAGE_KEY = 'showdown-bot-side-menu-open';
const SIDE_MENU_STORAGE_KEY_MOBILE = 'showdown-bot-side-menu-open-mobile';

/**
 * AppLayout component that wraps the main application content
 * with a sidebar and main content area.
 */
const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {

    const [isSideMenuOpen, setIsSideMenuOpen] = useState(() => {
        try {
            const stored = localStorage.getItem(SIDE_MENU_STORAGE_KEY);
            return stored !== null ? JSON.parse(stored) : true;
        } catch {
            return true; // Fallback to true if localStorage fails
        }
    });
    const [isSideMenuOpenMobile, setIsSideMenuOpenMobile] = useState(() => {
        try {
            const stored = localStorage.getItem(SIDE_MENU_STORAGE_KEY_MOBILE);
            return stored !== null ? JSON.parse(stored) : false;
        } catch {
            return false; // Fallback to false if localStorage fails
        }
    });
    const { userShowdownSet, setUserShowdownSet } = useSiteSettings();

    const contentPadding = isSideMenuOpen ? 'md:pl-48' : 'md:pl-12';
    const location = useLocation();
    const locationName = location.pathname.split('/')[1] || 'customs';

    const headerTitle: string = TITLE_MAP[locationName] || "customs";

    // Save side menu state to localStorage whenever it changes
    useEffect(() => {
        try {
            localStorage.setItem(SIDE_MENU_STORAGE_KEY, JSON.stringify(isSideMenuOpen));
        } catch (error) {
            console.warn('Failed to save side menu state to localStorage:', error);
        }
    }, [isSideMenuOpen]);

    return (
        <div className="bg-primary flex relative">
            {/* Desktop Sidebar */}
            <SideMenu className="hidden md:block" isOpen={isSideMenuOpen} setIsOpen={setIsSideMenuOpen} />

            {/* Mobile slide-over sidebar */}
            {isSideMenuOpenMobile && (
                <div className="fixed inset-0 z-40 md:hidden">
                    <div
                        className="absolute inset-0 bg-black/40"
                        onClick={() => setIsSideMenuOpenMobile(false)}
                        aria-hidden
                    />
                        <SideMenu isOpen={true} setIsOpen={setIsSideMenuOpenMobile} isMobile={true} />
                </div>
            )}


            <div className={`flex flex-col h-full w-full transition-[padding-left] duration-300 ${contentPadding}`}>
                {/* Header */}
                <header className={`
                    sticky top-0 z-30
                    flex h-12 p-4 w-full items-center 
                    justify-between
                    border-b-gray-600 shadow-md
                    bg-primary/95 backdrop-blur
                `}>
                    {/* Logo and Title */}
                    <div className="flex items-center space-x-4">

                        <button
                            type="button"
                            className="
                                md:hidden inline-flex items-center justify-center p-2 
                                rounded-md border border-form-element 
                                text-secondary hover:bg-background-secondary
                                cursor-pointer
                            "
                            aria-label="Open menu"
                            onClick={() => setIsSideMenuOpenMobile(true)}
                            >
                            <FiMenu className="h-5 w-5" />
                        </button>
                        
                        {/* Show logo on small always */}
                        <ShowdownBotLogo className="max-w-48 md:hidden" />
                        {!isSideMenuOpen && <ShowdownBotLogo className="max-w-48 hidden md:block" />}
                        <h1 className="hidden sm:block text-xl font-semibold text-secondary">
                            {headerTitle}
                        </h1>
                    </div>

                    {/* Showdown Set */}
                    <CustomSelect
                        className="font-showdown-set-italic w-20 text-xl"
                        buttonClassName="flex justify-center cursor-pointer select-none"
                        imageClassName="object-contain object-center"
                        value={userShowdownSet}
                        onChange={setUserShowdownSet}
                        options={showdownSets}
                    />
                    
                </header>

                {/* Main content */}
                <main className={`flex-1 overflow-auto w-full relative`}>
                    { children }
                </main>
            </div>
            
        </div>
    );
};

export default AppLayout;
