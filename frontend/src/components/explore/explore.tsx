/**
 * @fileoverview Explore - Advanced card database browser and filter system
 * 
 * This component provides a comprehensive interface for exploring the MLB Showdown card database
 * with advanced filtering, sorting, and team hierarchy navigation capabilities.
 */

import { useState, useEffect } from "react";
import ShowdownBotSearch from "../cards/ShowdownCardSearch";
import { CardSource, isValidCardSource } from '../../types/cardSource';
import { FaRobot } from "react-icons/fa6";

export default function Explore() {

    // State - Initialize from localStorage or default to BOT
    const [tab, setTab] = useState<CardSource>(() => {
        if (typeof window !== 'undefined') {
            const savedTab = localStorage.getItem('explore-tab');
            if (savedTab && isValidCardSource(savedTab)) {
                return savedTab as CardSource;
            }
        }
        return CardSource.BOT;
    });

    // Persist tab selection to localStorage whenever it changes
    useEffect(() => {
        if (typeof window !== 'undefined') {
            localStorage.setItem('explore-tab', tab);
        }
    }, [tab]);

    const tabSelectedStyle = "bg-[var(--divider)] font-bold text-[var(--showdown-blue)]";
    const tabUnselectedStyle = "text-gray-500 font-medium hover:bg-[var(--divider)]";

    const getTabClasses = (src: CardSource) => {
        const baseClasses = "relative flex gap-x-1 items-center px-4 py-3 text-sm transition-colors duration-200 rounded-lg";
        const stateClasses = tab === src ? tabSelectedStyle : tabUnselectedStyle;
        return `${baseClasses} ${stateClasses}`;
    };

    const tabButton = (src: CardSource) => {
        const isSelected = tab === src;

        return (
            <button
                key={src} // Add key to force re-render
                className={getTabClasses(src)}
                onClick={() => setTab(src)}
                aria-selected={isSelected} // For accessibility
            >
                {src === CardSource.WOTC && <div className="text-[9px] bg-secondary px-1 rounded-sm">OG</div>}
                {src === CardSource.BOT && <FaRobot />}
                {src} Cards
            </button>
        );
    }

    // Explore Component Layout
    return (
        <div>
            {/* Tab Selection */}
            <div className="flex px-3 border-b-2 pt-2 pb-1 border-form-element gap-x-2">
                {tabButton(CardSource.BOT)}
                {tabButton(CardSource.WOTC)}
            </div>

            {/* Tab Content */}
            <div>
                <div className={tab === CardSource.BOT ? 'block' : 'hidden'}>
                    <ShowdownBotSearch source={CardSource.BOT} />
                </div>
                <div className={tab === CardSource.WOTC ? 'block' : 'hidden'}>
                    <ShowdownBotSearch source={CardSource.WOTC} />
                </div>
            </div>
        </div>
    );
}