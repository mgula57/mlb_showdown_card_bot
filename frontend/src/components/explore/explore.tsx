/**
 * @fileoverview Explore - Advanced card database browser and filter system
 * 
 * This component provides a comprehensive interface for exploring the MLB Showdown card database
 * with advanced filtering, sorting, and team hierarchy navigation capabilities.
 */

import { useState } from "react";
import * as Tabs from '@radix-ui/react-tabs';
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
    const handleTabChange = (value: string) => {
        const newTab = value as CardSource;
        setTab(newTab);
        if (typeof window !== 'undefined') {
            localStorage.setItem('explore-tab', newTab);
        }
    };

    // Explore Component Layout
    return (
        <Tabs.Root value={tab} onValueChange={handleTabChange}>
            {/* Tab Selection */}
            <Tabs.List className="flex px-3 border-b-2 pt-2 pb-1 border-form-element gap-x-2 h-12">
                <Tabs.Trigger 
                    value={CardSource.BOT}
                    className="relative flex gap-x-1 items-center px-4 py-3 text-sm rounded-lg
                               data-[state=active]:bg-[var(--background-quaternary)] 
                               data-[state=active]:font-bold 
                               data-[state=active]:text-[var(--showdown-blue)]
                               data-[state=inactive]:text-tertiary 
                               data-[state=inactive]:font-medium 
                               data-[state=inactive]:hover:bg-[var(--divider)]"
                >
                    <FaRobot />
                    BOT Cards
                </Tabs.Trigger>
                <Tabs.Trigger 
                    value={CardSource.WOTC}
                    className="relative flex gap-x-1 items-center px-4 py-3 text-sm rounded-lg
                               data-[state=active]:bg-[var(--background-quaternary)] 
                               data-[state=active]:font-bold 
                               data-[state=active]:text-[var(--showdown-blue)]
                               data-[state=inactive]:text-tertiary 
                               data-[state=inactive]:font-medium 
                               data-[state=inactive]:hover:bg-[var(--divider)]"
                >
                    <div className="text-[9px] bg-secondary px-1 rounded-sm shrink-0">OG</div>
                    WOTC Cards
                </Tabs.Trigger>
            </Tabs.List>

            {/* Tab Content */}
            <Tabs.Content 
                value={CardSource.BOT} 
                className="focus:outline-none data-[state=inactive]:hidden"
                forceMount
            >
                <ShowdownBotSearch source={CardSource.BOT} />
            </Tabs.Content>
            <Tabs.Content 
                value={CardSource.WOTC} 
                className="focus:outline-none data-[state=inactive]:hidden"
                forceMount
            >
                <ShowdownBotSearch source={CardSource.WOTC} />
            </Tabs.Content>
        </Tabs.Root>
    );
}