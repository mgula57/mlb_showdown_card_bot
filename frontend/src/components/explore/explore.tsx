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

    const tabSelectedStyle = "text-[var(--showdown-blue)] border-b-2 border-[var(--showdown-blue)]";
    const tabUnselectedStyle = "text-gray-500 hover:text-gray-700";

    const tabButton = (src: CardSource) => {

        return (
            <button
                className={`
                    relative flex gap-x-1 items-center
                    px-6 py-3 font-medium text-sm transition-colors duration-200
                    ${tab === src ? tabSelectedStyle : tabUnselectedStyle}
                `}
                onClick={() => setTab(src)}
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
            <div className="flex px-3 border-b-2 border-form-element">
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