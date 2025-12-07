/**
 * @fileoverview Explore - Advanced card database browser and filter system
 * 
 * This component provides a comprehensive interface for exploring the MLB Showdown card database
 * with advanced filtering, sorting, and team hierarchy navigation capabilities.
 */

import { useState } from "react";
import ShowdownBotSearch from "../cards/ShowdownCardSearch";

export default function Explore() {

    // State
    const [tab, setTab] = useState<'BOT' | 'WOTC'>('BOT');

    const tabSelectedStyle = "text-[var(--showdown-blue)] border-b-2 border-[var(--showdown-blue)]";
    const tabUnselectedStyle = "text-gray-500 hover:text-gray-700";

    // Explore Component Layout
    return (
        <div>
            {/* Tab Selection */}
            <div className="flex px-4 border-b-2 border-form-element">
                <button
                    className={`px-6 py-3 font-medium text-sm transition-colors duration-200 relative ${
                        tab === 'BOT' ? tabSelectedStyle : tabUnselectedStyle
                    }`}
                    onClick={() => setTab('BOT')}
                >
                    Showdown Bot Cards
                </button>
                <button
                    className={`px-6 py-3 font-medium text-sm transition-colors duration-200 relative ${
                        tab === 'WOTC' ? tabSelectedStyle : tabUnselectedStyle
                    }`}
                    onClick={() => setTab('WOTC')}
                >
                    WOTC Cards
                </button>
            </div>

            {/* Tab Content */}
            <div>
                <div className={tab === 'BOT' ? 'block' : 'hidden'}>
                    <ShowdownBotSearch source="BOT" />
                </div>
                <div className={tab === 'WOTC' ? 'block' : 'hidden'}>
                    <ShowdownBotSearch source="WOTC" />
                </div>
            </div>
        </div>
    );
}