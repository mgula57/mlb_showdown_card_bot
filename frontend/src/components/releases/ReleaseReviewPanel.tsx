/**
 * @fileoverview Step 3 of the Release Builder: the release-wide checklist an owner sees before
 * publishing (from `GET /releases/<id>/review`), the release tile as others will see it, and the
 * publish / unpublish controls. Publishing is release-wide, so this is one panel for every edition.
 */

import { useEffect, useRef, useState } from 'react';
import { FaCircleCheck, FaCircleInfo, FaCircleXmark, FaGlobe, FaLink, FaSpinner, FaTriangleExclamation } from 'react-icons/fa6';
import type { Release, ReleaseReviewItem, ReleaseReviewLevel } from '../../api/releases';
import { setReleasePublished, updateRelease } from '../../api/releases';
import type { ReleaseReviewState } from './useReleaseReview';
import { ReleaseItem, ReleaseItemSkeleton } from './ReleaseItem';
import { Heading } from '../shared/Heading';
import { Plate } from '../shared/Plate';
import { StatTile } from '../shared/StatTile';
import { InlineError } from '../shared/InlineError';
import { buttonClass } from '../shared/buttonStyles';
import { CAPS_LABEL_CLASS, FIELD_LABEL_CLASS, fieldClass } from '../shared/fieldStyles';

const LEVEL_ORDER: ReleaseReviewLevel[] = ['blocker', 'check', 'polish'];
const LEVEL_LABELS: Record<ReleaseReviewLevel, string> = { blocker: 'Must fix', check: 'Check', polish: 'Polish' };
const FIX_LABELS: Record<NonNullable<ReleaseReviewItem['fix']>['step'], string> = {
    pool: 'Open pool',
    images: 'Open images',
    style: 'Card style',
    details: 'Edit',
};
const PANEL_CLASS = 'rounded-card border border-(--divider) bg-(--background-secondary) min-w-0';

type ReleaseReviewPanelProps = {
    release: Release;
    review: ReleaseReviewState;
    /** Editions showing an unapplied Algorithm run, which only the browser knows about. */
    unsavedPreviewEditionIds: string[];
    token: string;
    onFix: (item: ReleaseReviewItem) => void;
    onReleaseUpdated: (release: Release) => void;
    onViewAsVisitor: () => void;
};

