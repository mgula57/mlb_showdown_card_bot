/**
 * @fileoverview Home's offseason band: trades and signings in the spot Today's Games holds during
 * the season, with a way into simming the season ahead. Viewers pick how it's ordered: the week's
 * biggest moves by card points, or a feed of the latest moves, newest first.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FaDice, FaFire } from 'react-icons/fa6';

import { fetchSeasonTransactions, type Season, type TransactionFeed, type TransactionMove } from '../../api/mlbAPI';
import type { ShowdownBotCard } from '../../api/showdownBotCard';
import { TransactionMoveItem, TransactionMoveItemSkeleton } from '../seasons/TransactionMoveItem';
import { formatMoveDay, groupByDay } from '../seasons/transactionMoves';
import { CarouselRow } from '../shared/CarouselRow';
import { Eyebrow } from '../shared/Eyebrow';
import { buttonClass } from '../shared/buttonStyles';
import { choiceClass } from '../shared/choiceStyles';
import { HomeBand } from './HomeBand';

const MOVE_COUNT = 8;
const RECENT_DAYS = 7;

type HotStoveOrder = 'biggest' | 'latest';

const ORDER_OPTIONS: { id: HotStoveOrder; label: string }[] = [
    { id: 'biggest', label: 'Biggest' },
    { id: 'latest', label: 'Latest' },
];

// A per-viewer preference, so it lives in this browser only (storage can be unavailable).
const ORDER_STORAGE_KEY = 'home.hotStove.order';
const readStoredOrder = (): HotStoveOrder => {
    try {
        return window.localStorage.getItem(ORDER_STORAGE_KEY) === 'latest' ? 'latest' : 'biggest';
    } catch {
        return 'biggest';
    }
};
const storeOrder = (order: HotStoveOrder) => {
    try {
        window.localStorage.setItem(ORDER_STORAGE_KEY, order);
    } catch {
        // Not remembered this time; the choice still applies.
    }
};

const isoDaysAgo = (days: number): string => {
    const date = new Date();
    date.setDate(date.getDate() - days);
    return `${date.getFullYear()}-${`${date.getMonth() + 1}`.padStart(2, '0')}-${`${date.getDate()}`.padStart(2, '0')}`;
};

type HomeHotStoveProps = {
    /** The upcoming season the offseason leads into. */
    season: Season;
    showdownSet: string;
    onCardSelect: (card: ShowdownBotCard) => void;
};

