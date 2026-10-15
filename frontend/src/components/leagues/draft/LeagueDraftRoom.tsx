import { useEffect, useMemo, useState } from 'react';
import { FaHandPointer, FaSpinner } from 'react-icons/fa6';
import ShowdownCardSearch, { type FilterSelections } from '../../cards/ShowdownCardSearch';
import { Modal } from '../../shared/Modal';
import { Tabs } from '../../shared/Tabs';
import { CardSource } from '../../../types/cardSource';
import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import { makeDraftPick, type League } from '../../../api/leagues';
import { useLeagueDraft } from '../../../hooks/useLeagueDraft';
import { useMediaQuery } from '../../../hooks/useMediaQuery';
import { ERROR_BOX_CLASS, PRIMARY_BUTTON_CLASS, SECONDARY_BUTTON_CLASS, errorMessage } from '../leagueUi';
import { DraftBoard, DraftBoardSkeleton } from './DraftBoard';
import { DraftHeader } from './DraftHeader';
import { DraftHistory } from './DraftHistory';
import { DraftTeamPanel } from './DraftTeamPanel';
import { draftView } from './draftView';

const LOCKED_FILTERS = ['release_edition_id'];

type MobileTab = 'board' | 'team' | 'history';
type SideTab = 'team' | 'history';
type BoardMode = 'picks' | 'pool';

type Props = {
    league: League;
    seasonNumber: number;
    token: string;
    myMemberId: string | null;
    isCommissioner: boolean;
    onOpenBigBoard: () => void;
    /** The draft just finished - the league page moves on to season setup. */
    onComplete: () => void;
};

/**
 * The live draft: header (on the clock, last pick, upcoming picks) over the board. On desktop the
 * board takes 2/3 of the width with Team / History tabbed beside it; on phones Board / Team /
 * History are tabs. The board area toggles between the pick grid and the player pool.
 */