export function ReleaseReviewPanel({ release, review, unsavedPreviewEditionIds, token, onFix, onReleaseUpdated, onViewAsVisitor }: ReleaseReviewPanelProps) {
    const descriptionRef = useRef<HTMLTextAreaElement>(null);
    const items = [
        ...(review.data?.items ?? []),
        ...unsavedPreviewEditionIds.map(unsavedPreviewItem),
    ];
    const openItems = items.filter(item => !item.passed);
    const blockerCount = openItems.filter(item => item.level === 'blocker').length;
    const checkCount = openItems.filter(item => item.level === 'check').length;
    const sections = [
        ...release.editions.map(edition => ({
            key: edition.id,
            title: edition.name,
            cardCount: edition.card_count as number | null,
            items: items.filter(item => item.edition_id === edition.id),
        })),
        { key: 'release', title: 'Release', cardCount: null, items: items.filter(item => item.edition_id === null) },
    ].filter(section => section.items.length > 0);

    function handleFix(item: ReleaseReviewItem) {
        if (item.fix?.step === 'details') {
            descriptionRef.current?.focus();
            return;
        }
        onFix(item);
    }

    return (
        <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="max-w-5xl mx-auto p-4 grid gap-4 md:grid-cols-[minmax(0,1fr)_260px] items-start">
                <div className={PANEL_CLASS}>
                    <div className="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-(--divider)">
                        <Heading level="panel" as="h2">Before you publish</Heading>
                        {review.data && blockerCount > 0 && <Plate variant="red" size="sm">{blockerCount} must fix</Plate>}
                        {review.data && checkCount > 0 && <Plate size="sm">{checkCount} to check</Plate>}
                        {review.data && openItems.length === 0 && <Plate variant="success" size="sm">All clear</Plate>}
                        {review.loading && review.data && <FaSpinner className="animate-spin text-[11px] text-(--text-tertiary)" />}
                        <button type="button" onClick={review.refresh} disabled={review.loading} className={buttonClass('ghost', 'sm', 'ml-auto')}>
                            Recheck
                        </button>
                    </div>
                    {review.error && <InlineError size="md" className="m-4">{review.error}</InlineError>}
                    {!review.data ? (
                        review.loading && <ReviewChecklistSkeleton />
                    ) : (
                        sections.map(section => (
                            <ReviewSection
                                key={section.key}
                                title={section.title}
                                cardCount={section.cardCount}
                                items={section.items}
                                onFix={handleFix}
                            />
                        ))
                    )}
                </div>

                <div className="flex flex-col gap-4 min-w-0">
                    <div className={`${PANEL_CLASS} flex flex-col gap-3 p-4`}>
                        <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>How others see it</span>
                        {/* The tile fills its cell on phones (for the 2-column list grid), so pin it to its desktop width here */}
                        <div className="w-52 max-w-full mx-auto">
                            {review.data?.tile ? <ReleaseItem release={review.data.tile} /> : <ReleaseItemSkeleton />}
                        </div>
                        <div className="flex gap-2">
                            <StatTile label="Cards" value={release.editions.reduce((sum, e) => sum + e.card_count, 0)} />
                            <StatTile label={release.editions.length === 1 ? 'Edition' : 'Editions'} value={release.editions.length} />
                        </div>
                        <DescriptionField release={release} token={token} inputRef={descriptionRef} onSaved={onReleaseUpdated} onRechecked={review.refresh} />
                    </div>
                    <PublishControls
                        release={release}
                        token={token}
                        ready={!!review.data && !review.loading}
                        blockerCount={blockerCount}
                        checkCount={checkCount}
                        onReleaseUpdated={onReleaseUpdated}
                        onBlocked={review.refresh}
                        onViewAsVisitor={onViewAsVisitor}
                    />
                </div>
            </div>
        </div>
    );
}

/** The one check only the browser can make: an Algorithm run still on screen that was never applied. */
function unsavedPreviewItem(editionId: string): ReleaseReviewItem {
    return {
        id: `${editionId}:unsaved_preview`,
        level: 'check',
        edition_id: editionId,
        title: 'Algorithm run not applied',
        detail: 'The pool is showing an unsaved preview. Apply it or discard it, or it won\'t be published.',
        passed: false,
        fix: { step: 'pool', edition_id: editionId, image_status: null },
    };
}

function ReviewSection({ title, cardCount, items, onFix }: { title: string; cardCount: number | null; items: ReleaseReviewItem[]; onFix: (item: ReleaseReviewItem) => void }) {
    const isClear = items.every(item => item.passed);
    return (
        <section className="border-b border-(--divider) last:border-b-0">
            <div className="flex items-center gap-2 px-4 py-2 bg-(--background-tertiary)">
                <span className="text-[13px] font-bold">{title}</span>
                {cardCount !== null && <Plate size="sm">{cardCount} cards</Plate>}
                {isClear && <Plate variant="success" size="sm">All clear</Plate>}
            </div>
            {LEVEL_ORDER.map(level => {
                // Problems first, then the checks that passed
                const levelItems = items
                    .filter(item => item.level === level)
                    .sort((a, b) => Number(a.passed) - Number(b.passed));
                if (levelItems.length === 0) return null;
                return (
                    <div key={level} className="pb-1">
                        <div className={`${CAPS_LABEL_CLASS} text-(--text-tertiary) px-4 pt-2.5 pb-1`}>{LEVEL_LABELS[level]}</div>
                        <ul>
                            {levelItems.map(item => <ReviewRow key={item.id} item={item} onFix={onFix} />)}
                        </ul>
                    </div>
                );
            })}
        </section>
    );
}

