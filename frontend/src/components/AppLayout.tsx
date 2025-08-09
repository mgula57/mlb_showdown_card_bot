import React, { type ReactNode, useState } from "react";
import SideMenu from "./side_menu/SideMenu";
import ShowdownBotLogo from "./shared/ShowdownBotLogo";

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

    const contentPadding = isSideMenuOpen ? 'pl-52' : 'pl-16';

    return (
        <div className="bg-primary flex h-screen relative w-screen">
            {/* Sidebar */}
            <SideMenu isOpen={isSideMenuOpen} setIsOpen={setIsSideMenuOpen} />

            <div className={`flex flex-col h-full transition-[padding-left] duration-300 ${contentPadding}`}>
                {/* Header */}
                <header className={
                    `flex h-12 p-4 w-full items-center 
                    border-b-gray-600 shadow-sm
                `}>
                    {!isSideMenuOpen && <ShowdownBotLogo className="max-w-48" />}
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
