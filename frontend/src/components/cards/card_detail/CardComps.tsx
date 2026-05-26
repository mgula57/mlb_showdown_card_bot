import { useState, useEffect } from 'react';
import { type ShowdownBotCard } from '../../../api/showdownBotCard';
import { fetchCardComps, type WotcCompCard } from '../../../api/card_db/cardDatabase';
import { CardItem, CardItemFromCard, CardItemSkeleton } from '../CardItem';

type CardCompsProps = {
    card: ShowdownBotCard | null | undefined;
    isLoading: boolean;
};

function similarityColor(pct: number): string {
    if (pct >= 92) return '#22c55e';
    if (pct >= 75) return '#eab308';
    if (pct >= 60) return '#f97316';
    return '#ef4444';
}

function CompCardItem({ comp }: { comp: WotcCompCard }) {
    const pct = Math.round(comp.similarity_score * 100);
    const barColor = similarityColor(pct);

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
                className="absolute top-2 right-2 z-10 flex items-center gap-1 rounded-full px-2 py-0.5 backdrop-blur-sm"
                style={{ backgroundColor: 'color-mix(in srgb, var(--background-secondary) 80%, transparent)' }}
            >
                <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: barColor }} />
                <span className="text-[10px] font-black tabular-nums" style={{ color: barColor }}>{pct}%</span>
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
            exclude_id: card.is_wotc ? (card as any).id : undefined,
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
            <p className="text-xs opacity-40 text-center py-6 italic">
                No WOTC comps found for this set.
            </p>
        );
    }

    return (
        <div className="space-y-2">
            <CardItemFromCard card={card} />

            {/* Divider */}
            <div className="border-t-3 border-form-element rounded my-2" />
            <span className="text-[10px] font-semibold uppercase tracking-wide opacity-40 text-center block">WOTC Comps</span>

            {comps.map(comp => (
                <CompCardItem key={comp.id} comp={comp} />
            ))}
        </div>
    );
}
