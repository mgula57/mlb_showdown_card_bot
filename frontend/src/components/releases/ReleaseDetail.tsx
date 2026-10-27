import { useState, useEffect, useCallback, useRef, type ReactNode } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import type { Release, ReleaseEdition, ReleaseEditionSummary, ReleaseReviewItem } from '../../api/releases';
import { fetchEdition, createEdition, updateEdition, editionSummaryOf, releaseDraftRequest } from '../../api/releases';
import { EditionBuilder, EditionBuilderSkeleton, type EditionNavRequest } from './EditionBuilder';
import { ReleaseReviewPanel } from './ReleaseReviewPanel';
import { useReleaseReview } from './useReleaseReview';
import { ReleaseShareSheet } from './ReleaseShareSheet';
import FormInput from '../customs/FormInput';
import { ModeBanner, ModeBannerButton } from '../shared/ModeBanner';
import { FaArrowLeft, FaCheck, FaEye, FaGlobe, FaPen, FaPlus, FaShareNodes, FaSpinner, FaXmark } from 'react-icons/fa6';

import { InlineError } from '../shared/InlineError';
import { Heading } from '../shared/Heading';
import { buttonClass, buttonVariantClass } from '../shared/buttonStyles';
import { Plate } from '../shared/Plate';
import { EmptyState } from '../shared/EmptyState';
type ReleaseDetailProps = {
    release: Release;
    readOnly: boolean;
    /** Slug of the edition in the URL (`/release-builder/:releaseId/:editionSlug`); falls back to the first edition. */
    editionSlug?: string | null;
    onEditionChange: (slug: string) => void;
    onBack: () => void;
    onReleaseUpdated: (release: Release) => void;
    token?: string;
};

/** Owners land in `browse` once a release is published (the view everyone else gets) and in
 *  `edit` while it's still a draft. Browsing a draft is the pre-publish preview. */
type ViewMode = 'browse' | 'edit';

// The tab strip's red active bar, in the body face rather than the display italic because each tab
// carries upright count and Draft plates (same reasoning as radixVerticalTabTriggerClass).
const EDITION_TAB_CLASS =
    'relative flex items-center px-3 py-2.5 text-[13px] font-bold transition-colors border-b-[3px] shrink-0 cursor-pointer ' +
    'data-[state=active]:border-(--showdown-red) data-[state=active]:text-(--text-primary) ' +
    'data-[state=inactive]:border-transparent data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:hover:text-(--text-secondary)';


