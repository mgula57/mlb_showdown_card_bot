import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { FaChevronRight, FaChevronLeft } from "react-icons/fa";
import { FaXmark } from "react-icons/fa6";
import { SideMenuItem, sideMenuItems } from "./SideMenuItem";
import { type SideMenuItem as SideMenuItemType } from "../../types/SideMenuItem";
import ShowdownBotLogo from "../shared/ShowdownBotLogo";
import ThemeToggleButton from "./ThemeToggleButton";

/** Interface for the side menu props. */
type SideMenuProps = {
    isOpen: boolean;
    setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
    className?: string;
    isMobile?: boolean;
};
    
/** Dynamic side menu component that displays navigation links. */
const SideMenu: React.FC<SideMenuProps> = ({ isOpen, setIsOpen, className, isMobile }) => {

    // State to manage the selected item
    const [selectedMenuItem, setSelectedMenuItem] = useState<SideMenuItemType | null>(sideMenuItems[0]);

    // Toggle side menu open/close state
    // Linked to parent component state
    const handleToggle = () => {
        setIsOpen(!isOpen);
    };

    // Set the selected menu item when clicked.
    const handleMenuItemClick = (item: SideMenuItemType) => {
        console.log(`Selected menu item: ${item.text}`);
        setSelectedMenuItem(item);
        if (isMobile) setIsOpen(false); // Close menu on mobile after selection
    };

    return (
        // Container
        <aside className={`h-screen fixed left-0 top-0 ${className}`}>

            {/* Navigation */}
            <nav className={`
                h-screen ${isOpen ? 'w-64 md:w-48' : 'w-12'} space-y-4
                bg-secondary border-r-divider shadow-sm
                transition-all duration-300 ease-in-out
                flex flex-col
            `}>
                {/* Header: Logo and Menu Button */}
                <div className={`${isOpen ? 'flex space-x-2' : ''} h-12 p-4 pb-2 w-full items-center cursor-pointer`}>
                    
                    {/* Logo */}
                    {isOpen && 
                        <NavLink to="/" className={`${isOpen ? 'w-7/8' : 'w-full'} flex items-center`}>
                            <ShowdownBotLogo/>
                        </NavLink>
                    }

                    {/* Open/Close Button */}
                    <button onClick={handleToggle} className="hover:text-secondary transition-colors duration-200">
                        {isOpen ? (isMobile ? <FaXmark className="h-8 w-8" /> : <FaChevronLeft />) : <FaChevronRight />}
                    </button>
                    
                </div>

                {/* Menu Items */}
                <ul className="flex-1 space-y-2 overflow-y-auto px-2">
                    {sideMenuItems.map((item) => (
                        <li key={item.path}>
                            <SideMenuItem
                                item={item}
                                isSideMenuOpen={isOpen}
                                selectedItem={selectedMenuItem} // Replace with actual selected item logic if needed
                                onClick={handleMenuItemClick}
                            />
                        </li>
                    ))}
                </ul>

                {/* Footer: Theme Toggle Button */}
                <div className="p-2">
                    <ThemeToggleButton />
                </div>

            </nav>

        </aside>
    );
};

export default SideMenu;