function ReviewRow({ item, onFix }: { item: ReleaseReviewItem; onFix: (item: ReleaseReviewItem) => void }) {
    return (
        <li className="flex items-start gap-2.5 px-4 py-2 border-t border-(--divider) first:border-t-0">
            <span className="mt-0.5 shrink-0 text-[13px]"><ReviewIcon item={item} /></span>
            <div className="flex-1 min-w-0">
                <div className={`text-[13px] ${item.passed ? 'text-(--text-tertiary)' : 'font-semibold text-(--text-primary)'}`}>{item.title}</div>
                {item.detail && <div className="text-[12px] text-(--text-tertiary)">{item.detail}</div>}
            </div>
            {item.fix && !item.passed && (
                <button type="button" onClick={() => onFix(item)} className={buttonClass('ghost', 'sm', 'text-(--showdown-blue)')}>
                    {FIX_LABELS[item.fix.step]}
                </button>
            )}
        </li>
    );
}

function ReviewIcon({ item }: { item: ReleaseReviewItem }) {
    if (item.passed) return <FaCircleCheck className="text-(--green)" aria-label="Passed" />;
    if (item.level === 'blocker') return <FaCircleXmark className="text-(--red)" aria-label="Must fix" />;
    if (item.level === 'check') return <FaTriangleExclamation className="text-(--warning)" aria-label="Check" />;
    return <FaCircleInfo className="text-(--text-tertiary)" aria-label="Polish" />;
}

