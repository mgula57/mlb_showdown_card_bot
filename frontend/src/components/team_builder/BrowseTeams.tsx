import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaLayerGroup, FaStar, FaUsers, FaClockRotateLeft, FaTrophy } from 'react-icons/fa6';
import { fetchPublicTeams, type TeamSummary } from '../../api/userTeams';
import { fetchHistoricalTeams, type HistoricalTeam, fetchEraTeams, type EraTeam, ALL_TIME_ERA_KEY } from '../../api/mlbAPI';
import { showdownSets, imageForSet } from '../shared/SiteSettingsContext';
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
const BROWSE_SET_STORAGE_KEY = 'browseTeams.set';

// "" = All Sets, meaning no set filter at all.
const SET_OPTIONS: SelectOption[] = [
    { value: '', label: 'All Sets', icon: <FaLayerGroup /> },
    ...showdownSets.map(s => ({ value: s.value, label: s.value, image: imageForSet(s.value, true) })),
];

// Navigating into a team's detail page fully unmounts this tree (it's a distinct top-level
// view in TeamBuilder, not a nested route), so scroll position can't just live in state here --
// it has to survive the unmount in storage instead.
const BROWSE_SCROLL_STORAGE_KEY = 'browseTeams.scrollY';

function loadStoredBrowseType(): BrowseType {
    try {
        const stored = localStorage.getItem(BROWSE_TYPE_STORAGE_KEY);
        if (TYPE_OPTIONS.some(o => o.value === stored)) return stored as BrowseType;
    } catch {
        // ignore
    }
    return 'all';
}

function loadStoredSetFilter(): string {
    try {
        const stored = localStorage.getItem(BROWSE_SET_STORAGE_KEY);
        if (stored !== null && SET_OPTIONS.some(o => o.value === stored)) return stored;
    } catch {
        // ignore
    }
    return '';
}

/** A merged search hit — either a saved public team, a pre-processed historical team, or a
 *  pre-processed era team (unified search only looks at the ALL_TIME era, not every decade). */
type Hit =
    | { kind: 'public'; team: TeamSummary }
    | { kind: 'era'; team: EraTeam }
    | { kind: 'historical'; team: HistoricalTeam };

const TYPE_RANK: Record<string, number> = { official: 0, user: 1, historical: 2, era: 3 };

// Per-section identity: alternating background tone, an accent color (reusing the existing
// challenge palette so we don't invent new brand colors — see index.css), and the icon/copy
// for a consistent large title + description atop every section, in every tab.
const SECTION_META: Record<'featured' | 'community' | 'era' | 'historical', {
    tone: string;
    accent: string;
    icon: ReactNode;
    title: string;
    description: string;
}> = {
    featured: {
        tone: 'bg-(--background-secondary)',
        accent: '--challenge-legendary',
        icon: <FaStar />,
        title: 'Featured',
        description: 'Teams featured by the creator of Showdown Bot.',
    },
    community: {
        tone: 'bg-(--background-tertiary)',
        accent: '--challenge-budget',
        icon: <FaUsers />,
        title: 'Community',
        description: 'Public teams built and shared by other users.',
    },
    era: {
        tone: 'bg-(--background-secondary)',
        accent: '--challenge-superteam',
        icon: <FaTrophy />,
        title: 'Eras',
        description: "Every franchise's best-ever roster — all-time, or a single decade — drafted from each player's single greatest qualifying season.",
    },
    historical: {
        tone: 'bg-(--background-tertiary)',
        accent: '--challenge-themed',
        icon: <FaClockRotateLeft />,
        title: 'Historical',
        description: 'Real MLB rosters and All-Star squads, season by season.',
    },
};

/** Full-bleed colored band around one browse section, with a large title + description and a
 *  faint oversized icon watermark tied to the section's accent color. Breaks out to the true
 *  edge of the nearest `@container` ancestor (ignoring the page's centered max-width), then
 *  re-centers its content with the same max-width so it still lines up with the header/tabs. */
