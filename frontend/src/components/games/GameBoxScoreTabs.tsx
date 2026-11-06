/**
 * @fileoverview A game's two box scores. Below @820px the container is too narrow for both teams'
 * tables side by side, so they collapse into tabs; at/above it, both panels are forced visible
 * (via forceMount + the @[820px] override below) and sit in a 2-column grid instead.
 */
import type { ReactNode } from "react";
import * as Tabs from '@radix-ui/react-tabs';

import { radixTabTriggerClass, tabListClass } from '../shared/tabStyles';

type GameBoxScoreTabsProps = {
    awayLabel: string;
    homeLabel: string;
    renderSide: (side: 'away' | 'home') => ReactNode;
};

export default function GameBoxScoreTabs({ awayLabel, homeLabel, renderSide }: GameBoxScoreTabsProps) {
    return (
        <Tabs.Root defaultValue="away">
            <Tabs.List className={tabListClass(true, '@[820px]:hidden mb-3')}>
                <Tabs.Trigger value="away" className={radixTabTriggerClass('md', true)}>
                    {awayLabel}
                </Tabs.Trigger>
                <Tabs.Trigger value="home" className={radixTabTriggerClass('md', true)}>
                    {homeLabel}
                </Tabs.Trigger>
            </Tabs.List>
            <div className="grid gap-4 @[820px]:grid-cols-2 min-w-0">
                {(['away', 'home'] as const).map((side) => (
                    <Tabs.Content key={side} value={side} forceMount className="min-w-0 space-y-4 data-[state=inactive]:hidden @[820px]:data-[state=inactive]:block">
                        {renderSide(side)}
                    </Tabs.Content>
                ))}
            </div>
        </Tabs.Root>
    );
}
