import React, { useState, type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { FaChevronRight, FaChevronLeft, FaBars } from "react-icons/fa";
import { SideMenuItem, sideMenuItems } from "./SideMenuItem"; // Adjust the import path as necessary
import showdownLogo from "../../assets/logo-light.png"; // Adjust the path as necessary

type SideMenuProps = {
    isOpen: boolean;
    setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
};

const SideMenu: React.FC<SideMenuProps> = ({ isOpen, setIsOpen }) => {

    const handleToggle = () => {
        setIsOpen(!isOpen);
    };

    return (
        // Container
        <aside className='h-screen fixed left-0 top-0'>

            {/* Navigation */}
            <nav className={`
                h-screen ${isOpen ? 'w-48' : 'w-12'} space-y-2
                bg-white border-r shadow-sm
                transition-all duration-300 ease-in-out
            `}>
                {/* Header: Logo and Menu Button */}
                <div className={`${isOpen ? 'flex space-x-2' : ''} h-12 p-4 pb-2 w-full items-center cursor-pointer`}>

                    {isOpen && 
                        <NavLink to="/" className={`${isOpen ? 'w-7/8' : 'w-full'} flex items-center`}>
                            <img src={showdownLogo} alt="Showdown logo" className="object-contain" />
                        </NavLink>
                    }

                    <button onClick={handleToggle}>
                        {isOpen ? <FaChevronLeft /> : <FaChevronRight />}
                    </button>
                    

                </div>

                {/* Menu Items */}
                <ul className="flex-1 space-y-4 p-4 overflow-y-auto">
                    {sideMenuItems.map((item) => (
                        <li key={item.path}>
                            <SideMenuItem
                                item={item}
                                isSideMenuOpen={isOpen}
                                selectedItem={null} // Replace with actual selected item logic if needed
                            />
                        </li>
                    ))}
                    
                </ul>
            </nav>

        </aside>
    );
};

export default SideMenu;