import { FaChevronRight, FaTrophy } from 'react-icons/fa6';
import { TeamChip } from '../shared/TeamChip';
import { fetchLeagueHistory, type LeagueHistoryEntry } from '../../api/leagues';
import { usePolling } from '../../hooks/usePolling';
import { SEASON_STATUS_LABEL } from './leagueUi';
import { InlineError } from '../shared/InlineError';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';

type Props = {
    leagueId: string;
    token: string;
    onOpenSeason: (seasonNumber: number) => void;
};

/** Every season, newest first: its champion and award winners. Opens a season's full results. */
export function LeagueHistoryTab({ leagueId, token, onOpenSeason }: Props) {
    const { data: seasons, error } = usePolling<LeagueHistoryEntry[]>(() => fetchLeagueHistory(token, leagueId), null, [leagueId]);

    if (error) return <InlineError size="md">{error}</InlineError>;
    if (!seasons) {
        return (
            <div aria-hidden className="flex flex-col gap-2 animate-pulse">
                {Array.from({ length: 3 }, (_, i) => <div key={i} className="h-16 rounded-card bg-(--background-tertiary)" />)}
            </div>
        );
    }

    return (
        <div className="flex flex-col rounded-card border border-(--divider) divide-y divide-(--divider) overflow-hidden">
            {seasons.map(season => {
                const mvp = season.awards?.mvp?.[0]?.player.name;
                const cyYoung = season.awards?.cy_young?.[0]?.player.name;
                return (
                    <button
                        key={season.season_id}
                        type="button"
                        onClick={() => onOpenSeason(season.season_number)}
                        className="flex items-center gap-3 px-3 py-2.5 bg-(--background-secondary) text-left hover:bg-(--background-tertiary) transition-colors cursor-pointer"
                    >
                        <div className="w-16 shrink-0">
                            <div className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Season</div>
                            <div className="font-display-upright text-[22px] leading-none tabular-nums text-(--text-primary)">{season.season_number}</div>
                        </div>
                        <div className="flex-1 min-w-0">
                            {season.champion_name ? (
                                <>
                                    <div className="flex items-center gap-2 min-w-0">
                                        <FaTrophy className="shrink-0 text-(--gold)" />
                                        <TeamChip
                                            team={{
                                                key: season.season_id,
                                                abbreviation: season.champion_abbreviation ?? '',
                                                name: season.champion_name,
                                                primaryColor: season.champion_primary_color ?? undefined,
                                                secondaryColor: season.champion_secondary_color ?? undefined,
                                            }}
                                            size="sm"
                                        />
                                        <span className="text-[13px] font-bold text-(--text-primary) truncate">{season.champion_name}</span>
                                    </div>
                                    <div className="text-[11px] text-(--text-tertiary) truncate">
                                        {[season.champion_member_name, mvp && `MVP ${mvp}`, cyYoung && `Cy Young ${cyYoung}`].filter(Boolean).join(' · ')}
                                    </div>
                                </>
                            ) : (
                                <div className="text-[12px] text-(--text-secondary)">{SEASON_STATUS_LABEL[season.status]}</div>
                            )}
                        </div>
                        <FaChevronRight className="shrink-0 text-[10px] text-(--text-tertiary)" />
                    </button>
                );
            })}
        </div>
    );
}
