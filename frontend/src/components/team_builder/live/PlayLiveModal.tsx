/**
 * @fileoverview Starts a live game from a team's page. That team takes one seat (away or home); the
 * other seat goes to a friend through an invite link, to the sim, or to the user too, playing their
 * own team or one picked for them, or a club drawn from baseball history.
 */
import { useState } from "react";
import { FaSpinner } from "react-icons/fa6";

import {
    createLiveGame, IDLE_AUTOPILOT_CHOICES,
    type IdleAutopilotMinutes, type LiveSide, type OpponentController, type TeamRef,
} from "../../../api/liveGame";
import { managerPayload, NEUTRAL_MANAGER, type ManagerPreference } from "../../../api/manager";
import type { Team, TeamSummary } from "../../../api/userTeams";
import { buttonClass } from "../../shared/buttonStyles";
import { choiceClass } from "../../shared/choiceStyles";
import { FIELD_LABEL_CLASS, fieldClass } from "../../shared/fieldStyles";
import { InlineError } from "../../shared/InlineError";
import { Modal } from "../../shared/Modal";
import { useSiteSettings } from "../../shared/SiteSettingsContext";
import { TeamPicker } from "../TeamPicker";
import LiveSideFields from "./LiveSideFields";

type OpponentTeam = "bring" | "pick" | "history";

const CONTROLLER_CHOICES: { id: OpponentController; label: string; hint: string }[] = [
    { id: "invite", label: "A friend", hint: "Send a link. They roll their own dice." },
    { id: "sim", label: "The sim", hint: "The sim's manager plays the other side." },
    { id: "me", label: "Me", hint: "You play both sides." },
];

const paceLabel = (minutes: IdleAutopilotMinutes) => (minutes === null ? "Take your time" : `Autopilot after ${minutes} min`);

function ChoiceRow<T extends string | number | null>({ label, options, value, onChange }: {
    label: string;
    options: { id: T; label: string }[];
    value: T;
    onChange: (value: T) => void;
}) {
    return (
        <div className="flex flex-col gap-2">
            <span className={FIELD_LABEL_CLASS}>{label}</span>
            <div className="flex flex-wrap gap-1.5">
                {options.map((option) => (
                    <button key={String(option.id)} type="button" onClick={() => onChange(option.id)} className={choiceClass(value === option.id, "sm")}>
                        {option.label}
                    </button>
                ))}
            </div>
        </div>
    );
}

type Props = {
    team: Team;
    token: string;
    /** The game plays the saved roster, so the page saves any pending edit first. */
    onBeforeStart: () => Promise<void>;
    onClose: () => void;
    onCreated: (liveGameId: string) => void;
};

