/**
 * @fileoverview A live game's page (/teams/live/:id): two seats, each a club managed by a person or
 * the sim, played a turn at a time. It plays on the same stage as every other game. The timeline is rebuilt from the server's
 * log on each move and the cursor follows it in "live" mode, so the other player's roll animates
 * before this player's prompt appears. While the game is being played, the turn bar takes the
 * transport strip's place; at the final out the transport comes back for a replay.
 *
 * Before the invite's open seat is taken, the page is the waiting room: the invite link for whoever
 * made the game, a note for anyone else.
 */
import { useEffect, useMemo, useState } from "react";
import { FaLink } from "react-icons/fa6";

import { cancelLiveGame, fetchLiveGameCards, inviteUrl, type LiveAction, type LiveGame } from "../../../api/liveGame";
import type { ShowdownBotCardAPIResponse } from "../../../api/showdownBotCard";
import { fromSimTimeline } from "../../../domain/adapters/fromSim";
import type { AdvantageSide } from "../../../domain/play";
import { bannerTokens, NEUTRAL_TEAM_COLOR } from "../../../functions/colors";
import { useCopyLink } from "../../../hooks/useCopyLink";
import { useLiveGame } from "../../../hooks/useLiveGame";
import { TeamMoveNote } from "../../games/GameBoardPanels";
import GameDetailSkeleton from "../../games/GameDetailSkeleton";
import GameStage from "../../games/GameStage";
import SimBoxScorePanels from "../../games/SimBoxScorePanels";
import TimelinePlayback from "../../games/TimelinePlayback";
import { useGameStage } from "../../games/useGameStage";
import TopBarButton from "../../games/detail/TopBarButton";
import BackButton from "../../shared/BackButton";
import { buttonClass } from "../../shared/buttonStyles";
import { Heading } from "../../shared/Heading";
import { InlineError } from "../../shared/InlineError";
import { actingSide, defaultPickerMode, liveTurnLabel, isMyTurn, LIVE_SIDES, liveEdgeOf, teamName, type SubPickerMode } from "./liveGameState";
import LiveSubPanel from "./LiveSubPanel";
import LiveActionButton, { LiveTurnStatus, ManagerButton } from "./LiveTurnControls";
import LiveStrategyPrototype from "./LiveStrategyPrototype";
import { useLiveTeamMoves } from "./useLiveTeamMoves";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

/** The engine's pitch results (see `advantageSideOf`). */
const ADVANTAGE_BY_PITCH_RESULT: Record<string, AdvantageSide | undefined> = { padv: "pitcher", hadv: "hitter" };

type Props = {
    liveGameId: string;
    token?: string;
    onBack: () => void;
};

function InviteWaitingRoom({ game, token, onBack, onCancelled }: { game: LiveGame; token?: string; onBack: () => void; onCancelled: () => void }) {
    const link = useCopyLink(game.invite_code ? inviteUrl(game.invite_code) : window.location.href);
    const [cancelError, setCancelError] = useState<string | null>(null);
    const openSide = LIVE_SIDES.find((side) => game.seats[side].is_open);
    const mySide = game.my_sides[0];
    const opponentLabel = openSide && !game.seats[openSide].identity ? "They pick one of their teams" : openSide ? `They play ${teamName(game, openSide)}` : "";

    async function cancel() {
        if (!token) return;
        try {
            await cancelLiveGame(game.live_game_id, token);
            onCancelled();
        } catch (err) {
            setCancelError(err instanceof Error ? err.message : "Couldn't cancel the invite.");
        }
    }

    return (
        <div className="mx-auto flex w-full max-w-lg flex-col gap-4 p-4">
            <BackButton onBack={onBack} />
            <Heading level="page">Waiting for an opponent</Heading>
            <p className="text-[13px] text-(--text-secondary)">
                {game.is_creator && mySide
                    ? `Send this link to whoever you want to play. ${opponentLabel} against ${teamName(game, mySide)}, and you each roll your own dice.`
                    : `${mySide ? teamName(game, mySide) : "This game"} is waiting for an opponent.`}
            </p>
            {game.is_creator && game.invite_code && (
                <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                        <code className="min-w-0 flex-1 truncate rounded-control border border-(--divider) bg-(--background-secondary) px-3 py-2 text-[12px]">{link.url}</code>
                        <button type="button" onClick={link.copy} className={buttonClass("primary", "md")}>
                            <FaLink /> {link.copied ? "Copied" : "Copy link"}
                        </button>
                    </div>
                    {link.error && <InlineError>{link.error}</InlineError>}
                    <button type="button" onClick={cancel} className={buttonClass("ghost", "sm", "self-start")}>Cancel invite</button>
                    {cancelError && <InlineError>{cancelError}</InlineError>}
                </div>
            )}
        </div>
    );
}

