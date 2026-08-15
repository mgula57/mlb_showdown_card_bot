/**
 * @fileoverview Cards - Advanced card database browser and filter system
 * 
 * This component provides a comprehensive interface for exploring the MLB Showdown card database
 * with advanced filtering, sorting, and team hierarchy navigation capabilities.
 */

import { useState } from "react";
import * as Tabs from '@radix-ui/react-tabs';
import ShowdownBotSearch from "./ShowdownCardSearch";
import { CardSource, isValidCardSource } from '../../types/cardSource';
import { FaRobot, FaHatWizard, FaWandMagicSparkles } from "react-icons/fa6";
import { radixTabTriggerClass } from "../shared/tabStyles";

const TAB_TRIGGER_CLASS = radixTabTriggerClass();

export default function Cards() {

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

    // Track which tabs have ever been shown, so each is only mounted (and its
    // queries fired) the first time a user visits it. Once mounted, a tab stays
    // mounted (via forceMount) so switching back and forth preserves its state.
    const [visitedTabs, setVisitedTabs] = useState<Set<CardSource>>(() => new Set([tab]));

    // Persist tab selection to localStorage whenever it changes
    const handleTabChange = (value: string) => {
        const newTab = value as CardSource;
        setTab(newTab);
        setVisitedTabs(prev => prev.has(newTab) ? prev : new Set(prev).add(newTab));
        if (typeof window !== 'undefined') {
            localStorage.setItem('explore-tab', newTab);
        }
    };

    // Cards Component Layout
    return (
        <Tabs.Root value={tab} onValueChange={handleTabChange}>
            {/* Tab Selection */}
            <Tabs.List className="flex px-3 border-b border-(--divider) gap-x-1 py-1 overflow-x-auto scrollbar-hide">
                <Tabs.Trigger value={CardSource.BOT} className={TAB_TRIGGER_CLASS}>
                    <FaRobot />
                    BOT
                </Tabs.Trigger>
                <Tabs.Trigger value={CardSource.WOTC} className={TAB_TRIGGER_CLASS}>
                    <FaHatWizard />
                    WOTC
                </Tabs.Trigger>
                <Tabs.Trigger value={CardSource.CUSTOM} className={TAB_TRIGGER_CLASS}>
                    <FaWandMagicSparkles />
                    My Customs
                </Tabs.Trigger>
            </Tabs.List>

            {/* Tab Content - only mounted once a tab has been visited, then kept alive */}
            {visitedTabs.has(CardSource.BOT) && (
                <Tabs.Content
                    value={CardSource.BOT}
                    className="focus:outline-none data-[state=inactive]:hidden"
                    forceMount
                >
                    <ShowdownBotSearch source={CardSource.BOT} />
                </Tabs.Content>
            )}
            {visitedTabs.has(CardSource.WOTC) && (
                <Tabs.Content
                    value={CardSource.WOTC}
                    className="focus:outline-none data-[state=inactive]:hidden"
                    forceMount
                >
                    <ShowdownBotSearch source={CardSource.WOTC} />
                </Tabs.Content>
            )}
            {visitedTabs.has(CardSource.CUSTOM) && (
                <Tabs.Content
                    value={CardSource.CUSTOM}
                    className="focus:outline-none data-[state=inactive]:hidden"
                    forceMount
                >
                    <ShowdownBotSearch source={CardSource.CUSTOM} />
                </Tabs.Content>
            )}
        </Tabs.Root>
    );
}