import { Link } from 'react-router-dom';
import {
    FaChevronRight, FaChevronDown, FaShieldAlt,
    FaUsers, FaFire, FaDiceD20, FaStar,
    FaCompass, FaCalendar, FaAward
} from 'react-icons/fa';
import CardBuildIcon from './customs/CardBuildIcon';
import { FaXmark, FaPeopleGroup } from 'react-icons/fa6';
import LiveIcon from './shared/icons/LiveIcon';
import { FaDiscord } from 'react-icons/fa';
import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useTheme } from './shared/SiteSettingsContext';
import { useSiteSettings } from './shared/SiteSettingsContext';
import { useAuth } from './auth/AuthContext';
import { fetchTodaysSchedule, fetchSeasons, fetchSeasonLeaders } from '../api/mlbAPI';
import type { GameScheduled, Season, LeadersGroup } from '../api/mlbAPI';
import { fromScheduledGame } from '../domain/adapters/fromMlbApi';
import type { GameState } from '../domain/game';
import { TeamChip } from './shared/TeamChip';
import { markNavItemSeen, useNavItemIsNew } from '../hooks/useSeenNavItems';
import HomeGameReel from './home/HomeGameReel';
import { Plate } from './shared/Plate';
import { Eyebrow } from './shared/Eyebrow';
import { NewBadge } from './shared/NewBadge';
import { buttonClass } from './shared/buttonStyles';
import { PinstripeBackdrop } from './shared/PinstripeBackdrop';

// Modal
import { Modal } from './shared/Modal';
import ShowdownBotLogo from './shared/ShowdownBotLogo';

// Card Components
import { CardItemFromCard } from './cards/CardItem';
import CardCommand from './cards/card_elements/CardCommand';
import { CardChart } from './cards/card_elements/CardChart';
import type { ShowdownBotCard, ShowdownBotCardAPIResponse } from '../api/showdownBotCard';
import { CardDetail } from './cards/CardDetail';

// API
import { buildCardsFromIds } from '../api/showdownBotCard';
import { fetchTotalCardCount, fetchTrendingPlayers, fetchPopularCards, fetchSpotlightCards, fetchCardOfTheDay } from '../api/card_db/cardDatabase';
import type { PopularCardRecord, TrendingCardRecord, SpotlightCardRecord, CardOfTheDayRecord } from '../api/card_db/cardDatabase';
import { fetchUserGallery, type GalleryImageRecord } from '../api/gallery';

import { Heading } from './shared/Heading';
import { CAPS_LABEL_CLASS } from './shared/fieldStyles';
import { GameStatePlate } from './games/GameStatePlate';
// TODO: replace hard-coded IDs with a general two-way player detection strategy
const TWO_WAY_PLAYER_IDS = new Set([660271]); // Ohtani
const PITCHING_LEADER_CATEGORIES = new Set(['walksAndHitsPerInningPitched', 'earnedRunAverage', 'strikeouts', 'wins', 'saves', 'inningsPitched', 'strikeoutsPer9Inn', 'strikeoutWalkRatio']);

const FAQ_LINK_CLASS = 'text-(--text-primary) underline';

const FAQ_ITEMS: { question: string; answer: React.ReactNode }[] = [
    {
        question: 'Can I print these?',
        answer: 'These cards are for personal, non-commercial use only. This is a fan project not affiliated with or endorsed by WOTC or MLB. Cards are not licensed for printing, distribution, or sale.',
    },
    {
        question: 'How does the formula work?',
        answer: <>The formula is designed to feel true to the original WOTC cards while being accurate when simulating a full season. The Bot's source code is publicly available on GitHub. Look at the <a href="https://github.com/mgula57/mlb_showdown_card_bot/blob/master/README.md" target="_blank" rel="noopener noreferrer" className={FAQ_LINK_CLASS}>README</a> for formula details.</>,
    },
    {
        question: 'What Showdown sets are supported?',
        answer: 'The Bot supports all original Showdown sets (2000-2005) and adds CLASSIC and EXPANDED sets, which are updated designs with more diverse and accurate charting. Each set has unique point values and chart distributions.',
    },
    {
        question: 'How can I contact the developers?',
        answer: <>Send an email to <a href="mailto:mlbshowdownbot@gmail.com" className={FAQ_LINK_CLASS}>mlbshowdownbot@gmail.com</a>, or join the conversation on <a href="https://discord.com/channels/669174897939054602/857237582740193282" target="_blank" rel="noopener noreferrer" className={`${FAQ_LINK_CLASS} inline-flex items-center gap-1 align-middle`}><FaDiscord className="w-4 h-4" />Discord</a>. Feel free to reach out with questions or feedback.</>,
    },
];