function LiveBoard({ game, cardMap, isLoadingCards, isSubmitting, moveError, submit, onBack }: {
    game: LiveGame;
    cardMap: CardMap;
    isLoadingCards: boolean;
    isSubmitting: boolean;
    moveError: string | null;
    submit: (action: LiveAction) => void;
    onBack: () => void;
}) {
    const stage = useGameStage();
    const [picker, setPicker] = useState<SubPickerMode | null>(null);
    const share = useCopyLink(window.location.href);
    const state = game.state!;

    const timeline = useMemo(
        () => fromSimTimeline(state.game, game.live_game_id, null, liveEdgeOf(state)),
        [state, game.live_game_id],
    );

    const side = actingSide(game);
    const mine = side ? state.sides[side] : null;
    const pending = state.pending;
    const myTurn = isMyTurn(game);
    const barColor = (side && game.seats[side].identity?.primary_color) || NEUTRAL_TEAM_COLOR;
    const barButton = `rounded-control px-2 py-1 h-7 ${bannerTokens(barColor).btnClass}`;

    // Dev only: `?strategy=1` puts the strategy-card prototype on the board (`LiveStrategyPrototype`).
    const isStrategyPrototype = import.meta.env.DEV && new URLSearchParams(window.location.search).get("strategy") === "1";

    const teamMoves = useLiveTeamMoves(state);

    const roll = () => pending && submit({ side: pending.side, kind: "roll", roll: pending.roll });
    const openManager = () => setPicker(defaultPickerMode(game));
    const toggleAutopilot = (enabled: boolean) => { if (side) submit({ side, kind: "autopilot", enabled }); };
    const heldAdvantage = pending?.roll === "swing" ? ADVANTAGE_BY_PITCH_RESULT[pending.pitch_result ?? ""] : undefined;

    return (
        <TimelinePlayback
            timeline={timeline}
            initialMode={state.is_final ? "playback" : "live"}
            initialCursor="live"
            showFrozenBoxscoreCaveat={false}
        >
            {({ activeView, activePlays, playbackBar, playbackControls, playbackState, isReplaying }) => {
                // The next roll waits until the last one has finished playing out on the field.
                const isCaughtUp = !isReplaying && playbackState.phase === "idle";
                // The island waits for the last roll to finish on the field, then grows out of the
                // scoreboard with whose turn it is now. An error shows straight away.
                const turn = isCaughtUp ? liveTurnLabel(game) : null;
                // A substitution drops from under its club once the field has caught up to it.
                const teamMoveAnnouncements = teamMoves
                    .filter((move) => isCaughtUp || move.seq < state.seq)
                    .map((move) => ({
                        side: move.side,
                        key: move.key,
                        content: <TeamMoveNote label={move.label}>{move.text}</TeamMoveNote>,
                    }));
                const islandTurn = (turn || moveError) ? {
                    key: `${turn?.label ?? ""}|${moveError ?? ""}`,
                    content: <LiveTurnStatus turn={turn} moveError={moveError} />,
                } : null;
                return (
                    <LiveStrategyPrototype game={game} isEnabled={isStrategyPrototype} isCaughtUp={isCaughtUp}>
                        {(strategy) => (
                            <GameStage
                                stage={stage}
                                game={activeView}
                                plays={activePlays}
                                playbackState={playbackState}
                                playbackControls={playbackControls}
                                isReplaying={isReplaying}
                                // The turn bar takes the transport's place until the final out.
                                playbackBar={state.is_final ? playbackBar : null}
                                detailedState="Final"
                                cardMap={cardMap}
                                isLoadingCards={isLoadingCards}
                                isSim={false}
                                gameKey={game.live_game_id}
                                title="Live Game"
                                modeBarColor={barColor}
                                onBack={onBack}
                                topBarStatus={share.error && <span className="text-[11px] text-(--red)">{share.error}</span>}
                                topBarActions={
                                    <TopBarButton label={share.copied ? "Copied" : "Share"} onClick={share.copy} className={barButton} />
                                }
                                boxScorePanels={<SimBoxScorePanels game={activeView} cardMap={cardMap} onCardSelect={stage.setSelectedCard} />}
                                boardAction={side && !state.is_final && (
                                    <LiveActionButton game={game} isCaughtUp={isCaughtUp} isSubmitting={isSubmitting} onRoll={roll} pass={strategy.pass} />
                                )}
                                // A strategy window speaks for the turn until it closes.
                                boardTurn={strategy.island ?? islandTurn}
                                boardTools={!state.is_final && <ManagerButton game={game} onOpen={openManager} />}
                        teamAnnouncements={[...teamMoveAnnouncements, ...strategy.announcements]}
                                strategy={strategy.slots}
                                rollPrompt={pending && isCaughtUp && !strategy.isHoldingRoll ? {
                                    kind: pending.roll,
                                    onRoll: myTurn ? roll : undefined,
                                    isBusy: isSubmitting,
                                    heldPitch: pending.roll === "swing" ? pending.pitch_roll : undefined,
                                } : undefined}
                                heldAdvantage={isCaughtUp ? heldAdvantage : undefined}
                            >
                                {side && mine && (
                                    <LiveSubPanel
                                        mode={picker}
                                        onModeChange={setPicker}
                                        side={side}
                                        mine={mine}
                                        names={state.player_names}
                                        cardMap={cardMap}
                                        isFielding={defaultPickerMode(game) === "pitcher"}
                                        isSubmitting={isSubmitting}
                                        onPick={submit}
                                        onToggleAutopilot={toggleAutopilot}
                                        onClose={() => setPicker(null)}
                                    />
                                )}
                            </GameStage>
                        )}
                    </LiveStrategyPrototype>
                );
            }}
        </TimelinePlayback>
    );
}

