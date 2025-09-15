import React from "react";
import { NavLink } from "react-router-dom";
import { type SideMenuItem as SideMenuItemType } from "../../types/SideMenuItem";
import { FaHome, FaAddressCard, FaCompass } from "react-icons/fa";

/** Props for the side menu item component */
type SideMenuItemProps = {
    item: SideMenuItemType;
    isSideMenuOpen: boolean;
    selectedItem: SideMenuItemType | undefined;
    onClick: (item: SideMenuItemType) => void;
}

/** 
 * Individual side menu item component for navigation links.
 * Navigates to the specified path and highlights the selected item.
 */
export const SideMenuItem: React.FC<SideMenuItemProps> = ({ item, isSideMenuOpen, selectedItem, onClick }) => {

    return (
        <NavLink 
            to={item.path} 
            onClick={() => onClick(item)}
            className={`
                flex items-center h-4 py-6 rounded-md
                hover:bg-[var(--background-tertiary)] cursor-pointer
                ${isSideMenuOpen ? 'justify-start pl-4' : 'justify-center'}
                ${selectedItem?.path === item.path ? 'bg-tertiary' : ''}
            `}>
                { item.icon && <item.icon/>}
                <h2 className={`${isSideMenuOpen ? 'block' : 'hidden'} pl-2 text-lg font-semibold text-primary`}>{item.text}</h2>
        </NavLink>
    );
}

/** Side menu items for navigation */
export const sideMenuItems: SideMenuItemType[] = [
    {
        text: "Home",
        icon: FaHome,
        path: "/"
    },
    {
        text: "Customs",
        icon: FaAddressCard,
        path: "/customs"
    },
    {
        text: "Explore",
        icon: FaCompass,
        path: "/explore"
    },

];