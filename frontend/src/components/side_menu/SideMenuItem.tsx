import React from "react";
import { NavLink } from "react-router-dom";
import { type SideMenuItem as SideMenuItemType } from "../../types/SideMenuItem";
import { FaGear } from "react-icons/fa6"
import { FaChartBar } from "react-icons/fa";

export const sideMenuItems: SideMenuItemType[] = [
    {
        text: "Customs",
        icon: FaGear,
        path: "/customs"
    },
    {
        text: "Explore",
        icon: FaChartBar,
        path: "/explore"
    },

];

type SideMenuItemProps = {
    item: SideMenuItemType;
    isSideMenuOpen: boolean;
    selectedItem: SideMenuItemType | null;
}

export const SideMenuItem: React.FC<SideMenuItemProps> = ({ item, isSideMenuOpen, selectedItem }) => {

    return (

        <NavLink to={item.path} className={`flex items-center h-4 py-4 rounded-md hover:bg-gray-100 cursor-pointer ${selectedItem?.path === item.path ? 'bg-gray-200' : ''}`}>
            { item.icon && <item.icon/>}
            <h2 className={`${isSideMenuOpen ? 'block' : 'hidden'} pl-2 text-lg font-semibold`}>{item.text}</h2>
        </NavLink>
    );
}