export function LiveGameView({ liveGameId, token, onBack }: Props) {
    const { game, loadError, moveError, isSubmitting, submit, refresh } = useLiveGame(liveGameId, token);
    const [cardMap, setCardMap] = useState<CardMap>({});
    const [isLoadingCards, setIsLoadingCards] = useState(true);
    const hasStarted = !!game && game.status !== "invited";

    // Cards are frozen when the game starts, so one fetch covers the whole game.
    useEffect(() => {
        if (!hasStarted) return;
        let stale = false;
        fetchLiveGameCards(liveGameId, token)
            .then((cards) => { if (!stale) setCardMap(cards); })
            .catch(() => {})
            .finally(() => { if (!stale) setIsLoadingCards(false); });
        return () => { stale = true; };
    }, [hasStarted, liveGameId, token]);

    if (loadError && !game) {
        return (
            <div className="flex flex-col gap-4 p-4">
                <BackButton onBack={onBack} />
                <InlineError size="md">{loadError}</InlineError>
            </div>
        );
    }
    if (!game) return <GameDetailSkeleton onBack={onBack} />;
    if (game.status === "cancelled") {
        return (
            <div className="flex flex-col gap-4 p-4">
                <BackButton onBack={onBack} />
                <InlineError size="md">This invite was cancelled.</InlineError>
            </div>
        );
    }
    if (!hasStarted || !game.state) return <InviteWaitingRoom game={game} token={token} onBack={onBack} onCancelled={refresh} />;

    return (
        <LiveBoard
            key={liveGameId}
            game={game}
            cardMap={cardMap}
            isLoadingCards={isLoadingCards}
            isSubmitting={isSubmitting}
            moveError={moveError}
            submit={submit}
            onBack={onBack}
        />
    );
}
