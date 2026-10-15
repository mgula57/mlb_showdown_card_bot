import { FaChevronRight, FaTrophy } from 'react-icons/fa6';
import { TeamChip } from '../shared/TeamChip';
import { fetchLeagueHistory, type LeagueHistoryEntry } from '../../api/leagues';
import { usePolling } from '../../hooks/usePolling';
import { ERROR_BOX_CLASS, SEASON_STATUS_LABEL } from './leagueUi';

type Props = {
    leagueId: string;
    token: string;
    onOpenSeason: (seasonNumber: number) => void;
};

/** Every season, newest first: its champion and award winners. Opens a season's full results. */
export function LeagueHistoryTab({ leagueId, token, onOpenSeason }: Props) {
    const { data: seasons, error } = usePolling<LeagueHistoryEntry[]>(() => fetchLeagueHistory(token, leagueId), null, [leagueId]);

    if (error) return <div className={ERROR_BOX_CLASS}>{error}</div>;
    if (!seasons) {
        return (
            <div className="flex flex-col gap-2 animate-pulse">
                {Array.from({ length: 3 }, (_, i) => <div key={i} className="h-16 rounded-xl bg-(--background-secondary)" />)}
            </div>
        );
    }

    return (
        <div className="flex flex-col rounded-xl border border-(--divider) divide-y divide-(--divider) overflow-hidden">
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
                            <div className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">Season</div>
                            <div className="text-[20px] font-black text-(--text-primary) leading-none">{season.season_number}</div>
                        </div>
                        <div className="flex-1 min-w-0">
                            {season.champion_name ? (
                                <>
                                    <div className="flex items-center gap-2 min-w-0">
                                        <FaTrophy className="shrink-0 text-(--secondary)" />
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
