import React, { type ReactNode, useState } from "react";
import SideMenu from "./side_menu/SideMenu";

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

    return (
        <div className="flex h-screen relative">
            {/* Sidebar */}
            <SideMenu isOpen={isSideMenuOpen} setIsOpen={setIsSideMenuOpen} />

            {/* Main content */}
            <main className={`${isSideMenuOpen ? 'ml-48' : 'ml-12'} flex-1 p-8 md:p-8 overflow-auto w-full`}>
                { children }
            </main>
        </div>
    );
};

export default AppLayout;
