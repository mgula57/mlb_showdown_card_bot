import { useEffect, useMemo, useState } from 'react';
import { fetchPublicTeams, type TeamSummary } from '../../api/userTeams';
import { TeamPreviewCard } from './TeamPreviewCard';
import { TeamShelf, TeamShelfSkeleton } from './TeamShelf';
import CustomSelect, { type SelectOption } from '../shared/CustomSelect';
import { TeamSearchInput } from './TeamSearchInput';
import { matchesTeamQuery } from './teamSearch';

// Set ordering for the "by set" shelves — newest curated sets first.
const SET_ORDER = ['2000', '2001', '2002', '2003', '2004', '2005', 'EXPANDED', 'CLASSIC'];

type SortKey = 'recent' | 'points' | 'name' | 'roster';

const SORT_OPTIONS: SelectOption[] = [
    { value: 'recent', label: 'Recently Added' },
    { value: 'points', label: 'Most Points' },
    { value: 'name', label: 'Name (A–Z)' },
    { value: 'roster', label: 'Roster Size' },
];

function sortTeams(list: TeamSummary[], sortBy: SortKey): TeamSummary[] {
    const sorted = [...list];
    switch (sortBy) {
        case 'points': sorted.sort((a, b) => b.total_points - a.total_points); break;
        case 'name': sorted.sort((a, b) => a.name.localeCompare(b.name)); break;
        case 'roster': sorted.sort((a, b) => b.roster_count - a.roster_count); break;
        case 'recent':
        default: sorted.sort((a, b) => (b.created_at ?? '') > (a.created_at ?? '') ? 1 : -1); break;
    }
    return sorted;
}

type CommunityTeamsProps = {
    onOpen: (team: TeamSummary) => void;
    /** Horizontal page padding — applied to headers/search, while shelves bleed to the screen edge. */
    horizontalPadding?: string;
    /** When embedded in the Browse tab, the parent owns the search box — hide the local one. */
    hideSearch?: boolean;
    /** Search query supplied by the parent when `hideSearch` is set. */
    externalQuery?: string;
};

/** Browse everyone's public teams music-app style: shelves of preview tiles, with search-as-a-mode.
 *  The viewer's own public teams are included here (tagged "Your team" on the tile), not hidden. */
export function CommunityTeams({ onOpen, horizontalPadding, hideSearch = false, externalQuery }: CommunityTeamsProps) {
    const [internalQuery, setInternalQuery] = useState('');
    const query = hideSearch ? (externalQuery ?? '') : internalQuery;
    const setQuery = setInternalQuery;
    const [sortBy, setSortBy] = useState<SortKey>('recent');
    const [allTeams, setAllTeams] = useState<TeamSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Initial browse payload — one larger page (backend's max) bucketed into shelves and searched
    // client-side. Runs once on mount; `loading` already starts true.
    useEffect(() => {
        fetchPublicTeams('user', 200, 0)
            .then(list => setAllTeams(list))
            .catch(err => setError(err.message ?? 'Failed to load teams.'))
            .finally(() => setLoading(false));
    }, []);

    // Only show teams whose roster is actually complete — in-progress drafts don't belong here.
    const completeTeams = useMemo(() => allTeams.filter(t => !t.is_drafting), [allTeams]);

    // Client-side search over the loaded pool — matches by name/abbreviation or by Showdown set.
    const results = useMemo(() => {
        const q = query.trim();
        if (!q) return null;
        return sortTeams(completeTeams.filter(t => matchesTeamQuery(t, q)), sortBy);
    }, [completeTeams, query, sortBy]);

    const shelves = useMemo(() => {
        const recentlyAdded = [...completeTeams]
            .sort((a, b) => (b.created_at ?? '') > (a.created_at ?? '') ? 1 : -1)
            .slice(0, 15);
        const topPoints = [...completeTeams]
            .filter(t => t.total_points > 0)
            .sort((a, b) => b.total_points - a.total_points)
            .slice(0, 15);

        const bySet = new Map<string, TeamSummary[]>();
        for (const t of completeTeams) {
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
    }, [completeTeams]);

    const px = horizontalPadding ?? '';

    return (
        <div className="flex flex-col gap-5">
            {/* Search bar — hidden when the Browse tab supplies the query */}
            {!hideSearch && (
                <div className={px}>
                    <TeamSearchInput
                        value={query}
                        onChange={setQuery}
                        placeholder="Search public teams by name or set (e.g. Expanded)…"
                    />
                </div>
            )}

            {error && (
                <div className={`${px} text-[12px] text-red-400`}>
                    <div className="px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                        {error}
                    </div>
                </div>
            )}

            {/* Initial payload still loading — skeleton shelves regardless of search mode */}
            {loading ? (
                <TeamShelfSkeleton shelves={3} className={px} />
            ) : results !== null ? (
                results.length === 0 ? (
                    <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No public teams match “{query.trim()}”.</p>
                ) : (
                    <div className={px}>
                        <div className="flex items-center justify-between mb-3">
                            <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide">
                                {results.length} result{results.length === 1 ? '' : 's'}
                            </div>
                            <CustomSelect
                                value={sortBy}
                                onChange={v => setSortBy(v as SortKey)}
                                options={SORT_OPTIONS}
                                buttonClassName="px-2.5 py-1.5 rounded-lg border border-(--divider) bg-(--background-secondary) text-(--text-primary) text-[12px] text-nowrap cursor-pointer flex items-center"
                                dropdownArrowSize={12}
                            />
                        </div>
                        <div className="flex flex-wrap gap-3">
                            {results.map(team => (
                                <TeamPreviewCard key={team.team_id} team={team} onClick={() => onOpen(team)} />
                            ))}
                        </div>
                    </div>
                )
            ) : shelves.recentlyAdded.length === 0 ? (
                <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No public teams yet.</p>
            ) : (
                /* Browse (shelves) mode — headers indented by `px`, tile rows bleed to the screen edge. */
                <>
                    <TeamShelf title="Recently Added" className={px} bleedRight>
                        {shelves.recentlyAdded.map(team => (
                            <TeamPreviewCard key={team.team_id} team={team} onClick={() => onOpen(team)} />
                        ))}
                    </TeamShelf>

                    {shelves.topPoints.length > 0 && (
                        <TeamShelf title="Heavy Hitters" subtitle="Most points" className={px} bleedRight>
                            {shelves.topPoints.map(team => (
                                <TeamPreviewCard key={team.team_id} team={team} onClick={() => onOpen(team)} />
                            ))}
                        </TeamShelf>
                    )}

                    {shelves.setShelves.map(([set, list]) => (
                        <TeamShelf key={set} title={set === 'Other' ? 'Other Sets' : `${set} Set`} className={px} bleedRight>
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
