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
            <div className="flex items-center justify-center gap-2 py-16">
                <span className="w-2 h-2 rounded-full bg-(--text-tertiary) animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-(--text-tertiary) animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-(--text-tertiary) animate-bounce" style={{ animationDelay: '300ms' }} />
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
