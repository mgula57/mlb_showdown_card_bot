import { useState } from "react";
import {
    useFloating, useHover, useInteractions, offset, flip, shift, autoUpdate, FloatingPortal
} from "@floating-ui/react";

import type { BoxscoreTeamData, BoxscorePitcher } from "../../../api/mlbAPI";
import type { ShowdownBotCardAPIResponse } from "../../../api/showdownBotCard";
import { cardKey } from "../../../domain/players";
import { useIsSmallScreen } from "../../../hooks/useIsSmallScreen";
import { CardItemCompactFromCard } from "../../cards/CardItemCompact";
import CardIdentityCell from "../../cards/card_elements/CardIdentityCell";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";
import TablePointsSummary from "./TablePointsSummary";
import TeamTableHeader from "./TeamTableHeader";
import { NEUTRAL_TEAM_COLOR_SECONDARY } from '../../../functions/colors';

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

export default function PitchingTable({ team, sportId, cardMap, onCardSelect, isShowingModal, isLoadingCards, hasGameStarted }: { team: BoxscoreTeamData; sportId?: number; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isShowingModal?: boolean; isLoadingCards?: boolean; hasGameStarted?: boolean }) {
    const badgeBgSecondary = team.team.secondary_color ?? NEUTRAL_TEAM_COLOR_SECONDARY;

    const hasCards = Object.keys(cardMap).length > 0;

    const totalPoints = hasCards
        ? team.pitching.reduce((sum, p) => sum + (cardMap[cardKey(p.id, 'P')]?.card?.points ?? 0), 0)
        : 0;
    const totalPointsChange = hasCards && hasGameStarted
        ? team.pitching.reduce((sum, p) => sum + (cardMap[cardKey(p.id, 'P')]?.in_season_trends?.pts_change.day ?? 0), 0)
        : 0;

    return (
        <div className="rounded-card border border-(--divider) bg-(--background-secondary) overflow-hidden">
            <TeamTableHeader team={team.team} sportId={sportId} title="Pitching">
                {hasCards && totalPoints > 0 && (
                    <TablePointsSummary totalPoints={totalPoints} pointsChange={totalPointsChange} backgroundColor={badgeBgSecondary} />
                )}
            </TeamTableHeader>

            <div className="overflow-x-auto scrollbar-hide">
                <table className="w-full text-xs tabular-nums">
                    <thead>
                        <tr className={`border-b border-(--divider) text-(--text-tertiary) ${CAPS_LABEL_CLASS}`}>
                            <th className="pl-3 pr-2 py-2 text-left min-w-36">Pitchers</th>
                            <th className="px-2 py-2 text-right">IP</th>
                            <th className="px-2 py-2 text-right">H</th>
                            <th className="px-2 py-2 text-right">R</th>
                            <th className="px-2 py-2 text-right">ER</th>
                            <th className="px-2 py-2 text-right">BB</th>
                            <th className="px-2 py-2 text-right">K</th>
                            <th className="px-2 py-2 text-right">HR</th>
                            <th className="px-2 py-2 text-right">P-S</th>
                            <th className="px-2 py-2 text-right pr-3">ERA</th>
                        </tr>
                    </thead>
                    <tbody>
                        {team.pitching.map((pitcher) => (
                            <PitcherRow key={pitcher.id} pitcher={pitcher} cardResponse={cardMap[cardKey(pitcher.id, 'P')]} onCardSelect={onCardSelect} isShowingModal={isShowingModal} isLoadingCards={isLoadingCards} />
                        ))}
                        {team.pitching.length === 0 && (
                            <tr>
                                <td colSpan={10} className="px-3 py-4 text-center text-(--text-secondary)">
                                    No pitching data available.
                                </td>
                            </tr>
                        )}
                        <tr className="border-t border-(--divider) font-bold">
                            <td className="pl-3 pr-2 py-2 text-left text-(--text-primary)">Totals</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.innings_pitched}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.hits}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.runs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.earned_runs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.base_on_balls}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.strike_outs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.home_runs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">
                                {team.pitching_totals.pitches_thrown}-{team.pitching_totals.strikes}
                            </td>
                            <td className="px-2 py-2 text-right pr-3 text-(--text-primary)" />
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function PitcherRow({ pitcher, cardResponse, onCardSelect, isShowingModal, isLoadingCards }: { pitcher: BoxscorePitcher; cardResponse?: ShowdownBotCardAPIResponse; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isShowingModal?: boolean; isLoadingCards?: boolean }) {

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
    return (
        <tr
            className={`border-b border-(--divider)/50 hover:bg-(--background-tertiary) ${cardResponse ? 'cursor-pointer' : ''}`}
            onClick={cardResponse ? () => onCardSelect?.(cardResponse) : undefined}
        >
            <td ref={refs.setReference} {...getReferenceProps()} className="pl-3 pr-2 py-1.5 text-left" >
                <CardIdentityCell
                    name={pitcher.name} position={'P'} hasCard={!!card}
                    isPitcher={card?.chart.is_pitcher} primaryColor={card?.image.color_primary} secondaryColor={card?.image.color_secondary}
                    command={card?.chart.command} team={card?.team} points={card?.points} positionsAndDefense={card?.positions_and_defense}
                    ptsChange={cardResponse?.in_season_trends?.pts_change.day} isLoadingCard={isLoadingCards && !cardResponse}
                />
            </td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.innings_pitched}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.hits}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.runs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.earned_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.base_on_balls}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.strike_outs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.home_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">
                {pitcher.stats.pitches_thrown}-{pitcher.stats.strikes}
            </td>
            <td className="px-2 py-1.5 text-right pr-3 text-(--text-secondary)">{pitcher.season_stats.era}</td>
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
