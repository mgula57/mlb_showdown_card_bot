import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    fetchHistoricalTeams, fetchAsgSeasons,
    type HistoricalTeam, type HistoricalSeasonRef, type AsgTeamRef,
} from '../../api/mlbAPI';
import { useSiteSettings } from '../shared/SiteSettingsContext';
import { TeamPreviewCard, type TeamPreviewData } from './TeamPreviewCard';
import { TeamShelf } from './TeamShelf';
import { FaSpinner, FaMagnifyingGlass, FaXmark } from 'react-icons/fa6';

// League team-colors for the All-Star tiles / detail header.
export const ASG_COLORS: Record<string, { primary: string; secondary: string }> = {
    AL: { primary: 'rgb(200,16,46)', secondary: 'rgb(255,255,255)' },
    NL: { primary: 'rgb(0,45,114)', secondary: 'rgb(255,255,255)' },
};

/** Display identity for an All-Star team — shared by the tile and the full-detail header overlay. */
export function asgIdentity(season: string | number, league: string) {
    return {
        abbr: league,
        name: `${season} ${league} All-Stars`,
        primary_color: ASG_COLORS[league]?.primary,
        secondary_color: ASG_COLORS[league]?.secondary,
    };
}

/** Identity carried on navigation so the detail view can render colors/name without re-resolving. */
export type HistoricalNavState = {
    abbr: string;
    name: string;
    primary_color?: string;
    secondary_color?: string;
};

/** How many season shelves to mount at a time as the user scrolls back through history. */
const SEASONS_PER_PAGE = 4;
const SEARCH_LIMIT = 60;

const teamToPreview = (team: HistoricalTeam): TeamPreviewData => ({
    abbreviation: team.abbreviation || team.name,
    name: team.name,
    primary_color: team.primary_color,
    secondary_color: team.secondary_color,
    total_points: team.total_points,
    top_players: team.top_players,
});

/** One season's shelf. Teams are fetched when the shelf mounts, so scrolling back through
 *  history pages the data in rather than loading every season up front. */
