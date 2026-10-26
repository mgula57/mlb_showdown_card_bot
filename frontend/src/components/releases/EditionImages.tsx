import { useState, useEffect, useCallback, useMemo } from 'react';
import type { ReleaseEdition, ReleaseCardImage, ReleaseCardImageStatus, EditionImages as EditionImagesData } from '../../api/releases';
import { fetchEditionImages, renderEditionImages, cancelEditionImageRender, isImageJobActive } from '../../api/releases';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { cardImagePublicUrl } from '../../api/supabase';
import { Modal } from '../shared/Modal';
import { CardItemFromCardDatabaseRecord } from '../cards/CardItem';
import { ReleaseCardPreviewRankPicker } from './ReleaseCardPreviewRank';
import { buildZipEntries, editionZipFileName, useEditionZipDownload, type ZipDownloadState } from './editionZipDownload';
import { FaArrowUpRightFromSquare, FaCheck, FaDownload, FaImage, FaSpinner, FaTriangleExclamation, FaWandMagicSparkles, FaXmark } from 'react-icons/fa6';

import { InlineError } from '../shared/InlineError';
import { buttonClass } from '../shared/buttonStyles';
import { Plate } from '../shared/Plate';
import { EmptyState } from '../shared/EmptyState';
/** How often to refresh statuses while a render job runs (each card takes a few seconds). */
const POLL_INTERVAL_MS = 2500;
/** Skeleton tiles shown while statuses load. */
const MAX_SKELETON_TILES = 24;
const TILE_GRID_CLASS = 'grid grid-cols-[repeat(auto-fill,minmax(140px,1fr))] gap-4';

const STATUS_META: Record<ReleaseCardImageStatus, { label: string; badgeClass: string }> = {
    rendered: { label: 'Rendered', badgeClass: 'bg-(--green) text-white' },
    stale: { label: 'Out of date', badgeClass: 'bg-(--gold) text-(--field-ink)' },
    failed: { label: 'Failed', badgeClass: 'bg-(--red) text-white' },
    missing: { label: 'Not rendered', badgeClass: 'bg-(--background-quaternary) text-(--text-secondary)' },
};
const STATUS_ORDER: ReleaseCardImageStatus[] = ['rendered', 'stale', 'missing', 'failed'];

type EditionImagesProps = {
    releaseId: string;
    /** Used to name the ZIP download. */
    releaseName: string;
    edition: ReleaseEdition;
    readOnly: boolean;
    token?: string;
    /** Release-tile slot (1-3) by source card id, for cards that have one. */
    previewRanks: Map<string, number>;
    onPreviewRankChange: (sourceCardId: string, rank: number | null) => void;
};

/** Step 2 of the Edition Builder: renders every card in the edition (with its edition style and set
 * number) to Supabase in a background job, and shows each card's image as it lands. */
export function EditionImages({ releaseId, releaseName, edition, readOnly, token, previewRanks, onPreviewRankChange }: EditionImagesProps) {
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
    const zipDownload = useEditionZipDownload();
    const zipEntries = useMemo(() => buildZipEntries(images, snapshotsById), [images, snapshotsById]);
    const isZipping = zipDownload.state.status === 'downloading';
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
            <EmptyState size="panel" title="No cards yet.">
                {readOnly ? 'This edition has no cards yet.' : 'Add cards to the player pool to render their images.'}
            </EmptyState>
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
                        <div className="h-8 w-64 rounded-control bg-(--background-quaternary) animate-pulse" />
                    )}

                    {data && (
                        <div className="flex items-center gap-2 ml-auto">
                            {zipEntries.length > 0 && !isZipping && (
                                <button
                                    type="button"
                                    onClick={() => zipDownload.start(zipEntries, editionZipFileName(releaseName, edition.name))}
                                    disabled={jobActive}
                                    title={jobActive ? 'Wait for rendering to finish' : 'Download every current full-size image as a ZIP'}
                                    className={buttonClass('secondary', 'sm')}
                                >
                                    <FaDownload className="text-[12px]" /> Download ZIP
                                    <Plate size="sm">{zipEntries.length}</Plate>
                                </button>
                            )}
                            {readOnly ? null : jobActive ? (
                                <button
                                    type="button"
                                    onClick={handleCancel}
                                    disabled={requesting}
                                    className={buttonClass('secondary', 'sm')}
                                >
                                    <FaXmark className="text-[12px]" /> Cancel
                                </button>
                            ) : needsRenderCount > 0 ? (
                                <button
                                    type="button"
                                    onClick={() => handleRender()}
                                    disabled={requesting || !token}
                                    className={buttonClass('primary', 'sm', 'min-h-9')}
                                >
                                    {requesting ? <FaSpinner className="animate-spin text-[12px]" /> : <FaWandMagicSparkles className="text-[12px]" />}
                                    Render {needsRenderCount} Card{needsRenderCount === 1 ? '' : 's'}
                                </button>
                            ) : (
                                <span className="flex items-center gap-1.5 text-[12px] font-semibold text-(--text-secondary)">
                                    <FaCheck className="text-(--green)" /> All images up to date
                                </span>
                            )}
                        </div>
                    )}
                </div>

                {job && <RenderJobStatus job={job} />}

                {zipDownload.state.status !== 'idle' && (
                    <ZipDownloadStatus state={zipDownload.state} onCancel={zipDownload.cancel} onDismiss={zipDownload.reset} />
                )}

                {error && (
                    <InlineError size="md">
                        {error}
                    </InlineError>
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
                    <EmptyState size="inline">No cards with this status.</EmptyState>
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
                    previewRank={previewRanks.get(detail.source_card_id) ?? null}
                    canEditPreviewRank={!readOnly && !!token}
                    onPreviewRankChange={rank => onPreviewRankChange(detail.source_card_id, rank)}
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
            className={`flex items-center gap-1.5 min-h-8 px-2.5 py-1 rounded-control text-[12px] font-bold border transition-colors cursor-pointer
                ${isActive ? 'border-(--secondary) text-(--text-primary)' : 'border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary)'}`}
        >
            <span className={`w-2 h-2 rounded-full ${STATUS_META[status].badgeClass}`} />
            {STATUS_META[status].label}
            <span className="text-[10px] font-normal text-(--text-tertiary) bg-(--background-secondary) py-0.5 px-1 rounded-control">{count}</span>
        </button>
    );
}

