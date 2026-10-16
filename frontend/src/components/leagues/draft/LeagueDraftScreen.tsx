import { createPortal } from 'react-dom';
import BackButton from '../../shared/BackButton';
import type { LeagueState } from '../../../api/leagues';
import { SEASON_STATUS_LABEL } from '../leagueUi';
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
 * context, so a fixed layer inside it would sit under the header.
 */
export function LeagueDraftScreen({ state, token, onBack, onOpenBigBoard, onComplete }: Props) {
    const { league, season, is_commissioner: isCommissioner, my_member_id: myMemberId } = state;

    return createPortal(
        <div className="fixed inset-0 z-[55] flex flex-col overflow-y-auto bg-(--background-primary) text-(--text-primary)">
            <div className="sticky top-0 z-30 flex items-center gap-3 px-4 sm:px-6 py-2 border-b border-(--divider) bg-(--background-primary)/90 backdrop-blur">
                <BackButton onBack={onBack} label="" />
                <div className="min-w-0">
                    <h1 className="text-[16px] sm:text-[18px] font-black truncate">{league.name} Draft</h1>
                    <p className="text-[11px] text-(--text-secondary)">
                        Set {league.showdown_set}
                        {season ? ` · Season ${season.season_number} · ${SEASON_STATUS_LABEL[season.status]}` : ''}
                    </p>
                </div>
            </div>

            <div className="flex-1 w-full max-w-[1800px] mx-auto px-4 sm:px-6 py-4">
                {season && (
                    <LeagueDraftRoom
                        key={season.season_number}
                        league={league}
                        seasonNumber={season.season_number}
                        token={token}
                        myMemberId={myMemberId}
                        isCommissioner={isCommissioner}
                        onOpenBigBoard={onOpenBigBoard}
                        onComplete={onComplete}
                    />
                )}
            </div>
        </div>,
        document.body,
    );
}
