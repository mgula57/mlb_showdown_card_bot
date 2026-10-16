import { useEffect, useMemo, useState } from 'react';
import { FaBookmark, FaHandPointer, FaListOl, FaMagnifyingGlass, FaRegBookmark, FaSpinner, FaTableCells, FaUsers } from 'react-icons/fa6';
import ShowdownCardSearch, { type FilterSelections } from '../../cards/ShowdownCardSearch';
import { Tabs } from '../../shared/Tabs';
import { DraftPositionModal, type DraftPositionOption } from '../../team_builder/DraftPositionModal';
import { type PendingSlot, getSearchFiltersForSlot, pendingSlotHighlight, pendingSlotLabel } from '../../team_builder/draftSlot';
import { PendingSlotChip } from '../../team_builder/PendingSlotChip';
import { CardSource } from '../../../types/cardSource';
import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import { makeDraftPick, type League } from '../../../api/leagues';
import { useLeagueDraft } from '../../../hooks/useLeagueDraft';
import { useCardMap } from '../../../hooks/useCardMap';
import { useDraftQueue } from '../../../hooks/useDraftQueue';
import { useMediaQuery } from '../../../hooks/useMediaQuery';
import { ERROR_BOX_CLASS, PRIMARY_BUTTON_CLASS, errorMessage } from '../leagueUi';
import { DraftBoard, DraftBoardSkeleton } from './DraftBoard';
import { DraftHeader } from './DraftHeader';
import { DraftHistory } from './DraftHistory';
import { DraftQueuePanel } from './DraftQueuePanel';
import { DraftTeamPanel } from './DraftTeamPanel';
import { draftView, legalDraftSlots } from './draftView';

const LOCKED_FILTERS = ['release_edition_id'];
// The pool leads with the best cards, not a release's card-number order
const POOL_DEFAULT_SORT = { sort_by: 'points', sort_direction: 'desc' };
const NO_IDS: string[] = [];

// One "picks" view everywhere: the grid on desktop (it needs the width), the newest-first list on phones
type MainTab = 'pool' | 'queue' | 'board';
type MobileTab = 'pool' | 'queue' | 'team' | 'picks';

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
 * The live draft: header (on the clock, last pick, upcoming picks) over the room. On desktop the
 * main 2/3 toggles Player Pool / Draft Board with the drafter's team pinned beside it, so a slot
 * clicked on the team filters the pool right next to it. On phones Pool / Team / Picks are tabs,
 * with picks as a list since the grid is too wide for a phone.
 */
