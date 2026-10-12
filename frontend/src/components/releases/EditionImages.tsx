import { useState, useEffect, useCallback, useMemo } from 'react';
import type { ReleaseEdition, ReleaseCardImage, ReleaseCardImageStatus, EditionImages as EditionImagesData } from '../../api/releases';
import { fetchEditionImages, renderEditionImages, cancelEditionImageRender, isImageJobActive } from '../../api/releases';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { cardImagePublicUrl } from '../../api/supabase';
import { Modal } from '../shared/Modal';
import { CardItemFromCardDatabaseRecord } from '../cards/CardItem';
import { FaArrowUpRightFromSquare, FaCheck, FaImage, FaSpinner, FaTriangleExclamation, FaWandMagicSparkles, FaXmark } from 'react-icons/fa6';

/** How often to refresh statuses while a render job runs (each card takes a few seconds). */
const POLL_INTERVAL_MS = 2500;
/** Skeleton tiles shown while statuses load. */
const MAX_SKELETON_TILES = 24;
const TILE_GRID_CLASS = 'grid grid-cols-[repeat(auto-fill,minmax(140px,1fr))] gap-4';

const STATUS_META: Record<ReleaseCardImageStatus, { label: string; badgeClass: string }> = {
    rendered: { label: 'Rendered', badgeClass: 'bg-green-600 text-white' },
    stale: { label: 'Out of date', badgeClass: 'bg-amber-500 text-black' },
    failed: { label: 'Failed', badgeClass: 'bg-red-600 text-white' },
    missing: { label: 'Not rendered', badgeClass: 'bg-(--background-quaternary) text-(--text-secondary)' },
};
const STATUS_ORDER: ReleaseCardImageStatus[] = ['rendered', 'stale', 'missing', 'failed'];

type EditionImagesProps = {
    releaseId: string;
    edition: ReleaseEdition;
    readOnly: boolean;
    token?: string;
};

/** Step 2 of the Edition Builder: renders every card in the edition (with its edition style and set
 * number) to Supabase in a background job, and shows each card's image as it lands. */