export function PlayLiveModal({ team, token, onBeforeStart, onClose, onCreated }: Props) {
    const { userShowdownSet } = useSiteSettings();
    const [mySide, setMySide] = useState<LiveSide>("away");
    const [starter, setStarter] = useState<string | undefined>(undefined);
    const [manager, setManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);
    const [controller, setController] = useState<OpponentController>("invite");
    const [opponentTeam, setOpponentTeam] = useState<OpponentTeam>("bring");
    const [picked, setPicked] = useState<TeamSummary | null>(null);
    const [historySeason, setHistorySeason] = useState("");
    const [pace, setPace] = useState<IdleAutopilotMinutes>(null);
    const [error, setError] = useState<string | null>(null);
    const [isCreating, setIsCreating] = useState(false);

    // Only an invitee can bring their own team; the sim and the user need one picked.
    const teamSource = controller !== "invite" && opponentTeam === "bring" ? "pick" : opponentTeam;
    const season = Number(historySeason);
    const opponentRef: TeamRef | undefined = teamSource === "pick"
        ? (picked ? { kind: "saved", team_id: picked.team_id } : undefined)
        : teamSource === "history"
            ? { kind: "random_historical", ...(historySeason && Number.isInteger(season) ? { season } : {}) }
            : undefined;
    const isReady = teamSource === "bring" || !!opponentRef;

    async function create() {
        setIsCreating(true);
        setError(null);
        try {
            await onBeforeStart();
            const { live_game_id } = await createLiveGame({
                team: { kind: "saved", team_id: team.team_id },
                starter_card_id: starter,
                manager: managerPayload(manager),
                my_side: mySide,
                opponent: { controller, team: opponentRef },
                idle_autopilot_minutes: controller === "invite" ? pace : null,
                showdown_set: userShowdownSet,
            }, token);
            onCreated(live_game_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to start the game.");
            setIsCreating(false);
        }
    }

    const teamChoices: { id: OpponentTeam; label: string }[] = [
        ...(controller === "invite" ? [{ id: "bring" as const, label: "They bring their own" }] : []),
        { id: "pick", label: "Pick a team" },
        { id: "history", label: "Random from history" },
    ];

    return (
        <Modal
            title="Play Live"
            subtitle={`Play ${team.name} a turn at a time, rolling your own dice.`}
            size="lg"
            onClose={onClose}
            footer={
                <div className="flex flex-col gap-2 p-3">
                    {error && <InlineError>{error}</InlineError>}
                    <button type="button" onClick={create} disabled={!isReady || isCreating} className={buttonClass("primary", "md", "w-full")}>
                        {isCreating && <FaSpinner className="animate-spin" />} {controller === "invite" ? "Create invite link" : "Start game"}
                    </button>
                </div>
            }
        >
            <div className="flex flex-col gap-5 p-4 pb-32">
                <section className="flex flex-col gap-3">
                    <ChoiceRow label={`${team.abbreviation} plays`} options={[{ id: "away" as LiveSide, label: "Away" }, { id: "home" as LiveSide, label: "Home" }]} value={mySide} onChange={setMySide} />
                    <LiveSideFields team={team} token={token} starter={starter} onStarterChange={setStarter} manager={manager} onManagerChange={setManager} />
                </section>

                <section className="flex flex-col gap-3">
                    <ChoiceRow label="The other side is played by" options={CONTROLLER_CHOICES} value={controller} onChange={setController} />
                    <p className="text-[12px] text-(--text-secondary)">{CONTROLLER_CHOICES.find((c) => c.id === controller)?.hint}</p>
                    <ChoiceRow label="With" options={teamChoices} value={teamSource} onChange={setOpponentTeam} />
                    {teamSource === "pick" && (
                        <TeamPicker
                            token={token}
                            selectedTeamId={picked?.team_id}
                            onPick={setPicked}
                            allowPublic
                            excludeTeamId={team.team_id}
                            excludePublicUserId={team.user_id}
                            emptyMessage="You need another finished team, or pick a public one."
                        />
                    )}
                    {teamSource === "history" && (
                        <label className="flex flex-col gap-2">
                            <span className={FIELD_LABEL_CLASS}>Season <span className="normal-case">(leave blank for any)</span></span>
                            <input
                                type="number"
                                inputMode="numeric"
                                placeholder="Any year"
                                value={historySeason}
                                onChange={(e) => setHistorySeason(e.target.value)}
                                className={fieldClass("md", "w-32")}
                            />
                        </label>
                    )}
                </section>

                {controller === "invite" && (
                    <section className="flex flex-col gap-2">
                        <ChoiceRow label="Pace" options={IDLE_AUTOPILOT_CHOICES.map((minutes) => ({ id: minutes, label: paceLabel(minutes) }))} value={pace} onChange={setPace} />
                        <p className="text-[12px] text-(--text-secondary)">
                            {pace === null
                                ? "The game waits for each turn as long as it takes, so you can play it out over hours or days."
                                : `A side that hasn't moved for ${pace} minutes on its turn goes on autopilot. Either player can switch theirs back off.`}
                        </p>
                    </section>
                )}
            </div>
        </Modal>
    );
}
