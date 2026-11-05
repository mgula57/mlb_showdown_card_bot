import { createPortal } from 'react-dom';
import BackButton from '../../shared/BackButton';
import { Heading } from '../../shared/Heading';
import { UnderToolbarFill } from '../../shared/UnderToolbarFill';
import { useBodyScrollLock } from '../../../hooks/useBodyScrollLock';
import type { LeagueState } from '../../../api/leagues';
import { SEASON_STATUS_LABEL } from '../leagueUi';
import { DraftTopBar } from './DraftHeader';
import { LeagueDraftRoom } from './LeagueDraftRoom';

type Props = {
    state: LeagueState;
    token: string;
    onBack: () => void;
    onOpenBigBoard: () => void;
    /** The draft just finished. */
    onComplete: () => void;
};

/**
 * The draft room as its own full-screen page (`/leagues/:id/draft`), covering the app's nav so
 * the board gets the whole window. Portaled to `<body>`: the app's `<main>` is its own stacking
 * context, so a fixed layer inside it would sit under the header. Locks the page behind it and
 * fills under mobile Safari's toolbar, like any full-screen overlay (see frontend/DESIGN.md).
 */
export function LeagueDraftScreen({ state, token, onBack, onOpenBigBoard, onComplete }: Props) {
    const { league, season, is_commissioner: isCommissioner, my_member_id: myMemberId } = state;
    useBodyScrollLock(true);

    // The live draft status shares this bar - on phones it gets the room the title would take
    const topBarLeading = (
        <>
            <BackButton onBack={onBack} label="" />
            <div className="hidden sm:block min-w-0">
                <Heading level="panel" as="h1" fit>{`${league.name} Draft`}</Heading>
                <p className="text-[11px] text-(--text-secondary) truncate">
                    Set {league.showdown_set}
                    {season ? ` · Season ${season.season_number} · ${SEASON_STATUS_LABEL[season.status]}` : ''}
                </p>
            </div>
        </>
    );

    return createPortal(
        <>
        <UnderToolbarFill zIndex={55} className="left-0 w-full bg-(--background-primary)" />
        <div className="fixed inset-0 z-[55] flex flex-col overflow-y-auto bg-(--background-primary) text-(--text-primary)">
            {season ? (
                <LeagueDraftRoom
                    key={season.season_number}
                    league={league}
                    seasonNumber={season.season_number}
                    token={token}
                    myMemberId={myMemberId}
                    isCommissioner={isCommissioner}
                    topBarLeading={topBarLeading}
                    onOpenBigBoard={onOpenBigBoard}
                    onComplete={onComplete}
                />
            ) : <DraftTopBar leading={topBarLeading} />}
        </div>
        </>,
        document.body,
    );
}
