import { useState } from "react";
import {
    useFloating, useHover, useInteractions, offset, flip, shift, autoUpdate, FloatingPortal
} from "@floating-ui/react";

import type { BoxscoreTeamData, BoxscoreBatter } from "../../../api/mlbAPI";
import type { ShowdownBotCardAPIResponse } from "../../../api/showdownBotCard";
import { cardKey } from "../../../domain/players";
import { useIsSmallScreen } from "../../../hooks/useIsSmallScreen";
import { defenseAtPosition } from "../../shared/DefenseUtils";
import { CardItemCompactFromCard } from "../../cards/CardItemCompact";
import CardIdentityCell from "../../cards/card_elements/CardIdentityCell";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";
import TablePointsSummary from "./TablePointsSummary";
import TeamTableHeader from "./TeamTableHeader";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

const cardDefenseForPosition = (card: ShowdownBotCardAPIResponse["card"] | undefined, position: string | null) =>
    defenseAtPosition(card?.positions_and_defense, position);

export default function BattingTable({ team, sportId, cardMap, onCardSelect, isShowingModal, isLoadingCards, hasGameStarted }: { team: BoxscoreTeamData; sportId?: number; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isShowingModal?: boolean; isLoadingCards?: boolean; hasGameStarted?: boolean }) {
    const badgeBgSecondary = team.team.secondary_color ?? '#4b5563';
    const hasCards = Object.keys(cardMap).length > 0;

    const sortedBatters = [...team.batting]
        .filter((b) => b.batting_order != null && b.batting_order !== "")
        .sort((a, b) => {
            const orderA = a.batting_order ? parseInt(a.batting_order, 10) : 9999;
            const orderB = b.batting_order ? parseInt(b.batting_order, 10) : 9999;
            return orderA - orderB;
        });

    // PTS
    const totalPoints = hasCards
        ? sortedBatters.reduce((sum, b) => sum + (cardMap[cardKey(b.id, 'H')]?.card?.points ?? 0), 0)
        : 0;
    const totalPointsChange = hasCards && hasGameStarted
        ? sortedBatters.reduce((sum, b) => sum + (cardMap[cardKey(b.id, 'H')]?.in_season_trends?.pts_change.day ?? 0), 0)
        : 0;

    // CURRENT DEFENSE
    const INFIELD = new Set(['1B', '2B', '3B', 'SS']);
    const OUTFIELD = new Set(['LF', 'CF', 'RF']);
    const defTotals = hasCards
        ? sortedBatters.filter((b) => b.is_in_lineup).reduce(
            (acc, b) => {
                const card = cardMap[cardKey(b.id, 'H')]?.card ?? undefined;
                const pos = b.position.replaceAll('PH-', '');
                const val = cardDefenseForPosition(card, pos ?? null);
                if (val == null) return acc;
                if (pos === 'C')                  acc.catcher += val;
                else if (INFIELD.has(pos ?? ''))  acc.infield += val;
                else if (OUTFIELD.has(pos ?? '')) acc.outfield += val;
                return acc;
            },
            { infield: 0, outfield: 0, catcher: 0 }
        )
        : null;

    return (
        <div className="rounded-card border border-(--divider) bg-(--background-secondary) overflow-hidden">
            <TeamTableHeader team={team.team} sportId={sportId} title="Batting">
                {defTotals && (
                    <div className="ml-auto flex items-center gap-x-3 text-[11px] font-semibold tabular-nums text-(--text-secondary)">
                        <span>C {defTotals.catcher >= 0 ? '+' : ''}{defTotals.catcher}</span>
                        <span>IF {defTotals.infield >= 0 ? '+' : ''}{defTotals.infield}</span>
                        <span>OF {defTotals.outfield >= 0 ? '+' : ''}{defTotals.outfield}</span>
                    </div>
                )}
                {hasCards && totalPoints > 0 && (
                    <TablePointsSummary totalPoints={totalPoints} pointsChange={totalPointsChange} backgroundColor={badgeBgSecondary} />
                )}
            </TeamTableHeader>

            <div className="overflow-x-auto scrollbar-hide">
                <table className="w-full text-xs tabular-nums">
                    <thead>
                        <tr className={`border-b border-(--divider) text-(--text-tertiary) ${CAPS_LABEL_CLASS}`}>
                            <th className="pl-3 pr-2 py-2 text-left min-w-36">Batters</th>
                            <th className="px-2 py-2 text-right">AB</th>
                            <th className="px-2 py-2 text-right">R</th>
                            <th className="px-2 py-2 text-right">H</th>
                            <th className="px-2 py-2 text-right">RBI</th>
                            <th className="px-2 py-2 text-right">BB</th>
                            <th className="px-2 py-2 text-right">HR</th>
                            <th className="px-2 py-2 text-right">AVG</th>
                            <th className="px-2 py-2 text-right pr-3">OPS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedBatters.map((batter) => (
                            <BatterRow key={batter.id} batter={batter} cardResponse={cardMap[cardKey(batter.id, 'H')]} onCardSelect={onCardSelect} isShowingModal={isShowingModal} isLoadingCards={isLoadingCards} />
                        ))}
                        {sortedBatters.length === 0 && (
                            <tr>
                                <td colSpan={9} className="px-3 py-4 text-center text-(--text-secondary)">
                                    No batting data available.
                                </td>
                            </tr>
                        )}
                        <tr className="border-t border-(--divider) font-bold">
                            <td className="pl-3 pr-2 py-2 text-left text-(--text-primary)">Totals</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.at_bats}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.runs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.hits}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.rbi}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.base_on_balls}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.home_runs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)" />
                            <td className="px-2 py-2 text-right pr-3 text-(--text-primary)" />
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function BatterRow({ batter, cardResponse, onCardSelect, isShowingModal, isLoadingCards }: { batter: BoxscoreBatter; cardResponse?: ShowdownBotCardAPIResponse; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isShowingModal?: boolean; isLoadingCards?: boolean }) {
    const [isOpen, setIsOpen] = useState(false);
    const isSmallScreen = useIsSmallScreen();
    const { refs, floatingStyles, context } = useFloating({
        open: isOpen,
        onOpenChange: setIsOpen,
        placement: "right",           // start right, auto-flips if near edge
        middleware: [offset(8), flip(), shift({ padding: 8 })],
        whileElementsMounted: autoUpdate,
    });
    const hover = useHover(context, { delay: { open: 300, close: 100 } }); // 300ms open delay prevents flicker
    const { getReferenceProps, getFloatingProps } = useInteractions([hover]);

    const card = cardResponse?.card ?? undefined;
    const indent = batter.is_substitute;
    const hasHit = (batter.stats.hits ?? 0) > 0;

    return (
        <tr
            className={`
                border-b border-(--divider)/50 hover:bg-(--background-tertiary)
                ${cardResponse ? 'cursor-pointer' : ''}
            `}
            onClick={cardResponse ? () => onCardSelect?.(cardResponse) : undefined}
        >
            <td
                ref={refs.setReference} {...getReferenceProps()}
                className={`
                    pl-3 pr-2 py-1.5 text-left
                    ${indent ? 'pl-8' : ''}
                    ${!batter.is_in_lineup ? 'opacity-60' : ''}
                `} >
                    <CardIdentityCell
                        name={batter.name} position={batter.position} hasCard={!!card}
                        isPitcher={card?.chart.is_pitcher} primaryColor={card?.image.color_primary} secondaryColor={card?.image.color_secondary}
                        command={card?.chart.command} team={card?.team} points={card?.points} positionsAndDefense={card?.positions_and_defense}
                        ptsChange={cardResponse?.in_season_trends?.pts_change.day} isLoadingCard={isLoadingCards && !cardResponse}
                    />
            </td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.at_bats}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.runs}</td>
            <td className={`px-2 py-1.5 text-right font-semibold ${hasHit ? 'text-(--text-primary)' : 'text-(--text-secondary)'}`}>{batter.stats.hits}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.rbi}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.base_on_balls}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.home_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-secondary)">{batter.season_stats.avg}</td>
            <td className="px-2 py-1.5 text-right pr-3 text-(--text-secondary)">{batter.season_stats.ops}</td>
            {isOpen && card && !isShowingModal && !isSmallScreen && (
                <FloatingPortal>
                    <div
                        ref={refs.setFloating}
                        style={floatingStyles}
                        className="z-50 w-48"
                        {...getFloatingProps()}
                    >
                        <CardItemCompactFromCard card={card} className="min-w-xs max-w-md" />
                    </div>
                </FloatingPortal>
            )}
        </tr>
    );
}