function ReviewChecklistSkeleton() {
    return (
        <div aria-label="Loading checklist" className="animate-pulse">
            {[0, 1].map(section => (
                <div key={section} className="border-b border-(--divider) last:border-b-0">
                    <div className="h-9 bg-(--background-tertiary)" />
                    {[0, 1, 2].map(row => (
                        <div key={row} className="flex items-center gap-2.5 px-4 py-3 border-t border-(--divider) first:border-t-0">
                            <div className="w-3.5 h-3.5 rounded-plate bg-(--background-tertiary)" />
                            <div className="h-3 w-2/3 rounded-plate bg-(--background-tertiary)" />
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
}

/** The release description, saved straight to the release (it isn't part of an edition). */
function DescriptionField({ release, token, inputRef, onSaved, onRechecked }: {
    release: Release;
    token: string;
    inputRef: React.RefObject<HTMLTextAreaElement | null>;
    onSaved: (release: Release) => void;
    /** Re-runs the checklist so the description item clears. */
    onRechecked: () => void;
}) {
    const [value, setValue] = useState(release.description ?? '');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => { setValue(release.description ?? ''); }, [release.description]);
    const isDirty = value.trim() !== (release.description ?? '').trim();

    async function handleSave() {
        setSaving(true);
        setError(null);
        try {
            const updated = await updateRelease(release.id, { description: value.trim() || null }, token);
            onSaved({ ...release, description: updated.description });
            onRechecked();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save the description.');
        } finally {
            setSaving(false);
        }
    }

    return (
        <div className="flex flex-col gap-1.5">
            <label htmlFor={`release-description-${release.id}`} className={FIELD_LABEL_CLASS}>Description</label>
            <textarea
                id={`release-description-${release.id}`}
                ref={inputRef}
                value={value}
                onChange={e => setValue(e.target.value)}
                rows={2}
                placeholder="A line about the set, shown under its name."
                className={fieldClass('md', 'h-auto py-2 resize-y')}
            />
            {isDirty && (
                <button type="button" onClick={handleSave} disabled={saving} className={buttonClass('secondary', 'sm', 'self-end')}>
                    {saving && <FaSpinner className="animate-spin text-[10px]" />} Save description
                </button>
            )}
            {error && <InlineError size="sm">{error}</InlineError>}
        </div>
    );
}

type PublishControlsProps = {
    release: Release;
    token: string;
    /** False until the checklist has loaded, so nothing publishes unreviewed. */
    ready: boolean;
    blockerCount: number;
    checkCount: number;
    onReleaseUpdated: (release: Release) => void;
    /** The server refused because a blocker appeared since the checklist loaded. */
    onBlocked: () => void;
    onViewAsVisitor: () => void;
};

function PublishControls({ release, token, ready, blockerCount, checkCount, onReleaseUpdated, onBlocked, onViewAsVisitor }: PublishControlsProps) {
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [confirmingUnpublish, setConfirmingUnpublish] = useState(false);
    const [justPublished, setJustPublished] = useState(false);
    const [copied, setCopied] = useState(false);

    const isPublished = release.editions.some(e => e.is_published);
    const draftCount = release.editions.filter(e => !e.is_published).length;

    async function handleSetPublished(published: boolean) {
        setBusy(true);
        setError(null);
        try {
            onReleaseUpdated(await setReleasePublished(release.id, published, token));
            setJustPublished(published);
            setConfirmingUnpublish(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : `Failed to ${published ? 'publish' : 'unpublish'} the release.`);
            if (published) onBlocked();
        } finally {
            setBusy(false);
        }
    }

    async function handleCopyLink() {
        const url = `${window.location.origin}/release-builder/${release.id}`;
        try {
            await navigator.clipboard.writeText(url);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            setError(`Couldn't copy. The link is ${url}`);
        }
    }

    const publishNote = !ready
        ? 'Checking your release…'
        : blockerCount > 0
            ? `Fix ${blockerCount} item${blockerCount === 1 ? '' : 's'} to publish.`
            : checkCount > 0
                ? `You can publish with ${checkCount} check${checkCount === 1 ? '' : 's'} still open.`
                : 'Everything checks out.';

    return (
        <div className={`${PANEL_CLASS} flex flex-col gap-3 p-4`}>
            {isPublished && (
                <div className="flex flex-col gap-1">
                    {justPublished && <Heading level="section" as="h2">{release.name} is live</Heading>}
                    <div className="flex items-center gap-2 flex-wrap">
                        <Plate variant="success" size="sm">Published</Plate>
                        {release.published_at && (
                            <span className="text-[12px] text-(--text-tertiary)">
                                v{release.published_version} · since {new Date(release.published_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                            </span>
                        )}
                    </div>
                    <span className="text-[12px] text-(--text-secondary)">Anyone can browse it and use its cards.</span>
                </div>
            )}

            {draftCount > 0 && (
                <>
                    <button
                        type="button"
                        onClick={() => handleSetPublished(true)}
                        disabled={!ready || busy || blockerCount > 0}
                        className={buttonClass('feature', 'md', 'w-full')}
                    >
                        {busy ? <FaSpinner className="animate-spin" /> : <FaGlobe />}
                        {isPublished ? `Publish ${draftCount} new edition${draftCount === 1 ? '' : 's'}` : 'Publish release'}
                    </button>
                    <span className="text-[12px] text-(--text-tertiary) text-center">{publishNote}</span>
                </>
            )}

            {error && <InlineError size="sm">{error}</InlineError>}

            {isPublished && (
                <div className="flex flex-col gap-2 pt-1 border-t border-(--divider)">
                    <div className="flex gap-2 pt-2">
                        <button type="button" onClick={handleCopyLink} className={buttonClass('secondary', 'sm', 'flex-1')}>
                            <FaLink className="text-[10px]" /> {copied ? 'Copied' : 'Copy link'}
                        </button>
                        <button type="button" onClick={onViewAsVisitor} className={buttonClass('secondary', 'sm', 'flex-1')}>
                            View as visitor
                        </button>
                    </div>
                    {confirmingUnpublish ? (
                        <div className="flex flex-col gap-2 p-2.5 rounded-control border border-(--divider)">
                            <span className="text-[12px] text-(--text-secondary)">Hide this release from everyone but you? Teams already using its cards keep them.</span>
                            <div className="flex gap-2">
                                <button type="button" onClick={() => handleSetPublished(false)} disabled={busy} className={buttonClass('danger', 'sm', 'flex-1')}>
                                    {busy && <FaSpinner className="animate-spin text-[10px]" />} Unpublish
                                </button>
                                <button type="button" onClick={() => setConfirmingUnpublish(false)} className={buttonClass('ghost', 'sm', 'flex-1')}>
                                    Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        <button type="button" onClick={() => setConfirmingUnpublish(true)} className={buttonClass('ghost', 'sm', 'self-start text-(--text-tertiary)')}>
                            Unpublish…
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
