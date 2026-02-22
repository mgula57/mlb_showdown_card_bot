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

import { FaRankingStar, FaClipboardList, FaUserGroup, FaGamepad } from "react-icons/fa6";

export default function Seasons() {
    const STORAGE_KEYS = {
        seasonId: "seasons.selectedSeasonId",
        sportId: "seasons.selectedSportId",
        leagueGroup: "seasons.selectedLeagueGroup",
        activeTab: "seasons.activeTab",
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

    const [seasons, setSeasons] = useState<Season[]>([]);
    const [selectedSeason, setSelectedSeason] = useState<Season | null>(null);
    
    const [sports, setSports] = useState<Sport[]>([]);
    const [selectedSport, setSelectedSport] = useState<Sport | null>(null);

    const [leagues, setLeagues] = useState<League[]>([]);

    const [teams, setTeams] = useState<Team[]>([]);
    const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);

    const [selectedRoster, setSelectedRoster] = useState<Roster | null>(null);

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
    const hasLoadedSeasonsRef = useRef(false);
    const isLoadingSeasonsRef = useRef(false);

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
        if (hasLoadedSeasonsRef.current || isLoadingSeasonsRef.current) {
            return;
        }

        isLoadingSeasonsRef.current = true;
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
        }
    };

    const loadSports = async () => {
        if (!selectedSeason) {
            return;
        }

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
        }
    };

    const loadLeagues = async () => {
        if (!selectedSeason || !selectedSport) {
            return;
        }
        
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
        try {
            standingsData = await fetchSeasonStandings(selectedSeason, leaguesToQuery);
            console.log(`Fetched standings for season ${selectedSeason.season_id}:`, standingsData);
            setStandings(standingsData);
        } catch (error) {
            console.error(`Error fetching standings for season ${selectedSeason.season_id}:`, error);
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

        try {
            const rosterData = await fetchTeamRoster(selectedSeason, team.id, "active", userShowdownSet, selectedSport.id);
            console.log(`Fetched roster for team ${team.name} in season ${selectedSeason.season_id}:`, rosterData);
            setSelectedRoster(rosterData);
        } catch (error) {
            console.error(`Error fetching roster for team ${team.name} in season ${selectedSeason.season_id}:`, error);
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

    return (
        <div className="w-full bg-(--background-primary)">
            <div className="max-w-6xl mx-auto p-6">
                {/* Header with Season Dropdown */}
                <div className="mb-4 flex items-end justify-between">
                    <div>
                        <h1 className="text-4xl font-bold text-(--text-primary) mb-2">
                            MLB Seasons
                        </h1>

                        {/* Season Dropdown */}
                        <div className="flex gap-x-2 mr-4">
                            <CustomSelect
                                value={selectedSeason?.season_id.toString() || "2026"}
                                onChange={(value) => setSelectedSeason(seasons.find(season => season.season_id === value) || null)}
                                options={seasonOptions}
                            />
                            <CustomSelect
                                value={selectedSport?.id?.toString() || ""}
                                onChange={(value) => setSelectedSport(sports.find(sport => sport.id.toString() === value) || null)}
                                options={sportOptions}
                            />
                            {leagueGroups.length > 1 && (
                                <CustomSelect
                                    value={selectedLeagueGroup || ""}
                                    onChange={(value) => setSelectedLeagueGroup(value || null)}
                                    options={leagueGroups.map(group => ({ value: group, label: group }))}
                                />
                            )}
                        </div>
                    </div>
                </div>

                {selectedSeason && (
                    <>
                        {/* Tabs */}
                        <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
                            {/* Tab List */}
                            <Tabs.List className="flex px-3 border-b-2 pt-2 pb-1 border-form-element gap-x-2 h-12">
                                {tabs.map(tab => (
                                    <Tabs.Trigger
                                        key={tab.id}
                                        value={tab.id}
                                        className="relative flex gap-x-1 items-center px-4 py-3 text-sm rounded-lg
                                                   data-[state=active]:bg-(--background-quaternary) 
                                                   data-[state=active]:font-bold 
                                                   data-[state=active]:text-(--showdown-blue)
                                                   data-[state=inactive]:text-tertiary 
                                                   data-[state=inactive]:font-medium 
                                                   data-[state=inactive]:hover:bg-(--divider)"
                                    >
                                        <span className="text-(--text-secondary)">{tab.icon}</span>
                                        {tab.label}
                                    </Tabs.Trigger>
                                ))}
                            </Tabs.List>

                            {/* Standings Tab */}
                            <Tabs.Content
                                value="standings"
                                className="focus:outline-none data-[state=inactive]:hidden"
                                forceMount
                            >
                                <div className="mt-6">
                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                        {Object.entries(standings).map(([leagueAbbreviation, leagueStandings]) => (
                                            <div key={leagueAbbreviation} className="bg-(--background-secondary) rounded-lg overflow-hidden border border-(--divider)">
                                                <h2 className="text-xl font-semibold text-(--text-primary) bg-(--background-quaternary) px-4 py-2">
                                                    {leagueAbbreviation}
                                                </h2>

                                                {leagueStandings.map((leagueStanding, index) => (
                                                    <div key={index} className="border-t border-(--divider)">
                                                        {leagueStanding.division && (
                                                            <h3 className="px-4 py-2 text-sm font-semibold uppercase text-(--text-secondary)">
                                                                {leagueStanding?.division?.name_short || leagueStanding?.division?.name}
                                                            </h3>
                                                        )}
                                                        <table className="w-full text-left">
                                                            <thead>
                                                                <tr className="text-(--text-secondary) text-sm uppercase">
                                                                    <th className="px-4 py-2">Team</th>
                                                                    <th className="px-4 py-2">Wins</th>
                                                                    <th className="px-4 py-2">Losses</th>
                                                                    <th className="px-4 py-2">Win %</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                {leagueStanding.team_records?.map((record) => (
                                                                    <tr key={record.team.id} className="border-t border-(--divider)">
                                                                        <td className="px-4 py-2">{record.team.abbreviation}</td>
                                                                        <td className="px-4 py-2">{record.league_record.wins}</td>
                                                                        <td className="px-4 py-2">{record.league_record.losses}</td>
                                                                        <td className="px-4 py-2">{record.league_record.percentage || '-'}</td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                ))}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </Tabs.Content>

                            {/* Teams Tab */}
                            <Tabs.Content
                                value="teams"
                                className="focus:outline-none data-[state=inactive]:hidden"
                                forceMount
                            >
                                <div className="mt-6">
                                    <div className="w-64 max-w-full">
                                        <CustomSelect
                                            value={selectedTeam?.id?.toString() || ""}
                                            onChange={(value) => setSelectedTeam(teams.find(team => team.id.toString() === value) || null)}
                                            options={teams.map(team => ({ value: team.id.toString(), label: team.abbreviation || team.name }))}
                                        />
                                    </div>
                                    {selectedTeam && (
                                        <div className="mt-4">
                                            <div>
                                                <h2 className="text-xl font-semibold text-(--text-primary)">
                                                    {selectedTeam.name}
                                                </h2>
                                                <p className="text-sm text-(--text-secondary)">
                                                    {selectedTeam.abbreviation || "N/A"} • {selectedTeam.season?.toString() || selectedSeason?.season_id || "N/A"}
                                                </p>
                                            </div>

                                            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                                                <div className="text-(--text-secondary)">
                                                    <span className="font-semibold">League:</span> {selectedTeam.league?.name || selectedTeam.league?.abbreviation || "N/A"}
                                                </div>
                                                <div className="text-(--text-secondary)">
                                                    <span className="font-semibold">Division:</span> {selectedTeam.division?.name_short || selectedTeam.division?.name || "N/A"}
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
                                forceMount
                            >
                                <div className="mt-6">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        
                                    </div>
                                </div>
                            </Tabs.Content>

                            {/* Games Tab - Only for ongoing seasons */}
                            {selectedSeason && isMidSeason(selectedSeason) && (
                                <Tabs.Content
                                    value="games"
                                    className="focus:outline-none data-[state=inactive]:hidden"
                                    forceMount
                                >
                                    <div className="mt-6">
                                        <div className="bg-(--background-secondary) rounded-lg p-8 border border-(--divider) border-dashed text-center">
                                            <p className="text-(--text-secondary)">
                                                Game data coming soon
                                            </p>
                                        </div>
                                    </div>
                                </Tabs.Content>
                            )}
                        </Tabs.Root>
                    </>
                )}
            </div>
        </div>
    );
}