/** "~4 min left" style label for a rough ETA. */
function formatEta(seconds: number): string {
    const minutes = Math.round(seconds / 60);
    if (minutes < 1) return '<1 min left';
    if (minutes < 60) return `~${minutes} min left`;
    const hours = Math.floor(minutes / 60);
    const rest = minutes % 60;
    return `~${hours} hr${rest > 0 ? ` ${rest} min` : ''} left`;
}

function RenderJobStatus({ job }: { job: NonNullable<EditionImagesData['job']> }) {
    const processed = job.completed + job.failed;
    const isActive = isImageJobActive(job);

    // Pace is measured from the first progress this view saw to the latest, using the job's server
    // timestamps (bumped on each card) so poll timing doesn't skew it.
    const [paceStart, setPaceStart] = useState<{ jobId: string; processed: number; at: number } | null>(null);
    if (isActive && job.total > 0 && paceStart?.jobId !== job.id) {
        setPaceStart({ jobId: job.id, processed, at: Date.parse(job.updated_at) });
    }
    const pacedCards = paceStart?.jobId === job.id ? processed - paceStart.processed : 0;
    const etaSeconds = pacedCards > 0 && paceStart
        ? ((Date.parse(job.updated_at) - paceStart.at) / 1000 / pacedCards) * (job.total - processed)
        : null;

    if (isActive) {
        const percent = job.total > 0 ? Math.round((processed / job.total) * 100) : 0;
        return (
            <div className="flex flex-col gap-1">
                <div className="flex items-center gap-1.5 text-[12px] font-semibold text-(--text-secondary)">
                    <FaSpinner className="animate-spin text-[11px]" />
                    {job.total > 0 ? `Rendering ${processed} of ${job.total}` : 'Starting render…'}
                    {job.failed > 0 && <span className="text-(--red)">· {job.failed} failed</span>}
                    {etaSeconds !== null && processed < job.total && (
                        <span className="font-normal text-(--text-tertiary)">· {formatEta(etaSeconds)}</span>
                    )}
                </div>
                <ProgressBar percent={percent} />
            </div>
        );
    }
    if (job.status === 'failed') {
        return (
            <div className="flex items-center gap-1.5 text-[12px] text-(--red)">
                <FaTriangleExclamation className="shrink-0" /> Rendering stopped: {job.error ?? 'unknown error'}
            </div>
        );
    }
    if (job.status === 'cancelled') {
        return <div className="text-[12px] text-(--text-tertiary)">Last render cancelled after {processed} of {job.total} cards.</div>;
    }
    if (job.failed > 0) {
        return (
            <div className="flex items-center gap-1.5 text-[12px] text-(--gold)">
                <FaTriangleExclamation className="shrink-0" /> Last render finished with {job.failed} failed card{job.failed === 1 ? '' : 's'}.
            </div>
        );
    }
    return null;
}

function ProgressBar({ percent }: { percent: number }) {
    return (
        <div className="h-1.5 rounded-full bg-(--background-quaternary) overflow-hidden">
            <div className="h-full bg-(--secondary) transition-[width] duration-500" style={{ width: `${percent}%` }} />
        </div>
    );
}

