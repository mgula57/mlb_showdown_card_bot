import { useEffect, useRef, useState } from "react";
import { FaMedal } from "react-icons/fa6";
import { fetchSeasonAwards, type AwardRecipient, type SeasonAwards } from "../../api/mlbAPI";
import { fetchCardById, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { fetchCardData, type CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { type Lineup, type LineupSlot } from "../../api/userTeams";
import { CardSource } from "../../types/cardSource";
import { CardItemFromCardDatabaseRecord, CardItemSkeleton } from "../cards/CardItem";
import { CardDetail } from "../cards/CardDetail";
import { Modal } from "../shared/Modal";
import { useTheme } from "../shared/SiteSettingsContext";
import { defenseAtPosition } from "../shared/DefenseUtils";
import { FieldView } from "../team_builder/FieldView";

// =============================================================================
// MARK: - Award Definitions
// =============================================================================

const LEAGUES = ['AL', 'NL'] as const;
type LeagueAbbr = typeof LEAGUES[number];

const SINGLE_WINNER_AWARDS: { key: 'MVP' | 'CY' | 'ROY'; label: string }[] = [
    { key: 'MVP', label: 'Most Valuable Player' },
    { key: 'CY', label: 'Cy Young' },
    { key: 'ROY', label: 'Rookie of the Year' },
];

const GG_POSITIONS = ['CF', 'LF', 'RF', 'SS', '2B', '3B', '1B', 'C', 'P', 'UT'];
const SS_POSITIONS = ['CF', 'LF', 'RF', 'SS', '2B', '3B', '1B', 'C', 'DH', 'UT'];
const OF_FIELD_SLOTS = ['CF', 'LF', 'RF'];

const PITCHING_POSITION_ABBRS = new Set(['P', 'SP', 'RP']);

/** Returns the card_bot map key for a recipient, disambiguating two-way players by hitting vs pitching card. */
const cardKey = (recipient: AwardRecipient): string => {
    const isPitching = PITCHING_POSITION_ABBRS.has(recipient.player.primary_position?.abbreviation ?? '');
    return `${recipient.player.id}-${isPitching ? 'P' : 'H'}`;
};

// =============================================================================
// MARK: - Props
// =============================================================================

type AwardWinnersProps = {
    seasonId: string;
    season: number;
    showdownSet: string;
    sportId?: number;
    isActive: boolean;
};

// =============================================================================
// MARK: - Component
// =============================================================================

export default function AwardWinners({ seasonId, season, showdownSet, isActive }: AwardWinnersProps) {
    const { isDark } = useTheme();

    const [awards, setAwards] = useState<SeasonAwards | null>(null);
    const [cardMap, setCardMap] = useState<Record<string, CardDatabaseRecord>>({});
    const [isLoadingAwards, setIsLoadingAwards] = useState(false);
    const [isLoadingCards, setIsLoadingCards] = useState(false);
    const [selectedModalCard, setSelectedModalCard] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isLoadingModalCard, setIsLoadingModalCard] = useState(false);

    const hasLoadedRef = useRef(false);
    const lastSeasonIdRef = useRef<string | null>(null);

    // Fetch awards when tab first becomes active or season changes
    useEffect(() => {
        if (!isActive) return;

        const seasonChanged = lastSeasonIdRef.current !== seasonId;
        if (hasLoadedRef.current && !seasonChanged) return;

        lastSeasonIdRef.current = seasonId;
        hasLoadedRef.current = false;

        setAwards(null);
        setCardMap({});
        setIsLoadingAwards(true);

        fetchSeasonAwards(seasonId)
            .then(data => {
                setAwards(data);
                hasLoadedRef.current = true;
            })
            .catch(err => {
                console.error('Failed to fetch season awards:', err);
                hasLoadedRef.current = true;
            })
            .finally(() => setIsLoadingAwards(false));
    }, [isActive, seasonId]);

    // Build card map once awards are loaded
    useEffect(() => {
        if (!awards) return;

        const allRecipients: AwardRecipient[] = [
            ...LEAGUES.map(l => awards.MVP[l]).filter((r): r is AwardRecipient => !!r),
            ...LEAGUES.map(l => awards.CY[l]).filter((r): r is AwardRecipient => !!r),
            ...LEAGUES.map(l => awards.ROY[l]).filter((r): r is AwardRecipient => !!r),
            ...LEAGUES.flatMap(l => awards.GG[l] ?? []),
            ...LEAGUES.flatMap(l => awards.SS[l] ?? []),
        ];
        if (allRecipients.length === 0) return;

        const uniqueIds = Array.from(new Set(allRecipients.map(r => String(r.player.id))));

        setIsLoadingCards(true);
        fetchCardData(CardSource.BOT, {
            mlb_id: uniqueIds,
            year: season,
            showdown_set: showdownSet,
        })
            .then(records => {
                const map: Record<string, CardDatabaseRecord> = {};
                records.forEach(record => {
                    if (!record.mlb_id) return;
                    map[`${record.mlb_id}-${record.is_pitcher ? 'P' : 'H'}`] = record;
                });
                setCardMap(map);
            })
            .catch(err => console.error('Failed to fetch award winner cards:', err))
            .finally(() => setIsLoadingCards(false));
    }, [awards, season, showdownSet]);

    const handleCardClick = (record: CardDatabaseRecord) => {
        if (isLoadingModalCard) return;
        setIsLoadingModalCard(true);
        fetchCardById(record.id, CardSource.BOT)
            .then(res => setSelectedModalCard(res))
            .catch(err => console.error('Failed to fetch full card:', err))
            .finally(() => setIsLoadingModalCard(false));
    };

    // ==========================================================================
    // MARK: - Lineup Building Helpers (feed FieldView's showcase mode)
    // ==========================================================================

    const toSlot = (recipient: AwardRecipient, fieldPosition: string): LineupSlot => ({
        card_id: cardKey(recipient),
        card_source: CardSource.BOT,
        field_position: fieldPosition,
        batting_order: null,
    });

    /** Gold Glove recipients already report a specific position (CF/LF/RF/1B/.../P/UT) — map directly. */
    const buildGoldGloveLineup = (league: LeagueAbbr): Lineup => {
        const recipients = awards?.GG[league] ?? [];
        const slots = recipients
            .filter(r => r.player.primary_position?.abbreviation)
            .map(r => toSlot(r, r.player.primary_position!.abbreviation!));
        return { name: 'Gold Glove', slots };
    };

    /**
     * Silver Slugger reports 3 undifferentiated "OF" winners (not split CF/LF/RF), so those are
     * assigned by comparing each winner's CF defense rating on their Showdown card — best CF fit
     * takes CF, the other two take LF/RF.
     */
    const buildSilverSluggerLineup = (league: LeagueAbbr): Lineup => {
        const recipients = awards?.SS[league] ?? [];
        const slots: LineupSlot[] = [];
        const outfielders: AwardRecipient[] = [];

        for (const recipient of recipients) {
            const pos = recipient.player.primary_position?.abbreviation;
            if (pos === 'P') {
                continue;
            }
            if (pos === 'OF') {
                outfielders.push(recipient);
            } else if (pos) {
                slots.push(toSlot(recipient, pos));
            }
        }

        outfielders
            .map(recipient => ({
                recipient,
                cfDefense: defenseAtPosition(cardMap[cardKey(recipient)]?.positions_and_defense, 'CF') ?? -Infinity,
            }))
            .sort((a, b) => b.cfDefense - a.cfDefense)
            .forEach(({ recipient }, i) => {
                const pos = OF_FIELD_SLOTS[i];
                if (pos) slots.push(toSlot(recipient, pos));
            });

        return { name: 'Silver Slugger', slots };
    };

    // Filter out the UT position for seasons prior to 2022
    const filteredGGPositions = GG_POSITIONS.filter(pos => (Number(season) < 2022 ? pos !== 'UT' : true));
    const filteredSSPositions = SS_POSITIONS.filter(pos => (Number(season) < 2022 ? pos !== 'UT' : true));

    // ==========================================================================
    // MARK: - Render
    // ==========================================================================

    return (
        <div className="pb-24">
            {/* Header */}
            <div className="flex items-center gap-2 mb-5 lg:pr-6">
                <FaMedal className={`text-sm ${isDark ? 'text-yellow-400' : 'text-yellow-500'}`} />
                <span className={`text-sm font-bold uppercase tracking-wide ${isDark ? 'text-neutral-400' : 'text-neutral-500'}`}>
                    Award Winners
                </span>
            </div>

            {isLoadingAwards && !awards ? (
                <div className="space-y-6">
                    {[0, 1, 2].map(i => (
                        <div key={i} className={`h-48 rounded-xl animate-pulse ${isDark ? 'bg-neutral-800' : 'bg-neutral-200'}`} />
                    ))}
                </div>
            ) : (
                <div className="space-y-6">
                    {/* MVP / Cy Young / Rookie of the Year */}
                    {SINGLE_WINNER_AWARDS.map(({ key, label }) => (
                        <div key={key}>
                            <div className="mb-3 lg:pr-6">
                                <span className={`text-xs font-bold uppercase tracking-wide ${isDark ? 'text-neutral-400' : 'text-neutral-500'}`}>
                                    {label}
                                </span>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 lg:pr-6">
                                {LEAGUES.map(league => {
                                    const recipient = awards?.[key]?.[league] ?? null;
                                    const card = recipient ? cardMap[cardKey(recipient)] : undefined;
                                    return (
                                        <div key={league} className="flex flex-col gap-1.5">
                                            <span className={`text-[10px] font-semibold uppercase tracking-wide px-1.5 ${isDark ? 'text-neutral-500' : 'text-neutral-400'}`}>
                                                {league}
                                            </span>
                                            {!recipient ? (
                                                <div className={`flex items-center justify-center h-48 rounded-xl border border-dashed text-xs ${isDark ? 'border-neutral-700 text-neutral-600' : 'border-neutral-300 text-neutral-400'}`}>
                                                    Not yet announced
                                                </div>
                                            ) : !card && isLoadingCards ? (
                                                <CardItemSkeleton className="max-w-full" />
                                            ) : (
                                                <CardItemFromCardDatabaseRecord
                                                    card={card}
                                                    className={card ? 'cursor-pointer' : 'pointer-events-none opacity-40'}
                                                    onClick={card ? () => handleCardClick(card) : undefined}
                                                />
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}

                    {/* Gold Glove */}
                    <div>
                        <div className="mb-3 lg:pr-6">
                            <span className={`text-xs font-bold uppercase tracking-wide ${isDark ? 'text-neutral-400' : 'text-neutral-500'}`}>
                                Gold Glove
                            </span>
                        </div>
                        <div className="grid grid-cols-[repeat(auto-fit,minmax(450px,1fr))] gap-6 lg:pr-6">
                            {LEAGUES.map(league => (
                                <div key={league} className="flex flex-col gap-1.5">
                                    <span className={`text-[10px] font-semibold uppercase tracking-wide px-1.5 ${isDark ? 'text-neutral-500' : 'text-neutral-400'}`}>
                                        {league}
                                    </span>
                                    <FieldView
                                        lineup={buildGoldGloveLineup(league)}
                                        cardMap={cardMap}
                                        onSlotClick={() => {}}
                                        readOnly
                                        isLoadingCards={isLoadingCards}
                                        positions={filteredGGPositions}
                                        headerLabel="Gold Glove"
                                        showDefenseSummary={true}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Silver Slugger */}
                    <div>
                        <div className="mb-3 lg:pr-6">
                            <span className={`text-xs font-bold uppercase tracking-wide ${isDark ? 'text-neutral-400' : 'text-neutral-500'}`}>
                                Silver Slugger
                            </span>
                        </div>
                        <div className="grid grid-cols-[repeat(auto-fit,minmax(450px,1fr))] gap-6 lg:pr-6">
                            {LEAGUES.map(league => (
                                <div key={league} className="flex flex-col gap-1.5">
                                    <span className={`text-[10px] font-semibold uppercase tracking-wide px-1.5 ${isDark ? 'text-neutral-500' : 'text-neutral-400'}`}>
                                        {league}
                                    </span>
                                    <FieldView
                                        lineup={buildSilverSluggerLineup(league)}
                                        cardMap={cardMap}
                                        onSlotClick={() => {}}
                                        readOnly
                                        isLoadingCards={isLoadingCards}
                                        positions={filteredSSPositions.filter(pos => (Number(season) < 2020 && Number(season) !== 2021 && league === 'NL' ? pos !== 'DH' : true))}
                                        headerLabel="Silver Slugger"
                                        showDefenseSummary={true}
                                        detailStat1Category="hr"
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Modal for selected card */}
            <div className={selectedModalCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={() => setSelectedModalCard(null)} isVisible={!!selectedModalCard}>
                    <CardDetail
                        showdownBotCardData={selectedModalCard!}
                        hideTrendGraphs={true}
                        context="home"
                        parent='home'
                    />
                </Modal>
            </div>
        </div>
    );
}
