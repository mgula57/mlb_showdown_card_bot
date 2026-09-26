import { useCallback, useEffect, useRef, useState } from 'react';
import BackButton from '../shared/BackButton';
import { TeamPreviewCard, TeamPreviewCardSkeleton, type TeamPreviewData } from './TeamPreviewCard';

const PAGE_SIZE = 60;

type TeamGridPageProps<T> = {
    title: string;
    subtitle?: string;
    onBack: () => void;
    horizontalPadding?: string;
    /** Fetches one page starting at `offset`. Fewer than `PAGE_SIZE` results signals the end. */
    fetchPage: (offset: number, limit: number) => Promise<T[]>;
    getKey: (item: T) => string | number;
    toPreview: (item: T) => TeamPreviewData;
    onOpenTeam: (item: T) => void;
    emptyMessage?: string;
};

/** Shared shell for a source's "See all" page — every team already sorted server-side (points
 *  descending), paged in as the user scrolls rather than loaded all at once. */
export function TeamGridPage<T>({
    title, subtitle, onBack, horizontalPadding, fetchPage, getKey, toPreview, onOpenTeam, emptyMessage,
}: TeamGridPageProps<T>) {
    const px = horizontalPadding ?? '';
    const [items, setItems] = useState<T[]>([]);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback((pageOffset: number, append: boolean) => {
        (append ? setIsLoadingMore : setIsLoading)(true);
        fetchPage(pageOffset, PAGE_SIZE)
            .then(page => {
                setItems(prev => append ? [...prev, ...page] : page);
                setOffset(pageOffset);
                setHasMore(page.length >= PAGE_SIZE);
                setError(null);
            })
            .catch((err: Error) => setError(err.message ?? 'Failed to load teams.'))
            .finally(() => { setIsLoading(false); setIsLoadingMore(false); });
    }, [fetchPage]);

    // Re-run from the top whenever the fetcher identity changes (e.g. its era/set changed).
    useEffect(() => { load(0, false); }, [load]);

    const observerRef = useRef<IntersectionObserver | null>(null);
    const sentinelRef = useCallback((node: HTMLDivElement | null) => {
        observerRef.current?.disconnect();
        if (!node) return;
        observerRef.current = new IntersectionObserver(entries => {
            if (entries[0]?.isIntersecting && hasMore && !isLoading && !isLoadingMore) {
                load(offset + PAGE_SIZE, true);
            }
        }, { rootMargin: '600px' });
        observerRef.current.observe(node);
    }, [hasMore, isLoading, isLoadingMore, offset, load]);

    return (
        <div className="flex flex-col gap-4 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
            <div className={`flex items-center gap-3 ${px}`}>
                <BackButton onBack={onBack} />
                <div>
                    <h1 className="text-[20px] font-black text-(--text-primary)">{title}</h1>
                    {subtitle && <p className="text-[12px] text-(--text-secondary)">{subtitle}</p>}
                </div>
            </div>

            {error && (
                <div className={`${px} text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5`}>
                    {error}
                </div>
            )}

            <div className={`flex flex-wrap gap-3 ${px}`}>
                {items.map(item => (
                    <TeamPreviewCard key={getKey(item)} team={toPreview(item)} onClick={() => onOpenTeam(item)} />
                ))}
                {(isLoading || isLoadingMore) && Array.from({ length: isLoading ? 12 : 6 }, (_, i) => (
                    <TeamPreviewCardSkeleton key={`skeleton-${i}`} />
                ))}
            </div>

            {!isLoading && items.length === 0 && !error && (
                <p className={`${px} text-[13px] text-(--text-tertiary) py-8 text-center`}>
                    {emptyMessage ?? 'No teams found.'}
                </p>
            )}

            {hasMore && !isLoading && <div ref={sentinelRef} className="h-8" />}
        </div>
    );
}

export default TeamGridPage;
