/**
 * @fileoverview Side menu navigation config — sections, the footer Account item, and a flat
 * list of every item for route lookups. Kept out of SideMenuItem.tsx so that file only
 * exports components (fast refresh).
 */

import { FaCalendar, FaHome, FaCompass, FaUserCircle } from "react-icons/fa";
import { FaPeopleGroup, FaLayerGroup } from "react-icons/fa6";
// import { FaDice } from "react-icons/fa6"; // re-add with the Simulate nav item below
import CardBuildIcon from "../customs/CardBuildIcon";
import { type SideMenuItem as SideMenuItemType, type SideMenuSection } from "../../types/SideMenuItem";

/**
 * Navigation menu configuration, grouped into sections
 * 
 * Each item includes:
 * - **text**: Display label shown when menu is expanded
 * - **icon**: React Icon component for visual identification
 * - **path**: React Router path for navigation destination
 * 
 * Sections render top to bottom in the order defined here. Account is pinned to the
 * menu footer separately (see `accountMenuItem`).
 */
export const sideMenuSections: SideMenuSection[] = [
    {
        items: [
            {
                text: "Home",
                icon: FaHome,      // Home icon representing home/exploration
                path: "/home"
            },
        ],
    },
    {
        title: "Build",
        items: [
            {
                text: "Card Builder",
                icon: CardBuildIcon,  // Card/profile icon representing custom card creation
                path: "/customs",
            },
            {
                text: "Team Builder",
                icon: FaPeopleGroup,      // Group icon representing teams/rosters
                path: "/teams"
            },
            {
                text: "Release Builder", // TODO: Update name once ready for public release
                icon: FaLayerGroup,      // Box icon representing a packaged card release/set
                path: "/release-builder",
                isNew: true
            },
        ],
    },
    {
        title: "Explore",
        items: [
            {
                text: "Card Explorer",
                icon: FaCompass,      // Compass icon representing exploration/discovery
                path: "/cards"
            },
            {
                text: "Seasons",
                icon: FaCalendar,      // Calendar icon representing seasons/schedules
                path: "/seasons"
            },
            // Hidden for this release — the Simulate flow is reached from the Seasons page instead.
            // {
            //     text: "Simulate",
            //     icon: FaDice,      // Dice icon representing a simulated season
            //     path: "/simulate",
            //     isNew: true
            // },
        ],
    },
];

/** Account lives in the menu footer next to the theme toggle rather than in a section. */
export const accountMenuItem: SideMenuItemType = {
    text: "Account",
    icon: FaUserCircle,
    path: "/account"
};

/** Flat list of every navigable item — used for route → active item / page title lookups. */
export const sideMenuItems: SideMenuItemType[] = [
    ...sideMenuSections.flatMap(section => section.items),
    accountMenuItem,
];
