import { useEffect, useMemo, useState } from 'react';
import { fetchPublicTeams, type TeamSummary } from '../../api/userTeams';
import { TeamPreviewCard } from './TeamPreviewCard';
import { TeamShelf } from './TeamShelf';
import { FaMagnifyingGlass, FaSpinner, FaXmark } from 'react-icons/fa6';

// Set ordering for the "by set" shelves — newest curated sets first.
const SET_ORDER = ['2000', '2001', '2002', '2003', '2004', '2005', 'EXPANDED', 'CLASSIC'];

type CommunityTeamsProps = {
    onOpen: (team: TeamSummary) => void;
    className?: string;
    /** Signed-in user's id — their own public teams are hidden here (they live under "My Teams"). */
    currentUserId?: string | null;
};

/** Browse other users' public teams music-app style: shelves of preview tiles, with search-as-a-mode. */
export function CommunityTeams({ onOpen, className, currentUserId }: CommunityTeamsProps) {
    const [query, setQuery] = useState('');
    const [allTeams, setAllTeams] = useState<TeamSummary[]>([]);
    const [results, setResults] = useState<TeamSummary[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [searching, setSearching] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const hideOwn = (list: TeamSummary[]) => currentUserId ? list.filter(t => t.user_id !== currentUserId) : list;

    // Initial browse payload — one larger page bucketed into shelves client-side.
    useEffect(() => {
        setLoading(true);
        fetchPublicTeams('user', 120, 0)
            .then(list => setAllTeams(hideOwn(list)))
            .catch(err => setError(err.message ?? 'Failed to load teams.'))
            .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentUserId]);

    // Debounced server search — switches the view to a results grid while a query is present.
    useEffect(() => {
        const q = query.trim();
        if (!q) { setResults(null); setSearching(false); return; }
        setSearching(true);
        const handle = setTimeout(() => {
            fetchPublicTeams('user', 60, 0, q)
                .then(list => setResults(hideOwn(list)))
                .catch(() => setResults([]))
                .finally(() => setSearching(false));
        }, 300);
        return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [query, currentUserId]);

    const shelves = useMemo(() => {
        const withRoster = allTeams.filter(t => t.roster_count > 0);
        const recentlyAdded = [...withRoster]
            .sort((a, b) => (b.created_at ?? '') > (a.created_at ?? '') ? 1 : -1)
            .slice(0, 15);
        const topPoints = [...withRoster]
            .filter(t => t.total_points > 0)
            .sort((a, b) => b.total_points - a.total_points)
            .slice(0, 15);

        const bySet = new Map<string, TeamSummary[]>();
        for (const t of withRoster) {
            const set = (t.allowed_sets && t.allowed_sets[0]) || 'Other';
            if (!bySet.has(set)) bySet.set(set, []);
            bySet.get(set)!.push(t);
        }
        const setShelves = [...bySet.entries()]
            .sort(([a], [b]) => {
                const ia = SET_ORDER.indexOf(a); const ib = SET_ORDER.indexOf(b);
                return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
            })
            .filter(([, list]) => list.length > 0);

        return { recentlyAdded, topPoints, setShelves };
    }, [allTeams]);

    return (
        <div className={`flex flex-col gap-5 ${className ?? ''}`}>
            {/* Search bar */}
            <div className="relative">
                <FaMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 text-[12px] text-(--text-tertiary)" />
                <input
                    type="text"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    placeholder="Search public teams by name…"
                    className="w-full pl-9 pr-9 py-2.5 rounded-xl bg-(--background-secondary) border border-(--divider) text-[13px] text-(--text-primary) placeholder:text-(--text-tertiary) focus:outline-none focus:border-(--text-tertiary)"
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

            {error && (
                <div className="mx-4 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                    {error}
                </div>
            )}

            {/* Search results mode */}
            {results !== null ? (
                searching && results.length === 0 ? (
                    <div className="flex justify-center py-12"><FaSpinner className="animate-spin text-(--text-tertiary) text-xl" /></div>
                ) : results.length === 0 ? (
                    <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No public teams match “{query.trim()}”.</p>
                ) : (
                    <div className="px-4">
                        <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide mb-3">
                            {results.length} result{results.length === 1 ? '' : 's'}
                        </div>
                        <div className="flex flex-wrap gap-3">
                            {results.map(team => (
                                <TeamPreviewCard key={team.team_id} team={team} size="sm" onClick={() => onOpen(team)} />
                            ))}
                        </div>
                    </div>
                )
            ) : loading ? (
                <div className="flex justify-center py-12"><FaSpinner className="animate-spin text-(--text-tertiary) text-xl" /></div>
            ) : shelves.recentlyAdded.length === 0 ? (
                <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No public teams yet.</p>
            ) : (
                /* Browse (shelves) mode */
                <>
                    <TeamShelf title="Recently Added">
                        {shelves.recentlyAdded.map(team => (
                            <TeamPreviewCard key={team.team_id} team={team} onClick={() => onOpen(team)} />
                        ))}
                    </TeamShelf>

                    {shelves.topPoints.length > 0 && (
                        <TeamShelf title="Heavy Hitters" subtitle="Most points">
                            {shelves.topPoints.map(team => (
                                <TeamPreviewCard key={team.team_id} team={team} onClick={() => onOpen(team)} />
                            ))}
                        </TeamShelf>
                    )}

                    {shelves.setShelves.map(([set, list]) => (
                        <TeamShelf key={set} title={set === 'Other' ? 'Other Sets' : `${set} Set`}>
                            {list.map(team => (
                                <TeamPreviewCard key={team.team_id} team={team} onClick={() => onOpen(team)} />
                            ))}
                        </TeamShelf>
                    ))}
                </>
            )}
        </div>
    );
}

export default CommunityTeams;
