import { Link } from 'react-router-dom';
import {
    FaBolt, FaChevronRight, FaChevronDown, FaShieldAlt,
    FaUsers, FaFire, FaDiceD20, FaStar
} from 'react-icons/fa';
import { useState, useEffect, useRef } from 'react';
import { useTheme } from './shared/SiteSettingsContext';
import { useSiteSettings } from './shared/SiteSettingsContext';
import { fetchTodaysSchedule, fetchSeasons, fetchSeasonLeaders } from '../api/mlbAPI';
import type { GameScheduled, Season, LeadersGroup } from '../api/mlbAPI';

// Modal
import { Modal } from './shared/Modal';

// Create Card Sampler
import { PlayerSearchInput } from './customs/PlayerSearchInput';
import type { PlayerSearchSelection } from './customs/PlayerSearchInput';

// Card Components
import { CardItemFromCard } from './cards/CardItem';
import CardCommand from './cards/card_elements/CardCommand';
import CardChart from './cards/card_elements/CardChart';
import type { ShowdownBotCard, ShowdownBotCardAPIResponse } from '../api/showdownBotCard';
import { CardDetail } from './cards/CardDetail';
import { getReadableTextColor } from '../functions/colors';

// API
import { fetchCardById, buildCardsFromIds } from '../api/showdownBotCard';
import { fetchTotalCardCount, fetchTrendingPlayers, fetchPopularCards, fetchSpotlightCards, fetchCardOfTheDay } from '../api/card_db/cardDatabase';
import type { PopularCardRecord, TrendingCardRecord, SpotlightCardRecord, CardOfTheDayRecord } from '../api/card_db/cardDatabase';

