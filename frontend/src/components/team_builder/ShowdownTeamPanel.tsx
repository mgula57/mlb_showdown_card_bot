import type { Team } from "../../api/userTeams";
import { TeamDetail } from "./TeamDetail";

type ShowdownTeamPanelProps = {
    showdownTeam: Team | null;
    isStarred?: boolean;
    onToggleStar?: () => void;
};

/**
 * Read-only, embedded team builder view for a backend-constructed roster (real MLB team,
 * historical team, or All-Star team), with loading + empty states. Shared by the Seasons
 * page and the Team Builder "Historical" tab.
 *
 * `showdownTeam === null` renders the loading state; a team with an empty roster renders the
 * empty state.
 */
export const ShowdownTeamPanel = ({ showdownTeam, isStarred, onToggleStar }: ShowdownTeamPanelProps) => {
    if (showdownTeam === null) {
        return (
            <div className="rounded-lg border border-(--divider) overflow-hidden animate-pulse">
                <div className="h-20 md:h-24 bg-(--background-secondary) flex items-center gap-3 px-4">
                    <div className="w-12 h-12 rounded-full bg-(--background-quaternary) shrink-0" />
                    <div className="flex flex-col gap-2">
                        <div className="h-4 w-40 rounded bg-(--background-quaternary)" />
                        <div className="h-3 w-24 rounded bg-(--background-quaternary)" />
                    </div>
                </div>
                <div className="flex flex-col gap-1.5 p-3">
                    {Array.from({ length: 9 }).map((_, index) => (
                        <div key={index} className="flex items-center gap-3 rounded-lg border border-(--divider) px-3 py-2">
                            <div className="w-6 h-6 rounded bg-(--background-quaternary) shrink-0" />
                            <div className="flex-1 h-3 rounded bg-(--background-quaternary)" />
                            <div className="w-8 h-3 rounded bg-(--background-quaternary)" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    if ((showdownTeam.roster ?? []).length === 0) {
        return (
            <div className="rounded-lg border border-(--divider) px-4 py-6 text-sm text-(--text-secondary)">
                No showdown card data available for this team.
            </div>
        );
    }
    return (
        <div className="rounded-lg border border-(--divider) overflow-hidden">
            <TeamDetail
                key={showdownTeam.team_id}
                team={showdownTeam}
                readOnly
                embedded
                onSave={async () => {}}
                isStarred={isStarred}
                onToggleStar={onToggleStar}
            />
        </div>
    );
};

export default ShowdownTeamPanel;
