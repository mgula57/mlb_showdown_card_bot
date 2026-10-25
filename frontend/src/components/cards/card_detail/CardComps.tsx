import { useState, useEffect } from 'react';
import { type ShowdownBotCard } from '../../../api/showdownBotCard';
import { fetchCardComps, type WotcCompCard } from '../../../api/card_db/cardDatabase';
import { CardItem, CardItemFromCard, CardItemSkeleton } from '../CardItem';
import { CAPS_LABEL_CLASS } from '../../shared/fieldStyles';
import { gradeColor } from '../../../functions/colors';

type CardCompsProps = {
    card: ShowdownBotCard | null | undefined;
    isLoading: boolean;
};

function CompCardItem({ comp }: { comp: WotcCompCard }) {
    const pct = Math.round(comp.similarity_score * 100);
    const barColor = gradeColor(pct / 100, [0.92, 0.75, 0.6]);

    const primaryColor = (['NYM', 'SDP'].includes(comp.team)
        ? comp.color_secondary
        : comp.color_primary) ?? undefined;
    const secondaryColor = (['NYM', 'SDP'].includes(comp.team)
        ? comp.color_primary
        : comp.color_secondary) ?? undefined;

    return (
        <div className="relative">
            {/* Similarity badge overlaid on the card */}
            <div
                className="absolute top-2 right-2 z-10 flex items-center gap-1 rounded-plate px-2 py-0.5 bg-(--background-secondary) border border-(--divider)"
            >
                <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: barColor }} />
                <span className="text-[10px] font-bold tabular-nums" style={{ color: barColor }}>{pct}%</span>
            </div>

            <CardItem
                cardId={comp.id}
                cardTeam={comp.team}
                cardName={comp.name}
                cardYear={comp.year}
                cardCommand={comp.command}
                cardOuts={comp.outs}
                cardIsPitcher={comp.is_pitcher}
                cardPoints={comp.points}
                cardPointsEstimated={comp.points_estimated ?? undefined}
                cardPointsDiffEstimatedVsActual={comp.points_diff_estimated_vs_actual ?? undefined}
                cardSpeed={comp.speed ?? undefined}
                cardHand={comp.hand ?? undefined}
                cardIp={comp.ip ?? undefined}
                cardPositionsAndDefenseString={comp.positions_and_defense_string ?? undefined}
                cardIsErrata={comp.is_errata ?? false}
                cardNotes={comp.notes ?? undefined}
                cardPrimaryColor={primaryColor}
                cardSecondaryColor={secondaryColor}
                cardEdition={comp.edition ?? undefined}
                cardSet={comp.showdown_set}
                cardExpansion={comp.expansion ?? undefined}
                cardSetNumber={comp.set_number ? parseInt(comp.set_number) : undefined}
                cardIcons={comp.icons_list ?? []}
                cardAwardList={comp.awards_list ?? []}
                cardStatHighlightsList={comp.stat_highlights_list ?? []}
                cardChartRanges={comp.chart_ranges ?? {}}
                cardSource='WOTC'
            />
        </div>
    );
}

export function CardComps({ card, isLoading }: CardCompsProps) {
    const [comps, setComps] = useState<WotcCompCard[]>([]);
    const [isFetching, setIsFetching] = useState(false);

    useEffect(() => {
        if (!card) {
            setComps([]);
            return;
        }

        setIsFetching(true);
        const excludeId = card.is_wotc && card && (
            // Concatination of year, bref_id, set, expansion, player_type_override (if exists), and "WOTC" if is_wotc to create a unique identifier for WOTC cards to exclude from comps since they won't be in the DB with a bref_id
            `${card.year}-${card.bref_id}-${card.set}-${card.image.expansion ?? 'BS'}-WOTC`
        ) || undefined;
        console.log("Excluding card ID from comps fetch:", excludeId);
        fetchCardComps({
            showdown_set: card.set,
            player_type: card.player_type.toUpperCase(),
            positions_list: Object.keys(card.positions_and_defense ?? {}),
            command: card.chart.command,
            outs: card.chart.outs,
            ip: card.ip ?? null,
            speed: card.speed?.speed ?? null,
            positions_and_defense: card.positions_and_defense ?? {},
            chart_values: card.chart.values ?? {},
            exclude_id: excludeId,
            limit: 3,
        })
            .then(setComps)
            .catch(() => setComps([]))
            .finally(() => setIsFetching(false));
    }, [card?.bref_id, card?.set, card?.year]);

    const isEmpty = !isFetching && comps.length === 0 && !isLoading;
    const showSkeletons = isLoading || isFetching;

    if (showSkeletons) {
        return (
            <div className="space-y-2">
                {[0, 1, 2].map(i => <CardItemSkeleton key={i} />)}
            </div>
        );
    }

    if (isEmpty) {
        return (
            <p className="text-xs text-(--text-tertiary) text-center py-6">
                No WOTC comps found for this set.
            </p>
        );
    }

    return (
        <div className="space-y-2">
            <CardItemFromCard card={card} />

            {/* Divider */}
            <div className="border-t-3 border-(--divider) my-2" />
            <span className={`opacity-40 text-center block ${CAPS_LABEL_CLASS}`}>WOTC Comps</span>

            {comps.map(comp => (
                <CompCardItem key={comp.id} comp={comp} />
            ))}
        </div>
    );
}