function BrowseSection({ meta, horizontalPadding, children }: {
    meta: typeof SECTION_META[keyof typeof SECTION_META];
    horizontalPadding: string;
    children: ReactNode;
}) {
    const { tone, accent, icon, title, description } = meta;
    return (
        <div
            className={`relative overflow-hidden ${tone}`}
            style={{ marginLeft: 'calc((100% - 100cqw) / 2)', marginRight: 'calc((100% - 100cqw) / 2)' }}
        >
            <div
                aria-hidden
                className="pointer-events-none absolute -top-8 -right-8 text-[160px] leading-none opacity-[0.06] select-none"
                style={{ color: `var(${accent})` }}
            >
                {icon}
            </div>
            <div className="relative max-w-4xl lg:max-w-7xl mx-auto w-full flex flex-col gap-3 py-6">
                <div className={horizontalPadding}>
                    <div className="flex items-center gap-2">
                        <span className="text-[18px]" style={{ color: `var(${accent})` }}>{icon}</span>
                        <h2 className="text-[22px] font-black text-(--text-primary) tracking-tight">{title}</h2>
                    </div>
                    <p className="text-[12px] text-(--text-secondary) mt-0.5 max-w-2xl">{description}</p>
                </div>
                {children}
            </div>
        </div>
    );
}

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
    const [type, setType] = useState<BrowseType>(loadStoredBrowseType);
    const [setFilter, setSetFilter] = useState<string>(loadStoredSetFilter);
    const [query, setQuery] = useState('');
    const px = horizontalPadding ?? '';
    const rootRef = useRef<HTMLDivElement | null>(null);

    // "All Sets" (empty) means no set filter at all; picking a specific set here filters
    // everywhere — Historical, Era, Featured, and Community.
    const effectiveSet = setFilter;

    // Re-apply the remembered filters after mount too, in case they changed in
    // another tab between the lazy-init read and this component mounting.
    useEffect(() => {
        setType(loadStoredBrowseType());
        setSetFilter(loadStoredSetFilter());
    }, []);

    // Remember scroll position while this tab is the one actually on screen. It stays mounted
    // (but `hidden`) behind the other tabs, so `offsetParent` guards against a background tab's
    // own scrolling overwriting the saved spot.
    useEffect(() => {
        const onScroll = () => {
            if (!rootRef.current || rootRef.current.offsetParent === null) return;
            try { sessionStorage.setItem(BROWSE_SCROLL_STORAGE_KEY, String(window.scrollY)); } catch {
                // ignore
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        return () => window.removeEventListener('scroll', onScroll);
    }, []);

    // Restore that spot once, on mount -- but only once the page has actually grown tall enough
    // to reach it. Scrolling immediately would just snap back to the top against the still-empty
    // (or skeleton) page every child component mounts in with; polling on a rAF loop instead of
    // scrolling on a fixed delay adapts to however long that first load actually takes.
    useEffect(() => {
        let target: number;
        try {
            target = Number(sessionStorage.getItem(BROWSE_SCROLL_STORAGE_KEY));
        } catch {
            return;
        }
        if (!Number.isFinite(target) || target <= 0) return;

        let attempts = 0;
        let frame = 0;
        const tryRestore = () => {
            attempts += 1;
            const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
            if (maxScroll >= target || attempts > 120) { // ~2s at 60fps before giving up and going as far as possible
                window.scrollTo(0, target);
                return;
            }
            frame = requestAnimationFrame(tryRestore);
        };
        frame = requestAnimationFrame(tryRestore);
        return () => cancelAnimationFrame(frame);
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
                fetchHistoricalTeams({ q, showdownSet: effectiveSet, limit: 40 })
                    .then(r => r.teams).catch(() => [] as HistoricalTeam[]),
                fetchEraTeams({ era: ALL_TIME_ERA_KEY, q, showdownSet: effectiveSet, limit: 40 })
                    .then(r => r.teams).catch(() => [] as EraTeam[]),
            ]);
            if (cancelled) return;
            const isOwn = (t: TeamSummary) => !!currentUserId && t.user_id === currentUserId;
            // A team with no explicit `allowed_sets` restriction still matches every set.
            const matchesSet = (t: TeamSummary) =>
                !effectiveSet || !t.allowed_sets || t.allowed_sets.length === 0 || t.allowed_sets.includes(effectiveSet);
            // In-progress drafts don't belong in Browse — the viewer's own included.
            const merged: Hit[] = [
                // The user's own teams (including private ones) aren't in the public payload.
                ...myTeams.filter(t => !t.is_drafting && matchesTeamQuery(t, q))
                    .map(team => ({ kind: 'public' as const, team })),
                ...publicTeams.filter(t => !isOwn(t) && !t.is_drafting && matchesSet(t))
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
    }, [type, q, effectiveSet, currentUserId, myTeams]);

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
    const hitPreview = (hit: Hit) => {
        if (hit.kind === 'era') return { ...hit.team, name: `All-Time ${hit.team.name}` };
        if (hit.kind === 'historical') return { ...hit.team, badge: String(hit.team.season) };
        return hit.team;
    };

    const searchModeResults = useMemo(() => {
        if (hits === null) return null;
        return hits;
    }, [hits]);

    return (
        <div ref={rootRef} className="flex flex-col gap-5">
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

                <CustomSelect
                    value={setFilter}
                    onChange={v => {
                        setSetFilter(v);
                        try {
                            localStorage.setItem(BROWSE_SET_STORAGE_KEY, v);
                        } catch {
                            // ignore
                        }
                    }}
                    options={SET_OPTIONS}
                    buttonClassName="px-2.5 py-2 rounded-lg border border-(--divider) bg-(--background-secondary) text-(--text-primary) text-[13px] text-nowrap cursor-pointer flex items-center"
                    imageClassName="mr-0.5 w-6 h-5 object-contain object-center"
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
                <div className="flex flex-col">
                    {(type === 'all' || type === 'featured') && (
                        <BrowseSection meta={SECTION_META.featured} horizontalPadding={px}>
                            <FeaturedCollections
                                onOpen={onOpenTeam}
                                onOpenCollection={slug => navigate(`/teams/collections/${slug}`)}
                                horizontalPadding={px}
                                query={type === 'featured' ? q : undefined}
                                showdownSet={effectiveSet}
                            />
                        </BrowseSection>
                    )}
                    {(type === 'all' || type === 'community') && (
                        <BrowseSection meta={SECTION_META.community} horizontalPadding={px}>
                            <CommunityTeams
                                onOpen={onOpenTeam}
                                horizontalPadding={px}
                                hideSearch
                                externalQuery={type === 'community' ? q : ''}
                                showdownSet={effectiveSet}
                            />
                        </BrowseSection>
                    )}
                    {(type === 'all' || type === 'era') && (
                        <BrowseSection meta={SECTION_META.era} horizontalPadding={px}>
                            <EraTeams horizontalPadding={px} hideSearch externalQuery={type === 'era' ? q : ''} showdownSet={effectiveSet} />
                        </BrowseSection>
                    )}
                    {(type === 'all' || type === 'historical') && (
                        <BrowseSection meta={SECTION_META.historical} horizontalPadding={px}>
                            <HistoricalTeams horizontalPadding={px} hideSearch externalQuery={type === 'historical' ? q : ''} showdownSet={effectiveSet} />
                        </BrowseSection>
                    )}
                </div>
            )}
        </div>
    );
}

export default BrowseTeams;
