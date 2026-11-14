/**
 * @fileoverview How a player sets up their side of a live game: who starts, and how the sim's
 * manager runs the club while it's on autopilot. Shared by the invite and the accept screens.
 */
import type { ManagerPreference } from "../../../api/manager";
import type { Team } from "../../../api/userTeams";
import { useCardMap } from "../../../hooks/useCardMap";
import FormDropdown from "../../customs/FormDropdown";
import ManagerStyleFields from "../../simulate/ManagerStyleFields";
import { rotationOf } from "../faceoff/teamPicking";

const MANAGER_DESCRIPTION = "How the sim manages your club whenever it's on autopilot.";

type Props = {
    team: Team;
    token: string;
    starter?: string;
    onStarterChange: (cardId: string) => void;
    manager: ManagerPreference;
    onManagerChange: (manager: ManagerPreference) => void;
};

export default function LiveSideFields({ team, token, starter, onStarterChange, manager, onManagerChange }: Props) {
    const rotation = rotationOf(team);
    const { cardMap } = useCardMap(rotation, token);
    return (
        <div className="flex flex-col gap-3">
            <FormDropdown
                label={`${team.abbreviation} starter`}
                options={rotation.map((slot) => ({ value: slot.card_id, label: `${slot.role} · ${cardMap[slot.card_id]?.name ?? "Loading…"}` }))}
                selectedOption={starter ?? rotation[0]?.card_id ?? ""}
                onChange={onStarterChange}
            />
            <ManagerStyleFields title={`${team.abbreviation} autopilot manager`} description={MANAGER_DESCRIPTION} value={manager} onChange={onManagerChange} />
        </div>
    );
}