export function HomeHotStove({ season, showdownSet, onCardSelect }: HomeHotStoveProps) {
    const [order, setOrder] = useState<HotStoveOrder>(readStoredOrder);
    const changeOrder = (next: HotStoveOrder) => {
        setOrder(next);
        storeOrder(next);
    };

    // The last finished request, tagged with what it asked for; loading is a tag mismatch.
    const requestKey = `${season.season_id}:${showdownSet}:${order}`;
    const [result, setResult] = useState<{ key: string; feed: TransactionFeed | null } | null>(null);

    useEffect(() => {
        const controller = new AbortController();
        const request = order === 'latest'
            // A feed: the newest moves across the whole offseason
            ? fetchSeasonTransactions(season.season_id, { showdownSet, sort: 'date', limit: MOVE_COUNT }, controller.signal)
            // This week's biggest moves; a quiet week falls back to the biggest of the whole offseason.
            : fetchSeasonTransactions(season.season_id, { showdownSet, sort: 'points', limit: MOVE_COUNT, since: isoDaysAgo(RECENT_DAYS) }, controller.signal)
                .then((recent) => recent.moves.length > 0 || !recent.window_start
                    ? recent
                    : fetchSeasonTransactions(season.season_id, { showdownSet, sort: 'points', limit: MOVE_COUNT }, controller.signal));
        request
            .then((feed) => setResult({ key: requestKey, feed }))
            .catch((err) => {
                if (err instanceof Error && err.name === 'AbortError') return;
                console.error('Failed to fetch Hot Stove moves:', err);
                setResult({ key: requestKey, feed: null });
            });
        return () => controller.abort();
    }, [season.season_id, showdownSet, order, requestKey]);

    const isLoading = result?.key !== requestKey;
    const feed = isLoading ? null : result?.feed ?? null;

    // Nothing to show until the World Series is over and a carded player has moved. Checked on the
    // last result even while a new order loads, so switching never makes the band vanish.
    const lastFeed = result?.feed ?? null;
    if (result && (!lastFeed?.window_start || lastFeed.moves.length === 0)) return null;

    const priorYear = Number(season.season_id) - 1;

    const renderMove = (move: TransactionMove, underDayHeading: boolean) => {
        // A two-club trade gets a wide tile so its "receives" columns sit side by side (they still
        // stack on a phone); every other move stays a narrow tile.
        const isTwoClubTrade = move.kind === 'trade' && move.team_ids.length === 2;
        return (
            <TransactionMoveItem
                key={move.id}
                move={move}
                teams={feed!.teams}
                cardYear={feed!.card_year}
                onCardSelect={onCardSelect}
                compact={!isTwoClubTrade}
                hideDescription
                hideDate={underDayHeading}
                className={`shrink-0 ${isTwoClubTrade ? 'w-72 sm:w-[25rem]' : 'w-72'}`}
            />
        );
    };

    return (
        <HomeBand
            title="Hot Stove"
            icon={<FaFire className="text-(--showdown-red) shrink-0" />}
            meta={order === 'latest' ? `Latest moves since the ${priorYear} World Series` : `Biggest moves since the ${priorYear} World Series`}
            link={{ label: 'All moves', to: `/seasons?season=${season.season_id}&tab=transactions` }}
        >
            {/* Control strip, matching the Today's Games strip: how the moves are ordered on the left
                (the band's meta line names the order), the sim hint and button on the right */}
            <div className="flex flex-wrap items-center justify-between gap-2 px-4 md:px-6 py-2 border-b border-(--divider) bg-(--background-tertiary)">
                <div className="flex items-center gap-1.5" role="group" aria-label="Order moves by">
                    {ORDER_OPTIONS.map((option) => (
                        <button
                            key={option.id}
                            type="button"
                            aria-pressed={order === option.id}
                            onClick={() => changeOrder(option.id)}
                            className={choiceClass(order === option.id, 'sm')}
                        >
                            {option.label}
                        </button>
                    ))}
                </div>
                <div className="flex flex-wrap items-center justify-end gap-2">
                    {/* The hint gives way on a phone, so the chips and the button share one line */}
                    <span className="hidden sm:flex items-center gap-1.5 text-[11px] font-medium text-(--text-tertiary)">
                        <FaDice className="text-(--text-secondary) shrink-0" />
                        Sim {season.season_id} with clubs as they stand today, on {priorYear} cards
                    </span>
                    <Link to={`/seasons?season=${season.season_id}&sim=1`} className={buttonClass('primary', 'sm')}>
                        Simulate {season.season_id}
                    </Link>
                </div>
            </div>

            <div className="px-4 md:px-6 py-4">
                <CarouselRow gutter="ticker" className="items-start">
                    {isLoading || !feed
                        ? [...Array(4)].map((_, i) => <TransactionMoveItemSkeleton key={i} compact className="w-72 shrink-0" />)
                        : order === 'latest'
                            // The feed, one group per day: an eyebrow label over that day's tiles, with
                            // a hairline between days
                            ? groupByDay(feed.moves).map((day, index) => (
                                <div key={day.date} className={`shrink-0 flex flex-col gap-2 ${index > 0 ? 'pl-3 border-l border-(--divider)' : ''}`}>
                                    <Eyebrow>{formatMoveDay(day.date)}</Eyebrow>
                                    <div className="flex gap-3 items-start">
                                        {day.moves.map((move) => renderMove(move, true))}
                                    </div>
                                </div>
                            ))
                            : feed.moves.map((move) => renderMove(move, false))}
                </CarouselRow>
            </div>
        </HomeBand>
    );
}

export default HomeHotStove;