export function EditionImages({ releaseId, edition, readOnly, token }: EditionImagesProps) {
    const [data, setData] = useState<EditionImagesData | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [requesting, setRequesting] = useState(false);
    const [statusFilter, setStatusFilter] = useState<ReleaseCardImageStatus | null>(null);
    const [detailImage, setDetailImage] = useState<ReleaseCardImage | null>(null);

    const load = useCallback(() => {
        return fetchEditionImages(releaseId, edition.id, token)
            .then(result => { setData(result); setError(null); })
            .catch(err => setError(err.message ?? 'Failed to load images.'));
    }, [releaseId, edition.id, token]);

    // `edition` is replaced on every save (cards, style, numbering), any of which can make images out of date
    useEffect(() => { load(); }, [load, edition]);

    const job = data?.job ?? null;
    const jobActive = isImageJobActive(job);
    useEffect(() => {
        if (!jobActive) return;
        const timer = window.setTimeout(load, POLL_INTERVAL_MS);
        return () => window.clearTimeout(timer);
    }, [jobActive, data, load]);

    const snapshotsById = useMemo(
        () => new Map(edition.cards.map(c => [c.source_card_id, c.card_snapshot])),
        [edition.cards]
    );
    const images = useMemo(() => data?.images ?? [], [data]);
    const counts = useMemo(() => {
        const result: Record<ReleaseCardImageStatus, number> = { rendered: 0, stale: 0, missing: 0, failed: 0 };
        images.forEach(image => { result[image.status] += 1; });
        return result;
    }, [images]);
    const needsRenderCount = counts.stale + counts.missing + counts.failed;
    const visibleImages = statusFilter ? images.filter(image => image.status === statusFilter) : images;
    // The detail modal follows its card's latest status (e.g. while a render of it runs)
    const detail = detailImage ? images.find(image => image.source_card_id === detailImage.source_card_id) ?? detailImage : null;

    async function handleRender(sourceCardIds?: string[]) {
        if (!token) return;
        setRequesting(true);
        setError(null);
        try {
            const startedJob = await renderEditionImages(releaseId, edition.id, token, sourceCardIds);
            setData(prev => prev ? { ...prev, job: startedJob } : prev);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start rendering.');
        } finally {
            setRequesting(false);
        }
    }

    async function handleCancel() {
        if (!token) return;
        setRequesting(true);
        try {
            const cancelledJob = await cancelEditionImageRender(releaseId, edition.id, token);
            setData(prev => prev ? { ...prev, job: cancelledJob } : prev);
            load();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to cancel rendering.');
        } finally {
            setRequesting(false);
        }
    }

    if (edition.cards.length === 0) {
        return (
            <p className="text-[13px] text-(--text-tertiary) py-8 text-center">
                {readOnly ? 'No cards in this edition yet.' : 'Add cards to the player pool to render their images.'}
            </p>
        );
    }

    return (
        <div className="flex flex-col flex-1 min-h-0">
            <div className="flex flex-col gap-2 px-4 py-3 border-b border-(--divider) shrink-0">
                <div className="flex flex-wrap items-center gap-2">
                    {data ? (
                        STATUS_ORDER.filter(status => counts[status] > 0).map(status => (
                            <StatusFilterChip
                                key={status}
                                status={status}
                                count={counts[status]}
                                isActive={statusFilter === status}
                                onClick={() => setStatusFilter(prev => prev === status ? null : status)}
                            />
                        ))
                    ) : (
                        <div className="h-8 w-64 rounded-lg bg-(--background-quaternary) animate-pulse" />
                    )}

                    {!readOnly && data && (
                        <div className="flex items-center gap-2 ml-auto">
                            {jobActive ? (
                                <button
                                    type="button"
                                    onClick={handleCancel}
                                    disabled={requesting}
                                    className="flex items-center gap-1.5 min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-bold border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors disabled:opacity-50 cursor-pointer"
                                >
                                    <FaXmark className="text-[12px]" /> Cancel
                                </button>
                            ) : needsRenderCount > 0 ? (
                                <button
                                    type="button"
                                    onClick={() => handleRender()}
                                    disabled={requesting || !token}
                                    className="flex items-center gap-1.5 min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-bold bg-(--secondary) text-(--background-primary) disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                                >
                                    {requesting ? <FaSpinner className="animate-spin text-[12px]" /> : <FaWandMagicSparkles className="text-[12px]" />}
                                    Render {needsRenderCount} Card{needsRenderCount === 1 ? '' : 's'}
                                </button>
                            ) : (
                                <span className="flex items-center gap-1.5 text-[12px] font-semibold text-(--text-secondary)">
                                    <FaCheck className="text-green-500" /> All images up to date
                                </span>
                            )}
                        </div>
                    )}
                </div>

                {job && <RenderJobStatus job={job} />}

                {error && (
                    <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                        {error}
                    </div>
                )}
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto p-4">
                {!data ? (
                    <div className={TILE_GRID_CLASS}>
                        {Array.from({ length: Math.min(edition.cards.length, MAX_SKELETON_TILES) }, (_, i) => (
                            <ReleaseImageTileSkeleton key={i} />
                        ))}
                    </div>
                ) : visibleImages.length === 0 ? (
                    <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No cards with this status.</p>
                ) : (
                    <div className={TILE_GRID_CLASS}>
                        {visibleImages.map(image => (
                            <ReleaseImageTile
                                // Keyed by path so a re-rendered image starts from its skeleton again
                                key={`${image.source_card_id}:${image.thumbnail_path}`}
                                image={image}
                                snapshot={snapshotsById.get(image.source_card_id)}
                                isQueued={jobActive && image.status !== 'rendered'}
                                onClick={() => setDetailImage(image)}
                            />
                        ))}
                    </div>
                )}
            </div>

            {detail && (
                <ReleaseImageDetailModal
                    image={detail}
                    snapshot={snapshotsById.get(detail.source_card_id)}
                    canRender={!readOnly && !!token && !jobActive && detail.status !== 'rendered'}
                    isRendering={jobActive && detail.status !== 'rendered'}
                    onRender={() => handleRender([detail.source_card_id])}
                    onClose={() => setDetailImage(null)}
                />
            )}
        </div>
    );
}

// =============================================================================
// MARK: - SUBCOMPONENTS
// =============================================================================