type HomeNavTileData = {
    label: string;
    desc: string;
    Icon: React.ComponentType<{ className?: string }>;
    to: string;
    iconColor: string;
    isNew?: boolean;
};

/**
 * A Home quick-nav tile. Shares the "NEW" badge state with the side menu — visiting
 * the destination from either surface clears the badge on both.
 */
function HomeNavTile({ tile }: { tile: HomeNavTileData }) {
    const { label, desc, Icon, to, iconColor } = tile;
    const isNew = useNavItemIsNew(to, tile.isNew);
    return (
        <Link
            to={to}
            onClick={() => markNavItemSeen(to)}
            className="relative overflow-hidden rounded-card p-4 flex flex-col gap-1 border border-(--divider) bg-(--background-secondary) hover:border-(--rule-strong) transition-[transform,border-color] duration-200 hover:scale-[1.03] active:scale-95 cursor-pointer"
        >
            <Icon className="absolute -bottom-2 -right-2 text-7xl opacity-5" />
            <Icon className={`text-3xl mb-1 ${iconColor}`} />
            <span className="font-display uppercase text-[17px] leading-none text-(--text-primary)">{label}</span>
            <span className="text-xs leading-snug text-(--text-tertiary)">{desc}</span>
            {isNew && <NewBadge className="absolute top-2 right-2" />}
        </Link>
    );
}

/** A landing-page section title (page-size, under the hero) with an optional secondary-button link
 *  on the right. Home's tiers: hero > section header (`page`) > block title (`section`) > `panel`. */
function HomeSectionHeader({ title, action }: { title: string; action?: { label: string; to: string } }) {
    return (
        <div className="flex justify-between items-end gap-4 mb-6">
            <Heading level="page" as="h2">{title}</Heading>
            {action && (
                <Link to={action.to} className={buttonClass('secondary')}>
                    {action.label} <FaChevronRight className="text-xs" />
                </Link>
            )}
        </div>
    );
}

/** Flat panel used for the card shelves and FAQ answers. */
function HomePanel({ children, className = '' }: { children: React.ReactNode; className?: string }) {
    return (
        <div className={`rounded-card p-5 border border-(--divider) bg-(--background-secondary) ${className}`}>
            {children}
        </div>
    );
}

/** Title + one-line description at the top of a card shelf panel. */
function HomePanelHeading({ Icon, title, description }: { Icon: React.ComponentType<{ className?: string }>; title: string; description: string }) {
    return (
        <div className="mb-3">
            <Heading level="section" as="h3" className="flex items-center gap-2">
                <Icon className="text-base text-(--text-tertiary)" /> {title}
            </Heading>
            <div className="text-sm mt-1.5 text-(--text-tertiary)">{description}</div>
        </div>
    );
}

/** Body text for a How to Play bullet, keyed to which side it favors. */
function HowToPlayBullet({ side, children }: { side: 'pitcher' | 'batter'; children: React.ReactNode }) {
    return (
        <div className="flex items-start gap-2">
            <span className={`font-bold ${side === 'pitcher' ? 'text-(--showdown-red)' : 'text-(--showdown-blue)'}`}>•</span>
            <span>{children}</span>
        </div>
    );
}

