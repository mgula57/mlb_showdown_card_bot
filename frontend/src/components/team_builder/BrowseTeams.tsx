import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchPublicTeams, type TeamSummary } from '../../api/userTeams';
import { fetchHistoricalTeams, type HistoricalTeam } from '../../api/mlbAPI';
import { useSiteSettings } from '../shared/SiteSettingsContext';
import { TeamPreviewCard } from './TeamPreviewCard';
import { TeamSearchInput } from './TeamSearchInput';
import { matchesTeamQuery } from './teamSearch';
import { CommunityTeams } from './CommunityTeams';
import { FeaturedCollections } from './FeaturedCollections';
import { HistoricalTeams, type HistoricalNavState } from './HistoricalTeams';
import CustomSelect, { type SelectOption } from '../shared/CustomSelect';
import { FaSpinner } from 'react-icons/fa6';

type BrowseType = 'all' | 'featured' | 'community' | 'historical';

const TYPE_OPTIONS: SelectOption[] = [
    { value: 'all', label: 'All Teams' },
    { value: 'featured', label: 'Featured' },
    { value: 'community', label: 'Community' },
    { value: 'historical', label: 'Historical' },
];

/** A merged search hit — either a saved public team or a pre-processed historical team. */
type Hit =
    | { kind: 'public'; team: TeamSummary }
    | { kind: 'historical'; team: HistoricalTeam };

const TYPE_RANK: Record<string, number> = { official: 0, user: 1, historical: 2 };

type BrowseTeamsProps = {
    onOpenTeam: (team: TeamSummary) => void;
    horizontalPadding?: string;
    currentUserId?: string | null;
    /** The signed-in user's own teams — folded into search so their private/unlisted teams
     *  surface alongside the public results (public ones already come back from the API). */
    myTeams?: TeamSummary[];
};