function StatusFilterChip({ status, count, isActive, onClick }: { status: ReleaseCardImageStatus; count: number; isActive: boolean; onClick: () => void }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`flex items-center gap-1.5 min-h-8 px-2.5 py-1 rounded-lg text-[12px] font-bold border transition-colors cursor-pointer
                ${isActive ? 'border-(--secondary) text-(--text-primary)' : 'border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary)'}`}
        >
            <span className={`w-2 h-2 rounded-full ${STATUS_META[status].badgeClass}`} />
            {STATUS_META[status].label}
            <span className="text-[10px] font-normal text-(--text-tertiary) bg-(--background-secondary) py-0.5 px-1 rounded-md">{count}</span>
        </button>
    );
}

function RenderJobStatus({ job }: { job: NonNullable<EditionImagesData['job']> }) {
    const processed = job.completed + job.failed;
    if (isImageJobActive(job)) {
        const percent = job.total > 0 ? Math.round((processed / job.total) * 100) : 0;
        return (
            <div className="flex flex-col gap-1">
                <div className="flex items-center gap-1.5 text-[12px] font-semibold text-(--text-secondary)">
                    <FaSpinner className="animate-spin text-[11px]" />
                    {job.total > 0 ? `Rendering ${processed} of ${job.total}` : 'Starting render…'}
                    {job.failed > 0 && <span className="text-red-400">· {job.failed} failed</span>}
                </div>
                <div className="h-1.5 rounded-full bg-(--background-quaternary) overflow-hidden">
                    <div className="h-full bg-(--secondary) transition-[width] duration-500" style={{ width: `${percent}%` }} />
                </div>
            </div>
        );
    }
    if (job.status === 'failed') {
        return (
            <div className="flex items-center gap-1.5 text-[12px] text-red-400">
                <FaTriangleExclamation className="shrink-0" /> Rendering stopped: {job.error ?? 'unknown error'}
            </div>
        );
    }
    if (job.status === 'cancelled') {
        return <div className="text-[12px] text-(--text-tertiary)">Last render cancelled after {processed} of {job.total} cards.</div>;
    }
    if (job.failed > 0) {
        return (
            <div className="flex items-center gap-1.5 text-[12px] text-amber-500">
                <FaTriangleExclamation className="shrink-0" /> Last render finished with {job.failed} failed card{job.failed === 1 ? '' : 's'}.
            </div>
        );
    }
    return null;
}

function StatusBadge({ status }: { status: ReleaseCardImageStatus }) {
    return (
        <span className={`text-[9px] font-black uppercase rounded px-1.5 py-0.5 leading-none ${STATUS_META[status].badgeClass}`}>
            {STATUS_META[status].label}
        </span>
    );
}

/** Card image that shows a skeleton of the same shape until it loads. */
function CardImageWithSkeleton({ src, alt, dimmed = false, className = '' }: { src: string; alt: string; dimmed?: boolean; className?: string }) {
    const [loaded, setLoaded] = useState(false);
    return (
        <>
            {!loaded && <div className="absolute inset-0 bg-(--background-quaternary) animate-pulse" />}
            <img
                src={src}
                alt={alt}
                loading="lazy"
                onLoad={() => setLoaded(true)}
                className={`${className} transition-opacity ${loaded ? (dimmed ? 'opacity-50' : 'opacity-100') : 'opacity-0'}`}
            />
        </>
    );
}

function ReleaseImageTileSkeleton() {
    return (
        <div className="flex flex-col gap-1.5 animate-pulse">
            <div className="aspect-[5/7] rounded-lg bg-(--background-quaternary)" />
            <div className="h-3 w-3/4 rounded bg-(--background-quaternary)" />
        </div>
    );
}

type ReleaseImageTileProps = {
    image: ReleaseCardImage;
    snapshot?: CardDatabaseRecord;
    /** Will be rendered by the running job. */
    isQueued: boolean;
    onClick: () => void;
};