export function LeagueDraftRoom({ league, seasonNumber, token, myMemberId, isCommissioner, onOpenBigBoard, onComplete }: Props) {
    const isDesktop = useMediaQuery('(min-width: 768px)');
    const [mobileTab, setMobileTab] = useState<MobileTab>('board');
    const [sideTab, setSideTab] = useState<SideTab>('team');
    const [boardMode, setBoardMode] = useState<BoardMode>('picks');
    const [confirmCard, setConfirmCard] = useState<CardDatabaseRecord | null>(null);
    const [picking, setPicking] = useState<'card' | 'auto' | null>(null);
    const [pickError, setPickError] = useState<string | null>(null);
    const [isLive, setIsLive] = useState(true);

    const { data, setData, error } = useLeagueDraft(token, league.league_id, seasonNumber, isLive);
    const draft = data?.draft ?? null;
    const view = useMemo(() => (draft ? draftView(draft, myMemberId) : null), [draft, myMemberId]);

    // Stop refreshing once the draft is done, and hand off to season setup
    const isComplete = !!view?.isComplete;
    useEffect(() => {
        if (!isComplete) return;
        setIsLive(false);
        onComplete();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isComplete]);

    const poolFilters = useMemo<Partial<FilterSelections>>(() => ({ release_edition_id: league.edition_ids }), [league.edition_ids]);

    async function pick(releaseCardId: string | null) {
        setPicking(releaseCardId ? 'card' : 'auto');
        setPickError(null);
        try {
            setData(await makeDraftPick(token, league.league_id, seasonNumber, releaseCardId));
            setConfirmCard(null);
        } catch (err) {
            setPickError(errorMessage(err));
            // A 409 means the board moved - the Realtime ping for that pick brings it up to date
        } finally {
            setPicking(null);
        }
    }

    if (!draft || !view) {
        return error ? <div className={ERROR_BOX_CLASS}>{error}</div> : (
            <div className="flex flex-col gap-3">
                <div className="h-28 rounded-2xl bg-(--background-secondary) animate-pulse" />
                <DraftBoardSkeleton />
            </div>
        );
    }

    const boardArea = (
        <div className="flex flex-col gap-2 min-w-0">
            <Tabs<BoardMode>
                tabs={[{ id: 'picks', label: 'Picks' }, { id: 'pool', label: 'Player Pool' }]}
                value={boardMode}
                onChange={setBoardMode}
                fullWidth
                size="sm"
            />
            {boardMode === 'picks' ? (
                <DraftBoard draft={draft} view={view} myMemberId={myMemberId} />
            ) : (
                <div className="min-h-[60vh] rounded-xl border border-(--divider) overflow-hidden">
                    <ShowdownCardSearch
                        source={CardSource.RELEASE}
                        defaultFilters={poolFilters}
                        lockedFilters={LOCKED_FILTERS}
                        excludeIds={view.draftedIds}
                        disableLocalStorage
                        compact
                        actionButton={{
                            icon: <FaHandPointer />,
                            label: view.isMyTurn ? 'Draft' : 'Not your pick',
                            onClick: card => setConfirmCard(card),
                            disabled: !view.isMyTurn || view.isComplete || picking !== null,
                        }}
                    />
                </div>
            )}
        </div>
    );

    const teamPanel = <DraftTeamPanel draft={draft} settings={league.settings} myMemberId={myMemberId} />;
    const historyPanel = <DraftHistory draft={draft} view={view} />;

    return (
        <div className="flex flex-col gap-3">
            <DraftHeader
                draft={draft}
                view={view}
                myMemberId={myMemberId}
                isCommissioner={isCommissioner}
                autoPicking={picking === 'auto'}
                onAutoPick={() => pick(null)}
                onOpenBigBoard={onOpenBigBoard}
            />
            {pickError && <div className={ERROR_BOX_CLASS}>{pickError}</div>}

            {isDesktop ? (
                <div className="grid grid-cols-3 gap-4 items-start">
                    <div className="col-span-2 min-w-0">{boardArea}</div>
                    <div className="flex flex-col gap-3 min-w-0">
                        <Tabs<SideTab>
                            tabs={[{ id: 'team', label: 'Team' }, { id: 'history', label: 'History' }]}
                            value={sideTab}
                            onChange={setSideTab}
                            fullWidth
                            size="sm"
                        />
                        {sideTab === 'team' ? teamPanel : historyPanel}
                    </div>
                </div>
            ) : (
                <div className="flex flex-col gap-3">
                    <Tabs<MobileTab>
                        tabs={[{ id: 'board', label: 'Board' }, { id: 'team', label: 'Team' }, { id: 'history', label: 'History' }]}
                        value={mobileTab}
                        onChange={setMobileTab}
                        fullWidth
                    />
                    {mobileTab === 'board' ? boardArea : mobileTab === 'team' ? teamPanel : historyPanel}
                </div>
            )}

            {confirmCard && (
                <Modal
                    title={`Draft ${confirmCard.name}?`}
                    subtitle={`${confirmCard.year} · ${confirmCard.points} pts`}
                    onClose={() => setConfirmCard(null)}
                    size="sm"
                    footer={
                        <div className="flex justify-end gap-2 w-full">
                            <button type="button" onClick={() => setConfirmCard(null)} className={SECONDARY_BUTTON_CLASS}>Cancel</button>
                            <button type="button" onClick={() => pick(confirmCard.id)} disabled={picking !== null || !view.isMyTurn} className={PRIMARY_BUTTON_CLASS}>
                                {picking === 'card' ? <FaSpinner className="animate-spin" /> : <FaHandPointer />}
                                Draft
                            </button>
                        </div>
                    }
                >
                    <p className="p-4 text-[13px] text-(--text-secondary)">
                        {view.isMyTurn ? 'They go straight onto your roster in the first open spot they fit.' : "It's no longer your pick."}
                    </p>
                </Modal>
            )}
        </div>
    );
}