export default function Home() {

    // State
    const [searchQuery, _] = useState<string>('');
    const [selectedCard, setSelectedCard] = useState<ShowdownBotCard | null>(null);
    const [isLoadingSearchCard, setIsLoadingSearchCard] = useState<boolean>(false);
    const [isRefreshingTrends, setIsRefreshingTrends] = useState<boolean>(false);
    const [selectedModalCard, setSelectedModalCard] = useState<ShowdownBotCard | null>(null);

    // Today's games ticker
    const [todaysGames, setTodaysGames] = useState<GameScheduled[]>([]);
    const [tickerSeason, setTickerSeason] = useState<Season | null>(null);
    const [isLoadingGames, setIsLoadingGames] = useState<boolean>(false);
    const [starredTeamKeys] = useState<string[]>(() => {
        try {
            const stored = window.localStorage.getItem('mlb.seasons.starredTeams');
            return stored ? JSON.parse(stored) : [];
        } catch { return []; }
    });

    // Ticker leaders
    const [leaderGroups, setLeaderGroups] = useState<LeadersGroup[]>([]);
    const [isLoadingLeaders, setIsLoadingLeaders] = useState<boolean>(false);
    const [leaderCards, setLeaderCards] = useState<{ [playerId: string]: ShowdownBotCard }>({});

    const LEADER_CATEGORY_LABELS: Record<string, string> = {
        onBasePlusSlugging:          'OPS Leaders',
        walksAndHitsPerInningPitched: 'WHIP Leaders',
    };

    // Trends
    const [totalCardCount, setTotalCardCount] = useState<number | null>(null);
    const [trendingPlayers, setTrendingPlayers] = useState<TrendingCardRecord[]>([]);
    const [popularCards, setPopularCards] = useState<PopularCardRecord[]>([]);
    const [spotlightCards, setSpotlightCards] = useState<SpotlightCardRecord[]>([]);
    const [cardOfTheDay, setCardOfTheDay] = useState<CardOfTheDayRecord | null>(null);

    // Theme & Settings
    const { isDark } = useTheme();
    const { userShowdownSet } = useSiteSettings();

    // Track if we've loaded settings from localStorage
    const hasLoadedSettings = useRef(false);

    // Styling
    const gradientBlueBg = isDark ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30' : 'bg-gradient-to-r from-blue-100 to-purple-100 border border-blue-300'
    const cardOfDayPlaceholder = `/images/blank_players/blankplayer-${userShowdownSet.toLowerCase()}-${isDark ? 'dark' : 'light'}.png`;
    const cardOfDayImageSrc = cardOfTheDay?.card_data.image.output_folder_path ? `${cardOfTheDay.card_data.image.output_folder_path}/${cardOfTheDay.card_data.image.output_file_name}` : cardOfDayPlaceholder;

    // Fetch today's games + leaders for the ticker
    useEffect(() => {
        setIsLoadingGames(true);
        fetchSeasons().then(seasons => {
            const today = new Date();
            const active = seasons.find(s => {
                const start = new Date(s.regular_season_start_date);
                const end = new Date(s.season_end_date);
                return today >= start && today <= end;
            });
            if (!active) { setIsLoadingGames(false); return; }
            setTickerSeason(active);

            const gamesPromise = fetchTodaysSchedule(1, active).then(schedule => {
                const games: GameScheduled[] = [];
                schedule.dates?.forEach(d => d.games?.forEach(g => games.push(g)));
                setTodaysGames(games);
            });

            setIsLoadingLeaders(true);
            const leadersPromise = fetchSeasonLeaders(active.season_id, ['ON_BASE_PLUS_SLUGGING', 'WALKS_HITS_PER_INNING_PITCHED'], 3)
                .then(({ leaders }) => {
                    const seenCategories = new Set<string>();
                    const deduped = leaders.filter(g => {
                        const key = g.leader_category ?? '';
                        if (seenCategories.has(key)) return false;
                        seenCategories.add(key);
                        return true;
                    });
                    setLeaderGroups(deduped);
                })
                .catch(err => console.error('Failed to fetch ticker leaders:', err))
                .finally(() => setIsLoadingLeaders(false));

            return Promise.all([gamesPromise, leadersPromise]);
        }).catch(err => {
            console.error('Failed to fetch ticker games:', err);
        }).finally(() => setIsLoadingGames(false));
    }, []);

    // Build leader cards whenever the groups or showdown set changes
    useEffect(() => {
        if (!tickerSeason || leaderGroups.length === 0) return;
        const allEntries = leaderGroups.flatMap(g => g.leaders ?? []);
        const seenIds = new Set<number>();
        const uniquePlayerIds = allEntries.map(e => String(e.person?.id)).filter((id): id is string => id !== undefined);
        const cardSettings = {
            year: tickerSeason.season_id,
            set: userShowdownSet,
            stat_highlights_type: 'ALL',
        };
        if (uniquePlayerIds.length === 0) return;
        setIsLoadingLeaders(true);
        buildCardsFromIds(uniquePlayerIds, tickerSeason.season_id, cardSettings, true).then(cardsResponse => {
            if (!cardsResponse.cards) { console.error('No cards returned from buildCardsFromIds for leader cards'); return; }
            const cardMap: { [playerId: string]: ShowdownBotCard } = {};
            cardsResponse.cards.forEach(cardRes => {
                if (cardRes.card?.mlb_id && !seenIds.has(cardRes.card.mlb_id)) {
                    seenIds.add(cardRes.card.mlb_id);
                    cardMap[String(cardRes.card.mlb_id)] = cardRes.card;
                }
            });
            setLeaderCards(cardMap);
        }).catch(err => {
            console.error('Failed to build leader cards:', err);
        }).finally(() => {
            setIsLoadingLeaders(false);
        });
    }, [leaderGroups, userShowdownSet]);

    // Fetch total card count on mount
    useEffect(() => {
        fetchTotalCardCount().then(count => {
            setTotalCardCount(count);
        }).catch(err => {
            console.error('Failed to fetch total card count:', err);
        });
    }, []);

    // Refresh player trends when showdown set is ready or changes
    useEffect(() => {
        // Small delay to ensure localStorage has been read
        const timer = setTimeout(() => {
            if (!hasLoadedSettings.current) {
                hasLoadedSettings.current = true;
            }
            refreshPlayerTrends();
        }, 100);

        return () => clearTimeout(timer);
    }, [userShowdownSet]);

    const refreshPlayerTrends = () => {
        setIsRefreshingTrends(true);
        // Fetch card of the day
        fetchCardOfTheDay(userShowdownSet).then(card => {
            setCardOfTheDay(card);
        }).catch(err => {
            console.error('Failed to fetch card of the day:', err);
        });

        // Fetch trending players
        fetchTrendingPlayers(userShowdownSet).then(players => {
            setTrendingPlayers(players);
        }).catch(err => {
            console.error('Failed to fetch trending players:', err);
        });

        // Fetch popular cards
        fetchPopularCards(userShowdownSet).then(cards => {
            setPopularCards(cards);
        }).catch(err => {
            console.error('Failed to fetch popular cards:', err);
        });

        // Spotlight cards
        fetchSpotlightCards(userShowdownSet).then(cards => {
            setSpotlightCards(cards);
        }).catch(err => {
            console.error('Failed to fetch spotlight cards:', err);
        }).finally(() => {
            setIsRefreshingTrends(false);
        });
    };

    /** Simulated card lookup based on search query */
    const handlePlayerSelect = (selection: PlayerSearchSelection) => {
        // Simulate fetching a card based on the selected player and year
        const cardId = `${selection.year}-${selection.bref_id}${selection.player_type_override ? `-(${selection.player_type_override.toLowerCase()})` : ''}-${userShowdownSet}`;
        setIsLoadingSearchCard(true);
        fetchCardById(cardId, 'home-search').then(card => {
            setSelectedCard(card.card || null);
            setIsLoadingSearchCard(false);
        });
    };

    const handleModalCardClose = () => {
        setSelectedModalCard(null);
    };

    /** Shows animated placeholder cards during loading */
    const renderBlankExploreCards = () => {
        return <>
            <div className='space-y-3'>
                {[...Array(4)].map((_, index) => (
                    <div key={index} className={`h-32 rounded-lg ${isDark ? 'bg-neutral-800 animate-pulse' : 'bg-neutral-200 animate-pulse'}`} />
                ))}
            </div>
        </>
    }

    return (
        <div
            className={`
                px-6
                md:px-8
                space-y-6
                md:space-y-10
                gradient-page
                pb-24
                pt-8
            `}>

            {/* Game Ticker */}
            <div
                className={`rounded-2xl border-2 overflow-hidden ${isDark ? 'bg-neutral-900/80 border-neutral-800' : 'bg-white/80 border-neutral-200'}`}
            >
                {/* Ticker header */}
                <div
                    className="flex items-center justify-between gap-4 px-4 md:px-6 py-3"
                    style={{ backgroundImage: 'linear-gradient(95deg, #1a2f6e, color-mix(in srgb, #1a2f6e 60%, #8b1a1a 40%), #8b1a1a)' }}
                >
                    <p className="text-xs font-bold uppercase tracking-widest text-white/90 flex items-center gap-2">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-400"></span>
                        </span>
                        Today's Games
                        {tickerSeason && (
                            <span className="text-white/60 font-normal normal-case tracking-normal">
                                {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                            </span>
                        )}
                    </p>
                    <Link to="/seasons" className="text-xs font-semibold text-white/80 hover:text-white flex items-center gap-1 shrink-0">
                        Full Season Details <FaChevronRight className="text-[10px]" />
                    </Link>
                </div>

                {/* Scrollable game cards row */}
                <div className="overflow-x-auto scrollbar-hide">
                    <div className="flex gap-0 min-w-max">
                        {isLoadingGames && (
                            [...Array(6)].map((_, i) => (
                                <div key={i} className={`w-36 shrink-0 px-4 py-3 border-r border-(--divider) animate-pulse ${isDark ? 'bg-neutral-800/40' : 'bg-neutral-100'}`}>
                                    <div className={`h-3 w-16 rounded mb-2 ${isDark ? 'bg-neutral-700' : 'bg-neutral-300'}`} />
                                    <div className={`h-3 w-20 rounded mb-1 ${isDark ? 'bg-neutral-700' : 'bg-neutral-300'}`} />
                                    <div className={`h-3 w-20 rounded ${isDark ? 'bg-neutral-700' : 'bg-neutral-300'}`} />
                                </div>
                            ))
                        )}
                        {!isLoadingGames && todaysGames.length === 0 && !tickerSeason && (
                            <div className={`px-6 py-4 text-sm ${isDark ? 'text-neutral-500' : 'text-neutral-400'}`}>
                                No games scheduled today.
                            </div>
                        )}
                        {!isLoadingGames && [...todaysGames].sort((a, b) => {
                            const seasonId = tickerSeason?.season_id ?? '';
                            const aStarred = starredTeamKeys.includes(`${a.teams?.away?.team?.id}-${seasonId}`) || starredTeamKeys.includes(`${a.teams?.home?.team?.id}-${seasonId}`);
                            const bStarred = starredTeamKeys.includes(`${b.teams?.away?.team?.id}-${seasonId}`) || starredTeamKeys.includes(`${b.teams?.home?.team?.id}-${seasonId}`);
                            if (aStarred !== bStarred) return aStarred ? -1 : 1;
                            const statusOrder: Record<string, number> = { "Live": 0, "Scheduled": 1, "Final": 2 };
                            return (statusOrder[a.status?.abstract_game_state || ""] ?? 3) - (statusOrder[b.status?.abstract_game_state || ""] ?? 3);
                        }).map((game) => {
                            const away = game.teams?.away;
                            const home = game.teams?.home;
                            const awayAbbr = away?.team?.abbreviation ?? '???';
                            const homeAbbr = home?.team?.abbreviation ?? '???';
                            const awayScore = away?.score;
                            const homeScore = home?.score;
                            const awayBadgeBg = away?.team?.primary_color ?? undefined;
                            const awayBadgeText = awayBadgeBg ? getReadableTextColor(awayBadgeBg, '#ffffff') : undefined;
                            const homeBadgeBg = home?.team?.primary_color ?? undefined;
                            const homeBadgeText = homeBadgeBg ? getReadableTextColor(homeBadgeBg, '#ffffff') : undefined;
                            const state = game.status?.abstract_game_state;
                            const detailedState = game.status?.detailed_state;
                            const isFinal = state === 'Final';
                            const isLive = state === 'Live';
                            const linescore = game.linescore;
                            const inning = linescore?.current_inning;
                            const inningHalf = linescore?.inning_half === 'Top' ? '▲' : linescore?.inning_half === 'Bottom' ? '▼' : '';
                            const isAwayStarred = starredTeamKeys.includes(`${away?.team?.id}-${tickerSeason?.season_id}`);
                            const isHomeStarred = starredTeamKeys.includes(`${home?.team?.id}-${tickerSeason?.season_id}`);
                            const statusLabel = isFinal
                                ? 'FINAL'
                                : isLive
                                ? `${inningHalf}${inning ?? ''}`
                                : game.game_date
                                ? new Date(game.game_date).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
                                : detailedState ?? '';

                            return (
                                <Link
                                    key={game.game_pk}
                                    to={`/seasons?gamePk=${game.game_pk}`}
                                    className={`w-36 shrink-0 px-4 py-3 border-r border-(--divider) hover:brightness-105 transition ${isDark ? 'hover:bg-neutral-800/60' : 'hover:bg-neutral-50'}`}
                                >
                                    {/* Status badge */}
                                    <div className="mb-2 flex items-center justify-between gap-1.5">
                                        <span className={`text-[10px] font-bold uppercase tracking-wide py-0.5 ${isLive || isFinal ? 'px-1.5 rounded' : ''} ${
                                            isLive
                                                ? 'bg-yellow-400/10 text-yellow-400'
                                                : isFinal
                                                ? 'bg-green-500/10 text-green-300'
                                                : isDark ? 'text-neutral-100' : 'text-neutral-500'
                                        }`}>
                                            {isLive ? 'LIVE' : statusLabel}
                                        </span>
                                        {isLive && inning != null && (
                                            <span className="text-[10px] font-bold text-yellow-400">
                                                {inningHalf} {inning}
                                            </span>
                                        )}
                                    </div>

                                    {/* Away team */}
                                    <div className={`flex items-center justify-between gap-1 mb-1`}>
                                        <div className="flex items-center gap-2">
                                            <span 
                                                className={`flex items-center gap-0.5 text-sm font-black leading-tight ${isDark ? 'text-white' : 'text-black'} ${awayBadgeBg ? 'px-1.5 py-0.5 rounded' : ''}`}
                                                style={awayBadgeBg ? { backgroundColor: awayBadgeBg, color: awayBadgeText } : undefined}
                                            >
                                                {awayAbbr}
                                                {isAwayStarred && <FaStar className="text-yellow-400 w-2 h-2" />}
                                            </span>
                                            {away?.league_record && (
                                                <span className={`text-[10px] leading-tight ${isDark ? 'text-neutral-500' : 'text-neutral-400'}`}>{away.league_record.wins}-{away.league_record.losses}</span>
                                            )}
                                        </div>
                                        <span className={`text-sm font-black tabular-nums `}>{awayScore === undefined || awayScore === null ? "-" : awayScore}</span>
                                    </div>

                                    {/* Home team */}
                                    <div className={`flex items-center justify-between gap-1`}>
                                        <div className="flex items-center gap-2">
                                            <span 
                                                className={`flex items-center gap-0.5 text-sm font-black leading-tight ${isDark ? 'text-white' : 'text-black'} ${homeBadgeBg ? 'px-1.5 py-0.5 rounded' : ''}`} 
                                                style={homeBadgeBg ? { backgroundColor: homeBadgeBg, color: homeBadgeText } : undefined}
                                            >
                                                {homeAbbr}
                                                {isHomeStarred && <FaStar className="text-yellow-400 w-2 h-2" />}
                                            </span>
                                            {home?.league_record && (
                                                <span className={`text-[10px] leading-tight ${isDark ? 'text-neutral-500' : 'text-neutral-400'}`}>{home.league_record.wins}-{home.league_record.losses}</span>
                                            )}
                                        </div>
                                            <span className={`text-sm font-black tabular-nums`}>{homeScore === undefined || homeScore === null ? "-" : homeScore}</span>
                                    </div>
                                </Link>
                            );
                        })}
                    </div>
                </div>

                {/* Leaders rows */}
                <div className="relative border-t border-(--divider) px-4 md:px-6 py-4 space-y-4">
                    {isLoadingLeaders && (
                        <div className={`absolute inset-0 z-10 flex items-center justify-center gap-2 rounded-b-2xl backdrop-blur-[2px] ${isDark ? 'bg-neutral-900/60' : 'bg-white/60'}`}>
                            <span className={`w-2 h-2 rounded-full animate-bounce [animation-delay:0ms] ${isDark ? 'bg-neutral-400' : 'bg-neutral-500'}`} />
                            <span className={`w-2 h-2 rounded-full animate-bounce [animation-delay:150ms] ${isDark ? 'bg-neutral-400' : 'bg-neutral-500'}`} />
                            <span className={`w-2 h-2 rounded-full animate-bounce [animation-delay:300ms] ${isDark ? 'bg-neutral-400' : 'bg-neutral-500'}`} />
                        </div>
                    )}
                    {(isLoadingLeaders && leaderGroups.length === 0 ? [null, null] : leaderGroups).map((group, gi) => {
                        const label = group?.leader_category ? (LEADER_CATEGORY_LABELS[group.leader_category] ?? group.leader_category) : '';
                        const entries = group ? (group.leaders ?? []).slice(0, 3) : [...Array(3)].map(() => null);
                        return (
                            <div key={group?.leader_category ?? gi}>
                                <span className={`text-xs font-bold uppercase tracking-wide ${isDark ? 'text-neutral-400' : 'text-neutral-500'}`}>{label}</span>
                                <div className="mt-2 flex gap-2 overflow-x-auto scrollbar-hide lg:grid lg:grid-cols-3">
                                    {entries.map((entry, i) => {
                                        const card = entry?.person?.id ? leaderCards[String(entry.person.id)] : undefined;
                                        return (
                                            <div key={entry?.rank ?? i} className="flex flex-col items-center gap-1 shrink-0 w-72 lg:w-auto">
                                                <CardItemFromCard
                                                    card={card}
                                                    className={`max-w-full w-full ${card ? 'cursor-pointer' : 'pointer-events-none'} ${!entry ? 'animate-pulse opacity-50' : ''}`}
                                                    onClick={card ? () => setSelectedModalCard(card) : undefined}
                                                />
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Hero Section */}
            <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-10">

                {/* Left: Text and Actions */}
                <div className="w-full md:w-1/2 3xl:flex-[0.6] flex flex-col gap-4 items-start">
                    <div className="flex items-center gap-3 mb-2">
                        <span className={`inline-flex items-center gap-2 px-4 py-1 rounded-full text-sm font-semibold ${isDark ? 'bg-white/10' : 'bg-gray-100'}`}>
                            <FaBolt className={`${isDark ? 'text-yellow-400' : 'text-yellow-500'}`} /> 
                            <span className='leading-tight'>Showdown cards in seconds</span>
                        </span>
                        <div className={`leading-tight inline-flex items-center gap-1.5 px-4 py-1 rounded-full text-sm font-semibold ${gradientBlueBg}`}>
                            <span className={`font-bold ${isDark ? 'text-blue-300' : 'text-blue-700'} ${totalCardCount !== null ? '' : 'redacted animate-pulse'}`}>{totalCardCount !== null ? totalCardCount.toLocaleString() : '---------'}</span>
                            <span className={`${isDark ? 'text-neutral-400' : 'text-neutral-600'}`}>cards created</span>
                        </div>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-extrabold leading-tight">
                        Digital Cards that Play Ball.
                    </h1>
                    <p className={`text-lg max-w-xl leading-6 ${isDark ? 'text-neutral-300' : 'text-neutral-700'}`}>
                        Enter a player and season. We turn real stats into a simulated card for the iconic 20-sided dice game — ready to share, use in your league, or just admire.
                    </p>
                    
                    <div className="flex gap-4 mt-2">
                        <Link to="/customs" className={`flex items-center gap-2 px-6 py-3 rounded-xl text-lg font-semibold shadow hover:bg-neutral-200 transition bg-(--showdown-red) ${isDark ? 'text-white' : 'text-white'}`}>
                            Build your Own <FaChevronRight />
                        </Link>
                        <Link to="/cards" className={`flex items-center gap-2 px-6 py-3 rounded-xl text-lg font-semibold shadow transition ${isDark ? 'bg-neutral-900 border border-neutral-700 text-white hover:bg-neutral-800' : 'bg-white border border-neutral-300 text-black hover:bg-neutral-100'}`}>
                            Explore Cards <FaChevronRight />
                        </Link>
                    </div>
                    <form className={`rounded-2xl p-6 flex flex-col w-full gap-4 ${isDark ? 'bg-neutral-900/80 border border-neutral-800' : 'bg-white/80 border border-neutral-200'}`}>
                        <PlayerSearchInput label='Try it out! Search for a player' value={searchQuery} onChange={handlePlayerSelect} searchOptions={{ exclude_multi_year: true }} />
                        <CardItemFromCard card={selectedCard || undefined} className={`${selectedCard ? '' : 'pointer-events-none'} ${isLoadingSearchCard ? 'blur-xs' : ''}`} onClick={() => setSelectedModalCard(selectedCard)} />
                    </form>
                </div>

                {/* Right: Random Card of the Day */}
                <div className="flex-1 3xl:flex-[0.4] flex flex-col items-center md:items-end w-full">
                    <div className={`rounded-3xl p-6 w-full max-w-md min-h-100 flex flex-col relative gap-2 ${isDark ? 'bg-neutral-900/80 border border-neutral-800' : 'bg-white/80 border border-neutral-200'}`}>
                        <div className="flex justify-between items-center mb-2">
                            <span className={`text-lg font-semibold ${isDark ? 'text-white/80' : 'text-black/80'}`}>Card of the Day</span>
                            <span className={`text-xs ${isDark ? 'text-neutral-400' : 'text-neutral-600'}`}>Generated by the Community</span>
                        </div>
                        <div className="flex-1 flex flex-col justify-center items-center gap-4">
                            <img src={cardOfDayImageSrc} alt="Sample Showdown Card" className={`min-h-64 max-h-124 rounded-lg object-contain shadow-2xl ${isRefreshingTrends ? 'animate-pulse' : ''}`} />                        </div>
                        <div className={`left-4 right-4 text-xs text-left pt-2 ${isDark ? 'text-neutral-500' : 'text-neutral-400'}`}>
                            {cardOfTheDay ? (
                                <>
                                    <span className="font-semibold">{cardOfTheDay.card_data.name}</span> - {cardOfTheDay.card_data.team} ({cardOfTheDay.card_data.year})<br />
                                </>
                            ) : (
                                <>Loading...</>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* How it Works */}
            <div className="max-w-7xl mx-auto py-6 border-t border-form-element">
                <h2 className="text-3xl font-bold mb-8">How to Play</h2>
                
                {/* Steps: Side by Side on md+ */}
                <div className="grid md:grid-cols-2 gap-8 mb-12">
                    {/* Step 1: The Pitch */}
                    <div>
                        <div className="mb-3">
                            <span className={`text-sm font-semibold uppercase tracking-wide ${isDark ? 'text-red-400' : 'text-red-600'}`}>Step 1</span>
                            <h3 className="text-xl font-bold mt-1">The Pitch</h3>
                            <p className={`text-sm mt-1 ${isDark ? 'text-neutral-400' : 'text-neutral-600'}`}>Pitcher rolls to see who gets the advantage</p>
                        </div>

                        <div className={`text-sm space-y-1.5 mb-3 ${isDark ? 'text-neutral-300' : 'text-neutral-700'}`}>
                            <div className="flex items-start gap-2">
                                <span className="text-red-500 font-bold">•</span>
                                <span>Pitcher's total <strong>(Control + Dice Roll)</strong> higher = Pitcher's advantage</span>
                            </div>
                            <div className="flex items-start gap-2">
                                <span className="text-blue-500 font-bold">•</span>
                                <span>Pitcher's total lower or tied = Batter's advantage</span>
                            </div>
                        </div>
                        
                        <div className={`rounded-xl p-4 ${isDark ? 'bg-neutral-800/50 border border-neutral-700' : 'bg-neutral-100 border border-neutral-300'}`}>
                            <div className='flex items-center justify-center gap-3'>
                                <div className='flex flex-col items-center gap-1'>
                                    <CardCommand isPitcher={true} primaryColor="rgb(200, 16, 46)" secondaryColor="rgb(255, 255, 255)" command={4} team="BOS" className="w-10 h-10 shrink-0" />
                                    <span className='text-[10px] font-bold text-tertiary'>Control</span>
                                </div>
                                <span className='text-lg font-bold'>+</span>
                                <div className='flex flex-col items-center gap-1'>
                                    <FaDiceD20 className="text-gray-500 w-10 h-10" />
                                    <span className='text-[10px] font-bold text-tertiary'>Dice Roll</span>
                                </div>
                                <span className={`text-xs font-bold uppercase px-3 ${isDark ? 'text-neutral-400' : 'text-neutral-600'}`}>vs</span>
                                <div className='flex flex-col items-center gap-1'>
                                    <CardCommand isPitcher={false} primaryColor="rgb(12, 35, 64)" secondaryColor="rgb(255, 255, 255)" command={8} team="NYY" className="w-10 h-10 shrink-0" />
                                    <span className='text-[10px] font-bold text-tertiary'>On-Base</span>
                                </div>
                            </div>
                        </div>
                        
                        
                    </div>

                    {/* Step 2: The Swing */}
                    <div>
                        <div className="mb-3">
                            <span className={`text-sm font-semibold uppercase tracking-wide ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>Step 2</span>
                            <h3 className="text-xl font-bold mt-1">The Swing</h3>
                            <p className={`text-sm mt-1 ${isDark ? 'text-neutral-400' : 'text-neutral-600'}`}>Batter rolls to see what happens</p>
                        </div>
                        
                        <div className={`text-sm space-y-1.5 mb-3 ${isDark ? 'text-neutral-300' : 'text-neutral-700'}`}>
                            <div className="flex items-start gap-2">
                                <span className="text-red-500 font-bold">•</span>
                                <span><strong>Pitcher's advantage:</strong> Find result on pitcher's chart</span>
                            </div>
                            <div className="flex items-start gap-2">
                                <span className="text-blue-500 font-bold">•</span>
                                <span><strong>Batter's advantage:</strong> Find result on batter's chart</span>
                            </div>
                        </div>
                        
                        <div className={`rounded-xl p-3 ${isDark ? 'bg-neutral-800/50 border border-neutral-700' : 'bg-neutral-100 border border-neutral-300'}`}>
                            <div className="flex flex-col lg:flex-row items-center lg:items-start gap-2 max-w-full">
                                
                                <div className='flex gap-3 items-center lg:items-start lg:mr-3'>
                                    <div className='flex flex-col items-center gap-1 pt-2'>
                                        <FaDiceD20 className="text-gray-500 w-6 h-6 lg:w-8 lg:h-8" />
                                        <span className='text-[10px] font-bold text-tertiary'>Roll</span>
                                    </div>
                                    <div className='flex flex-col items-center justify-center gap-0.5 pt-3'>
                                        <FaChevronRight className={`hidden lg:block ${isDark ? 'text-neutral-400' : 'text-neutral-600'}`} />
                                        <FaChevronDown className={`lg:hidden ${isDark ? 'text-neutral-400' : 'text-neutral-600'}`} />
                                        <span className={`text-[7px] font-semibold uppercase ${isDark ? 'text-neutral-500' : 'text-neutral-600'}`}>Find</span>
                                    </div>
                                </div>
                                
                                <div className="flex-1 ">
                                    <CardChart
                                        chartRanges={{"SO":"1-2","GB":"3-4","FB":"5-6","BB":"7-8","1B":"9-15","1B+":"-","2B":"16-17","3B":"18","HR":`${['2000', '2001', 'CLASSIC'].includes(userShowdownSet)? '19-20' : '19+'}`}} 
                                        showdownSet={userShowdownSet || '2001'}
                                        primaryColor="rgb(12, 35, 64)"
                                        secondaryColor="rgb(255, 255, 255)"
                                        team="NYY"
                                        cellClassName="lg:min-w-8 xl:min-w-10"
                                        className="mb-1"
                                    />
                                    <p className={`text-[10px] ${isDark ? 'text-neutral-500' : 'text-neutral-600'}`}>Example: Roll 16 = Double!</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* Next Steps and Why it Works */}
                <div className="grid md:grid-cols-2 gap-8 mb-12">
                    {/* The Rest */}
                    <div>
                        <h2 className="text-2xl font-bold mb-4">Play out the Game</h2>
                        <ul className="space-y-2 mb-4">
                            <li className={`flex items-start gap-2 ${isDark ? 'text-neutral-300' : 'text-neutral-700'}`}>
                                <span className="text-primary font-bold mt-0.5">•</span>
                                <span><strong>Build your team:</strong> <span className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>Draft players within a salary cap budget (or just pick your favorite all-stars!)</span></span>
                            </li>
                            <li className={`flex items-start gap-2 ${isDark ? 'text-neutral-300' : 'text-neutral-700'}`}>
                                <span className="text-primary font-bold mt-0.5">•</span>
                                <span><strong>Play 9 innings:</strong> <span className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>Alternate pitching and batting through 9 innings</span></span>
                            </li>
                            <li className={`flex items-start gap-2 ${isDark ? 'text-neutral-300' : 'text-neutral-700'}`}>
                                <span className="text-primary font-bold mt-0.5">•</span>
                                <span><strong>Advanced Gameplay:</strong> <span className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>Incorporate baserunning, fielding, and strategic decisions</span></span>
                            </li>
                        </ul>
                        {/* <Link to="/rules" className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition ${isDark ? 'bg-neutral-900 border border-neutral-700 text-white hover:bg-neutral-800' : 'bg-white border border-neutral-300 text-black hover:bg-neutral-100'}`}>
                            Learn more about gameplay <FaChevronRight />
                        </Link> */}
                    </div>

                    {/* Why it works */}
                    <div className="max-w-3xl mx-auto">
                        <h2 className="text-2xl font-bold mb-4">Why it works</h2>
                        <ul className="space-y-3 mb-4">
                            <li className="flex items-center gap-2"><FaDiceD20 className="text-primary" /> <span>20-sided dice system <span className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>— Every at-bat is different to the randomness of a dice roll.</span></span></li>
                            <li className="flex items-center gap-2"><FaShieldAlt className="text-primary" /> <span>Real stats, simulated play <span className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>— Players perform like they did in their actual season.</span></span></li>
                        </ul>
                        <div className={`rounded-xl p-4 text-sm ${isDark ? 'bg-neutral-800/80 text-neutral-300' : 'bg-neutral-200/80 text-neutral-700'}`}>
                            <div className="font-semibold mb-1">The beauty of Showdown</div>
                            <div className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>"Dice rolls meet baseball stats. Fast-paced strategy with authentic player performance."</div>
                        </div>
                    </div>
                </div>
                
            </div>

            {/* Cards Section */}
            <div className="max-w-7xl mx-auto py-6 border-t border-form-element">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold">Cards</h2>
                    <Link to="/cards" className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition ${isDark ? 'bg-neutral-900 border border-neutral-700 text-white hover:bg-neutral-800' : 'bg-white border border-neutral-300 text-black hover:bg-neutral-100'}`}>
                        Explore Cards <FaChevronRight />
                    </Link>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className={`rounded-2xl p-6 overflow-hidden ${isDark ? 'bg-neutral-900/80 border border-neutral-800' : 'bg-white/80 border border-neutral-200'}`}>
                        <div className="font-semibold mb-2 flex items-center gap-2"><FaFire className="text-red-500" /> Trending this week</div>
                        <div className={`text-sm mb-2 ${isDark ? 'text-neutral-400' : 'text-neutral-600'}`}>Players and seasons gaining attention recently.</div>
                        {trendingPlayers.length > 0 ? (
                            <div className='space-y-3'>
                                {trendingPlayers.slice(0, 4).map((card, index) => (
                                    <CardItemFromCard key={index} card={card.card_data} className="max-w-full" onClick={() => setSelectedModalCard(card.card_data)} />
                                ))}
                            </div>
                        ) : (
                            renderBlankExploreCards()
                        )}
                    </div>
                    <div className={`rounded-2xl p-6 overflow-hidden ${isDark ? 'bg-neutral-900/80 border border-neutral-800' : 'bg-white/80 border border-neutral-200'}`}>
                        <div className="font-semibold mb-2 flex items-center gap-2"><FaStar className="text-yellow-400" /> Most Popular</div>
                        <div className={`text-sm mb-2 ${isDark ? 'text-neutral-400' : 'text-neutral-600'}`}>Most created custom cards all-time.</div>
                        {popularCards.length > 0 ? (
                            <div className='space-y-3'>
                                {popularCards.slice(0, 4).map((card, index) => (
                                    <div className="relative max-w-full">
                                        <span className={`absolute text-[12px] -right-2 -top-2 ${gradientBlueBg} font-bold backdrop-blur-sm rounded-full px-2 py-1`}>{card.num_creations.toLocaleString()}</span>
                                        <CardItemFromCard key={index} card={card.card_data} className="max-w-full" onClick={() => setSelectedModalCard(card.card_data)} />
                                    </div>
                                ))}
                            </div>
                        ) : (
                            renderBlankExploreCards()
                        )}
                    </div>
                    <div className={`rounded-2xl p-6 overflow-hidden ${isDark ? 'bg-neutral-900/80 border border-neutral-800' : 'bg-white/80 border border-neutral-200'}`}>
                        <div className="font-semibold mb-2 flex items-center gap-2"><FaUsers className="text-primary" />Spotlight</div>
                        <div className={`text-sm mb-2 ${isDark ? 'text-neutral-400' : 'text-neutral-600'}`}>{spotlightCards.length > 0 ? spotlightCards[0].spotlight_reason : 'Curated sets and fun themes.'}</div>
                        {spotlightCards.length > 0 ? (
                            <div className='space-y-3'>
                                {spotlightCards.slice(0, 4).map((card, index) => (
                                    <CardItemFromCard key={index} card={card.card_data} className="max-w-full" onClick={() => setSelectedModalCard(card.card_data)} />
                                ))}
                            </div>
                        ) : (
                            renderBlankExploreCards()
                        )}
                    </div>
                </div>
            </div>
        
            {/* FAQ Section */}
            <div className="max-w-7xl mx-auto py-6 border-t border-form-element">
                <h2 className="text-2xl font-bold mb-8">FAQ</h2>
                <div className="grid md:grid-cols-2 gap-6">
                    <div className={`rounded-2xl p-6 ${isDark ? 'bg-neutral-900/80 border border-neutral-800' : 'bg-white/80 border border-neutral-200'}`}>
                        <h3 className="text-lg font-semibold mb-2">Can I print these?</h3>
                        <p className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>These cards are for personal, non-commercial use only. This is a fan project not affiliated with or endorsed by WOTC or MLB. Cards are not licensed for printing, distribution, or sale.</p>
                    </div>
                    <div className={`rounded-2xl p-6 ${isDark ? 'bg-neutral-900/80 border border-neutral-800' : 'bg-white/80 border border-neutral-200'}`}>
                        <h3 className="text-lg font-semibold mb-2">How does the formula work?</h3>
                        <p className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>The formula is designed to feel true to the original WOTC cards while being accurate when simulating a full season. The Bot's source code is publicly available on GitHub. Look at the <a href="https://github.com/mgula57/mlb_showdown_card_bot/blob/master/README.md" target="_blank" rel="noopener noreferrer" className="text-primary underline">README</a> for formula details.</p>
                    </div>
                    <div className={`rounded-2xl p-6 ${isDark ? 'bg-neutral-900/80 border border-neutral-800' : 'bg-white/80 border border-neutral-200'}`}>
                        <h3 className="text-lg font-semibold mb-2">What Showdown sets are supported?</h3>
                        <p className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>The Bot supports all original Showdown sets (2000-2005) and adds CLASSIC and EXPANDED sets, which are updated designs with more diverse and accurate charting. Each set has unique point values and chart distributions.</p>
                    </div>
                    <div className={`rounded-2xl p-6 ${isDark ? 'bg-neutral-900/80 border border-neutral-800' : 'bg-white/80 border border-neutral-200'}`}>
                        <h3 className="text-lg font-semibold mb-2">How can I contact the developers?</h3>
                        <p className={isDark ? 'text-neutral-400' : 'text-neutral-600'}>Send an email to <a href="mailto:mlbshowdownbot@gmail.com" className="text-primary underline">mlbshowdownbot@gmail.com</a>. Feel free to reach out with questions or feedback.</p>
                    </div>
                </div>
            </div>

            {/* Modal */}
            <div className={selectedModalCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={handleModalCardClose} isVisible={!!selectedModalCard}>
                    <CardDetail
                        showdownBotCardData={{ card: selectedModalCard} as ShowdownBotCardAPIResponse} 
                        hideTrendGraphs={true}
                        context="home"
                        parent='home'
                    />
                </Modal>
            </div>
        </div>
    );
}