function ReleaseImageTile({ image, snapshot, isQueued, onClick }: ReleaseImageTileProps) {
    const thumbnailSrc = image.thumbnail_path ? cardImagePublicUrl(image.thumbnail_path) : null;
    return (
        <button type="button" onClick={onClick} className="group flex flex-col gap-1.5 text-left min-w-0 cursor-pointer">
            <div className="relative aspect-[5/7] rounded-lg overflow-hidden border border-(--divider) bg-(--background-secondary) group-hover:border-(--text-tertiary) transition-colors">
                {thumbnailSrc ? (
                    <CardImageWithSkeleton
                        src={thumbnailSrc}
                        alt={snapshot?.name ?? image.source_card_id}
                        dimmed={image.status === 'stale'}
                        className="w-full h-full object-contain"
                    />
                ) : (
                    <div className={`absolute inset-0 flex items-center justify-center text-(--text-tertiary) ${isQueued ? 'bg-(--background-quaternary) animate-pulse' : ''}`}>
                        <FaImage className="text-2xl opacity-40" />
                    </div>
                )}
                {image.status !== 'rendered' && (
                    <div className="absolute top-1.5 left-1.5"><StatusBadge status={image.status} /></div>
                )}
                {isQueued && thumbnailSrc && (
                    <div className="absolute bottom-1.5 right-1.5 flex items-center justify-center w-5 h-5 rounded-full bg-(--background-primary)/80">
                        <FaSpinner className="animate-spin text-[10px] text-(--text-secondary)" />
                    </div>
                )}
            </div>
            <div className="flex items-baseline gap-1.5 min-w-0 text-[12px]">
                {image.set_number && <span className="font-mono text-(--text-tertiary) shrink-0">{image.set_number}</span>}
                <span className="font-semibold text-(--text-primary) truncate">{snapshot?.name ?? image.source_card_id}</span>
            </div>
        </button>
    );
}

type ReleaseImageDetailModalProps = {
    image: ReleaseCardImage;
    snapshot?: CardDatabaseRecord;
    canRender: boolean;
    isRendering: boolean;
    onRender: () => void;
    onClose: () => void;
};

function ReleaseImageDetailModal({ image, snapshot, canRender, isRendering, onRender, onClose }: ReleaseImageDetailModalProps) {
    const fullSrc = image.storage_path ? cardImagePublicUrl(image.storage_path) : null;
    const title = [image.set_number, snapshot?.name ?? image.source_card_id].filter(Boolean).join(' · ');
    return (
        <Modal
            title={title}
            subtitle={[snapshot?.year, snapshot?.team, snapshot?.showdown_set].filter(Boolean).join(' · ')}
            size="md"
            onClose={onClose}
            footer={
                <div className="flex items-center justify-end gap-2">
                    {fullSrc && (
                        <a
                            href={fullSrc}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-center gap-1.5 min-h-9 px-3.5 py-2 mr-auto rounded-lg text-[13px] font-semibold text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer"
                        >
                            <FaArrowUpRightFromSquare className="text-[11px]" /> Open Full Size
                        </a>
                    )}
                    {canRender && (
                        <button
                            type="button"
                            onClick={onRender}
                            className="flex items-center gap-1.5 min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-bold bg-(--secondary) text-(--background-primary) cursor-pointer"
                        >
                            <FaWandMagicSparkles className="text-[12px]" /> Render This Card
                        </button>
                    )}
                </div>
            }
        >
            <div className="flex flex-col items-center gap-3 p-4">
                {/* The card's stats as stored in the pool, to check against what was rendered */}
                {snapshot && <CardItemFromCardDatabaseRecord card={snapshot} className="w-full max-w-sm" />}
                <div className="flex items-center gap-2">
                    <StatusBadge status={image.status} />
                    {isRendering && (
                        <span className="flex items-center gap-1 text-[11px] text-(--text-tertiary)">
                            <FaSpinner className="animate-spin text-[10px]" /> Rendering…
                        </span>
                    )}
                </div>
                {image.status === 'stale' && (
                    <p className="text-[12px] text-(--text-secondary) text-center">
                        This card's style, set number, or stats changed since it was rendered. Showing the previous image.
                    </p>
                )}
                {image.status === 'failed' && image.error && (
                    <p className="text-[12px] text-red-400 text-center wrap-anywhere">{image.error}</p>
                )}
                {fullSrc ? (
                    <div className="relative w-full max-w-sm aspect-[5/7] rounded-xl overflow-hidden">
                        <CardImageWithSkeleton key={fullSrc} src={fullSrc} alt={title} className="w-full h-full object-contain" />
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center gap-2 w-full max-w-sm aspect-[5/7] rounded-xl border border-dashed border-(--divider) text-(--text-tertiary)">
                        <FaImage className="text-3xl opacity-40" />
                        <span className="text-[12px]">Not rendered yet</span>
                    </div>
                )}
            </div>
        </Modal>
    );
}