function SeasonShelf({ season, teamCount, asgLeagues, showdownSet, onOpenTeam, onOpenAsg, className }: {
    season: number;
    teamCount: number;
    asgLeagues: string[];
    showdownSet?: string;
    onOpenTeam: (team: HistoricalTeam) => void;
    onOpenAsg: (season: number, league: string) => void;
    className?: string;
}) {
    const [teams, setTeams] = useState<HistoricalTeam[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        fetchHistoricalTeams({ season, showdownSet, limit: 200 })
            .then(result => { if (!cancelled) setTeams(result.teams); })
            .catch(() => { if (!cancelled) setTeams([]); })
            .finally(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, [season, showdownSet]);

    const asgPreview = (league: string): TeamPreviewData => {
        const id = asgIdentity(season, league);
        return {
            abbreviation: id.abbr, name: id.name,
            primary_color: id.primary_color, secondary_color: id.secondary_color,
            badge: 'All-Star',
        };
    };

    return (
        <TeamShelf title={String(season)} subtitle={`${teamCount} teams`} className={className}>
            {asgLeagues.map(league => (
                <TeamPreviewCard key={`asg-${season}-${league}`} team={asgPreview(league)} onClick={() => onOpenAsg(season, league)} />
            ))}
            {loading
                ? <div className="flex items-center px-6"><FaSpinner className="animate-spin text-(--text-tertiary)" /></div>
                : teams.map(team => (
                    <TeamPreviewCard key={team.team_id} team={teamToPreview(team)} onClick={() => onOpenTeam(team)} />
                ))}
        </TeamShelf>
    );
}

/** Browse pre-processed historical MLB rosters and All-Star teams music-app style.
 *  Seasons are shelves ordered newest-first — no dropdowns; each tile opens its own shareable page. */
export function HistoricalTeams({ horizontalPadding }: { horizontalPadding?: string }) {
    const { userShowdownSet } = useSiteSettings();
    const navigate = useNavigate();

    const [seasons, setSeasons] = useState<HistoricalSeasonRef[]>([]);
    const [visibleCount, setVisibleCount] = useState(SEASONS_PER_PAGE);
    const [asgTeams, setAsgTeams] = useState<AsgTeamRef[]>([]);

    const [query, setQuery] = useState('');
    const [searchResults, setSearchResults] = useState<HistoricalTeam[]>([]);
    const [searching, setSearching] = useState(false);

    const [loadingSeasons, setLoadingSeasons] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const sentinelRef = useRef<HTMLDivElement | null>(null);

    // Initial load: which seasons have pre-processed teams, and which have All-Star data.
    useEffect(() => {
        fetchHistoricalTeams({ showdownSet: userShowdownSet, limit: 1 })
            .then(result => setSeasons(result.seasons))
            .catch(err => setError(err.message ?? 'Failed to load historical teams.'))
            .finally(() => setLoadingSeasons(false));
        fetchAsgSeasons().then(setAsgTeams).catch(() => setAsgTeams([]));
    }, [userShowdownSet]);

    // Server-side search across every season, debounced.
    const searchQuery = query.trim();
    useEffect(() => {
        if (!searchQuery) { setSearchResults([]); setSearching(false); return; }
        let cancelled = false;
        setSearching(true);
        const timer = setTimeout(() => {
            fetchHistoricalTeams({ q: searchQuery, showdownSet: userShowdownSet, limit: SEARCH_LIMIT })
                .then(result => { if (!cancelled) setSearchResults(result.teams); })
                .catch(() => { if (!cancelled) setSearchResults([]); })
                .finally(() => { if (!cancelled) setSearching(false); });
        }, 300);
        return () => { cancelled = true; clearTimeout(timer); };
    }, [searchQuery, userShowdownSet]);

    // Mount more season shelves as the sentinel scrolls into view.
    useEffect(() => {
        const sentinel = sentinelRef.current;
        if (!sentinel || searchQuery) return;
        const observer = new IntersectionObserver(entries => {
            if (entries[0]?.isIntersecting) {
                setVisibleCount(count => Math.min(count + SEASONS_PER_PAGE, seasons.length));
            }
        }, { rootMargin: '400px' });
        observer.observe(sentinel);
        return () => observer.disconnect();
    }, [seasons.length, searchQuery]);

    // Navigate to a team's own shareable detail page. Identity is passed via nav state so the
    // detail view renders instantly; a cold link resolves identity server-side.
    const openTeam = useCallback((team: HistoricalTeam) => {
        const state: HistoricalNavState = {
            abbr: team.abbreviation || team.name,
            name: team.name,
            primary_color: team.primary_color ?? undefined,
            secondary_color: team.secondary_color ?? undefined,
        };
        navigate(`/teams/historical/${team.sport_id}/${team.season}/${team.team_id}`, { state });
    }, [navigate]);

    const openAsg = useCallback((season: number, league: string) => {
        navigate(`/teams/asg/${season}/${league}`);
    }, [navigate]);

    // AL before NL, so the All-Star tiles lead each shelf in a stable order.
    const asgLeaguesBySeason = useMemo(() => {
        const map = new Map<number, string[]>();
        for (const asg of asgTeams) {
            const leagues = map.get(asg.season) ?? [];
            leagues.push(asg.league);
            map.set(asg.season, leagues);
        }
        map.forEach(leagues => leagues.sort());
        return map;
    }, [asgTeams]);

    return (
        <div className="relative flex flex-col gap-5">
            {/* Search across every season — replaces the old season/sport dropdowns */}
            <div className={horizontalPadding ?? ''}>
                <div className="relative w-full sm:max-w-xs">
                    <FaMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 text-[12px] text-(--text-tertiary)" />
                    <input
                        type="text"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder="Search all teams…"
                        className="w-full pl-9 pr-9 py-2 rounded-xl bg-(--background-secondary) border border-(--divider) text-[13px] text-(--text-primary) placeholder:text-(--text-tertiary) focus:outline-none focus:border-(--text-tertiary)"
                    />
                    {query && (
                        <button
                            type="button"
                            onClick={() => setQuery('')}
                            className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 rounded-full text-(--text-tertiary) hover:bg-(--divider) cursor-pointer"
                            aria-label="Clear search"
                        >
                            <FaXmark className="text-[12px]" />
                        </button>
                    )}
                </div>
            </div>

            {error && (
                <div className={`${horizontalPadding ?? ''} mx-4 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5`}>
                    {error}
                </div>
            )}

            {searchQuery ? (
                /* Search results — a flat grid spanning every season */
                searching ? (
                    <div className="flex justify-center py-12"><FaSpinner className="animate-spin text-(--text-tertiary) text-xl" /></div>
                ) : searchResults.length === 0 ? (
                    <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No teams match “{searchQuery}”.</p>
                ) : (
                    <div className={`flex flex-wrap gap-3 ${horizontalPadding ?? ''}`}>
                        {searchResults.map(team => (
                            <TeamPreviewCard
                                key={`${team.season}-${team.team_id}`}
                                team={{ ...teamToPreview(team), badge: String(team.season) }}
                                onClick={() => openTeam(team)}
                            />
                        ))}
                    </div>
                )
            ) : loadingSeasons ? (
                <div className="flex justify-center py-12"><FaSpinner className="animate-spin text-(--text-tertiary) text-xl" /></div>
            ) : seasons.length === 0 ? (
                <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No historical teams have been processed yet.</p>
            ) : (
                <>
                    {seasons.slice(0, visibleCount).map(({ season, team_count }) => (
                        <SeasonShelf
                            key={season}
                            season={season}
                            teamCount={team_count}
                            asgLeagues={asgLeaguesBySeason.get(season) ?? []}
                            showdownSet={userShowdownSet}
                            onOpenTeam={openTeam}
                            onOpenAsg={openAsg}
                            className={horizontalPadding ?? ''}
                        />
                    ))}
                    <div ref={sentinelRef} className="h-8" />
                </>
            )}
        </div>
    );
}

export default HistoricalTeams;