function ZipDownloadStatus({ state, onCancel, onDismiss }: { state: ZipDownloadState; onCancel: () => void; onDismiss: () => void }) {
    const failedCount = state.failedNames.length;
    if (state.status === 'downloading') {
        const percent = state.total > 0 ? Math.round((state.completed / state.total) * 100) : 0;
        return (
            <div className="flex flex-col gap-1">
                <div className="flex items-center gap-1.5 text-[12px] font-semibold text-(--text-secondary)">
                    <FaSpinner className="animate-spin text-[11px]" />
                    Zipping {state.completed} of {state.total}
                    {failedCount > 0 && <span className="text-(--red)">· {failedCount} failed</span>}
                    <button
                        type="button"
                        onClick={onCancel}
                        className="ml-auto flex items-center gap-1 text-[12px] font-semibold text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer"
                    >
                        <FaXmark className="text-[11px]" /> Cancel
                    </button>
                </div>
                <ProgressBar percent={percent} />
            </div>
        );
    }

    const message = state.status === 'done'
        ? (failedCount > 0
            ? `ZIP saved without ${failedCount} image${failedCount === 1 ? '' : 's'} that failed to download: ${state.failedNames.join(', ')}`
            : `ZIP saved with ${state.total} image${state.total === 1 ? '' : 's'}.`)
        : state.status === 'cancelled'
            ? 'ZIP download cancelled.'
            : `ZIP download failed: ${state.error ?? 'unknown error'}`;
    const tone = state.status === 'error' || failedCount > 0 ? 'text-(--gold)' : 'text-(--text-secondary)';
    return (
        <div className={`flex items-start gap-1.5 text-[12px] ${tone}`}>
            {state.status === 'done' && failedCount === 0
                ? <FaCheck className="shrink-0 mt-0.5 text-(--green)" />
                : <FaTriangleExclamation className="shrink-0 mt-0.5" />}
            <span className="flex-1 min-w-0 wrap-anywhere">{message}</span>
            <button type="button" onClick={onDismiss} title="Dismiss" className="shrink-0 text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer">
                <FaXmark className="text-[12px]" />
            </button>
        </div>
    );
}

function StatusBadge({ status }: { status: ReleaseCardImageStatus }) {
    return (
        <Plate variant="custom" size="sm" className={STATUS_META[status].badgeClass}>
            {STATUS_META[status].label}
        </Plate>
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
            <div className="aspect-5/7 rounded-card bg-(--background-tertiary)" />
            <div className="h-3 w-3/4 rounded-plate bg-(--background-tertiary)" />
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
            <div className="relative aspect-5/7 rounded-control overflow-hidden border border-(--divider) bg-(--background-secondary) group-hover:border-(--text-tertiary) transition-colors">
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
    previewRank: number | null;
    canEditPreviewRank: boolean;
    onPreviewRankChange: (rank: number | null) => void;
    onClose: () => void;
};

function ReleaseImageDetailModal({ image, snapshot, canRender, isRendering, onRender, previewRank, canEditPreviewRank, onPreviewRankChange, onClose }: ReleaseImageDetailModalProps) {
    const fullSrc = image.storage_path ? cardImagePublicUrl(image.storage_path) : null;
    const title = [image.set_number, snapshot?.name ?? image.source_card_id].filter(Boolean).join(' · ');
    return (
        <Modal
            title={title}
            subtitle={[snapshot?.year, snapshot?.team, snapshot?.showdown_set].filter(Boolean).join(' · ')}
            size="md"
            onClose={onClose}
            footer={
                <div className="flex flex-wrap items-center justify-end gap-x-2 gap-y-3">
                    <div className="mr-auto">
                        <ReleaseCardPreviewRankPicker rank={previewRank} readOnly={!canEditPreviewRank} onChange={onPreviewRankChange} />
                    </div>
                    {fullSrc && (
                        <a
                            href={fullSrc}
                            target="_blank"
                            rel="noreferrer"
                            className={buttonClass('ghost', 'sm')}
                        >
                            <FaArrowUpRightFromSquare className="text-[11px]" /> Open full size
                        </a>
                    )}
                    {canRender && (
                        <button
                            type="button"
                            onClick={onRender}
                            className={buttonClass('primary', 'sm', 'min-h-9')}
                        >
                            <FaWandMagicSparkles className="text-[12px]" /> Render this card
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
                    <p className="text-[12px] text-(--red) text-center wrap-anywhere">{image.error}</p>
                )}
                {fullSrc ? (
                    <div className="relative w-full max-w-sm aspect-5/7 rounded-card overflow-hidden">
                        <CardImageWithSkeleton key={fullSrc} src={fullSrc} alt={title} className="w-full h-full object-contain" />
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center gap-2 w-full max-w-sm aspect-5/7 rounded-card border border-dashed border-(--divider) text-(--text-tertiary)">
                        <FaImage className="text-3xl opacity-40" />
                        <span className="text-[12px]">Not rendered yet</span>
                    </div>
                )}
            </div>
        </Modal>
    );
}
