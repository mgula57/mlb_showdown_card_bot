/**
 * @fileoverview Where an invite link lands (/teams/play/:code): who's asking and the seat on offer.
 * When the inviter left the seat's team to the invitee, they pick one of their own (with a starter and
 * an autopilot manager); when the inviter picked it (a public team, a club from history), they just
 * take it. Accept starts the game. An invite that's already been taken sends the visitor to watch.
 */
import { useEffect, useState } from "react";
import { FaSpinner } from "react-icons/fa6";

import { acceptLiveGame, fetchLiveGameInvite, type LiveGameInvite } from "../../../api/liveGame";
import { managerPayload, NEUTRAL_MANAGER, type ManagerPreference } from "../../../api/manager";
import { fetchTeam, type Team, type TeamSummary } from "../../../api/userTeams";
import BackButton from "../../shared/BackButton";
import { buttonClass } from "../../shared/buttonStyles";
import { Heading } from "../../shared/Heading";
import { InlineError } from "../../shared/InlineError";
import { SignInPrompt } from "../../shared/SignInPrompt";
import { TeamPicker } from "../TeamPicker";
import { otherSide, seatName } from "./liveGameState";
import LiveSideFields from "./LiveSideFields";

type Props = {
    inviteCode: string;
    token?: string;
    onBack: () => void;
    onOpenGame: (liveGameId: string) => void;
};

export function LiveInviteAccept({ inviteCode, token, onBack, onOpenGame }: Props) {
    const [invite, setInvite] = useState<LiveGameInvite | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [picked, setPicked] = useState<Team | null>(null);
    const [starter, setStarter] = useState<string | undefined>(undefined);
    const [manager, setManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);
    const [error, setError] = useState<string | null>(null);
    const [isAccepting, setIsAccepting] = useState(false);

    useEffect(() => {
        let stale = false;
        fetchLiveGameInvite(inviteCode, token)
            .then((data) => { if (!stale) setInvite(data); })
            .catch((err) => { if (!stale) setLoadError(err instanceof Error ? err.message : "Failed to load the invite."); });
        return () => { stale = true; };
    }, [inviteCode, token]);

    async function pickTeam(summary: TeamSummary) {
        if (!token) return;
        setError(null);
        setStarter(undefined);
        try {
            setPicked(await fetchTeam(summary.team_id, token));
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load that team.");
        }
    }

    const bringsOwnTeam = !!invite && !invite.open_seat_team_ref;

    async function accept() {
        if (!token || (bringsOwnTeam && !picked)) return;
        setIsAccepting(true);
        setError(null);
        try {
            const { live_game_id } = await acceptLiveGame(inviteCode, bringsOwnTeam && picked
                ? { team: { kind: "saved", team_id: picked.team_id }, starter_card_id: starter, manager: managerPayload(manager) }
                : {}, token);
            onOpenGame(live_game_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to accept the invite.");
            setIsAccepting(false);
        }
    }

    const shell = (body: React.ReactNode) => (
        <div className="mx-auto flex w-full max-w-2xl flex-col gap-4 p-4 pb-32">
            <BackButton onBack={onBack} />
            {body}
        </div>
    );

    if (loadError) return shell(<InlineError size="md">{loadError}</InlineError>);
    if (!invite) {
        return shell(
            <div className="flex flex-col gap-3 animate-pulse" aria-label="Loading invite">
                <div className="h-8 w-2/3 rounded-control bg-(--background-tertiary)" />
                <div className="h-4 w-1/2 rounded-control bg-(--background-tertiary)" />
            </div>,
        );
    }

    const openSide = invite.open_side;
    const host = openSide ? seatName(invite.seats[otherSide(openSide)], otherSide(openSide)) : "Someone";
    const heading = <Heading level="page">{host} wants to play</Heading>;
    if (invite.status !== "invited" || invite.is_mine || !openSide) {
        return shell(
            <>
                {heading}
                <p className="text-[13px] text-(--text-secondary)">
                    {invite.is_mine ? "This is your own invite. Send the link to someone else to play." : "Someone already took this game."}
                </p>
                <button type="button" onClick={() => onOpenGame(invite.live_game_id)} className={buttonClass("primary", "md", "self-start")}>
                    {invite.status === "invited" ? "Open game" : "Watch the game"}
                </button>
            </>,
        );
    }
    if (!token) return shell(<>{heading}<SignInPrompt size="panel" message="Sign in to pick one of your teams and play." /></>);

    return shell(
        <>
            {heading}
            <p className="text-[13px] text-(--text-secondary)">
                {bringsOwnTeam
                    ? `Pick one of your teams to face ${host}, as the ${openSide} side.`
                    : `You'd play ${seatName(invite.seats[openSide], openSide)} as the ${openSide} side, against ${host}.`}
                {" "}You'll each roll your own dice
                {invite.settings.idle_autopilot_minutes === null
                    ? ", and the game waits for each turn as long as it takes."
                    : `. A side that sits for ${invite.settings.idle_autopilot_minutes} minutes on its turn goes on autopilot.`}
            </p>

            {bringsOwnTeam && (
                <TeamPicker token={token} selectedTeamId={picked?.team_id} onPick={pickTeam} emptyMessage="You need a finished team to play." />
            )}

            {bringsOwnTeam && picked && (
                <LiveSideFields team={picked} token={token} starter={starter} onStarterChange={setStarter} manager={manager} onManagerChange={setManager} />
            )}
            {error && <InlineError>{error}</InlineError>}
            <button type="button" onClick={accept} disabled={(bringsOwnTeam && !picked) || isAccepting} className={buttonClass("primary", "md", "w-full sm:w-auto sm:self-start")}>
                {isAccepting && <FaSpinner className="animate-spin" />} Accept and play
            </button>
        </>,
    );
}