export function ReleaseDetail({ release, readOnly, editionSlug, onEditionChange, onBack, onReleaseUpdated, token }: ReleaseDetailProps) {
    const isOwner = !readOnly;
    // Other users can only open published editions — the release itself still lists drafts.
    const editions = isOwner ? release.editions : release.editions.filter(e => e.is_published);
    const isPublished = release.editions.some(e => e.is_published);
    const hasDrafts = release.editions.some(e => !e.is_published);
    // Once published, edits go to private working copies until the owner publishes them
    const isStaged = release.published_version > 0;
    const hasUnpublishedWork = isStaged ? release.has_pending_changes : hasDrafts;

    const [mode, setMode] = useState<ViewMode>(() => isPublished ? 'browse' : 'edit');
    const isEditing = isOwner && mode === 'edit';
    /** The edition the builder loads: its working copy while editing a published release. */
    const loadedIdOf = (edition: ReleaseEditionSummary) => isEditing && edition.draft ? edition.draft.id : edition.id;
    /** What the tab shows for an edition: the working copy's name and count while editing it. */
    const shownOf = (edition: ReleaseEditionSummary) => isEditing && edition.draft ? edition.draft : edition;
    // A published edition without a working copy yet can't be edited, so open them first
    const needsDraft = isEditing && isStaged && release.editions.some(e => e.published_at && !e.draft);

    /** Step 3 is release-wide, so it lives here rather than in each edition's builder. */
    const [reviewOpen, setReviewOpen] = useState(false);
    const isReviewing = isEditing && reviewOpen && !!token;
    const review = useReleaseReview(release.id, token, isReviewing);
    const [navRequest, setNavRequest] = useState<{ editionId: string; request: EditionNavRequest } | null>(null);
    const [unsavedPreviews, setUnsavedPreviews] = useState<Record<string, boolean>>({});
    const handleUnsavedPreviewChange = useCallback((editionId: string, hasUnsavedPreview: boolean) => {
        setUnsavedPreviews(prev => prev[editionId] === hasUnsavedPreview ? prev : { ...prev, [editionId]: hasUnsavedPreview });
    }, []);

    const activeEdition = editions.find(e => e.slug === editionSlug) ?? editions[0] ?? null;
    const activeEditionId = activeEdition?.id ?? null;
    const activeLoadedId = activeEdition && !needsDraft ? loadedIdOf(activeEdition) : null;
    const [editionCache, setEditionCache] = useState<Record<string, ReleaseEdition>>({});
    const [error, setError] = useState<string | null>(null);
    /** Set right after a publish, for the confirmation strip. */
    const [publishedVersion, setPublishedVersion] = useState<number | null>(null);
    const [confirmingDiscard, setConfirmingDiscard] = useState(false);
    const [discarding, setDiscarding] = useState(false);
    /** The share sheet, with an eyebrow line when it opens right after a first publish. */
    const [shareSheet, setShareSheet] = useState<{ eyebrow?: string } | null>(null);

    /** Releases from publish/draft endpoints lack the list-only fields, so keep ours for those. */
    function mergeRelease(updated: Release) {
        onReleaseUpdated({ ...release, ...updated });
    }

    const draftRequested = useRef(false);
    useEffect(() => {
        if (!needsDraft || !token || draftRequested.current) return;
        draftRequested.current = true;
        releaseDraftRequest(release.id, 'start', token)
            .then(mergeRelease)
            .catch(err => setError(err instanceof Error ? err.message : 'Failed to start editing.'))
            .finally(() => { draftRequested.current = false; });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [needsDraft, token, release.id]);

    /** Inline name form above the builder — creates a new edition or renames the active one. */
    const [editionForm, setEditionForm] = useState<'create' | 'rename' | null>(null);
    const [editionFormName, setEditionFormName] = useState('');
    const [savingEditionForm, setSavingEditionForm] = useState(false);
    const activeEditionName = activeEdition ? shownOf(activeEdition).name : '';

    useEffect(() => {
        if (!activeLoadedId || editionCache[activeLoadedId]) return;
        setError(null);
        fetchEdition(release.id, activeLoadedId, token)
            .then(edition => setEditionCache(prev => ({ ...prev, [edition.id]: edition })))
            .catch(err => setError(err.message ?? 'Failed to load edition.'));
    }, [activeLoadedId, release.id, token]);

    function changeMode(next: ViewMode) {
        setMode(next);
        if (next === 'browse') setReviewOpen(false);
        if (next === 'edit') setPublishedVersion(null);
        setConfirmingDiscard(false);
        closeEditionForm();
    }

    function openReview() {
        changeMode('edit');
        setReviewOpen(true);
    }

    /** A review fix link: leave the review for the edition and step where the item gets fixed. */
    function handleReviewFix(item: ReleaseReviewItem) {
        const fix = item.fix;
        const edition = release.editions.find(e => fix?.edition_id && loadedIdOf(e) === fix.edition_id);
        if (!fix || fix.step === 'details' || !edition) return;
        setReviewOpen(false);
        onEditionChange(edition.slug);
        setNavRequest({ editionId: edition.id, request: { step: fix.step, imageStatus: fix.image_status } });
    }

    /** Unpublish and description saves from the Review step. */
    function handleReviewReleaseUpdated(updated: Release) {
        const publishedById = new Map(updated.editions.map(e => [e.id, e.is_published]));
        setEditionCache(prev => Object.fromEntries(Object.entries(prev).map(([id, edition]) => [
            id, publishedById.has(id) ? { ...edition, is_published: publishedById.get(id)! } : edition,
        ])));
        mergeRelease(updated);
    }

    /** Publishing replaces the live editions (and drops the working copies), so reload everything. */
    function handlePublished(updated: Release) {
        setEditionCache({});
        mergeRelease(updated);
        changeMode('browse');
        setPublishedVersion(updated.published_version);
        // The first publish is when there's a link to send for the first time
        if (updated.published_version === 1) setShareSheet({ eyebrow: 'Published · v1' });
    }

    async function handleDiscard() {
        if (!token || discarding) return;
        setDiscarding(true);
        setError(null);
        try {
            const updated = await releaseDraftRequest(release.id, 'discard', token);
            setEditionCache({});
            mergeRelease(updated);
            changeMode('browse');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to discard changes.');
        } finally {
            setDiscarding(false);
        }
    }

    function openEditionForm(mode: 'create' | 'rename') {
        setEditionForm(mode);
        setEditionFormName(mode === 'rename' ? activeEditionName : '');
    }

    function closeEditionForm() {
        setEditionForm(null);
        setEditionFormName('');
    }

    async function handleSubmitEditionForm() {
        const name = editionFormName.trim();
        if (!token || !name || savingEditionForm) return;
        if (editionForm === 'rename') {
            if (!activeLoadedId || name === activeEditionName) { closeEditionForm(); return; }
            setSavingEditionForm(true);
            setError(null);
            try {
                handleEditionUpdated(await updateEdition(release.id, activeLoadedId, { name }, token));
                closeEditionForm();
            } catch (err: any) {
                setError(err.message ?? 'Failed to rename edition.');
            } finally {
                setSavingEditionForm(false);
            }
            return;
        }
        setSavingEditionForm(true);
        setError(null);
        try {
            const edition = await createEdition(release.id, { name }, token);
            setEditionCache(prev => ({ ...prev, [edition.id]: edition }));
            onReleaseUpdated({
                ...release,
                has_pending_changes: isStaged || release.has_pending_changes,
                editions: [
                    ...release.editions,
                    editionSummaryOf(edition),
                ].sort((a, b) => a.name.localeCompare(b.name)),
            });
            onEditionChange(edition.slug);
            closeEditionForm();
        } catch (err: any) {
            setError(err.message ?? 'Failed to create edition.');
        } finally {
            setSavingEditionForm(false);
        }
    }

    /** Folds several edition saves into the cache and the release in one pass, so concurrent
     *  saves (e.g. publishing every edition) don't overwrite each other's release update. */
    function applyEditionUpdates(updates: ReleaseEdition[]) {
        if (updates.length === 0) return;
        const byId = new Map(updates.map(u => [u.id, u]));
        setEditionCache(prev => ({ ...prev, ...Object.fromEntries(byId) }));
        onReleaseUpdated({
            ...release,
            // Any save while staged is unpublished work (to a working copy or a new edition)
            has_pending_changes: isStaged || release.has_pending_changes,
            editions: release.editions.map(e => {
                const updated = byId.get(e.id);
                if (updated) {
                    return { ...e, name: updated.name, attributes: updated.attributes, is_published: updated.is_published, card_count: updated.cards.length };
                }
                const updatedDraft = e.draft && byId.get(e.draft.id);
                return updatedDraft && e.draft
                    ? { ...e, draft: { ...e.draft, name: updatedDraft.name, card_count: updatedDraft.cards.length } }
                    : e;
            }).sort((a, b) => shownOf(a).name.localeCompare(shownOf(b).name)),
        });
    }

    function handleEditionUpdated(updated: ReleaseEdition) {
        applyEditionUpdates([updated]);
    }

    return (
        // Height-locked from md up only — on phones the page scrolls naturally so Safari's URL bar can
        // collapse (a dvh-locked shell leaves a black bar at the bottom as the bar animates).
        <div className="flex flex-col md:h-[calc(100dvh-2.5rem)] md:overflow-hidden">
            <Tabs.Root
                value={activeEditionId ?? undefined}
                onValueChange={id => {
                    const edition = editions.find(e => e.id === id);
                    if (edition) onEditionChange(edition.slug);
                }}
                className="flex flex-col flex-1 min-h-0"
            >
                {/* Desktop: one row — back + name, edition tabs, actions. Mobile: the edition tabs wrap onto their own row. */}
                <div className="flex flex-wrap md:flex-nowrap items-stretch gap-x-3 px-4 bg-(--background-secondary) border-b border-(--divider) shrink-0">
                    <button type="button" onClick={onBack} aria-label="Back" className="text-(--text-tertiary) opacity-70 hover:text-(--text-primary) transition-colors shrink-0 cursor-pointer">
                        <FaArrowLeft />
                    </button>
                    <div className="flex flex-col justify-center min-w-0 flex-1 md:flex-none md:max-w-[40%] py-1.5" title={release.description || undefined}>
                        <div className="flex items-center gap-2 min-w-0">
                            <Heading level="section" as="h1" fit>{release.name}</Heading>
                            {release.is_official && <Plate variant="navy" size="sm">Official</Plate>}
                            {isOwner && !isPublished && <Plate variant="outline" size="sm">Draft</Plate>}
                        </div>
                        {release.description && (
                            <div className="text-[11px] text-(--text-secondary) truncate">{release.description}</div>
                        )}
                    </div>
                    <div className="hidden md:block w-px my-2.5 bg-(--divider) shrink-0" />
                    <Tabs.List className="order-last md:order-0 w-full md:w-auto md:flex-1 flex items-stretch gap-x-3 min-w-0 overflow-x-auto scrollbar-hide border-t border-(--divider) md:border-t-0">
                        {editions.map(edition => (
                            <Tabs.Trigger key={edition.id} value={edition.id} className={EDITION_TAB_CLASS}>
                                {shownOf(edition).name}
                                <Plate size="sm" className="ml-1.5">{shownOf(edition).card_count}</Plate>
                                {/* Only worth flagging per edition when the rest of the release is already public */}
                                {isOwner && isPublished && !edition.is_published && (
                                    <Plate variant="outline" size="sm" className="ml-1.5">Draft</Plate>
                                )}
                            </Tabs.Trigger>
                        ))}
                        {isEditing && (
                            <button
                                type="button"
                                onClick={() => openEditionForm('create')}
                                className="flex items-center gap-1 px-2 py-2.5 text-[13px] font-semibold text-(--text-tertiary) hover:text-(--text-secondary) transition-colors shrink-0 cursor-pointer"
                            >
                                <FaPlus className="text-[10px]" /> Edition
                            </button>
                        )}
                        {isEditing && activeEditionId && (
                            <button
                                type="button"
                                onClick={() => openEditionForm('rename')}
                                title="Rename edition"
                                className="flex items-center gap-1 px-2 py-2.5 text-[13px] font-semibold text-(--text-tertiary) hover:text-(--text-secondary) transition-colors shrink-0 cursor-pointer"
                            >
                                <FaPen className="text-[10px]" /> Rename
                            </button>
                        )}
                    </Tabs.List>

                    {!isOwner && isPublished && (
                        <div className="flex items-center gap-1.5 shrink-0 py-1.5">
                            <HeaderButton icon={<FaShareNodes />} label="Share" collapseLabel onClick={() => setShareSheet({})} />
                        </div>
                    )}
                    {isOwner && (
                        <div className="flex items-center gap-1.5 shrink-0 py-1.5">
                            {isPublished && !isEditing && (
                                <HeaderButton icon={<FaShareNodes />} label="Share" collapseLabel onClick={() => setShareSheet({})} />
                            )}
                            {isEditing ? (
                                <>
                                    <HeaderButton
                                        icon={<FaEye />}
                                        label={isStaged ? 'View live' : 'Preview'}
                                        collapseLabel
                                        onClick={() => changeMode('browse')}
                                        title={isStaged ? 'See the published version' : 'See this release the way others will'}
                                    />
                                    {hasUnpublishedWork && !reviewOpen && (
                                        <HeaderButton icon={<FaGlobe />} label={isStaged && isPublished ? 'Publish changes' : 'Publish'} tone="primary" onClick={openReview} title="Review the release, then publish it" />
                                    )}
                                </>
                            ) : (
                                <HeaderButton icon={<FaPen />} label="Edit" onClick={() => changeMode('edit')} />
                            )}
                        </div>
                    )}
                </div>

                {isOwner && !isEditing && publishedVersion !== null && (
                    <ModeBanner tone="navy" label="PUBLISHED" detail={`— v${publishedVersion} is live. Anyone can browse it.`}>
                        <ModeBannerButton onClick={() => setShareSheet({})}>
                            <FaShareNodes /> Share
                        </ModeBannerButton>
                        <ModeBannerButton onClick={() => setPublishedVersion(null)}>
                            <FaXmark /> Dismiss
                        </ModeBannerButton>
                    </ModeBanner>
                )}

                {isOwner && !isEditing && publishedVersion === null && hasUnpublishedWork && (
                    <ModeBanner
                        tone="navy"
                        label={isStaged ? 'LIVE VERSION' : 'PREVIEW'}
                        detail={isStaged
                            ? `— this is v${release.published_version}. Your unpublished changes show up once you publish them`
                            : isPublished
                                ? '— editions marked DRAFT are only visible to you until published'
                                : '— this is how your release will look to others once published'}
                    >
                        <ModeBannerButton onClick={() => changeMode('edit')}>
                            Back to Editing
                        </ModeBannerButton>
                        <ModeBannerButton onClick={openReview}>
                            <FaGlobe /> Review and publish
                        </ModeBannerButton>
                    </ModeBanner>
                )}

                {isEditing && isStaged && (
                    <ModeBanner
                        tone="red"
                        label="EDITING"
                        detail={confirmingDiscard
                            ? '— throw away every change since you last published? This can\'t be undone'
                            : `— changes stay private until you publish them. Everyone else sees v${release.published_version}`}
                    >
                        {confirmingDiscard ? (
                            <>
                                <ModeBannerButton onClick={handleDiscard} disabled={discarding}>
                                    {discarding && <FaSpinner className="animate-spin" />} Discard changes
                                </ModeBannerButton>
                                <ModeBannerButton onClick={() => setConfirmingDiscard(false)}>
                                    Keep editing
                                </ModeBannerButton>
                            </>
                        ) : (
                            <>
                                {release.has_pending_changes && (
                                    <ModeBannerButton onClick={() => setConfirmingDiscard(true)}>
                                        Discard changes…
                                    </ModeBannerButton>
                                )}
                                <ModeBannerButton onClick={() => changeMode('browse')}>
                                    <FaCheck /> Done
                                </ModeBannerButton>
                            </>
                        )}
                    </ModeBanner>
                )}

                {error && (
                    <InlineError size="md" className="mx-4 mt-2 shrink-0">
                        {error}
                    </InlineError>
                )}

                {isEditing && editionForm && (
                    <div className="flex items-center gap-2 px-3 py-2 border-b border-(--divider) shrink-0">
                        <div className="flex-1 max-w-xs">
                            <FormInput
                                label=""
                                value={editionFormName}
                                onChange={v => setEditionFormName(v ?? '')}
                                placeholder="Edition name (e.g. 2001, Rainbow Foil)"
                            />
                        </div>
                        <button
                            type="button"
                            onClick={handleSubmitEditionForm}
                            disabled={!editionFormName.trim() || savingEditionForm}
                            className={buttonClass('primary', 'sm')}
                        >
                            {savingEditionForm
                                ? <FaSpinner className="animate-spin text-[10px]" />
                                : editionForm === 'rename' ? <FaCheck className="text-[10px]" /> : <FaPlus className="text-[10px]" />}
                            {editionForm === 'rename' ? 'Save' : 'Create'}
                        </button>
                        <button
                            type="button"
                            onClick={closeEditionForm}
                            className="text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer"
                        >
                            <FaXmark className="text-[14px]" />
                        </button>
                    </div>
                )}

                {editions.length === 0 && !(isEditing && editionForm) ? (
                    <EmptyState size="page" title="No editions yet.">
                        {isEditing ? 'Add an edition to start building your player pool.' : 'This release has no editions yet.'}
                    </EmptyState>
                ) : (
                    editions.map(edition => {
                        const loadedEdition = needsDraft ? undefined : editionCache[loadedIdOf(edition)];
                        return (
                        <Tabs.Content
                            key={edition.id}
                            value={edition.id}
                            // Kept mounted once loaded (just hidden) so each edition's builder state survives tab switches.
                            forceMount
                            className="flex-1 min-h-0 flex flex-col focus:outline-none data-[state=inactive]:hidden"
                        >
                            {!loadedEdition ? (
                                edition.id === activeEditionId && (
                                    <EditionBuilderSkeleton />
                                )
                            ) : (
                                <EditionBuilder
                                    // The live edition and its working copy are different builders
                                    key={loadedEdition.id}
                                    releaseId={release.id}
                                    releaseName={release.name}
                                    edition={loadedEdition}
                                    readOnly={!isEditing}
                                    token={token}
                                    defaultShowdownSet={release.default_showdown_set}
                                    onEditionUpdated={handleEditionUpdated}
                                    reviewOpen={isReviewing}
                                    onReviewOpenChange={isEditing && token ? setReviewOpen : undefined}
                                    review={isReviewing && edition.id === activeEditionId ? (
                                        <ReleaseReviewPanel
                                            release={release}
                                            review={review}
                                            unsavedPreviewEditionIds={release.editions.map(loadedIdOf).filter(id => unsavedPreviews[id])}
                                            token={token}
                                            onFix={handleReviewFix}
                                            onReleaseUpdated={handleReviewReleaseUpdated}
                                            onPublished={handlePublished}
                                            onShare={() => setShareSheet({})}
                                            onViewAsVisitor={() => changeMode('browse')}
                                        />
                                    ) : null}
                                    navRequest={navRequest?.editionId === edition.id ? navRequest.request : null}
                                    onUnsavedPreviewChange={handleUnsavedPreviewChange}
                                />
                            )}
                        </Tabs.Content>
                        );
                    })
                )}
            </Tabs.Root>

            {shareSheet && <ReleaseShareSheet release={release} eyebrow={shareSheet.eyebrow} onClose={() => setShareSheet(null)} />}
        </div>
    );
}

const HEADER_BUTTON_TONES = {
    neutral: buttonVariantClass('secondary'),
    primary: buttonVariantClass('primary'),
} as const;

type HeaderButtonProps = {
    icon: ReactNode;
    label: string;
    onClick: () => void;
    tone?: keyof typeof HEADER_BUTTON_TONES;
    /** Swaps the icon for a spinner and blocks re-entry while an async action is in flight. */
    busy?: boolean;
    /** Icon-only below `sm`, so secondary actions don't crowd the release name on phones. */
    collapseLabel?: boolean;
    title?: string;
};

function HeaderButton({ icon, label, onClick, tone = 'neutral', busy = false, collapseLabel = false, title }: HeaderButtonProps) {
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={busy}
            title={title ?? label}
            aria-label={label}
            className={`flex items-center justify-center gap-1.5 h-8 min-w-8 px-2 sm:px-3 rounded-control text-[12px] font-semibold whitespace-nowrap ${HEADER_BUTTON_TONES[tone]}`}
        >
            <span className="text-[12px]">{busy ? <FaSpinner className="animate-spin" /> : icon}</span>
            <span className={collapseLabel ? 'hidden sm:inline' : ''}>{label}</span>
        </button>
    );
}
