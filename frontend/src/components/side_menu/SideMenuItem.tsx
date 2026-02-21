/**
 * @fileoverview SideMenuItem Component
 * 
 * Individual navigation item component that renders within the SideMenu.
 * Provides adaptive UI that transforms between icon-only and full-text modes
 * based on the parent menu's expanded state.
 * 
 * Features:
 * - Responsive layout: icon-only when collapsed, icon+text when expanded
 * - Smart active state detection with visual highlighting
 * - Smooth hover effects and transitions
 * - React Router integration for client-side navigation
 * - Accessibility-conscious design with proper semantic elements
 * - Custom active state logic for special route handling
 * 
 * The component integrates with React Router's NavLink for navigation
 * while providing custom selection logic that can handle complex routing scenarios.
 * 
 * @component
 * @example
 * ```tsx
 * <SideMenuItem
 *   item={menuItem}
 *   isSideMenuOpen={isExpanded}
 *   selectedItem={currentItem}
 *   onClick={handleItemClick}
 * />
 * ```
 */

import React from "react";
import { NavLink } from "react-router-dom";
import { type SideMenuItem as SideMenuItemType } from "../../types/SideMenuItem";
import { FaAddressCard, FaCalendar, FaHome, FaLayerGroup } from "react-icons/fa";

/**
 * Props for the SideMenuItem component
 */
type SideMenuItemProps = {
    /** The menu item data including path, icon, and display text */
    item: SideMenuItemType;
    /** Whether the parent side menu is in expanded state */
    isSideMenuOpen: boolean;
    /** Currently selected menu item for highlighting active state */
    selectedItem: SideMenuItemType | undefined;
    /** Callback function triggered when the item is clicked */
    onClick: (item: SideMenuItemType) => void;
}

/**
 * Individual navigation menu item with responsive icon/text display
 * 
 * This component adapts its layout based on the parent menu's state:
 * - **Collapsed Menu**: Shows only the icon, centered
 * - **Expanded Menu**: Shows icon + text label, left-aligned
 * 
 * Features:
 * - Visual active state highlighting based on current route
 * - Smooth hover effects with background color transitions
 * - React Router NavLink integration for proper navigation
 * - Custom selection logic that handles special routing cases
 * - Responsive text visibility with smooth transitions
 * 
 * @param props - Component props
 * @returns A clickable navigation item with adaptive layout
 */
export const SideMenuItem: React.FC<SideMenuItemProps> = ({ item, isSideMenuOpen, selectedItem, onClick }) => {

    // Determine active state based on current selection
    const selectedPath = selectedItem?.path || '/';
    // Special case: highlight home when on root path as fallback behavior
    const isSelected = selectedPath === item.path || (selectedPath === '/' && item.path === '/home');

    return (
        <NavLink 
            to={item.path} 
            onClick={() => onClick(item)}
            className={`
                flex items-center h-4 py-6 rounded-md w-full
                hover:bg-[var(--background-tertiary)] cursor-pointer
                ${isSideMenuOpen ? 'justify-start pl-4' : 'justify-center'}
                ${isSelected ? 'bg-tertiary' : ''}
            `}
        >
        
            {/* Icon - Always visible, serves as the collapsed state identifier */}
            <div className="flex flex-col items-center justify-center text-primary">
                {item.icon && <item.icon />}
                <span className={`${isSideMenuOpen ? 'hidden' : 'block'} mt-1 text-[7px] font-semibold text-primary`}>
                    {item.text}
                </span>
            </div>
            
            {/* Text Label - Only visible when menu is expanded */}
            <h2 className={`${isSideMenuOpen ? 'block' : 'hidden'} pl-2 text-lg font-semibold text-primary`}>
                {item.text}
            </h2>
        </NavLink>
    );
}

/**
 * Configuration array defining all available navigation menu items
 * 
 * Each item includes:
 * - **text**: Display label shown when menu is expanded
 * - **icon**: React Icon component for visual identification
 * - **path**: React Router path for navigation destination
 * 
 * Items are rendered in the order defined here and automatically
 * integrate with the routing system for active state detection.
 */
export const sideMenuItems: SideMenuItemType[] = [
    {
        text: "Home",
        icon: FaHome,      // Home icon representing home/exploration
        path: "/home"
    },
    {
        text: "Custom",
        icon: FaAddressCard,  // Card/profile icon representing custom card creation
        path: "/customs"
    },
    {
        text: "Cards",
        icon: FaLayerGroup,      // Compass icon representing exploration/discovery
        path: "/cards"
    },
    {
        text: "Seasons",
        icon: FaCalendar,     // Calendar icon representing seasonal data
        path: "/seasons"
    },
];