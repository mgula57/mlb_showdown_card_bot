/**
 * @fileoverview Seasons - MLB Season Results with Showdown Context
 * 
 * Displays real MLB season results with Showdown context including
 * player cards, team points, and performance analytics.
 */
import { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { DayPicker } from "react-day-picker";
import "react-day-picker/style.css";
import * as Tabs from '@radix-ui/react-tabs';
import CustomSelect, { type SelectOption } from '../shared/CustomSelect';
import {
    fetchSeasons, fetchSeasonSports, fetchSeasonLeagues, fetchSeasonStandings, fetchTeamRoster,
    fetchSchedule, fetchSeasonTeams,
    type Season, type Sport, type League, type Standings, type Team, type Roster,
    type Schedule
} from '../../api/mlbAPI';
import { useSiteSettings } from "../shared/SiteSettingsContext";
import TeamRoster from "../teams/TeamRoster";
import SidebarPanel, { type SidebarSection } from "../shared/SidebarPanel";
import ReactCountryFlag from "react-country-flag";
import { countryCodeForTeam } from "../../functions/flags";
import StandingsTab from "./Standings";

import {
    FaRankingStar, FaClipboardList, FaEarthAmericas, FaCalendarDays,
    FaChevronDown, FaBaseball, FaChevronRight, FaChevronLeft,
    FaStar, FaRegStar, FaArrowsRotate, FaTrophy
} from "react-icons/fa6";

import ShowdownCardSearch from "../cards/ShowdownCardSearch";
import GameSchedule from "../games/GameSchedule";
import GameDetail from "../games/GameDetail";
import SeasonLeaders from "./SeasonLeaders";
import { getReadableTextColor } from "../../functions/colors";

const formatScheduleDate = (date?: string): string => {
    if (!date) {
        return "Today's Games";
    }

    const parsedDate = new Date(`${date}T00:00:00`);
    if (Number.isNaN(parsedDate.getTime())) {
        return "Today's Games";
    }

    return new Intl.DateTimeFormat(undefined, {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
    }).format(parsedDate);
};

const formatDateForApi = (date: Date): string => {
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    const day = `${date.getDate()}`.padStart(2, '0');
    return `${year}-${month}-${day}`;
};

const isSameCalendarDay = (a: Date, b: Date): boolean => {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
};

const formatGamesHeaderDate = (date: Date): string => {
    return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date).toUpperCase();
};

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
        sidebarCollapsed: `${type}.seasons.sidebarCollapsed`,
        starredTeams: `${type}.seasons.starredTeams`,
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

    const [gamesSchedule, setGamesSchedule] = useState<Schedule | null>(null);
    const [gamesDate, setGamesDate] = useState<Date>(() => {
        const now = new Date();
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    });
    const [selectedGamePk, setSelectedGamePk] = useState<number | null>(null);
    const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);
    const datePickerRef = useRef<HTMLDivElement>(null);

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

    const [activeTab, setActiveTab] = useState<string>(() => getStoredValue(STORAGE_KEYS.activeTab) ?? "schedule");

    // Open a specific game if ?gamePk=XXX is in the URL (e.g. linked from Home ticker)
    const location = useLocation();
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const gamePkParam = params.get('gamePk');
        if (gamePkParam) {
            const pk = parseInt(gamePkParam, 10);
            if (!isNaN(pk)) {
                setSelectedGamePk(pk);
                setActiveTab('schedule');
            }
        }
    }, [location.search]);

    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(() => getStoredValue(STORAGE_KEYS.sidebarCollapsed) === "true");
    const [starredTeamKeys, setStarredTeamKeys] = useState<string[]>(() => {
        const stored = getStoredValue(STORAGE_KEYS.starredTeams);
        if (!stored) {
            return [];
        }

        try {
            const parsed = JSON.parse(stored);
            return Array.isArray(parsed) ? parsed.filter((value): value is string => typeof value === 'string') : [];
        } catch {
            return [];
        }
    });
    const [isTeamsNavOpen, setIsTeamsNavOpen] = useState<boolean>(true);
    const hasLoadedSeasonsRef = useRef(false);
    const isLoadingSeasonsRef = useRef(false);
    const pendingRequestsRef = useRef(0);
    const isRunningLoadAllRef = useRef(false);
    const scheduleAbortControllerRef = useRef<AbortController | null>(null);

    // Close date picker when clicking outside
    useEffect(() => {
        if (!isDatePickerOpen) return;
        const handleClickOutside = (event: MouseEvent) => {
            if (datePickerRef.current && !datePickerRef.current.contains(event.target as Node)) {
                setIsDatePickerOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [isDatePickerOpen]);

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

    const teamOptions: SelectOption[] = teams
        .map((team) => {
            const teamKey = `${team.id}-${team.season}`;
            const isStarred = starredTeamKeys.includes(teamKey);
            const teamLabel = `${isStarred ? '★ ' : ''}${team.abbreviation || team.name}${team.season ? ` (${team.season})` : ""}`;
            return {
                value: teamKey,
                label: teamLabel,
            };
        })
        .sort((a, b) => {
            const aStarred = starredTeamKeys.includes(a.value);
            const bStarred = starredTeamKeys.includes(b.value);
            if (aStarred !== bStarred) {
                return aStarred ? -1 : 1;
            }
            return a.label.localeCompare(b.label);
        });

    const sortedTeams = [...teams].sort((a, b) => {
        const aKey = `${a.id}-${a.season}`;
        const bKey = `${b.id}-${b.season}`;
        const aStarred = starredTeamKeys.includes(aKey);
        const bStarred = starredTeamKeys.includes(bKey);
        if (aStarred !== bStarred) {
            return aStarred ? -1 : 1;
        }
        return (a.abbreviation || a.name || "").localeCompare(b.abbreviation || b.name || "");
    });

    const tabs = [
        { id: "schedule", label: "Schedule", icon: <FaCalendarDays /> },
        { id: "standings", label: "Standings", icon: <FaRankingStar /> },
        { id: "leaders", label: "Leaders", icon: <FaTrophy /> },
        { id: "teams", label: "Teams", icon: <FaClipboardList /> },
        // { id: "players", label: "Players", icon: <FaUserGroup /> },
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
        let standingsFailed = false;
        beginLoading();
        try {
            standingsData = await fetchSeasonStandings(selectedSeason, leaguesToQuery, userShowdownSet);
            console.log(`Fetched standings for season ${selectedSeason.season_id}:`, standingsData);
            setStandings(standingsData);
        } catch (error) {
            console.error(`Error fetching standings for season ${selectedSeason.season_id}:`, error);
            standingsFailed = true;
        } finally {
            endLoading();
        }

        // Populate Teams for Teams Tab
        let allTeams: Team[] = [];
        Object.values(standingsData).forEach((leagueStandings) => {
            leagueStandings.forEach((standing) => {
                standing.team_records?.forEach((record) => {
                    allTeams.push(record.team);
                });
            });
        });

        if (standingsFailed || allTeams.length === 0) {
            // Standings endpoint unavailable; fetch teams directly
            const fetched = await Promise.all(
                leaguesToQuery.map(league =>
                    fetchSeasonTeams(selectedSeason, league, selectedSport?.id ?? 1).catch(() => [] as Team[])
                )
            );
            allTeams = fetched.flat();
        }
        allTeams.sort((a, b) => (a.abbreviation || "").localeCompare(b.abbreviation || ""));
        // Check if currently selected team still exists in the new data, otherwise set to first value
        setSelectedTeam((prevTeam) => {
            if (prevTeam && allTeams.some((team) => (`${team.id}-${team.season}` === `${prevTeam.id}-${prevTeam.season}`))) {
                return prevTeam;
            }
            return allTeams.sort(
                // Sort by starred first, then alphabetically by abbreviation
                (a, b) => {
                    const aStarred = starredTeamKeys.includes(`${a.id}-${a.season}`);
                    const bStarred = starredTeamKeys.includes(`${b.id}-${b.season}`);
                    if (aStarred && !bStarred) return -1;
                    if (!aStarred && bStarred) return 1;
                    return (a.abbreviation || "").localeCompare(b.abbreviation || "");
                }
            )[0] || null;
        });
        console.log("All teams extracted from standings:", allTeams);
        setTeams(allTeams);
    };

    const loadAll = async () => {
        if (!selectedSeason) return;

        isRunningLoadAllRef.current = true;
        beginLoading();
        try {
            // 1. Resolve sport (without waiting for state to settle)
            let resolvedSport: Sport | null = null;
            if (hasStaticSports) {
                const storedSportId = getStoredValue(STORAGE_KEYS.sportId);
                resolvedSport = storedSportId
                    ? (staticSports!.find(s => s.id.toString() === storedSportId) ?? staticSports![0] ?? null)
                    : (staticSports![0] ?? null);
                setSelectedSport(resolvedSport);
            } else {
                const sportsData = await fetchSeasonSports(selectedSeason);
                setSports(sportsData);
                const storedSportId = getStoredValue(STORAGE_KEYS.sportId);
                resolvedSport = storedSportId
                    ? (sportsData.find(s => s.id.toString() === storedSportId) ?? sportsData[0] ?? null)
                    : (sportsData[0] ?? null);
                setSelectedSport(resolvedSport);
            }

            if (!resolvedSport) return;

            // 2. Resolve leagues
            const resolvedLeagues = await fetchSeasonLeagues(selectedSeason, resolvedSport);
            const resolvedLeagueGroups = Array.from(
                new Set(
                    resolvedLeagues
                        .map(league => getLeagueGroupForLeague(league))
                        .filter((g): g is string => g !== null && g !== "Spring Training")
                        
                )
            );
            console.log("Unique league groups identified:", resolvedLeagueGroups);
            const resolvedLeagueGroup = resolvedLeagueGroups.length > 1
                ? (() => {
                    const stored = getStoredValue(STORAGE_KEYS.leagueGroup);
                    return stored && resolvedLeagueGroups.includes(stored) ? stored : resolvedLeagueGroups[0];
                })()
                : null;

            setLeagueGroups(resolvedLeagueGroups);
            setSelectedLeagueGroup(resolvedLeagueGroup);
            setLeagues(resolvedLeagues);

            // 3. Determine filtered leagues
            const shouldFilter = resolvedLeagueGroups.length > 1 && resolvedLeagueGroup !== null;
            const leaguesToQuery = shouldFilter
                ? resolvedLeagues.filter(l => getLeagueGroupForLeague(l) === resolvedLeagueGroup)
                : resolvedLeagues;

            if (leaguesToQuery.length === 0) return;

            const selectedDate = formatDateForApi(gamesDate);

            // 4. Parallel: standings + todaysSchedule + gamesSchedule
            const [standingsData] = await Promise.all([
                fetchSeasonStandings(selectedSeason, leaguesToQuery, userShowdownSet)
                    .then(data => {
                        setStandings(data);
                        return data;
                    })
                    .catch(error => {
                        console.error(`Standings fetch failed, will fall back to teams endpoint:`, error);
                        return {} as { [leagueAbbreviation: string]: Standings[] };
                    }),
                fetchSchedule(resolvedSport.id, selectedSeason, selectedDate, leaguesToQuery, userShowdownSet)
                    .then(data => {
                        setGamesSchedule(data);
                        console.log(`Fetched games schedule for season ${selectedSeason.season_id} on date ${selectedDate}:`, data);
                        return data;
                    })
                    .catch(() => setGamesSchedule(null)),
            ]);

            // 5. Populate teams from standings, or fetch separately if standings failed
            let allTeams: Team[] = [];
            Object.values(standingsData).forEach(leagueStandings => {
                leagueStandings.forEach(standing => {
                    standing.team_records?.forEach(record => allTeams.push(record.team));
                });
            });

            if (allTeams.length === 0) {
                // Standings endpoint unavailable; fetch teams directly
                const fetched = await Promise.all(
                    leaguesToQuery.map(league =>
                        fetchSeasonTeams(selectedSeason, league, resolvedSport.id).catch(() => [] as Team[])
                    )
                );
                allTeams = fetched.flat();
            }

            allTeams.sort((a, b) => (a.abbreviation || "").localeCompare(b.abbreviation || ""));
            setTeams(allTeams);
            setSelectedTeam(prevTeam => {
                if (prevTeam && allTeams.some(t => `${t.id}-${t.season}` === `${prevTeam.id}-${prevTeam.season}`)) {
                    return prevTeam;
                }
                return allTeams.sort((a, b) => {
                    const aStarred = starredTeamKeys.includes(`${a.id}-${a.season}`);
                    const bStarred = starredTeamKeys.includes(`${b.id}-${b.season}`);
                    if (aStarred !== bStarred) return aStarred ? -1 : 1;
                    return (a.abbreviation || "").localeCompare(b.abbreviation || "");
                })[0] ?? null;
            });

        } catch (error) {
            console.error(`Error in loadAll for season ${selectedSeason.season_id}:`, error);
        } finally {
            isRunningLoadAllRef.current = false;
            endLoading();
        }
    };

    const loadTeamRoster = async (team: Team) => {
        if (!selectedSeason || !selectedSport || !team) {
            return;
        }

        beginLoading();
        try {
            const rosterType = "active";
            const rosterData = await fetchTeamRoster(selectedSeason, team.id, rosterType, selectedSport.id, team.abbreviation || team.name);
            console.log(`Fetched roster for team ${team.name} in season ${selectedSeason.season_id}:`, rosterData);
            setSelectedRoster(rosterData);
        } catch (error) {
            console.error(`Error fetching roster for team ${team.name} in season ${selectedSeason.season_id}:`, error);
        } finally {
            endLoading();
        }
    };

    const loadGamesSchedule = async () => {
        if (!selectedSeason || leagues.length === 0) {
            setGamesSchedule(null);
            return;
        }

        const shouldFilterByLeagueGroup = leagueGroups.length > 1 && selectedLeagueGroup !== null;
        const leaguesToQuery = shouldFilterByLeagueGroup
            ? leagues.filter((league) => getLeagueGroupForLeague(league) === selectedLeagueGroup)
            : leagues;

        if (leaguesToQuery.length === 0) {
            setGamesSchedule(null);
            return;
        }

        // Cancel any in-flight schedule request
        scheduleAbortControllerRef.current?.abort();
        const controller = new AbortController();
        scheduleAbortControllerRef.current = controller;

        beginLoading();
        try {
            const selectedDate = formatDateForApi(gamesDate);
            const scheduleData = await fetchSchedule(selectedSport?.id || 1, selectedSeason, selectedDate, leaguesToQuery, userShowdownSet, controller.signal);
            setGamesSchedule(scheduleData);
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                return;
            }
            console.error(`Error fetching games schedule for season ${selectedSeason.season_id}:`, error);
            setGamesSchedule(null);
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

    // Single orchestrated load: sports → leagues → standings + schedules in parallel
    useEffect(() => {
        if (!selectedSeason) return;
        loadAll();
    }, [selectedSeason]);

    // Re-run standings + both schedules when user changes league group or showdown set
    useEffect(() => {
        if (isRunningLoadAllRef.current || !selectedSeason || leagues.length === 0) return;
        loadStandings();
        loadGamesSchedule();
    }, [selectedLeagueGroup, userShowdownSet]);

    // Re-run only games schedule when selected date changes
    useEffect(() => {
        if (!selectedSeason || leagues.length === 0) return;
        loadGamesSchedule();
    }, [gamesDate]);

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
        setStoredValue(STORAGE_KEYS.sidebarCollapsed, isSidebarCollapsed ? "true" : "false");
    }, [isSidebarCollapsed]);

    useEffect(() => {
        setStoredValue(STORAGE_KEYS.starredTeams, JSON.stringify(starredTeamKeys));
    }, [starredTeamKeys]);

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
        if (selectedTeam === null || selectedTeam.id === undefined) {
            return;
        }
        loadTeamRoster(selectedTeam);
    }, [selectedTeam, userShowdownSet]);

    const selectedTeamKey = selectedTeam ? `${selectedTeam.id}-${selectedTeam.season}` : null;
    const isSelectedTeamStarred = selectedTeamKey ? starredTeamKeys.includes(selectedTeamKey) : false;
    const standingsEntries = Object.entries(standings);

    const gamesScheduleDates = gamesSchedule?.dates ?? [];
    const gamesTabGames = gamesScheduleDates.flatMap((scheduleDate) => scheduleDate.games ?? []);
    const gamesTabDateLabel = formatScheduleDate(gamesScheduleDates[0]?.date || formatDateForApi(gamesDate));
    const gamesTabDescription = gamesTabGames[0]?.series_description || gamesTabGames[0]?.description || "";
    const today = new Date();
    const isGamesDateToday = isSameCalendarDay(gamesDate, today);
    const gamesHeaderTopText = isGamesDateToday ? "TODAY" : new Intl.DateTimeFormat(undefined, { weekday: 'short' }).format(gamesDate).toUpperCase();
    const gamesHeaderBottomText = formatGamesHeaderDate(gamesDate);

    const handleStandingsTeamSelect = (team: Team) => {
        const matchedTeam = teams.find((existingTeam) => {
            const sameId = existingTeam.id === team.id;
            const sameSeason = `${existingTeam.season ?? ""}` === `${team.season ?? ""}`;
            return sameId && sameSeason;
        })
            ?? teams.find((existingTeam) => existingTeam.id === team.id)
            ?? team;

        setSelectedTeam(matchedTeam);
        setActiveTab("teams");
    };

    const toggleStarTeam = (team: Team) => {
        const teamKey = `${team.id}-${team.season}`;
        setStarredTeamKeys((previous) => (
            previous.includes(teamKey)
                ? previous.filter((key) => key !== teamKey)
                : [...previous, teamKey]
        ));
    };

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
                                                   data-[state=active]:text-(--showdown-blue)
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
                                                {sortedTeams.map((team) => {
                                                    const teamKey = `${team.id}-${team.season}`;
                                                    const isSelected = selectedTeamKey === teamKey && activeTab === "teams";
                                                    const isStarred = starredTeamKeys.includes(teamKey);
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
                                                                        : "text-(--text-primary) hover:bg-(--team-primary-color) hover:text-(--team-hover-text-color)"
                                                            }`}
                                                            style={{
                                                                ["--team-primary-color" as string]: team.primary_color || "var(--divider)",
                                                                ["--team-hover-text-color" as string]: team.primary_color ? getReadableTextColor(team.primary_color, "#ffffff") : "var(--text-primary)",
                                                                backgroundColor: isSelected ? team.primary_color || "var(--background-quaternary)" : "",
                                                                color: isSelected
                                                                    ? (team.primary_color ? getReadableTextColor(team.primary_color, "#ffffff") : "white")
                                                                    : undefined,
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
                                                                
                                                                <div className="flex items-center gap-1">
                                                                    <span
                                                                        role="button"
                                                                        tabIndex={0}
                                                                        aria-label={isStarred ? `Unstar ${team.abbreviation || team.name}` : `Star ${team.abbreviation || team.name}`}
                                                                        onClick={(event) => {
                                                                            event.preventDefault();
                                                                            event.stopPropagation();
                                                                            toggleStarTeam(team);
                                                                        }}
                                                                        onKeyDown={(event) => {
                                                                            if (event.key === "Enter" || event.key === " ") {
                                                                                event.preventDefault();
                                                                                event.stopPropagation();
                                                                                toggleStarTeam(team);
                                                                            }
                                                                        }}
                                                                        className={`text-sm leading-none cursor-pointer ${isStarred ? 'text-yellow-300' : 'text-(--quaternary) hover:text-yellow-300'}`}
                                                                    >
                                                                        {isStarred ? <FaStar className="h-3.5 w-3.5" /> : <FaRegStar className="h-3.5 w-3.5" />}
                                                                    </span>
                                                                    <span className="text-[10px] text-(--text-secondary)">{team.season || selectedSeason?.season_id}</span>
                                                                </div>
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
            <div className="max-w-full mx-6 lg:mx-auto py-6 sm:py-0 lg:h-[calc(100dvh-3rem)] lg:overflow-hidden">
                {selectedSeason && (
                    <>
                        <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="lg:h-full lg:min-h-0">
                            <div className={`grid grid-cols-1 ${isSidebarCollapsed ? 'lg:grid-cols-[3.25rem_minmax(0,1fr)]' : 'lg:grid-cols-[18.5rem_minmax(0,1fr)]'} transition-[grid-template-columns] duration-300 ease-in-out gap-y-5 lg:h-full lg:min-h-0 lg:overflow-hidden`}>
                                <div className={`hidden lg:block order-1 lg:h-full lg:min-h-0 overflow-hidden transition-[max-height,opacity] duration-300 ease-in-out ${isSidebarCollapsed ? 'max-h-16' : 'max-h-480'} lg:max-h-480`}>
                                    {isSidebarCollapsed ? (
                                        <aside className="w-full p-2 lg:pt-6 lg:sticky lg:top-0 lg:self-start lg:min-h-0">
                                            <div className="rounded-2xl border border-(--divider) bg-(--background-secondary) overflow-hidden lg:h-full">
                                                <div className="px-2 py-2 lg:py-3 flex items-center justify-center lg:items-start lg:justify-center">
                                                    <button
                                                        type="button"
                                                        onClick={() => setIsSidebarCollapsed(false)}
                                                        className="p-2 rounded-full text-(--text-secondary) hover:bg-(--divider) cursor-pointer flex items-center justify-center gap-2"
                                                        aria-label="Expand sidebar panel"
                                                        title="Expand sidebar panel"
                                                    >
                                                        <FaChevronRight className="h-3.5 w-3.5" />
                                                        <span className="lg:hidden text-xs font-semibold uppercase tracking-wide">
                                                            Show WBC Navigation
                                                        </span>
                                                    </button>
                                                </div>
                                            </div>
                                        </aside>
                                    ) : (
                                        <SidebarPanel
                                            title={title}
                                            subtitle={subtitle}
                                            sections={sidebarSections}
                                            className="p-2 lg:p-6 lg:sticky lg:top-0 lg:self-start lg:h-full lg:min-h-0 lg:overflow-y-auto"
                                            headerAction={(
                                                <div className="flex items-center gap-1">
                                                    <button
                                                        type="button"
                                                        onClick={() => loadAll()}
                                                        disabled={isLoading}
                                                        className="p-2 rounded-full text-(--text-secondary) hover:bg-(--divider) cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                                                        aria-label="Refresh data"
                                                        title="Refresh data"
                                                    >
                                                        <FaArrowsRotate className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
                                                    </button>
                                                    <button
                                                        type="button"
                                                        onClick={() => setIsSidebarCollapsed(true)}
                                                        className="p-2 rounded-full text-(--text-secondary) hover:bg-(--divider) cursor-pointer"
                                                        aria-label="Collapse sidebar panel"
                                                        title="Collapse sidebar panel"
                                                    >
                                                        <FaChevronLeft className="h-3.5 w-3.5" />
                                                    </button>
                                                </div>
                                            )}
                                        />
                                    )}
                                </div>

                                <div className="min-w-0 order-2 lg:h-full lg:min-h-0 lg:overflow-y-auto lg:overscroll-contain">
                                    <div className="lg:hidden mb-4 rounded-2xl space-y-4">
                                        <div className="space-y-2">
                                            {hasStaticSports && sportOptions.length <= 1 && selectedSport && (
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center font-bold text-2xl">
                                                        {type === "wbc" ? <FaEarthAmericas className="inline-block mr-2" /> : <FaCalendarDays className="inline-block mr-2" />}
                                                        {title}
                                                    </div>
                                                    <button
                                                        type="button"
                                                        onClick={() => loadAll()}
                                                        disabled={isLoading}
                                                        className="p-2 rounded-full text-(--text-secondary) hover:bg-(--divider) cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                                                        aria-label="Refresh data"
                                                        title="Refresh data"
                                                    >
                                                        <FaArrowsRotate className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
                                                    </button>
                                                </div>
                                            )}
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

                                        <Tabs.List
                                            className="flex gap-1 rounded-lg bg-(--background-tertiary) p-1 overflow-x-auto scrollbar-hide"
                                        >
                                            {tabs.map((tab) => (
                                                <Tabs.Trigger
                                                    key={tab.id}
                                                    value={tab.id}
                                                    className="flex flex-1 min-w-fit items-center justify-center gap-1.5 px-3 py-2 text-xs rounded-md whitespace-nowrap transition-colors duration-150
                                                               data-[state=active]:bg-(--showdown-blue) data-[state=active]:text-white data-[state=active]:font-semibold data-[state=active]:shadow-sm
                                                               data-[state=inactive]:text-tertiary data-[state=inactive]:hover:text-secondary"
                                                >
                                                    <span>{tab.icon}</span>
                                                    <span>{tab.label}</span>
                                                </Tabs.Trigger>
                                            ))}
                                        </Tabs.List>

                                        {activeTab === "teams" && (
                                            <CustomSelect
                                                value={selectedTeamKey ?? ""}
                                                onChange={(value) => {
                                                    const team = teams.find((candidate) => `${candidate.id}-${candidate.season}` === value) ?? null;
                                                    setSelectedTeam(team);
                                                }}
                                                options={teamOptions}
                                            />
                                        )}
                                    </div>

                                    {/* Standings Tab */}
                            		<Tabs.Content
                                        value="standings"
                                        className="focus:outline-none data-[state=inactive]:hidden"
                                        forceMount
                                    >
                                        <div className="space-y-2 pb-24 lg:pt-6 lg:pr-6">
                                            <StandingsTab
                                                standingsEntries={standingsEntries}
                                                selectedSportId={selectedSport?.id}
                                                onTeamSelect={handleStandingsTeamSelect}
                                            />
                                            
                                        </div>
                                    </Tabs.Content>

                                    {/* Schedule Tab - Only for ongoing seasons */}
                                    <Tabs.Content
                                        value="schedule"
                                        className="focus:outline-none data-[state=inactive]:hidden"
                                        forceMount
                                    >
                                        {selectedGamePk !== null ? (
                                            <GameDetail
                                                gamePk={selectedGamePk}
                                                sportId={selectedSport?.id}
                                                season={selectedSeason?.season_id ? parseInt(selectedSeason.season_id) : undefined}
                                                showdownSet={userShowdownSet}
                                                isActive={activeTab === 'schedule'}
                                                className="lg:py-6 lg:pr-6"
                                                onBack={() => setSelectedGamePk(null)}
                                            />
                                        ) : (
                                        <div className="space-y-5 lg:pt-6 lg:pr-6">
                                                <div className="rounded-xl border border-(--divider) bg-(--background-secondary) px-4 py-3">
                                                    <div className="flex items-center justify-between">
                                                        <button
                                                            type="button"
                                                            onClick={() => {
                                                                setGamesDate((previous) => {
                                                                    const next = new Date(previous);
                                                                    next.setDate(next.getDate() - 1);
                                                                    return next;
                                                                });
                                                            }}
                                                            className="p-2 rounded-full text-(--text-secondary) hover:bg-(--divider) cursor-pointer"
                                                            aria-label="Previous date"
                                                        >
                                                            <FaChevronLeft className="h-5 w-5" />
                                                        </button>

                                                        <div className="relative" ref={datePickerRef}>
                                                            <button
                                                                type="button"
                                                                onClick={() => setIsDatePickerOpen((prev) => !prev)}
                                                                className="flex flex-col items-center text-center leading-tight hover:opacity-70 transition-opacity cursor-pointer group"
                                                                aria-label="Pick a date"
                                                            >
                                                                <div className="text-sm font-extrabold tracking-wide text-(--text-secondary)">{gamesHeaderTopText}</div>
                                                                <div className="flex items-center gap-1">
                                                                    <span className="text-xl font-black text-(--text-primary)">{gamesHeaderBottomText}</span>
                                                                    <FaChevronDown className={`h-3 w-3 text-(--text-secondary) transition-transform ${isDatePickerOpen ? 'rotate-180' : ''}`} />
                                                                </div>
                                                            </button>
                                                            {isDatePickerOpen && (
                                                                <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50 rounded-xl border border-(--divider) bg-(--background-secondary) shadow-xl p-2">
                                                                    <DayPicker
                                                                        mode="single"
                                                                        selected={gamesDate}
                                                                        onSelect={(day) => {
                                                                            if (day) {
                                                                                setGamesDate(new Date(day.getFullYear(), day.getMonth(), day.getDate()));
                                                                                setIsDatePickerOpen(false);
                                                                            }
                                                                        }}
                                                                        defaultMonth={gamesDate}
                                                                    />
                                                                </div>
                                                            )}
                                                        </div>

                                                        <button
                                                            type="button"
                                                            onClick={() => {
                                                                setGamesDate((previous) => {
                                                                    const next = new Date(previous);
                                                                    next.setDate(next.getDate() + 1);
                                                                    return next;
                                                                });
                                                            }}
                                                            className="p-2 rounded-full text-(--text-secondary) hover:bg-(--divider) cursor-pointer"
                                                            aria-label="Next date"
                                                        >
                                                            <FaChevronRight className="h-5 w-5" />
                                                        </button>
                                                    </div>
                                                </div>

                                                <GameSchedule
                                                    games={gamesTabGames}
                                                    dateLabel={gamesTabDateLabel}
                                                    description={gamesTabDescription}
                                                    sportId={selectedSport?.id}
                                                    season={selectedSeason?.season_id ? parseInt(selectedSeason.season_id) : undefined}
                                                    showdownSet={userShowdownSet}
                                                    starredTeamIds={new Set(starredTeamKeys.map((key) => parseInt(key.split('-')[0], 10)))}
                                                    onGameSelect={(gamePk) => setSelectedGamePk(gamePk)}
                                                    onRefresh={() => {
                                                        // Force re-fetch games schedule for the current date
                                                        setGamesDate((previous) => new Date(previous));
                                                    }}
                                                />
                                            </div>
                                        )}
                                    </Tabs.Content>

                                    {/* Teams Tab */}
                                    <Tabs.Content
                                        value="teams"
                                        className="focus:outline-none data-[state=inactive]:hidden"
                                    >
                                        <div className="lg:pt-6 lg:pr-6">
                                            {selectedTeam && (
                                                <TeamRoster
                                                    team={selectedTeam}
                                                    sportId={selectedSport?.id || null}
                                                    roster={selectedRoster}
                                                    isStarred={isSelectedTeamStarred}
                                                    season={Number(selectedSeason.season_id)}
                                                    loadShowdownCards={true}
                                                    onToggleStar={() => toggleStarTeam(selectedTeam)}
                                                />
                                            )}
                                        </div>
                                    </Tabs.Content>

                                    {/* Leaders Tab */}
                                    <Tabs.Content
                                        value="leaders"
                                        className="focus:outline-none data-[state=inactive]:hidden"
                                    >
                                        <div className="lg:pt-6">
                                            <SeasonLeaders
                                                seasonId={selectedSeason.season_id}
                                                season={selectedSeason.season_id ? parseInt(selectedSeason.season_id) : 2026}
                                                showdownSet={userShowdownSet}
                                                sportId={selectedSport?.id}
                                                isActive={activeTab === 'leaders'}
                                            />
                                        </div>
                                    </Tabs.Content>

                                    {/* Players Tab */}
                                    <Tabs.Content
                                        value="players"
                                        className="focus:outline-none data-[state=inactive]:hidden"
                                    >
                                        {/* {hasLoadedTeams && (
                                            <ShowdownCardSearch
                                                source="WBC"
                                                verticalOffset="12"
                                                defaultFilters={{
                                                    min_year: Number(selectedSeason.season_id) - 1,
                                                    max_year: Number(selectedSeason.season_id) - 1,
                                                }}
                                                disableLocalStorage={true}
                                            />
                                        )} */}
                                        <div className="flex justify-center p-24 text-2xl">
                                            <span className="p-12 rounded-lg bg-secondary">Coming soon - once 2026 stats mature!</span>
                                        </div>
                                    </Tabs.Content>

                                </div>

                            </div>
                        </Tabs.Root>
                    </>
                )}
            </div>

            {isLoading && activeTab !== "players" && (
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
