import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaLayerGroup, FaStar, FaUsers, FaClockRotateLeft, FaTrophy } from 'react-icons/fa6';
import { fetchPublicTeams, type TeamSummary } from '../../api/userTeams';
import { fetchHistoricalTeams, type HistoricalTeam, fetchEraTeams, type EraTeam, ALL_TIME_ERA_KEY } from '../../api/mlbAPI';
import { useSiteSettings } from '../shared/SiteSettingsContext';
import { TeamPreviewCard, TeamPreviewCardSkeleton } from './TeamPreviewCard';
import { TeamSearchInput } from './TeamSearchInput';
import { matchesTeamQuery } from './teamSearch';
import { CommunityTeams } from './CommunityTeams';
import { FeaturedCollections } from './FeaturedCollections';
import { HistoricalTeams, type HistoricalNavState } from './HistoricalTeams';
import { EraTeams } from './EraTeams';
import CustomSelect, { type SelectOption } from '../shared/CustomSelect';

type BrowseType = 'all' | 'featured' | 'community' | 'historical' | 'era';

const TYPE_OPTIONS: SelectOption[] = [
    { value: 'all', label: 'All Teams', icon: <FaLayerGroup /> },
    { value: 'featured', label: 'Featured', icon: <FaStar /> },
    { value: 'community', label: 'Community', icon: <FaUsers /> },
    { value: 'era', label: 'Eras', icon: <FaTrophy /> },
    { value: 'historical', label: 'Historical', icon: <FaClockRotateLeft /> },
];

const BROWSE_TYPE_STORAGE_KEY = 'browseTeams.type';

function loadStoredBrowseType(): BrowseType {
    try {
        const stored = localStorage.getItem(BROWSE_TYPE_STORAGE_KEY);
        if (TYPE_OPTIONS.some(o => o.value === stored)) return stored as BrowseType;
    } catch {
        // ignore
    }
    return 'all';
}

/** A merged search hit — either a saved public team, a pre-processed historical team, or a
 *  pre-processed era team (unified search only looks at the ALL_TIME era, not every decade). */
type Hit =
    | { kind: 'public'; team: TeamSummary }
    | { kind: 'era'; team: EraTeam }
    | { kind: 'historical'; team: HistoricalTeam };

const TYPE_RANK: Record<string, number> = { official: 0, user: 1, historical: 2, era: 3 };

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
    const [type, setType] = useState<BrowseType>(loadStoredBrowseType);
    const [query, setQuery] = useState('');
    const px = horizontalPadding ?? '';

    // Re-apply the remembered filter after mount too, in case it changed in
    // another tab between the lazy-init read and this component mounting.
    useEffect(() => {
        setType(loadStoredBrowseType());
    }, []);

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
            const [publicTeams, historical, eraTeams] = await Promise.all([
                fetchPublicTeams(['official', 'user'], 60, 0, q).catch(() => [] as TeamSummary[]),
                fetchHistoricalTeams({ q, showdownSet: userShowdownSet, limit: 40 })
                    .then(r => r.teams).catch(() => [] as HistoricalTeam[]),
                fetchEraTeams({ era: ALL_TIME_ERA_KEY, q, showdownSet: userShowdownSet, limit: 40 })
                    .then(r => r.teams).catch(() => [] as EraTeam[]),
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
                ...eraTeams.map(team => ({ kind: 'era' as const, team })),
            ];
            merged.sort((a, b) => {
                const an = a.team.name.toLowerCase() === q.toLowerCase() ? 0 : 1;
                const bn = b.team.name.toLowerCase() === q.toLowerCase() ? 0 : 1;
                if (an !== bn) return an - bn;
                const ao = a.kind === 'public' && isOwn(a.team) ? 0 : 1;
                const bo = b.kind === 'public' && isOwn(b.team) ? 0 : 1;
                if (ao !== bo) return ao - bo;
                const at = a.kind === 'public' ? (a.team.source ?? 'user') : a.kind;
                const bt = b.kind === 'public' ? (b.team.source ?? 'user') : b.kind;
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
    function openEra(team: EraTeam) {
        const state: HistoricalNavState = {
            abbr: team.abbreviation || team.name,
            name: team.name,
            primary_color: team.primary_color ?? undefined,
            secondary_color: team.secondary_color ?? undefined,
        };
        navigate(`/teams/era/${team.sport_id}/${team.era}/${team.team_id}`, { state });
    }
    const openHit = (hit: Hit) => {
        if (hit.kind === 'public') return onOpenTeam(hit.team);
        if (hit.kind === 'historical') return openHistorical(hit.team);
        return openEra(hit.team);
    };
    // Unified search only ever queries the ALL_TIME era (see the Promise.all above), so the
    // display prefix here is fixed rather than looked up — hit.team.name itself stays plain.
    const hitPreview = (hit: Hit) => hit.kind === 'era' ? { ...hit.team, name: `All-Time ${hit.team.name}` } : hit.team;

    const searchModeResults = useMemo(() => {
        if (hits === null) return null;
        return hits;
    }, [hits]);

    return (
        <div className="flex flex-col gap-5">
            {/* Type filter + unified search */}
            <div className={`${px} flex flex-wrap items-center gap-2`}>

                <CustomSelect
                    value={type}
                    onChange={v => {
                        const next = v as BrowseType;
                        setType(next);
                        try {
                            localStorage.setItem(BROWSE_TYPE_STORAGE_KEY, next);
                        } catch {
                            // ignore
                        }
                    }}
                    options={TYPE_OPTIONS}
                    buttonClassName="px-2.5 py-2 rounded-lg border border-(--divider) bg-(--background-secondary) text-(--text-primary) text-[13px] text-nowrap cursor-pointer flex items-center"
                    dropdownArrowSize={12}
                />

                <div className="flex-1 min-w-48 max-w-88">
                    <TeamSearchInput
                        value={query}
                        onChange={setQuery}
                        placeholder="Search teams by name or set…"
                    />
                </div>
                
            </div>

            {/* "All" + query → merged results grid */}
            {type === 'all' && q ? (
                searching ? (
                    <div className={px}>
                        <div className="flex flex-wrap gap-3">
                            {Array.from({ length: 12 }, (_, i) => <TeamPreviewCardSkeleton key={i} />)}
                        </div>
                    </div>
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
                                    key={`${hit.kind}-${hit.team.team_id}`}
                                    team={hitPreview(hit)}
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
                    {(type === 'all' || type === 'era') && (
                        <>
                            {type === 'all' && (
                                <div className={px}>
                                    <h3 className="text-[15px] font-black text-(--text-primary)">Era Teams</h3>
                                    <p className="text-[12px] text-(--text-secondary)">
                                        Every franchise's best-ever roster — all-time, or a single decade — drafted from each player's single greatest qualifying season.
                                    </p>
                                </div>
                            )}
                            <EraTeams horizontalPadding={px} hideSearch externalQuery={type === 'era' ? q : ''} />
                        </>
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
                            <HistoricalTeams horizontalPadding={px} hideSearch externalQuery={type === 'historical' ? q : ''} />
                        </>
                    )}

                </>
            )}
        </div>
    );
}

export default BrowseTeams;
