import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchEraTeams, fetchRosterEras, type EraTeam, type RosterEra, ALL_TIME_ERA_KEY } from '../../api/mlbAPI';
import { useSiteSettings } from '../shared/SiteSettingsContext';
import { TeamPreviewCard, TeamPreviewCardSkeleton, type TeamPreviewData } from './TeamPreviewCard';
import { TeamShelf } from './TeamShelf';
import CustomSelect, { type SelectOption } from '../shared/CustomSelect';
import type { HistoricalNavState } from './HistoricalTeams';

// Label lookup falls back to the same formatting the backend uses (RosterEra.label) so a tile
// still reads correctly before /api/seasons/eras has loaded.
const eraLabel = (eraKey: string, eras: RosterEra[]): string =>
    eras.find(e => e.key === eraKey)?.label ?? (eraKey === ALL_TIME_ERA_KEY ? 'All-Time' : eraKey);

// The era label is baked into the displayed name only -- `team.name` itself stays the plain
// franchise/league name everywhere else (nav state, API payloads), so it can't get prefixed
// twice when fetchEraShowdownTeam applies RosterEra.team_name server-side.
const teamToPreview = (team: EraTeam, label: string, showdownSet?: string): TeamPreviewData => ({
    abbreviation: team.abbreviation || team.name,
    name: `${label} ${team.name}`,
    primary_color: team.primary_color,
    secondary_color: team.secondary_color,
    total_points: team.total_points,
    top_players: team.top_players,
    source: 'mlb',
    allowed_sets: showdownSet ? [showdownSet] : undefined,
});

/** Browse pre-processed Era Rosters — one shelf of every current MLB franchise's best roster
 *  for the selected era (All-Time, or a single decade). Unlike HistoricalTeams there's no
 *  season pagination: the full set of ~30 teams for the selected era is fetched at once. */
type EraTeamsProps = {
    horizontalPadding?: string;
    /** When embedded in the Browse tab, the parent owns the search box — hide the local one. */
    hideSearch?: boolean;
    /** Search query supplied by the parent when `hideSearch` is set. */
    externalQuery?: string;
};

export function EraTeams({ horizontalPadding, hideSearch = false, externalQuery }: EraTeamsProps) {
    const { userShowdownSet } = useSiteSettings();
    const navigate = useNavigate();

    const [eras, setEras] = useState<RosterEra[]>([]);
    const [era, setEra] = useState<string>(ALL_TIME_ERA_KEY);
    const [teams, setTeams] = useState<EraTeam[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const query = hideSearch ? (externalQuery ?? '') : '';
    const searchQuery = query.trim();

    useEffect(() => {
        fetchRosterEras().then(setEras).catch(() => setEras([]));
    }, []);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        fetchEraTeams({ era, showdownSet: userShowdownSet, q: searchQuery || undefined, limit: 60 })
            .then(result => { if (!cancelled) setTeams(result.teams); })
            .catch(err => { if (!cancelled) setError(err.message ?? 'Failed to load era teams.'); })
            .finally(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, [era, userShowdownSet, searchQuery]);

    // Navigate to the team's own shareable detail page. Identity is passed via nav state so the
    // detail view renders instantly; a cold link resolves identity server-side.
    const openTeam = useCallback((team: EraTeam) => {
        const state: HistoricalNavState = {
            abbr: team.abbreviation || team.name,
            name: team.name,
            primary_color: team.primary_color ?? undefined,
            secondary_color: team.secondary_color ?? undefined,
        };
        navigate(`/teams/era/${team.sport_id}/${team.era}/${team.team_id}`, { state });
    }, [navigate]);

    const eraOptions: SelectOption[] = useMemo(
        () => eras.map(e => ({ value: e.key, label: e.label })),
        [eras],
    );

    const currentEraLabel = useMemo(() => eraLabel(era, eras), [era, eras]);
    const previews = useMemo(
        () => teams.map(team => ({ team, preview: teamToPreview(team, currentEraLabel, userShowdownSet) })),
        [teams, currentEraLabel, userShowdownSet],
    );

    return (
        <div className="flex flex-col gap-3">
            {eraOptions.length > 0 && (
                <div className={horizontalPadding ?? ''}>
                    <CustomSelect
                        value={era}
                        onChange={setEra}
                        options={eraOptions}
                        buttonClassName="px-2.5 py-1.5 rounded-lg border border-(--divider) bg-(--background-secondary) text-(--text-primary) text-[12px] text-nowrap cursor-pointer flex items-center"
                        dropdownArrowSize={12}
                    />
                </div>
            )}

            {error ? (
                <div className={`${horizontalPadding ?? ''} mx-4 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5`}>
                    {error}
                </div>
            ) : loading ? (
                <TeamShelf title="Era Teams" className={horizontalPadding ?? ''} bleed>
                    {Array.from({ length: 8 }, (_, i) => <TeamPreviewCardSkeleton key={i} />)}
                </TeamShelf>
            ) : teams.length === 0 ? (
                <p className="text-[13px] text-(--text-tertiary) py-8 text-center">
                    {searchQuery ? `No teams match "${searchQuery}".` : 'No era teams have been processed yet.'}
                </p>
            ) : (
                <TeamShelf title="Era Teams" subtitle={`${teams.length} teams`} className={horizontalPadding ?? ''} bleed>
                    {previews.map(({ team, preview }) => (
                        <TeamPreviewCard key={team.team_id} team={preview} onClick={() => openTeam(team)} />
                    ))}
                </TeamShelf>
            )}
        </div>
    );
}

export default EraTeams;
