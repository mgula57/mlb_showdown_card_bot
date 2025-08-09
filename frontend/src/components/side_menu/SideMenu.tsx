import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { FaChevronRight, FaChevronLeft } from "react-icons/fa";
import { SideMenuItem, sideMenuItems } from "./SideMenuItem";
import { type SideMenuItem as SideMenuItemType } from "../../types/SideMenuItem";
import ShowdownBotLogo from "../shared/ShowdownBotLogo";

/** Interface for the side menu props. */
type SideMenuProps = {
    isOpen: boolean;
    setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
};
    
/** Dynamic side menu component that displays navigation links. */
const SideMenu: React.FC<SideMenuProps> = ({ isOpen, setIsOpen }) => {

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
    };

    return (
        // Container
        <aside className='h-screen fixed left-0 top-0'>

            {/* Navigation */}
            <nav className={`
                h-screen ${isOpen ? 'w-48' : 'w-12'} space-y-4
                bg-secondary border-r-divider shadow-sm
                transition-all duration-300 ease-in-out
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
                    <button onClick={handleToggle} className="text-primary hover:text-secondary transition-colors duration-200">
                        {isOpen ? <FaChevronLeft /> : <FaChevronRight />}
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

            </nav>

        </aside>
    );
};

export default SideMenu;