/**
 * @fileoverview TeamRoster - Depth chart display grouped by roster position
 */

import { useEffect, useState } from "react";

import { type Roster, type RosterSlot, type Team } from "../../api/mlbAPI";
import type { ShowdownBotCard, ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { buildCardsFromIds } from "../../api/showdownBotCard";
import { useSiteSettings } from "../shared/SiteSettingsContext";

import { CardItemFromCard } from "../cards/CardItem";
import TeamRosterPositionTable from "./TeamRosterPositionTable";
import { Modal } from "../shared/Modal";
import { CardDetail } from "../cards/CardDetail";
import { FaRegStar, FaStar } from "react-icons/fa6";

import { countryCodeForTeam } from "../../functions/flags";
import ReactCountryFlag from "react-country-flag";


interface TeamRosterProps {
    team: Team;
    sportId: number | null;
    roster: Roster | null;
    isStarred?: boolean;
    season?: number | null;
    loadShowdownCards?: boolean;
    onToggleStar?: () => void;
}

const getTopPlayerLimit = (width: number): number => {
    if (width < 640) {
        return 3;
    }
    if (width < 1280) {
        return 4;
    }
    if (width < 1536) {
        return 6;
    }
    return 8;
};

const getPositionLabel = (slot: RosterSlot): string => {
    if (typeof slot.position === "string") {
        return slot.position;
    }
    return slot.position.type || slot.position.abbreviation || slot.position.code || slot.position.name || "Unknown";
};

export default function TeamRoster({ team, sportId, roster, isStarred = false, onToggleStar, season, loadShowdownCards = false }: TeamRosterProps) {
    const [enrichedRoster, setEnrichedRoster] = useState<Roster | null>(roster);
    const [isLoadingCards, setIsLoadingCards] = useState(false);
    const { userShowdownSet, isDark } = useSiteSettings();

    useEffect(() => {
        setEnrichedRoster(roster);
    }, [roster]);

    useEffect(() => {
        if (!loadShowdownCards || !roster || !season) return;

        const ids = (roster.roster ?? [])
            .map((slot) => slot.person.id)
            .filter((id) => id != null)
            .map(String);

        if (ids.length === 0) return;

        setIsLoadingCards(true);
        const cardSettings = {
            year: season,
            set: userShowdownSet,
            stat_highlights_type: "ALL",
        }
        buildCardsFromIds(ids, season, cardSettings)
            .then((response) => {
                const cardsByMlbId = new Map<number, ShowdownBotCard>();
                for (const entry of response.cards ?? []) {
                    if (entry.card?.mlb_id != null) {
                        cardsByMlbId.set(entry.card.mlb_id, entry.card);
                    }
                }
                console.log("Loaded showdown cards for roster:", cardsByMlbId);
                setEnrichedRoster({
                    ...roster,
                    roster: (roster.roster ?? []).map((slot) => ({
                        ...slot,
                        person: {
                            ...slot.person,
                            showdown_card_data: cardsByMlbId.get(slot.person.id) ?? slot.person.showdown_card_data,
                        },
                    })),
                });
            })
            .catch((err) => console.error("Failed to load showdown cards:", err))
            .finally(() => setIsLoadingCards(false));
    }, [loadShowdownCards, roster, season, userShowdownSet]);

    const rosterSlots = enrichedRoster?.roster ?? [];
    const [topPlayerLimit, setTopPlayerLimit] = useState<number>(() => {
        if (typeof window === "undefined") {
            return 3; // Default for server-side rendering
        }
        return getTopPlayerLimit(window.innerWidth);
    });
    const [selectedCard, setSelectedCard] = useState<ShowdownBotCard | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Calculate team points summary
    const teamRosterSlots = enrichedRoster?.roster ?? [];
    const teamShowdownPointsTotal = teamRosterSlots.reduce((total, slot) => {
        const playerPoints = slot.person.showdown_card_data?.stats_period?.type !== "REPLACEMENT" ? slot.person.showdown_card_data?.points ?? 0 : 0;
        return total + playerPoints;
    }, 0);
    const teamPlayersWithShowdownCards = teamRosterSlots.filter((slot) =>
        (slot.person.showdown_card_data?.points !== undefined || slot.person.points !== undefined) && slot.person.showdown_card_data?.stats_period?.type !== "REPLACEMENT"
    ).length;
    const teamAvgPointsPerPlayer = teamRosterSlots.length > 0 ? teamShowdownPointsTotal / teamRosterSlots.length : 0;

    // Handle selection of players
    const handleRowClick = (slot: RosterSlot) => {
        if (!slot.person.showdown_card_data) {
            return;
        }
        setSelectedCard(slot.person.showdown_card_data);
        setIsModalOpen(true);
    }

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedCard(null);
    };

    useEffect(() => {
        const handleResize = () => {
            setTopPlayerLimit(getTopPlayerLimit(window.innerWidth));
        };

        handleResize();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    const isLoadingRoster = roster === null;
    const isLoading = isLoadingRoster || isLoadingCards;

    const groupedByPosition = rosterSlots.reduce<Record<string, RosterSlot[]>>((groups, slot) => {
        const positionKey = getPositionLabel(slot);
        if (!groups[positionKey]) {
            groups[positionKey] = [];
        }
        groups[positionKey].push(slot);
        return groups;
    }, {});

    const orderedPositions = Object.keys(groupedByPosition)
        .sort((a, b) => a.localeCompare(b));
    const topPlayers = [...rosterSlots]
        .filter((slot) => slot.person.showdown_card_data)
        .sort((a, b) => (b.person.showdown_card_data?.stats_period.type === "REPLACEMENT" ? -1 : 0) - (a.person.showdown_card_data?.stats_period?.type === "REPLACEMENT" ? -1 : 0))
        .sort((a, b) => (b.person.showdown_card_data?.points || 0) - (a.person.showdown_card_data?.points || 0))
        .slice(0, topPlayerLimit);

    const loadingOverlay = (
        <div className={`absolute inset-0 z-10 flex items-center justify-center gap-2 backdrop-blur-[2px] ${isDark ? 'bg-neutral-900/60' : 'bg-white/60'}`}>
            <span className={`w-2 h-2 rounded-full animate-bounce [animation-delay:0ms] ${isDark ? 'bg-neutral-400' : 'bg-neutral-500'}`} />
            <span className={`w-2 h-2 rounded-full animate-bounce [animation-delay:150ms] ${isDark ? 'bg-neutral-400' : 'bg-neutral-500'}`} />
            <span className={`w-2 h-2 rounded-full animate-bounce [animation-delay:300ms] ${isDark ? 'bg-neutral-400' : 'bg-neutral-500'}`} />
        </div>
    );

    return (
        <div className="space-y-4">
            {/* Team Header */}
            <div
                className="rounded-lg border border-(--divider) p-4"
                style={{
                    backgroundImage: `linear-gradient(120deg, color-mix(in srgb, ${team.primary_color || "var(--background-primary)"} 12%, transparent) 0%, color-mix(in srgb, ${(team.secondary_color || team.primary_color || "var(--background-primary)")} 12%, transparent) 100%)`,
                }}
            >
                <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_auto] gap-4 items-start">
                    <div>
                        
                        <h2 className="flex gap-2 text-xl font-semibold text-(--text-primary)">
                            {sportId === 51 && countryCodeForTeam(sportId, team.abbreviation || team.name) && (
                                <ReactCountryFlag
                                    countryCode={countryCodeForTeam(sportId, team.abbreviation || team.name) || ""}
                                    svg
                                    style={{
                                        width: '1.5em',
                                        height: '1.5em',
                                        marginBottom: '-0.25em',
                                    }}
                                />
                            )}
                            {team.name}
                        </h2>
                        <div className="mt-1 flex items-center gap-2 text-sm text-(--text-secondary)">
                            <p>
                                {team.abbreviation || "N/A"} • {team.season?.toString() || team?.season || "N/A"}
                            </p>
                            {onToggleStar && (
                                <button
                                    type="button"
                                    onClick={onToggleStar}
                                    className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-semibold hover:bg-(--divider)"
                                    aria-label={isStarred ? `Unstar ${team.abbreviation || team.name}` : `Star ${team.abbreviation || team.name}`}
                                >
                                    {isStarred ? (
                                        <FaStar className="h-3.5 w-3.5 text-yellow-300" />
                                    ) : (
                                        <FaRegStar className="h-3.5 w-3.5" />
                                    )}
                                    {isStarred ? "Starred" : "Star"}
                                </button>
                            )}
                        </div>

                        <div className="mt-3 gap-2 text-sm">
                            <div className="text-(--text-secondary)">
                                <span className="font-semibold">League:</span> {team.league?.name || team.league?.abbreviation || "N/A"}
                            </div>
                            <div className="text-(--text-secondary)">
                                <span className="font-semibold">Division:</span> {team.division?.name || team.division?.name || "N/A"}
                            </div>
                        </div>
                    </div>

                    <div className="relative rounded-lg border border-(--divider) px-4 py-3 min-w-44">
                        {isLoading && loadingOverlay}
                        <p className="text-[11px] font-semibold uppercase tracking-wide text-(--text-secondary)">
                            Total PTS
                        </p>
                        <p className="mt-1 text-2xl font-bold text-(--text-primary)">
                            {teamShowdownPointsTotal.toLocaleString()}
                        </p>
                        <p className="text-xs text-(--text-secondary)">
                            {teamAvgPointsPerPlayer > 0 ? `Avg ${teamAvgPointsPerPlayer.toFixed(0)} / Player` : "No player points"}
                        </p>
                        <p className="text-xs text-(--text-tertiary)">
                            {teamPlayersWithShowdownCards} player{teamPlayersWithShowdownCards === 1 ? "" : "s"} with cards
                        </p>
                    </div>
                </div>
            </div>

            {/* Team Content */}
            <div className="mt-6 space-y-8">
                <section className="relative bg-(--background-secondary) rounded-lg border border-(--divider) overflow-hidden">
                    {isLoading && loadingOverlay}
                    <h3 className="px-4 py-2 text-sm font-semibold uppercase text-(--text-secondary) bg-(--background-quaternary)">
                        Top Players
                    </h3>
                    {topPlayers.length === 0 ? (
                        <div className="px-4 py-3 text-sm text-(--text-secondary)">No showdown card data available.</div>
                    ) : (
                        <div className="p-3 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-2">
                            {topPlayers.map((slot) => {
                                const card = slot.person.showdown_card_data;
                                return (
                                    <CardItemFromCard
                                        key={slot.person.id}
                                        card={card}
                                        className="w-full"
                                        hideYear={true}
                                        onClick={() => handleRowClick(slot)}
                                    />
                                );
                            })}
                        </div>
                    )}
                </section>

                <div className="relative bg-(--background-secondary) rounded-lg border border-(--divider) overflow-hidden">
                    {isLoading && loadingOverlay}
                    <h3 className="px-4 py-2 text-sm font-semibold uppercase text-(--text-secondary) bg-(--background-quaternary)">
                        Roster
                    </h3>
                    {rosterSlots.length === 0 ? (
                        <div className="px-4 py-3 text-sm text-(--text-secondary)">No roster data available.</div>
                    ) : (
                        orderedPositions.map((position) => (
                            <TeamRosterPositionTable
                                key={position}
                                position={position}
                                slots={groupedByPosition[position]}
                                className="p-3"
                            />
                        ))
                    )}
                </div>

                <div className={isModalOpen ? '' : 'hidden pointer-events-none'}>
                    <Modal onClose={handleCloseModal} isVisible={!!selectedCard}>
                        <CardDetail
                            showdownBotCardData={{ card: selectedCard } as ShowdownBotCardAPIResponse} 
                            hideTrendGraphs={true}
                            context="home"
                            parent='home'
                        />
                    </Modal>
                </div>
            </div>
        </div>
    );
}

