import React, { type ReactNode, useState } from "react";
import SideMenu from "./side_menu/SideMenu";
import ShowdownBotLogo from "./shared/ShowdownBotLogo";
import { useLocation } from "react-router-dom";
import { useSiteSettings, showdownSets } from "./shared/SiteSettingsContext";
import { CustomSelect } from "./shared/CustomSelect";

// *********************************
// App Layout
// *********************************

type AppLayoutProps = {
    children: ReactNode;
};

const TITLE_MAP: Record<string, string> = {
  customs: "Custom Card",
  explore: "Explore",
};

/**
 * AppLayout component that wraps the main application content
 * with a sidebar and main content area.
 */
const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {

    const [isSideMenuOpen, setIsSideMenuOpen] = useState(true);
    const { userShowdownSet, setUserShowdownSet } = useSiteSettings();

    const contentPadding = isSideMenuOpen ? 'pl-48' : 'pl-12';
    const location = useLocation();
    const locationName = location.pathname.split('/')[1] || 'home';

    const headerTitle: string = TITLE_MAP[locationName] || "Home";

    return (
        <div className="bg-primary flex h-screen relative w-screen">
            {/* Sidebar */}
            <SideMenu isOpen={isSideMenuOpen} setIsOpen={setIsSideMenuOpen} />

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
                        {!isSideMenuOpen && <ShowdownBotLogo className="max-w-48" />}
                        <h1 className="text-xl font-semibold text-secondary">
                            {headerTitle}
                        </h1>
                    </div>

                    {/* Showdown Set */}
                    <CustomSelect
                        value={userShowdownSet}
                        onChange={setUserShowdownSet}
                        options={showdownSets}
                        suffix="Set"
                        disableMinWidth={true}
                    />
                    
                </header>

                {/* Main content */}
                <main className={`flex-1 py-1 overflow-auto w-full relative`}>
                    { children }
                </main>
            </div>
            
        </div>
    );
};

export default AppLayout;
