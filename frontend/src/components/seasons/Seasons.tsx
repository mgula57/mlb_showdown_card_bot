/**
 * @fileoverview Seasons - MLB Season Results with Showdown Context
 * 
 * Displays real MLB season results with Showdown context including
 * player cards, team points, and performance analytics.
 */

import { useState, useEffect, useRef } from "react";
import * as Tabs from '@radix-ui/react-tabs';
import CustomSelect, { type SelectOption } from '../shared/CustomSelect';
import { 
    fetchSeasons, fetchSeasonSports, fetchSeasonLeagues, fetchSeasonStandings, fetchTeamRoster,
    type Season, type Sport, type League, type Standings, type Team, type Roster
} from '../../api/mlbAPI';
import { useSiteSettings } from "../shared/SiteSettingsContext";
import TeamRoster from "../teams/TeamRoster";
import SidebarPanel, { type SidebarSection } from "../shared/SidebarPanel";
import ReactCountryFlag from "react-country-flag";
import { countryCodeForTeam } from "../../functions/flags";
import StandingsTab from "./Standings";

import { FaRankingStar, FaClipboardList, FaUserGroup, FaGamepad, FaChevronDown, FaBaseball } from "react-icons/fa6";

import ShowdownCardSearch from "../cards/ShowdownCardSearch";

type SeasonsProps = {
    type: 'mlb' | 'wbc';
    title: string;
    subtitle?: string;
    staticSports?: Sport[]; // Optional prop to provide static sports data
    staticSeasons?: Season[]; // Optional prop to provide static seasons data
};

