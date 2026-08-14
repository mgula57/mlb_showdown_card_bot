import type { AwardWinner, SeasonAwards, SimTeamIdentity } from '../../../api/sim';
import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import type { CardSource as CardSourceType } from '../../../types/cardSource';
import type { Lineup, LineupSlot } from '../../../api/userTeams';
import { CardItemFromCardDatabaseRecord, CardItemSkeleton } from '../../cards/CardItem';
import { CardDetail } from '../../cards/CardDetail';
import { Modal } from '../../shared/Modal';
import { FieldView, FIELD_POSITIONS } from '../FieldView';
import { buildSimStatHighlights, SIM_STATS_TOOLTIP } from './simStatColumns';
import { useCardLinks } from './useCardLinks';

const CATEGORY_LABELS: Record<AwardWinner['category'], string> = {
    MVP: 'Most Valuable Player',
    CY_YOUNG: 'Cy Young',
    ROY: 'Rookie of the Year',
    SILVER_SLUGGER: 'Silver Slugger',
};

/** Rendered as a single card per league (MVP/CY/ROY have exactly one winner each). Silver
 * Slugger has one winner per position and gets its own `FieldView` showcase below. */
const SINGLE_WINNER_CATEGORIES: AwardWinner['category'][] = ['MVP', 'CY_YOUNG', 'ROY'];

type Props = {
    awards: SeasonAwards;
    /** Schedule key -> branding (`SeasonSimSummary.identities`) — see `SimStatsTable`'s prop of
     * the same name. A winner's sim-team colors win over their card's own archived colors. */
    identities?: Record<string, SimTeamIdentity>;
};

/**
 * Award winners rendered as real Showdown cards, grouped by category then league — the same
 * treatment `AwardWinners.tsx` uses for real MLB awards (single-winner card grid, Silver Slugger
 * as a `FieldView` showcase), minus Gold Glove, which the sim has no fielding-award model to back.
 */
export function SimAwardsList({ awards, identities }: Props) {
    const winnersByCategory: Record<AwardWinner['category'], AwardWinner[]> = {
        MVP: awards.mvp,
        CY_YOUNG: awards.cy_young,
        ROY: awards.rookie_of_year,
        SILVER_SLUGGER: awards.silver_sluggers,
    };
    const allWinners = [...awards.mvp, ...awards.cy_young, ...awards.rookie_of_year, ...awards.silver_sluggers];
    const leagues = Array.from(new Set(allWinners.map(a => a.league))).sort();
    const players = allWinners.map(a => a.player);
    const { cardMap, isLoadingCards, recordFor, isLoadingCard, selected, selectedSimStats, open, close, isFetching } = useCardLinks(players, true);

    /** The winner's card, recolored to their sim team's identity (see `SimStatsTable`) — a
     * takeover/tournament team's winners should show that team's colors, not their card's own. */
    const coloredRecord = (award: AwardWinner): CardDatabaseRecord | undefined => {
        const record = recordFor(award.player) ?? undefined;
        const teamIdentity = record && identities?.[award.player.team ?? ''];
        if (!record || !teamIdentity) return record;
        return {
            ...record,
            team: award.player.team ?? record.team,
            color_primary: teamIdentity.primary_color ?? record.color_primary,
            color_secondary: teamIdentity.secondary_color ?? record.color_secondary,
        };
    };

    const renderCard = (award: AwardWinner) => {
        const record = coloredRecord(award);
        const isLoading = isLoadingCard(award.player) || (record ? isFetching(record.card_id) : false);
        return !record && isLoading ? (
            <CardItemSkeleton className="max-w-full" />
        ) : (
            <CardItemFromCardDatabaseRecord
                card={record}
                className={record ? 'cursor-pointer' : 'pointer-events-none opacity-40'}
                onClick={record ? () => open(record.card_id, record.source, award.player.stats) : undefined}
                statHighlightsOverride={buildSimStatHighlights(award.player)}
                awardListOverride={['SIM:']}
            />
        );
    };

    const silverSluggers = winnersByCategory.SILVER_SLUGGER;
    const silverSluggerCardMap: Record<string, CardDatabaseRecord | null> = {};
    const silverSluggerSimStatsMap: Record<string, Record<string, number>> = {};
    for (const award of silverSluggers) {
        silverSluggerCardMap[award.player.id] = coloredRecord(award) ?? cardMap[award.player.id] ?? null;
        silverSluggerSimStatsMap[award.player.id] = award.player.stats;
    }
    const buildSilverSluggerLineup = (league: string): Lineup => ({
        name: 'Silver Slugger',
        index: 0,
        slots: silverSluggers
            .filter((award): award is AwardWinner & { position: string } => award.league === league && !!award.position)
            .map((award): LineupSlot => ({
                card_id: award.player.id,
                card_source: (award.player.card_source ?? 'BOT') as CardSourceType,
                field_position: award.position,
                batting_order: 1,
            })),
    });

    if (allWinners.length === 0) return null;

    return (
        <div className="flex flex-col gap-6">
            {SINGLE_WINNER_CATEGORIES.map(category => {
                const winners = winnersByCategory[category];
                if (winners.length === 0) return null;
                return (
                    <div key={category}>
                        <p className="text-[12px] font-bold uppercase tracking-wide text-(--text-tertiary) mb-3">
                            {CATEGORY_LABELS[category]}
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {leagues.map(league => {
                                const award = winners.find(w => w.league === league);
                                if (!award) return null;
                                return (
                                    <div key={league} className="flex flex-col gap-1.5">
                                        <span className="text-[10px] font-semibold uppercase tracking-wide text-(--text-tertiary) px-1.5">
                                            {league}
                                        </span>
                                        {renderCard(award)}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                );
            })}

            {silverSluggers.length > 0 && (
                <div>
                    <p className="text-[12px] font-bold uppercase tracking-wide text-(--text-tertiary) mb-3">
                        {CATEGORY_LABELS.SILVER_SLUGGER}
                    </p>
                    <div className="grid grid-cols-[repeat(auto-fit,minmax(450px,1fr))] gap-6">
                        {leagues.filter(league => silverSluggers.some(w => w.league === league)).map(league => (
                            <div key={league} className="flex flex-col gap-1.5 bg-secondary py-2 rounded-xl shadow-2xl">
                                <span className="text-[10px] font-semibold uppercase tracking-wide px-3 text-(--text-tertiary)">
                                    {league}
                                </span>
                                <FieldView
                                    lineup={buildSilverSluggerLineup(league)}
                                    cardMap={silverSluggerCardMap}
                                    onSlotClick={() => {}}
                                    readOnly
                                    isLoadingCards={isLoadingCards}
                                    positions={FIELD_POSITIONS}
                                    headerLabel="Silver Slugger"
                                    showDefenseSummary
                                    detailStat1Category="hr"
                                    simStatsMap={silverSluggerSimStatsMap}
                                    simStatsTooltip={SIM_STATS_TOOLTIP}
                                />
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className={selected ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={close} isVisible={!!selected} size='xl'>
                    <CardDetail showdownBotCardData={selected} hideTrendGraphs={true} context="sim_result" parent="sim_result" simStats={selectedSimStats} tooltip={selectedSimStats ? SIM_STATS_TOOLTIP : undefined} />
                </Modal>
            </div>
        </div>
    );
}