export function BrowseTeams({ onOpenTeam, horizontalPadding, currentUserId, myTeams = [] }: BrowseTeamsProps) {
    const navigate = useNavigate();
    const { userShowdownSet } = useSiteSettings();
    const [type, setType] = useState<BrowseType>('all');
    const [query, setQuery] = useState('');
    const px = horizontalPadding ?? '';

    const q = query.trim();
    const [hits, setHits] = useState<Hit[] | null>(null);
    const [searching, setSearching] = useState(false);

    // Unified search across public + historical teams. Only runs for the "all" type — the
    // scoped types delegate to their own components' search paths.
    useEffect(() => {
        if (type !== 'all' || !q) { setHits(null); setSearching(false); return; }
        let cancelled = false;
        setSearching(true);
        const timer = setTimeout(async () => {
            const [publicTeams, historical] = await Promise.all([
                fetchPublicTeams(['official', 'user'], 60, 0, q).catch(() => [] as TeamSummary[]),
                fetchHistoricalTeams({ q, showdownSet: userShowdownSet, limit: 40 })
                    .then(r => r.teams).catch(() => [] as HistoricalTeam[]),
            ]);
            if (cancelled) return;
            const isOwn = (t: TeamSummary) => !!currentUserId && t.user_id === currentUserId;
            // In-progress drafts don't belong in Browse — the viewer's own included.
            const merged: Hit[] = [
                // The user's own teams (including private ones) aren't in the public payload.
                ...myTeams.filter(t => !t.is_drafting && matchesTeamQuery(t, q))
                    .map(team => ({ kind: 'public' as const, team })),
                ...publicTeams.filter(t => !isOwn(t) && !t.is_drafting)
                    .map(team => ({ kind: 'public' as const, team })),
                ...historical.map(team => ({ kind: 'historical' as const, team })),
            ];
            merged.sort((a, b) => {
                const an = a.team.name.toLowerCase() === q.toLowerCase() ? 0 : 1;
                const bn = b.team.name.toLowerCase() === q.toLowerCase() ? 0 : 1;
                if (an !== bn) return an - bn;
                const ao = a.kind === 'public' && isOwn(a.team) ? 0 : 1;
                const bo = b.kind === 'public' && isOwn(b.team) ? 0 : 1;
                if (ao !== bo) return ao - bo;
                const at = a.kind === 'public' ? (a.team.source ?? 'user') : 'historical';
                const bt = b.kind === 'public' ? (b.team.source ?? 'user') : 'historical';
                if (TYPE_RANK[at] !== TYPE_RANK[bt]) return TYPE_RANK[at] - TYPE_RANK[bt];
                return (b.team.total_points ?? 0) - (a.team.total_points ?? 0);
            });
            setHits(merged);
            setSearching(false);
        }, 300);
        return () => { cancelled = true; clearTimeout(timer); };
    }, [type, q, userShowdownSet, currentUserId, myTeams]);

    function openHistorical(team: HistoricalTeam) {
        const state: HistoricalNavState = {
            abbr: team.abbreviation || team.name,
            name: team.name,
            primary_color: team.primary_color ?? undefined,
            secondary_color: team.secondary_color ?? undefined,
        };
        navigate(`/teams/historical/${team.sport_id}/${team.season}/${team.team_id}`, { state });
    }
    const openHit = (hit: Hit) => hit.kind === 'public' ? onOpenTeam(hit.team) : openHistorical(hit.team);

    const searchModeResults = useMemo(() => {
        if (hits === null) return null;
        return hits;
    }, [hits]);

    return (
        <div className="flex flex-col gap-5">
            {/* Type filter + unified search */}
            <div className={`${px} flex flex-wrap items-center gap-2`}>

                <div className="flex-1 min-w-48">
                    <TeamSearchInput
                        value={query}
                        onChange={setQuery}
                        placeholder="Search teams by name or set…"
                    />
                </div>
                <CustomSelect
                    value={type}
                    onChange={v => setType(v as BrowseType)}
                    options={TYPE_OPTIONS}
                    buttonClassName="px-2.5 py-2 rounded-lg border border-(--divider) bg-(--background-secondary) text-(--text-primary) text-[13px] text-nowrap cursor-pointer flex items-center"
                    dropdownArrowSize={12}
                />
            </div>

            {/* "All" + query → merged results grid */}
            {type === 'all' && q ? (
                searching ? (
                    <div className="flex justify-center py-12"><FaSpinner className="animate-spin text-(--text-tertiary) text-xl" /></div>
                ) : !searchModeResults || searchModeResults.length === 0 ? (
                    <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No teams match “{q}”.</p>
                ) : (
                    <div className={px}>
                        <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide mb-3">
                            {searchModeResults.length} result{searchModeResults.length === 1 ? '' : 's'}
                        </div>
                        <div className="flex flex-wrap gap-3">
                            {searchModeResults.map(hit => (
                                <TeamPreviewCard
                                    key={hit.team.team_id}
                                    team={hit.team}
                                    onClick={() => openHit(hit)}
                                />
                            ))}
                        </div>
                    </div>
                )
            ) : (
                <>
                    {(type === 'all' || type === 'featured') && (
                        <FeaturedCollections
                            onOpen={onOpenTeam}
                            onOpenCollection={slug => navigate(`/teams/collections/${slug}`)}
                            horizontalPadding={px}
                            query={type === 'featured' ? q : undefined}
                        />
                    )}
                    {(type === 'all' || type === 'community') && (
                        <CommunityTeams
                            onOpen={onOpenTeam}
                            horizontalPadding={px}
                            hideSearch
                            externalQuery={type === 'community' ? q : ''}
                        />
                    )}
                    {(type === 'all' || type === 'historical') && (
                        <>
                            {type === 'all' && (
                                <div className={px}>
                                    <h3 className="text-[15px] font-black text-(--text-primary)">Historical Teams</h3>
                                    <p className="text-[12px] text-(--text-secondary)">
                                        Real MLB rosters and All-Star squads, season by season.
                                    </p>
                                </div>
                            )}
                            <HistoricalTeams horizontalPadding={px} hideSearch={type === 'all'} />
                        </>
                    )}
                </>
            )}
        </div>
    );
}

export default BrowseTeams;
