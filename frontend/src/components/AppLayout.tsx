import React, { type ReactNode, useState } from "react";
import SideMenu from "./side_menu/SideMenu";
import ShowdownBotLogo from "./shared/ShowdownBotLogo";
import { useLocation } from "react-router-dom";

// *********************************
// App Layout
// *********************************

type AppLayoutProps = {
    children: ReactNode;
};

/**
 * AppLayout component that wraps the main application content
 * with a sidebar and main content area.
 */
const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {

    const [isSideMenuOpen, setIsSideMenuOpen] = useState(true);

    const contentPadding = isSideMenuOpen ? 'pl-48' : 'pl-12';
    const location = useLocation();
    const locationName = location.pathname.split('/')[1] || 'home';

    return (
        <div className="bg-primary flex h-screen relative w-screen">
            {/* Sidebar */}
            <SideMenu isOpen={isSideMenuOpen} setIsOpen={setIsSideMenuOpen} />

            <div className={`flex flex-col h-full w-full transition-[padding-left] duration-300 ${contentPadding}`}>
                {/* Header */}
                <header className={
                    `flex h-12 p-4 w-full items-center 
                    space-x-4
                    border-b-gray-600 shadow-sm
                `}>
                    {!isSideMenuOpen && <ShowdownBotLogo className="max-w-48" />}
                    <h1 className="text-xl font-semibold text-secondary">
                        {locationName.charAt(0).toUpperCase() + locationName.slice(1) || 'Home'}
                    </h1>
                </header>

                {/* Main content */}
                <main className={`flex-1 py-2overflow-auto w-full relative`}>
                    { children }
                </main>
            </div>
            
        </div>
    );
};

export default AppLayout;