export default function Seasons({ type, title, subtitle, staticSports, staticSeasons }: SeasonsProps) {
    const STORAGE_KEYS = {
        seasonId: `${type}.seasons.selectedSeasonId`,
        sportId: `${type}.seasons.selectedSportId`,
        leagueGroup: `${type}.seasons.selectedLeagueGroup`,
        activeTab: `${type}.seasons.activeTab`,
    };

    const getStoredValue = (key: string): string | null => {
        if (typeof window === "undefined") {
            return null;
        }
        return window.localStorage.getItem(key);
    };

    const setStoredValue = (key: string, value: string | null) => {
        if (typeof window === "undefined") {
            return;
        }
        if (value === null || value === "") {
            window.localStorage.removeItem(key);
            return;
        }
        window.localStorage.setItem(key, value);
    };

    const { userShowdownSet } = useSiteSettings();
    const hasStaticSeasons = staticSeasons !== undefined;
    const hasStaticSports = staticSports !== undefined;

    const [seasons, setSeasons] = useState<Season[]>(staticSeasons || []);
    const [selectedSeason, setSelectedSeason] = useState<Season | null>(null);
    
    const [sports, setSports] = useState<Sport[]>(staticSports || []);
    const [selectedSport, setSelectedSport] = useState<Sport | null>(null);

    const [leagues, setLeagues] = useState<League[]>([]);

    const [teams, setTeams] = useState<Team[]>([]);
    const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);

    const [selectedRoster, setSelectedRoster] = useState<Roster | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(false);

    const [leagueGroups, setLeagueGroups] = useState<string[]>([]);
    const [selectedLeagueGroup, setSelectedLeagueGroup] = useState<string | null>(() => getStoredValue(STORAGE_KEYS.leagueGroup));
    const leagueGroupMappings: { [key: string]: string[] } = {
        "Regular Season": ["AL", "NL"],
        "Spring Training": ["CL", "GL"],
    };

    const getLeagueGroupForLeague = (league: League): string | null => {
        const leagueAbbreviation = league.abbreviation ?? "";
        const matchedGroup = Object.entries(leagueGroupMappings).find(([, abbreviations]) =>
            abbreviations.includes(leagueAbbreviation)
        );
        return matchedGroup?.[0] ?? null;
    };

    const [standings, setStandings] = useState<{ [leagueAbbreviation: string]: Standings[] }>({});

    const [activeTab, setActiveTab] = useState<string>(() => getStoredValue(STORAGE_KEYS.activeTab) ?? "standings");
    const [isTeamsNavOpen, setIsTeamsNavOpen] = useState<boolean>(true);
    const hasLoadedSeasonsRef = useRef(false);
    const isLoadingSeasonsRef = useRef(false);
    const pendingRequestsRef = useRef(0);

    const beginLoading = () => {
        pendingRequestsRef.current += 1;
        setIsLoading(true);
    };

    const endLoading = () => {
        pendingRequestsRef.current = Math.max(0, pendingRequestsRef.current - 1);
        if (pendingRequestsRef.current === 0) {
            setIsLoading(false);
        }
    };

    const isMidSeason = (season: Season) => {
        const today = new Date();
        const startDate = new Date(season.regular_season_start_date);
        const endDate = new Date(season.season_end_date);
        return today >= startDate && today <= endDate;
    };

    const seasonOptions: SelectOption[] = seasons
        .filter(season => season.season_id != null)
        .map(season => ({
            value: season.season_id.toString(),
            label: season.season_id.toString()
        }));
    
    const sportOptions: SelectOption[] = sports
        .filter(sport => sport.id != null && sport.abbreviation != null)
        .map(sport => ({
            value: sport.id.toString(),
            label: sport.abbreviation || ""
        }));

    const tabs = [
        { id: "standings", label: "Standings", icon: <FaRankingStar /> },
        { id: "teams", label: "Teams", icon: <FaClipboardList /> },
        { id: "players", label: "Players", icon: <FaUserGroup /> },
        ...(selectedSeason && isMidSeason(selectedSeason) ? [{ id: "games", label: "Games", icon: <FaGamepad /> }] : [])
    ];

    // ************************
    // Loading Methods
    // ************************

    const loadSeasons = async () => {
        if (hasStaticSeasons) {
            const normalizedSeasons = staticSeasons ?? [];
            setSeasons(normalizedSeasons);
            hasLoadedSeasonsRef.current = true;

            if (normalizedSeasons.length > 0) {
                const storedSeasonId = getStoredValue(STORAGE_KEYS.seasonId);
                const seasonFromStorage = storedSeasonId
                    ? normalizedSeasons.find((season) => season.season_id.toString() === storedSeasonId)
                    : null;

                setSelectedSeason((previousSeason) => {
                    if (previousSeason && normalizedSeasons.some((season) => season.season_id === previousSeason.season_id)) {
                        return previousSeason;
                    }
                    return seasonFromStorage ?? normalizedSeasons[0];
                });
            }
            return;
        }

        if (hasLoadedSeasonsRef.current || isLoadingSeasonsRef.current) {
            return;
        }

        isLoadingSeasonsRef.current = true;
        beginLoading();
        try {
            const seasonsData = await fetchSeasons();
            console.log("Raw seasons data from API:", seasonsData);
            const normalizedSeasons = seasonsData === undefined ? [] : seasonsData;
            setSeasons(normalizedSeasons);
            hasLoadedSeasonsRef.current = true;
            console.log("Fetched seasons:", normalizedSeasons);
            if (normalizedSeasons.length > 0) {
                const storedSeasonId = getStoredValue(STORAGE_KEYS.seasonId);
                const seasonFromStorage = storedSeasonId
                    ? normalizedSeasons.find((season) => season.season_id.toString() === storedSeasonId)
                    : null;

                setSelectedSeason((previousSeason) => {
                    if (previousSeason && normalizedSeasons.some((season) => season.season_id === previousSeason.season_id)) {
                        return previousSeason;
                    }
                    return seasonFromStorage ?? normalizedSeasons[0];
                });
            }
        } catch (error) {
            console.error("Error fetching seasons:", error);
        } finally {
            isLoadingSeasonsRef.current = false;
            endLoading();
        }
    };

    const loadSports = async () => {
        if (!selectedSeason) {
            return;
        }

        if (hasStaticSports) {
            const staticSportsData = staticSports ?? [];
            setSports(staticSportsData);

            const storedSportId = getStoredValue(STORAGE_KEYS.sportId);
            const sportFromStorage = storedSportId
                ? staticSportsData.find((sport) => sport.id.toString() === storedSportId)
                : null;

            setSelectedSport((previousSport) => {
                if (previousSport && staticSportsData.some((sport) => sport.id === previousSport.id)) {
                    return previousSport;
                }
                return sportFromStorage ?? (staticSportsData.length > 0 ? staticSportsData[0] : null);
            });
            return;
        }

        beginLoading();
        try {
            const sportsData = await fetchSeasonSports(selectedSeason);
            console.log(`Fetched sports for season ${selectedSeason.season_id}:`, sportsData);
            setSports(sportsData);

            const storedSportId = getStoredValue(STORAGE_KEYS.sportId);
            const sportFromStorage = storedSportId
                ? sportsData.find((sport) => sport.id.toString() === storedSportId)
                : null;

            setSelectedSport((previousSport) => {
                if (previousSport && sportsData.some((sport) => sport.id === previousSport.id)) {
                    return previousSport;
                }
                return sportFromStorage ?? (sportsData.length > 0 ? sportsData[0] : null);
            });
        } catch (error) {
            console.error(`Error fetching sports for season ${selectedSeason.season_id}:`, error);
        } finally {
            endLoading();
        }
    };

    const loadLeagues = async () => {
        if (!selectedSeason || !selectedSport) {
            return;
        }
        
        beginLoading();
        try {
            
            const leaguesData = await fetchSeasonLeagues(selectedSeason, selectedSport);
            console.log(`Fetched leagues for season ${selectedSeason.season_id}:`, leaguesData);

            const uniqueLeagueGroups = Array.from(
                new Set(
                    leaguesData
                        .map((league) => getLeagueGroupForLeague(league))
                        .filter((group): group is string => group !== null)
                )
            );
            console.log("Unique league groups identified:", uniqueLeagueGroups);
            setLeagueGroups(uniqueLeagueGroups);

            setSelectedLeagueGroup((prevGroup) => {
                if (uniqueLeagueGroups.length <= 1) {
                    return null;
                }
                if (prevGroup && uniqueLeagueGroups.includes(prevGroup)) {
                    return prevGroup;
                }
                return uniqueLeagueGroups[0] ?? null;
            });

            setLeagues(leaguesData);
            
        } catch (error) {
            console.error(`Error fetching leagues for season ${selectedSeason.season_id}:`, error);
        } finally {
            endLoading();
        }
    };

    // ************************
    // Loading for individual tabs
    // ************************

    const loadStandings = async () => {
        if (!selectedSeason || leagues.length === 0) {
            return;
        }

        const shouldFilterByLeagueGroup = leagueGroups.length > 1 && selectedLeagueGroup !== null;
        const leaguesToQuery = shouldFilterByLeagueGroup
            ? leagues.filter((league) => getLeagueGroupForLeague(league) === selectedLeagueGroup)
            : leagues;

        if (leaguesToQuery.length === 0) {
            setStandings({});
            return;
        }

        var standingsData: { [leagueAbbreviation: string]: Standings[] } = {};
        beginLoading();
        try {
            standingsData = await fetchSeasonStandings(selectedSeason, leaguesToQuery);
            console.log(`Fetched standings for season ${selectedSeason.season_id}:`, standingsData);
            setStandings(standingsData);
        } catch (error) {
            console.error(`Error fetching standings for season ${selectedSeason.season_id}:`, error);
        } finally {
            endLoading();
        }

        // Populate Teams for Teams Tab
        const allTeams: Team[] = [];
        Object.values(standingsData).forEach((leagueStandings) => {
            leagueStandings.forEach((standing) => {
                standing.team_records?.forEach((record) => {
                    allTeams.push(record.team);
                });
            });
        });
        allTeams.sort((a, b) => (a.abbreviation || "").localeCompare(b.abbreviation || ""));
        // Check if currently selected team still exists in the new data, otherwise set to first value
        setSelectedTeam((prevTeam) => {
            if (prevTeam && allTeams.some((team) => (`${team.id}-${team.season}` === `${prevTeam.id}-${prevTeam.season}`))) {
                return prevTeam;
            }
            return allTeams[0] || null;
        });
        console.log("All teams extracted from standings:", allTeams);
        setTeams(allTeams);
    };

    const loadTeamRoster = async (team: Team) => {
        if (!selectedSeason || !selectedSport || !team) {
            return;
        }

        beginLoading();
        try {
            const rosterType = "active";
            const rosterData = await fetchTeamRoster(selectedSeason, team.id, rosterType, userShowdownSet, selectedSport.id);
            console.log(`Fetched roster for team ${team.name} in season ${selectedSeason.season_id}:`, rosterData);
            setSelectedRoster(rosterData);
        } catch (error) {
            console.error(`Error fetching roster for team ${team.name} in season ${selectedSeason.season_id}:`, error);
        } finally {
            endLoading();
        }
    };

    // ************************
    // Effects
    // ************************
    useEffect(() => {
        loadSeasons();
    }, []);

    useEffect(() => {
        if (selectedSeason === null || selectedSeason.season_id === undefined) {
            return;
        }
        loadSports();
    }, [selectedSeason]);

    useEffect(() => {
        setStoredValue(STORAGE_KEYS.seasonId, selectedSeason?.season_id?.toString() ?? null);
    }, [selectedSeason]);

    useEffect(() => {
        setStoredValue(STORAGE_KEYS.sportId, selectedSport?.id?.toString() ?? null);
    }, [selectedSport]);

    useEffect(() => {
        setStoredValue(STORAGE_KEYS.activeTab, activeTab);
    }, [activeTab]);

    useEffect(() => {
        setStoredValue(STORAGE_KEYS.leagueGroup, selectedLeagueGroup);
    }, [selectedLeagueGroup]);

    useEffect(() => {
        if (!tabs.some((tab) => tab.id === activeTab)) {
            setActiveTab("standings");
        }
    }, [tabs, activeTab]);

    useEffect(() => {
        if (activeTab === "teams") {
            setIsTeamsNavOpen(true);
        }
    }, [activeTab]);

    useEffect(() => {
        if (selectedSeason === null || selectedSeason.season_id === undefined || selectedSport === null || selectedSport.id === undefined) {
            return;
        }
        loadLeagues();
    }, [selectedSeason, selectedSport]);

    useEffect(() => {
        if (selectedSeason === null || selectedSeason.season_id === undefined || leagues.length === 0) {
            return;
        }
        loadStandings();
    }, [selectedSeason, leagues, leagueGroups, selectedLeagueGroup]);

    useEffect(() => {
        if (selectedTeam === null || selectedTeam.id === undefined) {
            return;
        }
        loadTeamRoster(selectedTeam);
    }, [selectedTeam, userShowdownSet]);

    const selectedTeamKey = selectedTeam ? `${selectedTeam.id}-${selectedTeam.season}` : null;
    const standingsEntries = Object.entries(standings);
    const teamRosterSlots = selectedRoster?.roster ?? [];
    const teamShowdownPointsTotal = teamRosterSlots.reduce((total, slot) => {
        const playerPoints = slot.person.showdown_card_data?.points ?? slot.person.points ?? 0;
        return total + playerPoints;
    }, 0);
    const teamPlayersWithShowdownCards = teamRosterSlots.filter((slot) =>
        (slot.person.showdown_card_data?.points !== undefined || slot.person.points !== undefined) && slot.person.showdown_card_data?.stats_period?.type !== "REPLACEMENT"
    ).length;
    const teamAvgPointsPerPlayer = teamRosterSlots.length > 0 ? teamShowdownPointsTotal / teamRosterSlots.length : 0;

    const sidebarSections: SidebarSection[] = [
        {
            id: "context",
            title: "Season/League",
            collapsible: false,
            isHidden: hasStaticSeasons && seasonOptions.length <= 1 && hasStaticSports && sportOptions.length <= 1 && leagueGroups.length <= 1,
            content: (
                <div className="space-y-2 pb-2">
                    {!(hasStaticSeasons && seasonOptions.length <= 1) && (
                        <CustomSelect
                            value={selectedSeason?.season_id.toString() || "2026"}
                            onChange={(value) => setSelectedSeason(seasons.find(season => season.season_id === value) || null)}
                            options={seasonOptions}
                        />
                    )}
                    {!(hasStaticSports && sportOptions.length <= 1) && (
                        <CustomSelect
                            value={selectedSport?.id?.toString() || ""}
                            onChange={(value) => setSelectedSport(sports.find(sport => sport.id.toString() === value) || null)}
                            options={sportOptions}
                        />
                    )}
                    {leagueGroups.length > 1 && (
                        <CustomSelect
                            value={selectedLeagueGroup || ""}
                            onChange={(value) => setSelectedLeagueGroup(value || null)}
                            options={leagueGroups.map(group => ({ value: group, label: group }))}
                        />
                    )}
                </div>
            ),
        },
        {
            id: "navigation",
            title: "Navigation",
            collapsible: false,
            content: (
                <Tabs.List className="flex flex-col gap-1">
                    {tabs.map(tab => {
                        const isTeamsTab = tab.id === "teams";
                        return (
                            <div key={tab.id} className="space-y-1">
                                <div className="flex items-center gap-1">
                                    <Tabs.Trigger
                                        value={tab.id}
                                        className="relative flex flex-1 gap-x-2 items-center justify-start px-3 py-2.5 text-sm rounded-lg
                                                   data-[state=active]:bg-(--background-quaternary)
                                                   data-[state=active]:font-bold
                                                   data-[state=active]:text-(--showdown-red)
                                                   data-[state=inactive]:text-tertiary
                                                   data-[state=inactive]:font-medium
                                                   data-[state=inactive]:hover:bg-(--divider)"
                                    >
                                        <span className="text-(--text-secondary)">{tab.icon}</span>
                                        {tab.label}
                                    </Tabs.Trigger>

                                    {isTeamsTab && (
                                        <button
                                            type="button"
                                            aria-label={isTeamsNavOpen ? "Collapse teams list" : "Expand teams list"}
                                            onClick={(event) => {
                                                event.preventDefault();
                                                event.stopPropagation();
                                                setIsTeamsNavOpen((previous) => !previous);
                                            }}
                                            className="p-2 rounded-md text-(--text-secondary) hover:bg-(--divider) cursor-pointer"
                                        >
                                            <FaChevronDown className={`h-3.5 w-3.5 transition-transform ${isTeamsNavOpen ? "rotate-180" : ""}`} />
                                        </button>
                                    )}
                                </div>

                                {isTeamsTab && isTeamsNavOpen && (
                                    <div className="ml-3 pl-2 border-l border-(--divider)">
                                        {teams.length === 0 ? (
                                            <div className="px-2 py-1 text-xs text-(--text-secondary)">No teams available.</div>
                                        ) : (
                                            <div className="max-h-64 sm:max-h-128 overflow-y-auto space-y-1 pr-1">
                                                {teams.map((team) => {
                                                    const teamKey = `${team.id}-${team.season}`;
                                                    const isSelected = selectedTeamKey === teamKey && activeTab === "teams";
                                                    const isoCountryCode = countryCodeForTeam(selectedSport?.id || 0, team.abbreviation || team.name);
                                                    return (
                                                        <button
                                                            key={teamKey}
                                                            type="button"
                                                            onClick={() => {
                                                                setSelectedTeam(team);
                                                                setActiveTab("teams");
                                                            }}
                                                            className={`w-full text-left px-2 py-1.5 rounded-md text-xs transition-colors ${
                                                                isSelected
                                                                    ? "bg-(--background-quaternary) font-semibold"
                                                                        : "text-(--text-primary) hover:bg-(--divider) hover:text-(--team-hover-color)"
                                                            }`}
                                                            style={{
                                                                ["--team-hover-color" as string]: team.primary_color || "var(--text-primary)",
                                                                backgroundColor: isSelected ? team.primary_color || "var(--background-quaternary)" : "",
                                                                color: isSelected ? "white" : undefined,
                                                            
                                                            }}
                                                        >
                                                            <div className="flex items-center justify-between gap-2">
                                                                <div className="flex gap-1 items-center">
                                                                    {selectedSport?.id === 51 && isoCountryCode && (
                                                                        <ReactCountryFlag
                                                                            countryCode={isoCountryCode}
                                                                            svg
                                                                            style={{
                                                                                width: '1em',
                                                                                height: '1em',
                                                                                marginRight: '0.25em',
                                                                            }}
                                                                        />
                                                                    )}
                                                                    <span className="truncate">{team.abbreviation || team.name}</span>
                                                                </div>
                                                                
                                                                <span className="text-[10px] text-(--text-secondary)">{team.season || selectedSeason?.season_id}</span>
                                                            </div>
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </Tabs.List>
            ),
        },
    ];

    return (
        <div className="w-full bg-(--background-primary)">
            <div className="max-w-full mx-6 lg:mx-auto py-6 sm:py-8 lg:py-0 lg:h-[calc(100dvh-3rem)] lg:overflow-hidden">
                {selectedSeason && (
                    <>
                        <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="lg:h-full lg:min-h-0">
                            <div className="grid grid-cols-1 lg:grid-cols-[18.5rem_minmax(0,1fr)] gap-y-5 lg:h-full lg:min-h-0 lg:overflow-hidden">
                                <SidebarPanel
                                    title={title}
                                    subtitle={subtitle}
                                    sections={sidebarSections}
                                    className="p-2 order-1 lg:p-6 lg:sticky lg:top-0 lg:self-start lg:h-full lg:min-h-0 lg:overflow-y-auto"
                                />

                                <div className="min-w-0 order-2 lg:h-full lg:min-h-0 lg:overflow-y-auto lg:overscroll-contain lg:p-6">

                            		<Tabs.Content
                                        value="standings"
                                        className="focus:outline-none data-[state=inactive]:hidden"
                                        forceMount
                                    >
                                        <StandingsTab standingsEntries={standingsEntries} selectedSportId={selectedSport?.id} />
                                    </Tabs.Content>

                                    {/* Teams Tab */}
                                    <Tabs.Content
                                        value="teams"
                                        className="focus:outline-none data-[state=inactive]:hidden"
                                        forceMount
                                    >
                                        <div className="space-y-4">
                        
                                            {selectedTeam && (
                                                <div
                                                    className="rounded-lg border border-(--divider) p-4"
                                                    style={{
                                                        backgroundImage: `linear-gradient(120deg, color-mix(in srgb, ${selectedTeam.primary_color || "var(--background-primary)"} 12%, transparent) 0%, color-mix(in srgb, ${(selectedTeam.secondary_color || selectedTeam.primary_color || "var(--background-primary)")} 12%, transparent) 100%)`,
                                                    }}
                                                >
                                                    <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_auto] gap-4 items-start">
                                                        <div>
                                                            
                                                            <h2 className="flex gap-2 text-xl font-semibold text-(--text-primary)">
                                                                {selectedSport?.id === 51 && countryCodeForTeam(selectedSport.id, selectedTeam.abbreviation || selectedTeam.name) && (
                                                                    <ReactCountryFlag
                                                                        countryCode={countryCodeForTeam(selectedSport.id, selectedTeam.abbreviation || selectedTeam.name) || ""}
                                                                        svg
                                                                        style={{
                                                                            width: '1.5em',
                                                                            height: '1.5em',
                                                                            marginBottom: '-0.25em',
                                                                        }}
                                                                    />
                                                                )}
                                                                {selectedTeam.name}
                                                            </h2>
                                                            <p className="text-sm text-(--text-secondary)">
                                                                {selectedTeam.abbreviation || "N/A"} • {selectedTeam.season?.toString() || selectedSeason?.season_id || "N/A"}
                                                            </p>

                                                            <div className="mt-3 gap-2 text-sm">
                                                                <div className="text-(--text-secondary)">
                                                                    <span className="font-semibold">League:</span> {selectedTeam.league?.name || selectedTeam.league?.abbreviation || "N/A"}
                                                                </div>
                                                                <div className="text-(--text-secondary)">
                                                                    <span className="font-semibold">Division:</span> {selectedTeam.division?.name || selectedTeam.division?.name || "N/A"}
                                                                </div>
                                                            </div>
                                                        </div>

                                                        <div className="rounded-lg border border-(--divider) px-4 py-3 min-w-44">
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
                                            )}
                                            <TeamRoster roster={selectedRoster} />
        
                                        </div>
                                    </Tabs.Content>

                                    {/* Players Tab */}
                                    <Tabs.Content
                                        value="players"
                                        className="focus:outline-none data-[state=inactive]:hidden"
                                    >
                                        {seasons.length === 0 || sports.length === 0 || !selectedSeason || !selectedSeason.season_id ? (
                                            <div className="mt-5 rounded-xl border border-(--divider) bg-(--background-secondary) p-4 text-sm text-(--text-secondary)">
                                                No season or sport data available for player search.
                                            </div>
                                        ) : (
                                            <div className="mt-5 rounded-xl border border-(--divider) bg-(--background-secondary) p-3 sm:p-4">
                                                <ShowdownCardSearch
                                                    source="BOT"
                                                    defaultFilters={{
                                                        min_year: Number(selectedSeason.season_id),
                                                        max_year: Number(selectedSeason.season_id),
                                                    }}
                                                    disableLocalStorage={true}
                                                />
                                            </div>
                                        )}
                                    </Tabs.Content>

                                    {/* Games Tab - Only for ongoing seasons */}
                                    {selectedSeason && isMidSeason(selectedSeason) && (
                                        <Tabs.Content
                                            value="games"
                                            className="focus:outline-none data-[state=inactive]:hidden"
                                            forceMount
                                        >
                                            <div className="mt-5">
                                                <div className="bg-(--background-secondary) rounded-xl p-8 border border-(--divider) border-dashed text-center">
                                                    <p className="text-(--text-secondary)">
                                                        Game data coming soon
                                                    </p>
                                                </div>
                                            </div>
                                        </Tabs.Content>
                                    )}
                                </div>

                            </div>
                        </Tabs.Root>
                    </>
                )}
            </div>

            {isLoading && (
                <div className="
                    fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                    bg-(--primary)/10 backdrop-blur 
                    p-4 rounded-2xl
                    flex items-center space-x-2
                ">
                    <FaBaseball
                        className="
                            text-3xl
                            animate-bounce
                        "
                        style={{
                            animationDuration: '0.7s',
                            animationIterationCount: 'infinite'
                        }}
                    />
                </div>
            )}
        </div>
    );
}
