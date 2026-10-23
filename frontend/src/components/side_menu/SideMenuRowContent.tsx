/**
 * @fileoverview SideMenuRowContent Component
 *
 * The inner layout shared by every side menu row (nav links and the theme toggle):
 * a fixed-width icon column with a stacked micro label for the collapsed rail, and a
 * full label that fades in when the menu expands.
 */

import React from "react";
import { type IconType } from "react-icons";
import { SIDE_MENU_MOTION } from "./sideMenuStyles";

type SideMenuRowContentProps = {
    /** Icon shown in the fixed-width column */
    icon: IconType;
    /** Label text (micro label when collapsed, full label when expanded) */
    text: string;
    /** Whether the parent side menu is in expanded state */
    isSideMenuOpen: boolean;
    /** Bold label + icon pop when true */
    isSelected?: boolean;
    /** Changing this replays the icon pop (e.g. the theme toggle cycling) */
    iconKey?: string;
    /** Optional badge pinned to the icon column (e.g. NEW) */
    badge?: React.ReactNode;
};

export const SideMenuRowContent: React.FC<SideMenuRowContentProps> = ({ icon: Icon, text, isSideMenuOpen, isSelected = false, iconKey, badge }) => (
    <>
        {/* Icon column - fixed width matching the collapsed rail, so the icon never shifts when the menu expands */}
        <div className="relative flex flex-col items-center justify-center w-12 shrink-0">
            <div
                key={iconKey}
                className={`flex items-center justify-center text-[20px] ${isSelected || iconKey ? 'side-menu-icon-pop' : ''}`}
            >
                <Icon />
            </div>

            <span
                aria-hidden={isSideMenuOpen}
                className={`
                    overflow-hidden text-[7px] text-center leading-tight max-w-12
                    transition-[max-height,opacity,margin] ${SIDE_MENU_MOTION}
                    ${isSelected ? 'font-bold' : 'font-semibold'}
                    ${isSideMenuOpen ? 'max-h-0 opacity-0 mt-0' : 'max-h-6 opacity-100 mt-1'}
                `}
            >
                {/* One word per line so every two-word label stacks the same way in the narrow rail */}
                {text.split(' ').map((word, i) => <span key={i} className="block">{word}</span>)}
            </span>
            {badge}
        </div>

        {/* Text Label - clipped by the nav width; fades in after the width has mostly opened, fades out immediately on collapse */}
        <span
            aria-hidden={!isSideMenuOpen}
            className={`
                min-w-0 flex-1 pl-1 text-left whitespace-nowrap overflow-hidden text-base leading-tight
                transition-opacity ${SIDE_MENU_MOTION}
                ${isSelected ? 'font-bold' : 'font-semibold'}
                ${isSideMenuOpen ? 'opacity-100 delay-100' : 'opacity-0 duration-100!'}
            `}
        >
            {text}
        </span>
    </>
);