export function LeagueDraftRoom({ league, seasonNumber, token, myMemberId, isCommissioner, onOpenBigBoard, onComplete }: Props) {
    const isDesktop = useMediaQuery('(min-width: 768px)');
    const [mobileTab, setMobileTab] = useState<MobileTab>('pool');
    const [mainTab, setMainTab] = useState<MainTab>('pool');
    const [confirmCard, setConfirmCard] = useState<CardDatabaseRecord | null>(null);
    // The empty slot on my roster the drafter clicked - narrows the player pool to cards that fit it
    const [pendingSlot, setPendingSlot] = useState<PendingSlot | null>(null);
    // The roster position being drafted into (or 'auto' / 'any' for an auto-pick / unslotted pick)
    const [picking, setPicking] = useState<string | null>(null);
    const [pickError, setPickError] = useState<string | null>(null);
    const [isLive, setIsLive] = useState(true);

    const { data, setData, error } = useLeagueDraft(token, league.league_id, seasonNumber, isLive);
    const draft = data?.draft ?? null;
    const view = useMemo(() => (draft ? draftView(draft, myMemberId) : null), [draft, myMemberId]);
    const pickSlots = useMemo(
        () => (draft?.picks ?? []).map(pick => ({ card_id: pick.release_card_id, card_source: CardSource.RELEASE })),
        [draft?.picks],
    );
    const { cardMap, loading: cardsLoading } = useCardMap(pickSlots, token);
    const queue = useDraftQueue(league.league_id, seasonNumber, view?.draftedIds ?? NO_IDS);

    // Stop refreshing once the draft is done, and hand off to season setup
    const isComplete = !!view?.isComplete;
    useEffect(() => {
        if (!isComplete) return;
        setIsLive(false);
        // Nothing left to draft - lead with the results
        setMainTab('board');
        setMobileTab('picks');
        onComplete();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isComplete]);

    const poolFilters = useMemo<Partial<FilterSelections>>(
        () => ({ release_edition_id: league.edition_ids, ...getSearchFiltersForSlot(pendingSlot) }),
        [league.edition_ids, pendingSlot],
    );

    /** A click on an empty slot of my roster: open the player pool filtered to what fits it. */
    function fillSlot(slot: PendingSlot) {
        setPendingSlot(slot);
        setMainTab('pool');
        setMobileTab('pool');
    }

    /** Draft `releaseCardId` into `rosterPosition` (null: the first open spot it fits), or
     *  auto-pick when `releaseCardId` is null. */
    async function pick(releaseCardId: string | null, rosterPosition: string | null = null) {
        setPicking(releaseCardId ? rosterPosition ?? 'any' : 'auto');
        setPickError(null);
        try {
            setData(await makeDraftPick(token, league.league_id, seasonNumber, releaseCardId, rosterPosition));
            setConfirmCard(null);
            setPendingSlot(null);
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

    // Where the card picked from the pool can go, with its points impact - the clicked slot first
    const myRoster = draft.my_roster;
    const { activePosition, activeRole } = pendingSlotHighlight(pendingSlot);
    const targetPosition = activePosition ?? activeRole;
    const confirmOptions: DraftPositionOption[] = confirmCard && myRoster
        ? legalDraftSlots(confirmCard, myRoster, league.settings)
            .sort((a, b) => Number(b === targetPosition) - Number(a === targetPosition))
            .map(position => {
            const projected = myRoster.points + confirmCard.points;
            return {
                position,
                currentPts: myRoster.points,
                projectedPts: projected,
                overLimit: !!league.settings.pts_cap && projected > league.settings.pts_cap,
            };
        })
        : [];

    const canPick = view.isMyTurn && !view.isComplete && picking === null;
    const fitsRoster = (card: CardDatabaseRecord) => !!myRoster && legalDraftSlots(card, myRoster, league.settings).length > 0;
    // Spectators (not in the league) and finished drafts have nothing to queue
    const showQueue = !!myMemberId && !view.isComplete;
    const queueTabLabel = queue.queue.length ? `Queue ${queue.queue.length}` : 'Queue';
    const queuePanel = (
        <DraftQueuePanel
            queue={queue.queue}
            onMove={queue.move}
            onRemove={queue.remove}
            onDraft={setConfirmCard}
            canDraft={canPick}
            fitsRoster={fitsRoster}
        />
    );

    const poolPanel = (
        <div className="min-h-[60vh] rounded-xl border border-(--divider) overflow-hidden">
            <ShowdownCardSearch
                source={CardSource.RELEASE}
                defaultFilters={poolFilters}
                lockedFilters={LOCKED_FILTERS}
                defaultSort={POOL_DEFAULT_SORT}
                excludeIds={view.draftedIds}
                disableLocalStorage
                compact
                toolbarSlot={pendingSlot && (
                    <PendingSlotChip label={pendingSlotLabel(pendingSlot)!} onDismiss={() => setPendingSlot(null)} />
                )}
                actionButton={{
                    icon: <FaHandPointer />,
                    label: 'Draft',
                    variant: 'prominent',
                    onClick: card => setConfirmCard(card),
                    disabled: !canPick,
                    disabledLabel: view.isComplete ? 'The draft is over' : !view.isMyTurn ? 'Not your pick' : undefined,
                }}
                secondaryAction={showQueue ? card => {
                    const isQueued = queue.isQueued(card.id);
                    return {
                        icon: isQueued ? <FaBookmark className="text-amber-500" /> : <FaRegBookmark />,
                        label: isQueued ? 'Remove from queue' : 'Add to queue',
                        placement: 'left',
                        onClick: () => queue.toggle(card),
                    };
                } : undefined}
            />
        </div>
    );

    const teamPanel = (
        <DraftTeamPanel
            draft={draft}
            settings={league.settings}
            myMemberId={myMemberId}
            cards={cardMap}
            isLoadingCards={cardsLoading}
            pendingSlot={pendingSlot}
            onFillSlot={view.isComplete ? undefined : fillSlot}
        />
    );

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
            {pickError && !confirmCard && <div className={ERROR_BOX_CLASS}>{pickError}</div>}

            {isDesktop ? (
                <div className="grid grid-cols-3 gap-4 items-start">
                    <div className="col-span-2 flex flex-col gap-2 min-w-0">
                        <Tabs<MainTab>
                            tabs={[
                                { id: 'pool', label: 'Player Pool', icon: <FaMagnifyingGlass /> },
                                ...(showQueue ? [{ id: 'queue' as const, label: queueTabLabel, icon: <FaBookmark /> }] : []),
                                { id: 'board', label: 'Draft Board', icon: <FaTableCells /> },
                            ]}
                            value={mainTab}
                            onChange={setMainTab}
                            fullWidth
                            size="sm"
                        />
                        {mainTab === 'pool' ? poolPanel
                            : mainTab === 'queue' && showQueue ? queuePanel
                            : <DraftBoard draft={draft} view={view} myMemberId={myMemberId} cards={cardMap} />}
                    </div>
                    {/* Pinned while the pool / board scrolls, so the team stays in view beside the search */}
                    <div className="sticky top-16 max-h-[calc(100dvh-5rem)] overflow-y-auto scrollbar-hide min-w-0">
                        {teamPanel}
                    </div>
                </div>
            ) : (
                <div className="flex flex-col gap-3">
                    <Tabs<MobileTab>
                        tabs={[
                            { id: 'pool', label: 'Pool', icon: <FaMagnifyingGlass /> },
                            ...(showQueue ? [{ id: 'queue' as const, label: queueTabLabel, icon: <FaBookmark /> }] : []),
                            { id: 'team', label: 'Team', icon: <FaUsers /> },
                            { id: 'picks', label: 'Picks', icon: <FaListOl /> },
                        ]}
                        value={mobileTab}
                        onChange={setMobileTab}
                        fullWidth
                    />
                    {mobileTab === 'pool' ? poolPanel
                        : mobileTab === 'queue' && showQueue ? queuePanel
                        : mobileTab === 'team' ? teamPanel
                        : <DraftHistory draft={draft} view={view} />}
                </div>
            )}

            {confirmCard && (
                <DraftPositionModal
                    card={confirmCard}
                    options={confirmOptions}
                    onSelect={position => pick(confirmCard.id, position)}
                    onClose={() => { setConfirmCard(null); setPickError(null); }}
                    savingPosition={picking}
                    disabled={!view.isMyTurn}
                >
                    {!view.isMyTurn ? (
                        <p className="text-[12px] text-(--text-secondary)">It's no longer your pick.</p>
                    ) : confirmOptions.length === 0 && (
                        // Nothing fits - the server only allows this when no card left in the pool fits either
                        <div className="flex flex-col items-start gap-2">
                            <p className="text-[12px] text-(--text-secondary)">No open spot on your roster fits this card. If nothing left in the pool fits either, it can be drafted out of position.</p>
                            <button type="button" onClick={() => pick(confirmCard.id)} disabled={picking !== null} className={PRIMARY_BUTTON_CLASS}>
                                {picking === 'any' ? <FaSpinner className="animate-spin" /> : <FaHandPointer />}
                                Draft anyway
                            </button>
                        </div>
                    )}
                    {pickError && <div className={ERROR_BOX_CLASS}>{pickError}</div>}
                </DraftPositionModal>
            )}
        </div>
    );
}
