import { useState, useEffect, useCallback, type ReactNode } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import type { Release, ReleaseEdition, ReleaseReviewItem } from '../../api/releases';
import { fetchEdition, createEdition, updateEdition } from '../../api/releases';
import { EditionBuilder, EditionBuilderSkeleton, type EditionNavRequest } from './EditionBuilder';
import { ReleaseReviewPanel } from './ReleaseReviewPanel';
import { useReleaseReview } from './useReleaseReview';
import FormInput from '../customs/FormInput';
import { ModeBanner, ModeBannerButton } from '../shared/ModeBanner';
import { FaArrowLeft, FaCheck, FaEye, FaGlobe, FaPen, FaPlus, FaSpinner, FaXmark } from 'react-icons/fa6';

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

    const [mode, setMode] = useState<ViewMode>(() => isPublished ? 'browse' : 'edit');
    const isEditing = isOwner && mode === 'edit';

    /** Step 3 is release-wide, so it lives here rather than in each edition's builder. */
    const [reviewOpen, setReviewOpen] = useState(false);
    const isReviewing = isEditing && reviewOpen && !!token;
    const review = useReleaseReview(release.id, token, isReviewing);
    const [navRequest, setNavRequest] = useState<{ editionId: string; request: EditionNavRequest } | null>(null);
    const [unsavedPreviews, setUnsavedPreviews] = useState<Record<string, boolean>>({});
    const handleUnsavedPreviewChange = useCallback((editionId: string, hasUnsavedPreview: boolean) => {
        setUnsavedPreviews(prev => prev[editionId] === hasUnsavedPreview ? prev : { ...prev, [editionId]: hasUnsavedPreview });
    }, []);

    const activeEditionId = (editions.find(e => e.slug === editionSlug) ?? editions[0])?.id ?? null;
    const [editionCache, setEditionCache] = useState<Record<string, ReleaseEdition>>({});
    const [error, setError] = useState<string | null>(null);

    /** Inline name form above the builder — creates a new edition or renames the active one. */
    const [editionForm, setEditionForm] = useState<'create' | 'rename' | null>(null);
    const [editionFormName, setEditionFormName] = useState('');
    const [savingEditionForm, setSavingEditionForm] = useState(false);
    const activeEditionName = editions.find(e => e.id === activeEditionId)?.name ?? '';

    useEffect(() => {
        if (!activeEditionId || editionCache[activeEditionId]) return;
        setError(null);
        fetchEdition(release.id, activeEditionId, token)
            .then(edition => setEditionCache(prev => ({ ...prev, [edition.id]: edition })))
            .catch(err => setError(err.message ?? 'Failed to load edition.'));
    }, [activeEditionId, release.id, token]);

    function changeMode(next: ViewMode) {
        setMode(next);
        if (next === 'browse') setReviewOpen(false);
        closeEditionForm();
    }

    function openReview() {
        changeMode('edit');
        setReviewOpen(true);
    }

    /** A review fix link: leave the review for the edition and step where the item gets fixed. */
    function handleReviewFix(item: ReleaseReviewItem) {
        const fix = item.fix;
        const edition = release.editions.find(e => e.id === fix?.edition_id);
        if (!fix || fix.step === 'details' || !edition) return;
        setReviewOpen(false);
        onEditionChange(edition.slug);
        setNavRequest({ editionId: edition.id, request: { step: fix.step, imageStatus: fix.image_status } });
    }

    /** Publish/unpublish and description saves return the release without its list-only fields. */
    function handleReviewReleaseUpdated(updated: Release) {
        const publishedById = new Map(updated.editions.map(e => [e.id, e.is_published]));
        setEditionCache(prev => Object.fromEntries(Object.entries(prev).map(([id, edition]) => [
            id, publishedById.has(id) ? { ...edition, is_published: publishedById.get(id)! } : edition,
        ])));
        onReleaseUpdated({ ...release, ...updated, editions: updated.editions.length ? updated.editions : release.editions });
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
            if (!activeEditionId || name === activeEditionName) { closeEditionForm(); return; }
            setSavingEditionForm(true);
            setError(null);
            try {
                handleEditionUpdated(await updateEdition(release.id, activeEditionId, { name }, token));
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
                editions: [
                    ...release.editions,
                    { id: edition.id, name: edition.name, attributes: edition.attributes, slug: edition.slug, is_published: edition.is_published, card_count: 0 },
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
            editions: release.editions.map(e => {
                const updated = byId.get(e.id);
                return updated
                    ? { ...e, name: updated.name, attributes: updated.attributes, is_published: updated.is_published, card_count: updated.cards.length }
                    : e;
            }).sort((a, b) => a.name.localeCompare(b.name)),
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
                                {edition.name}
                                <Plate size="sm" className="ml-1.5">{edition.card_count}</Plate>
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

                    {isOwner && (
                        <div className="flex items-center gap-1.5 shrink-0 py-1.5">
                            {isEditing ? (
                                <>
                                    <HeaderButton icon={<FaEye />} label="Preview" collapseLabel onClick={() => changeMode('browse')} title="See this release the way others will" />
                                    {hasDrafts && !reviewOpen && (
                                        <HeaderButton icon={<FaGlobe />} label="Publish" tone="primary" onClick={openReview} title="Review the release, then publish it" />
                                    )}
                                </>
                            ) : (
                                <HeaderButton icon={<FaPen />} label="Edit" onClick={() => changeMode('edit')} />
                            )}
                        </div>
                    )}
                </div>

                {isOwner && !isEditing && hasDrafts && (
                    <ModeBanner
                        tone="navy"
                        label="PREVIEW"
                        detail={isPublished
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

                {isEditing && isPublished && (
                    <ModeBanner
                        tone="red"
                        label="EDITING"
                        detail="— this release is published, so changes are live as soon as they save"
                    >
                        <ModeBannerButton onClick={() => changeMode('browse')}>
                            <FaCheck /> Done
                        </ModeBannerButton>
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
                    editions.map(edition => (
                        <Tabs.Content
                            key={edition.id}
                            value={edition.id}
                            // Kept mounted once loaded (just hidden) so each edition's builder state survives tab switches.
                            forceMount
                            className="flex-1 min-h-0 flex flex-col focus:outline-none data-[state=inactive]:hidden"
                        >
                            {!editionCache[edition.id] ? (
                                edition.id === activeEditionId && (
                                    <EditionBuilderSkeleton />
                                )
                            ) : (
                                <EditionBuilder
                                    releaseId={release.id}
                                    releaseName={release.name}
                                    edition={editionCache[edition.id]}
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
                                            unsavedPreviewEditionIds={release.editions.filter(e => unsavedPreviews[e.id]).map(e => e.id)}
                                            token={token}
                                            onFix={handleReviewFix}
                                            onReleaseUpdated={handleReviewReleaseUpdated}
                                            onViewAsVisitor={() => changeMode('browse')}
                                        />
                                    ) : null}
                                    navRequest={navRequest?.editionId === edition.id ? navRequest.request : null}
                                    onUnsavedPreviewChange={handleUnsavedPreviewChange}
                                />
                            )}
                        </Tabs.Content>
                    ))
                )}
            </Tabs.Root>
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
