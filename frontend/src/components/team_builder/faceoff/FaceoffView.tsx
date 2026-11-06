/**
 * @fileoverview A Faceoff's shareable replay page. It opens parked on the first pitch with the result
 * hidden, like every sim, and plays on the same stage as a real game. A series picks its game with
 * `?game=N`; a single game needs no parameter.
 */
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { fetchFaceoff, fetchFaceoffCards, rematchPayload, startFaceoff, type Faceoff, type FaceoffGame } from '../../../api/faceoff';
import type { ShowdownBotCardAPIResponse } from '../../../api/showdownBotCard';
import { fromSimTimeline } from '../../../domain/adapters/fromSim';
import { bannerTokens, NEUTRAL_TEAM_COLOR } from '../../../functions/colors';
import GameBoxScoreTabs from '../../games/GameBoxScoreTabs';
import GameDetailSkeleton from '../../games/GameDetailSkeleton';
import GameLinescore from '../../games/GameLinescore';
import GameStage, { SimTopBarControls } from '../../games/GameStage';
import SimBoxScoreTable from '../../games/SimBoxScoreTable';
import TimelinePlayback from '../../games/TimelinePlayback';
import { useGameStage } from '../../games/useGameStage';
import TopBarButton from '../../games/detail/TopBarButton';
import BackButton from '../../shared/BackButton';
import { InlineError } from '../../shared/InlineError';

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

type Props = {
    faceoffId: string;
    token?: string;
    onBack: () => void;
    onOpenFaceoff: (faceoffId: string) => void;
};

function FaceoffReplay({ faceoffId, entry, cardMap, isLoadingCards, onBack, onRematch, isStartingRematch, rematchError }: {
    faceoffId: string;
    entry: FaceoffGame;
    cardMap: CardMap;
    isLoadingCards: boolean;
    onBack: () => void;
    /** Absent when this viewer can't run the matchup again. */
    onRematch?: () => void;
    isStartingRematch: boolean;
    rematchError: string | null;
}) {
    const stage = useGameStage();
    const timeline = useMemo(() => fromSimTimeline(entry.game, `${faceoffId}:${entry.game_number}`), [faceoffId, entry]);
    const barColor = entry.game.away_team_identity?.primary_color ?? NEUTRAL_TEAM_COLOR;

    return (
        <TimelinePlayback timeline={timeline} initialMode="playback" initialCursor="start" showFrozenBoxscoreCaveat={false}>
            {({ activeView, activePlays, playbackBar, playbackControls, playbackState, isReplaying }) => (
                <GameStage
                    stage={stage}
                    game={activeView}
                    plays={activePlays}
                    playbackState={playbackState}
                    playbackControls={playbackControls}
                    isReplaying={isReplaying}
                    playbackBar={playbackBar}
                    detailedState="Faceoff Final"
                    cardMap={cardMap}
                    isLoadingCards={isLoadingCards}
                    isSim
                    gameKey={`${faceoffId}:${entry.game_number}`}
                    title="Faceoff"
                    modeBarColor={barColor}
                    onBack={onBack}
                    topBarStatus={rematchError && <span className="text-[11px] text-(--red)">{rematchError}</span>}
                    topBarActions={
                        <>
                            {/* Offered once the result is in, so it never competes with the replay. */}
                            {onRematch && !isReplaying && (
                                <TopBarButton
                                    label={isStartingRematch ? 'Starting…' : 'Rematch'}
                                    onClick={onRematch}
                                    className={`rounded-control px-2 py-1 h-7 ${bannerTokens(barColor).btnClass}`}
                                />
                            )}
                            <SimTopBarControls
                                cursor={playbackState.cursor}
                                controls={playbackControls}
                                isMidReplay={isReplaying}
                                onExit={onBack}
                                buttonClass={`rounded-control px-2 py-1 h-7 ${bannerTokens(barColor).btnClass}`}
                            />
                        </>
                    }
                    boxScorePanels={
                        <div className="@container space-y-4">
                            <GameLinescore game={activeView} />
                            <GameBoxScoreTabs
                                awayLabel={activeView.away.team.abbreviation}
                                homeLabel={activeView.home.team.abbreviation}
                                renderSide={(side) => {
                                    const boxscore = activeView[side].boxscore;
                                    return boxscore
                                        ? <SimBoxScoreTable boxscore={boxscore} cardMap={cardMap} onCardSelect={stage.setSelectedCard} />
                                        : null;
                                }}
                            />
                        </div>
                    }
                />
            )}
        </TimelinePlayback>
    );
}

export function FaceoffView({ faceoffId, token, onBack, onOpenFaceoff }: Props) {
    const [searchParams] = useSearchParams();
    const [faceoff, setFaceoff] = useState<Faceoff | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [cardMap, setCardMap] = useState<CardMap>({});
    const [isLoadingCards, setIsLoadingCards] = useState(true);
    const [isStartingRematch, setIsStartingRematch] = useState(false);
    const [rematchError, setRematchError] = useState<string | null>(null);

    useEffect(() => {
        let stale = false;
        fetchFaceoff(faceoffId, token)
            .then(data => { if (!stale) setFaceoff(data); })
            .catch(err => { if (!stale) setError(err instanceof Error ? err.message : 'Failed to load Faceoff.'); });
        // The replay still works from names alone, so a card failure doesn't block it.
        fetchFaceoffCards(faceoffId, token)
            .then(cards => { if (!stale) setCardMap(cards); })
            .catch(() => {})
            .finally(() => { if (!stale) setIsLoadingCards(false); });
        return () => { stale = true; };
    }, [faceoffId, token]);

    if (error) {
        return (
            <div className="flex flex-col gap-4 p-4">
                <BackButton onBack={onBack} />
                <InlineError size="md">{error}</InlineError>
            </div>
        );
    }
    if (!faceoff) return <GameDetailSkeleton onBack={onBack} />;

    const rematch = faceoff.is_mine && token ? rematchPayload(faceoff) : null;
    async function handleRematch() {
        if (!rematch || !token || isStartingRematch) return;
        setIsStartingRematch(true);
        setRematchError(null);
        try {
            onOpenFaceoff(await startFaceoff(rematch, token));
        } catch (err) {
            setRematchError(err instanceof Error ? err.message : 'Failed to start rematch.');
            setIsStartingRematch(false);
        }
    }

    const gameNumber = Number(searchParams.get('game')) || 1;
    const entry = faceoff.games.find(game => game.game_number === gameNumber) ?? faceoff.games[0];
    return (
        <FaceoffReplay
            key={entry.game_number}
            faceoffId={faceoffId}
            entry={entry}
            cardMap={cardMap}
            isLoadingCards={isLoadingCards}
            onBack={onBack}
            onRematch={rematch ? handleRematch : undefined}
            isStartingRematch={isStartingRematch}
            rematchError={rematchError}
        />
    );
}