export default function Home() {

    // State
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

    // Auth
    const { user, session, loading: authLoading } = useAuth();

    // What's New banner
    type RecentCardItem = { record: GalleryImageRecord; thumbUrl: string; fullUrl: string };
    const [recentCards, setRecentCards] = useState<RecentCardItem[]>([]);
    const [isLoadingRecentCards, setIsLoadingRecentCards] = useState<boolean>(false);
    const [recentCardModal, setRecentCardModal] = useState<string | null>(null);

    // Theme & Settings
    const { isDark } = useTheme();
    const { userShowdownSet } = useSiteSettings();

    // Track if we've loaded settings from localStorage
    const hasLoadedSettings = useRef(false);
    const lastFetchedUserId = useRef<string | null>(null);

    // Styling
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
            const leadersPromise = fetchSeasonLeaders(active.season_id, ['ON_BASE_PLUS_SLUGGING', 'WALKS_HITS_PER_INNING_PITCHED'], undefined, 3)
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
                if (cardRes.card?.mlb_id != null) {
                    const id = cardRes.card.mlb_id;
                    if (TWO_WAY_PLAYER_IDS.has(id)) {
                        const suffix = cardRes.card.player_type === 'Pitcher' ? 'P' : 'H';
                        cardMap[`${id}-${suffix}`] = cardRes.card;
                    } else if (!seenIds.has(id)) {
                        seenIds.add(id);
                        cardMap[String(id)] = cardRes.card;
                    }
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

    useEffect(() => {
        if (authLoading) return;
        if (!user) { setRecentCards([]); lastFetchedUserId.current = null; return; }
        if (user.id === lastFetchedUserId.current) return;
        lastFetchedUserId.current = user.id;
        const token = session?.access_token;
        if (!token) return;
        setIsLoadingRecentCards(true);
        fetchUserGallery(token, 15).then(({ gallery }) => {
            const seen = new Set<string>();
            const items: RecentCardItem[] = [];
            for (const r of gallery) {
                const thumbUrl = r.thumbnail_public_url ?? r.public_url;
                const fullUrl = r.public_url ?? r.thumbnail_public_url;
                if (!thumbUrl || !fullUrl) continue;
                const key = `${r.player_name}-${r.year}-${r.set_name}`;
                if (seen.has(key)) continue;
                seen.add(key);
                items.push({ record: r, thumbUrl, fullUrl });
            }
            setRecentCards(items);
        }).catch(() => setRecentCards([])).finally(() => setIsLoadingRecentCards(false));
    }, [user, authLoading]);

    useEffect(() => {
        if (!recentCardModal) return;
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setRecentCardModal(null); };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [recentCardModal]);

    const refreshPlayerTrends = () => {
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
                    <div key={index} className="h-32 rounded-card bg-(--background-tertiary) animate-pulse" />
                ))}
            </div>
        </>
    }

    return (
        <div
            className={`
                relative isolate
                px-6
                md:px-8
                space-y-6
                md:space-y-10
                bg-(--background-primary)
                pb-24
                pt-3 sm:pt-5 lg:pt-8
            `}>

            {/* Hero Section */}
            <div className="max-w-7xl mx-auto py-2 grid lg:grid-cols-2 gap-6 lg:gap-8 items-center">
                <div className="flex flex-col items-start gap-4 min-w-0">
                    <div className="flex flex-col items-start gap-3 max-w-2xl">
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                            <Eyebrow className="hidden sm:inline">Showdown cards in seconds</Eyebrow>
                            <Plate size="md">
                                <span className={totalCardCount !== null ? '' : 'redacted animate-pulse'}>
                                    {totalCardCount !== null ? totalCardCount.toLocaleString() : '---------'}
                                </span>
                                cards created
                            </Plate>
                        </div>
                        {/* The hero is the one title set larger than the `page` level (see DESIGN.md). */}
                        <Heading level="page" className="text-4xl! md:text-5xl! leading-[0.95]!">
                            Digital Cards that <span className="text-(--showdown-red)">Play Ball.</span>
                        </Heading>
                        <p className="text-base max-w-xl leading-6 text-(--text-secondary)">
                            Turn real stats into Showdown cards, draft a team, and simulate full seasons — you're the GM of your own digital baseball-verse.
                        </p>
                    </div>

                    {/* Quick Nav */}
                    <div className="w-full pt-1">
                        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-2 xl:grid-cols-4 gap-3 max-w-3xl">
                            {([
                                { label: 'Card Builder',  desc: 'Build and customize your own cards', Icon: CardBuildIcon,   to: '/customs', iconColor: 'text-(--showdown-red)' },
                                { label: 'Card Explorer', desc: 'Browse our library of 100K+ cards', Icon: FaCompass,  to: '/cards',   iconColor: 'text-(--showdown-blue)' },
                                { label: 'Team Builder',  desc: 'Build teams and play 162 game sim challenges',   Icon: FaPeopleGroup, to: '/teams', iconColor: 'text-(--showdown-red)', isNew: true },
                                { label: 'Seasons',       desc: 'Live games, stats, and full-season simulations',   Icon: FaCalendar, to: '/seasons', iconColor: 'text-(--showdown-blue)', isNew: true },
                            ] as const).map((tile) => (
                                <HomeNavTile key={tile.to} tile={tile} />
                            ))}
                        </div>
                    </div>
                </div>

                {/* Game reel — replays a scoring half-inning from a real game with Showdown dice */}
                <HomeGameReel onCardSelect={setSelectedModalCard} />
            </div>

            {/* Game Ticker */}
            <div className="rounded-card border border-(--divider) overflow-hidden max-w-7xl mx-auto bg-(--background-secondary)">
                {/* Ticker header: navy band over a red rule, from the Showdown logo */}
                <div className="flex items-center justify-between gap-4 px-4 md:px-6 py-2.5 bg-(--showdown-blue) border-b-2 border-(--showdown-red)">
                    <p className="flex items-center gap-2 text-white">
                        <LiveIcon size={7} title="Live" color="var(--field-live)" />
                        <Heading level="section" as="h2" style={{ color: 'white' }}>Today's Games</Heading>
                        {tickerSeason && (
                            <span className="text-xs text-white/70">
                                {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                            </span>
                        )}
                    </p>
                    <Link to="/seasons" className="text-xs font-semibold text-white/80 hover:text-white flex items-center gap-1 shrink-0">
                        Full season details <FaChevronRight className="text-[10px]" />
                    </Link>
                </div>

                {/* Sim hint */}
                {todaysGames.length > 0 && (
                    <div className="flex items-center gap-1.5 px-4 md:px-6 py-1.5 text-[11px] font-medium border-b border-(--divider) bg-(--background-tertiary) text-(--text-tertiary)">
                        <FaDiceD20 className="text-(--text-secondary) shrink-0" />
                        <span>Click a game to watch it play out pitch by pitch, or take over and sim the rest yourself</span>
                    </div>
                )}

                {/* Scrollable game cards row */}
                <div className="overflow-x-auto scrollbar-hide">
                    <div className="flex gap-0 min-w-max">
                        {isLoadingGames && (
                            [...Array(6)].map((_, i) => (
                                <div key={i} className="w-36 shrink-0 px-4 py-3 border-r border-(--divider) animate-pulse">
                                    <div className="h-3 w-16 rounded-plate mb-2 bg-(--background-tertiary)" />
                                    <div className="h-3 w-20 rounded-plate mb-1 bg-(--background-tertiary)" />
                                    <div className="h-3 w-20 rounded-plate bg-(--background-tertiary)" />
                                </div>
                            ))
                        )}
                        {!isLoadingGames && todaysGames.length === 0 &&  (
                            <div className="px-6 py-4 text-sm text-(--text-tertiary)">
                                No games scheduled today.
                            </div>
                        )}
                        {!isLoadingGames && todaysGames.map((game) => fromScheduledGame(game)).sort((a, b) => {
                            const seasonId = tickerSeason?.season_id ?? '';
                            const aStarred = starredTeamKeys.includes(`${a.away.team.id}-${seasonId}`) || starredTeamKeys.includes(`${a.home.team.id}-${seasonId}`);
                            const bStarred = starredTeamKeys.includes(`${b.away.team.id}-${seasonId}`) || starredTeamKeys.includes(`${b.home.team.id}-${seasonId}`);
                            if (aStarred !== bStarred) return aStarred ? -1 : 1;
                            const statusOrder: Record<GameState, number> = { LIVE: 0, PREVIEW: 1, FINAL: 2, POSTPONED: 3 };
                            return statusOrder[a.state] - statusOrder[b.state];
                        }).map((game) => {
                            const isFinal = game.state === 'FINAL';
                            const isLive = game.state === 'LIVE';
                            const inning = game.situation?.inning;
                            const inningHalf = game.situation?.isTop ? '▲' : game.situation ? '▼' : '';
                            const isAwayStarred = starredTeamKeys.includes(`${game.away.team.id}-${tickerSeason?.season_id}`);
                            const isHomeStarred = starredTeamKeys.includes(`${game.home.team.id}-${tickerSeason?.season_id}`);
                            const statusLabel = game.date
                                ? new Date(game.date).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
                                : game.detailedState ?? '';

                            return (
                                <Link
                                    key={game.id}
                                    to={`/seasons/game/${game.id}${tickerSeason ? `?season=${tickerSeason.season_id}` : ''}`}
                                    className="w-36 shrink-0 px-4 py-3 border-r border-(--divider) transition-colors hover:bg-(--background-tertiary)"
                                >
                                    {/* Status */}
                                    <div className="mb-2 flex items-center justify-between gap-1.5 min-h-4.25">
                                        <GameStatePlate
                                            state={game.state}
                                            detailedState={isFinal ? (game.detailedState ?? 'Final') : statusLabel}
                                            liveDetail={isLive && inning != null ? `${inningHalf} ${inning}` : undefined}
                                        />
                                    </div>

                                    {/* Away team */}
                                    <div className="flex items-center justify-between gap-1 mb-1">
                                        <TeamChip team={game.away.team} record={game.away.record} size="sm" isStarred={isAwayStarred} />
                                        <span className="font-display-upright text-[17px] leading-none tabular-nums">{game.away.score == null ? "-" : game.away.score}</span>
                                    </div>

                                    {/* Home team */}
                                    <div className="flex items-center justify-between gap-1">
                                        <TeamChip team={game.home.team} record={game.home.record} size="sm" isStarred={isHomeStarred} />
                                        <span className="font-display-upright text-[17px] leading-none tabular-nums">{game.home.score == null ? "-" : game.home.score}</span>
                                    </div>
                                </Link>
                            );
                        })}
                    </div>
                </div>

                {/* Leaders rows */}
                <div className="relative border-t border-(--divider) px-4 md:px-6 py-4 space-y-4">
                    {isLoadingLeaders && (
                        <div className="absolute inset-0 z-10 flex items-center justify-center gap-2 bg-(--background-secondary)/70">
                            <span className="w-2 h-2 rounded-full animate-bounce [animation-delay:0ms] bg-(--text-tertiary)" />
                            <span className="w-2 h-2 rounded-full animate-bounce [animation-delay:150ms] bg-(--text-tertiary)" />
                            <span className="w-2 h-2 rounded-full animate-bounce [animation-delay:300ms] bg-(--text-tertiary)" />
                        </div>
                    )}
                    {(isLoadingLeaders && leaderGroups.length === 0 ? [null, null] : leaderGroups).map((group, gi) => {
                        const label = group?.leader_category ? (LEADER_CATEGORY_LABELS[group.leader_category] ?? group.leader_category) : '';
                        const entries = group ? (group.leaders ?? []).slice(0, 3) : [...Array(3)].map(() => null);
                        const isPitchingGroup = PITCHING_LEADER_CATEGORIES.has(group?.leader_category ?? '');
                        return (
                            <div key={group?.leader_category ?? gi}>
                                <Eyebrow>{label}</Eyebrow>
                                <div className="mt-2 flex gap-2 overflow-x-auto scrollbar-hide lg:grid lg:grid-cols-3">
                                    {entries.map((entry, i) => {
                                        const rawId = entry?.person?.id;
                                        const lookupKey = rawId != null && TWO_WAY_PLAYER_IDS.has(rawId)
                                            ? `${rawId}-${isPitchingGroup ? 'P' : 'H'}`
                                            : rawId != null ? String(rawId) : undefined;
                                        const card = lookupKey ? leaderCards[lookupKey] : undefined;
                                        return (
                                            <div key={entry?.rank ?? i} className="flex flex-col items-center gap-1 shrink-0 w-72 lg:w-auto">
                                                <CardItemFromCard
                                                    card={card}
                                                    className={`max-w-full w-full ${card ? 'cursor-pointer' : 'pointer-events-none'} ${!entry ? 'animate-pulse opacity-50' : ''}`}
                                                    onClick={card ? () => setSelectedModalCard(card) : undefined}
                                                    ptsChange={card?.points_change?.week || undefined}
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

            {/* Your Recent Cards - logged in users only */}
            {user && (isLoadingRecentCards || recentCards.length > 0) && (
                <div className="max-w-7xl mx-auto border-y py-4 border-(--divider)">
                    <HomeSectionHeader title="Your Recent Custom Cards" action={{ label: 'Build More', to: '/customs' }} />
                    <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
                        {isLoadingRecentCards
                            ? Array.from({ length: 8 }).map((_, i) => (
                                <div key={i} className="shrink-0 w-32 animate-pulse">
                                    <div
                                        className="w-full rounded-card bg-(--background-tertiary)"
                                        style={{ aspectRatio: '2.5 / 3.5' }}
                                    />
                                    <div className="mt-1.5 h-3 w-3/4 rounded-plate bg-(--background-tertiary)" />
                                    <div className="mt-1 h-2.5 w-1/2 rounded-plate bg-(--background-tertiary)" />
                                </div>
                            ))
                            : recentCards.map((item, index) => (
                                <button
                                    key={index}
                                    className="shrink-0 w-40 text-left group/card cursor-zoom-in"
                                    onClick={() => setRecentCardModal(item.fullUrl)}
                                >
                                    <div
                                        className="w-full rounded-card overflow-hidden bg-(--background-tertiary) relative"
                                        style={{ aspectRatio: '2.5 / 3.5' }}
                                    >
                                        <img
                                            src={item.thumbUrl}
                                            alt={`${item.record.player_name} card`}
                                            loading="lazy"
                                            className="w-full h-full object-center transition-transform duration-200 group-hover/card:scale-105"
                                        />
                                    </div>
                                    <div className="mt-1.5 px-0.5">
                                        <div className="text-xs font-semibold truncate">{item.record.player_name}</div>
                                        <div className="text-[11px] tabular-nums text-(--text-tertiary)">{item.record.year}</div>
                                    </div>
                                </button>
                            ))
                        }
                    </div>
                </div>
            )}

            {/* Recent card lightbox */}
            {recentCardModal && createPortal(
                <div
                    className="fixed inset-0 z-9999 flex items-center justify-center bg-black/80"
                    onClick={() => setRecentCardModal(null)}
                >
                    <button
                        className="absolute top-4 right-4 text-white/70 hover:text-white transition-colors text-xl cursor-pointer"
                        onClick={() => setRecentCardModal(null)}
                    >
                        <FaXmark />
                    </button>
                    <img
                        src={recentCardModal}
                        alt="Card full view"
                        className="max-h-[90vh] max-w-[90vw] object-contain rounded-card shadow-overlay"
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>,
                document.body
            )}

            {/* How it Works */}
            <div className="max-w-7xl mx-auto py-6 border-t border-(--divider)">
                <HomeSectionHeader title="How to Play" />

                {/* Steps: Side by Side on md+ */}
                <div className="grid md:grid-cols-2 gap-8 mb-12">
                    {/* Step 1: The Pitch */}
                    <div>
                        <div className="mb-3">
                            <Eyebrow className="text-(--showdown-red)">Step 1</Eyebrow>
                            <Heading level="section" as="h3" className="mt-1.5">The Pitch</Heading>
                            <p className="text-sm mt-1.5 text-(--text-tertiary)">Pitcher rolls to see who gets the advantage</p>
                        </div>

                        <div className="text-sm space-y-1.5 mb-3 text-(--text-secondary)">
                            <HowToPlayBullet side="pitcher">Pitcher's total <strong>(Control + Dice Roll)</strong> higher = Pitcher's advantage</HowToPlayBullet>
                            <HowToPlayBullet side="batter">Pitcher's total lower or tied = Batter's advantage</HowToPlayBullet>
                        </div>

                        <HomePanel className="p-4">
                            <div className='flex items-center justify-center gap-3'>
                                <div className='flex flex-col items-center gap-1'>
                                    <CardCommand isPitcher={true} primaryColor="rgb(200, 16, 46)" secondaryColor="rgb(255, 255, 255)" command={4} team="BOS" className="w-10 h-10 shrink-0" />
                                    <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Control</span>
                                </div>
                                <span className='text-lg font-display-upright leading-none'>+</span>
                                <div className='flex flex-col items-center gap-1'>
                                    <FaDiceD20 className="text-(--text-tertiary) w-10 h-10" />
                                    <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Dice Roll</span>
                                </div>
                                <span className="font-display uppercase text-sm px-3 text-(--text-tertiary)">vs</span>
                                <div className='flex flex-col items-center gap-1'>
                                    <CardCommand isPitcher={false} primaryColor="rgb(12, 35, 64)" secondaryColor="rgb(255, 255, 255)" command={8} team="NYY" className="w-10 h-10 shrink-0" />
                                    <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>On-Base</span>
                                </div>
                            </div>
                        </HomePanel>
                    </div>

                    {/* Step 2: The Swing */}
                    <div>
                        <div className="mb-3">
                            <Eyebrow className="text-(--showdown-blue)">Step 2</Eyebrow>
                            <Heading level="section" as="h3" className="mt-1.5">The Swing</Heading>
                            <p className="text-sm mt-1.5 text-(--text-tertiary)">Batter rolls to see what happens</p>
                        </div>

                        <div className="text-sm space-y-1.5 mb-3 text-(--text-secondary)">
                            <HowToPlayBullet side="pitcher"><strong>Pitcher's advantage:</strong> Find result on pitcher's chart</HowToPlayBullet>
                            <HowToPlayBullet side="batter"><strong>Batter's advantage:</strong> Find result on batter's chart</HowToPlayBullet>
                        </div>

                        <HomePanel className="p-3">
                            <div className="flex flex-col lg:flex-row items-center lg:items-start gap-2 max-w-full">

                                <div className='flex gap-3 items-center lg:items-start lg:mr-3'>
                                    <div className='flex flex-col items-center gap-1 pt-2'>
                                        <FaDiceD20 className="text-(--text-tertiary) w-6 h-6 lg:w-8 lg:h-8" />
                                        <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Roll</span>
                                    </div>
                                    <div className='flex flex-col items-center justify-center gap-0.5 pt-3 text-(--text-tertiary)'>
                                        <FaChevronRight className="hidden lg:block" />
                                        <FaChevronDown className="lg:hidden" />
                                        <span className="text-[7px] font-semibold uppercase">Find</span>
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
                                    <p className="text-[10px] text-(--text-tertiary)">Example: Roll 16 = Double!</p>
                                </div>
                            </div>
                        </HomePanel>
                    </div>
                </div>

                {/* Next Steps and Why it Works */}
                <div className="grid md:grid-cols-2 gap-8 mb-12">
                    {/* The Rest */}
                    <div>
                        <Heading level="section" as="h3" className="mb-4">Play out the Game</Heading>
                        <ul className="space-y-2 mb-4 text-(--text-secondary)">
                            <li className="flex items-start gap-2">
                                <span className="text-(--text-primary) font-bold mt-0.5">•</span>
                                <span><strong>Build your team:</strong> <span className="text-(--text-tertiary)">Draft players within a salary cap budget (or just pick your favorite all-stars!)</span></span>
                            </li>
                            <li className="flex items-start gap-2">
                                <span className="text-(--text-primary) font-bold mt-0.5">•</span>
                                <span><strong>Play 9 innings:</strong> <span className="text-(--text-tertiary)">Alternate pitching and batting through 9 innings</span></span>
                            </li>
                            <li className="flex items-start gap-2">
                                <span className="text-(--text-primary) font-bold mt-0.5">•</span>
                                <span><strong>Advanced Gameplay:</strong> <span className="text-(--text-tertiary)">Incorporate baserunning, fielding, and strategic decisions</span></span>
                            </li>
                        </ul>
                    </div>

                    {/* Why it works */}
                    <div className="max-w-3xl mx-auto">
                        <Heading level="section" as="h3" className="mb-4">Why it works</Heading>
                        <ul className="space-y-3 mb-4">
                            <li className="flex items-center gap-2"><FaDiceD20 className="text-(--text-secondary)" /> <span>20-sided dice system <span className="text-(--text-tertiary)">— Every at-bat is different to the randomness of a dice roll.</span></span></li>
                            <li className="flex items-center gap-2"><FaShieldAlt className="text-(--text-secondary)" /> <span>Real stats, simulated play <span className="text-(--text-tertiary)">— Players perform like they did in their actual season.</span></span></li>
                        </ul>
                        <div className="rounded-card p-4 text-sm bg-(--background-tertiary) text-(--text-secondary)">
                            <Heading level="panel" as="h4" className="mb-1">The beauty of Showdown</Heading>
                            <div className="text-(--text-tertiary)">"Dice rolls meet baseball stats. Fast-paced strategy with authentic player performance."</div>
                        </div>
                    </div>
                </div>

            </div>

            {/* Cards Section */}
            <div className="max-w-7xl mx-auto py-6 border-t border-(--divider)">
                <HomeSectionHeader title="Cards" action={{ label: 'Explore Cards', to: '/cards' }} />
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
                    <HomePanel className="overflow-hidden flex flex-col">
                        <HomePanelHeading Icon={FaAward} title="Card of the Day" description="Generated by the community, refreshed daily." />
                        <div className="flex-1 min-h-0 flex flex-col items-center justify-center gap-2">
                            <img
                                src={cardOfDayImageSrc}
                                alt="Card of the Day"
                                className={`w-full h-full max-w-full max-h-full rounded-card object-contain ${cardOfTheDay ? 'cursor-pointer' : 'animate-pulse'}`}
                                onClick={cardOfTheDay ? () => setSelectedModalCard(cardOfTheDay.card_data) : undefined}
                            />
                            <div className="text-xs text-center text-(--text-tertiary)">
                                {cardOfTheDay ? (
                                    <><span className="font-semibold">{cardOfTheDay.card_data.name}</span> - {cardOfTheDay.card_data.team} ({cardOfTheDay.card_data.year})</>
                                ) : (
                                    <div className="h-3 w-40 mx-auto rounded-plate bg-(--background-tertiary) animate-pulse" />
                                )}
                            </div>
                        </div>
                    </HomePanel>
                    <HomePanel className="overflow-hidden">
                        <HomePanelHeading Icon={FaFire} title="Trending this week" description="Players and seasons gaining attention recently." />
                        {trendingPlayers.length > 0 ? (
                            <div className='space-y-3'>
                                {trendingPlayers.slice(0, 4).map((card, index) => (
                                    <CardItemFromCard key={index} card={card.card_data} className="max-w-full" onClick={() => setSelectedModalCard(card.card_data)} />
                                ))}
                            </div>
                        ) : (
                            renderBlankExploreCards()
                        )}
                    </HomePanel>
                    <HomePanel className="overflow-visible">
                        <HomePanelHeading Icon={FaStar} title="Most Popular" description="Most created custom cards all-time." />
                        {popularCards.length > 0 ? (
                            <div className='space-y-3'>
                                {popularCards.slice(0, 4).map((card, index) => (
                                    <div key={index} className="relative max-w-full">
                                        <Plate variant="navy" size="sm" className="absolute z-10 -right-1.5 -top-1.5" title="Times created">
                                            {card.num_creations.toLocaleString()}
                                        </Plate>
                                        <CardItemFromCard card={card.card_data} className="max-w-full" onClick={() => setSelectedModalCard(card.card_data)} />
                                    </div>
                                ))}
                            </div>
                        ) : (
                            renderBlankExploreCards()
                        )}
                    </HomePanel>
                    <HomePanel className="overflow-hidden">
                        <HomePanelHeading Icon={FaUsers} title="Spotlight" description={spotlightCards.length > 0 ? spotlightCards[0].spotlight_reason : 'Curated sets and fun themes.'} />
                        {spotlightCards.length > 0 ? (
                            <div className='space-y-3'>
                                {spotlightCards.slice(0, 4).map((card, index) => (
                                    <CardItemFromCard key={index} card={card.card_data} className="max-w-full" onClick={() => setSelectedModalCard(card.card_data)} />
                                ))}
                            </div>
                        ) : (
                            renderBlankExploreCards()
                        )}
                    </HomePanel>
                </div>
            </div>

            {/* FAQ Section */}
            <div className="max-w-7xl mx-auto py-6 border-t border-(--divider)">
                <HomeSectionHeader title="FAQ" />
                <div className="grid md:grid-cols-2 gap-6">
                    {FAQ_ITEMS.map(({ question, answer }) => (
                        <HomePanel key={question} className="p-6">
                            <Heading level="panel" className="mb-2">{question}</Heading>
                            <p className="text-(--text-tertiary)">{answer}</p>
                        </HomePanel>
                    ))}
                </div>
            </div>

            {/* Footer */}
            <div className="max-w-7xl mx-auto py-4 border-t border-(--divider) flex flex-col items-center gap-2">
                <ShowdownBotLogo className="max-w-28 opacity-70" />
                <Link to="/privacy" className="text-xs text-(--text-tertiary) hover:text-(--text-primary) transition-colors">
                    Privacy Policy
                </Link>
            </div>

            {/* Card-back pinstripes behind the hero; last in the DOM so it doesn't take the
                first-child slot in the page's vertical spacing */}
            <PinstripeBackdrop heightClass="h-84" />

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
