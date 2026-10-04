import { useState, useEffect } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import type { Release, ReleaseEdition } from '../../api/releases';
import { fetchEdition, createEdition, updateEdition } from '../../api/releases';
import { EditionBuilder } from './EditionBuilder';
import FormInput from '../customs/FormInput';
import { FaArrowLeft, FaCheck, FaPen, FaPlus, FaSpinner, FaXmark } from 'react-icons/fa6';

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

const EDITION_TAB_CLASS =
    'relative flex items-center px-3 py-2.5 text-[13px] font-bold transition-colors border-b-2 -mb-px ' +
    'data-[state=active]:border-(--secondary) data-[state=active]:text-(--text-primary) ' +
    'data-[state=inactive]:border-transparent data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:hover:text-(--text-secondary)';

export function ReleaseDetail({ release, readOnly, editionSlug, onEditionChange, onBack, onReleaseUpdated, token }: ReleaseDetailProps) {
    const activeEditionId = (release.editions.find(e => e.slug === editionSlug) ?? release.editions[0])?.id ?? null;
    const [editionCache, setEditionCache] = useState<Record<string, ReleaseEdition>>({});
    const [error, setError] = useState<string | null>(null);

    /** Inline name form above the builder — creates a new edition or renames the active one. */
    const [editionForm, setEditionForm] = useState<'create' | 'rename' | null>(null);
    const [editionFormName, setEditionFormName] = useState('');
    const [savingEditionForm, setSavingEditionForm] = useState(false);
    const activeEditionName = release.editions.find(e => e.id === activeEditionId)?.name ?? '';

    useEffect(() => {
        if (!activeEditionId || editionCache[activeEditionId]) return;
        setError(null);
        fetchEdition(release.id, activeEditionId, token)
            .then(edition => setEditionCache(prev => ({ ...prev, [edition.id]: edition })))
            .catch(err => setError(err.message ?? 'Failed to load edition.'));
    }, [activeEditionId, release.id, token]);

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

    function handleEditionUpdated(updated: ReleaseEdition) {
        setEditionCache(prev => ({ ...prev, [updated.id]: updated }));
        onReleaseUpdated({
            ...release,
            editions: release.editions.map(e => e.id === updated.id
                ? { ...e, name: updated.name, attributes: updated.attributes, is_published: updated.is_published, card_count: updated.cards.length }
                : e
            ).sort((a, b) => a.name.localeCompare(b.name)),
        });
    }

    return (
        <div className="flex flex-col h-[calc(100dvh-2.5rem)] overflow-hidden">
            <div className="flex items-start gap-3 px-4 py-2.5 border-b border-(--divider) shrink-0">
                <button type="button" onClick={onBack} className="text-(--text-tertiary) opacity-70 hover:text-(--text-primary) transition-colors shrink-0 mt-0.5 h-full">
                    <FaArrowLeft />
                </button>
                <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2 min-w-0">
                        <div className="text-xl font-black text-(--text-primary) truncate uppercase">{release.name}</div>
                        {release.is_official && (
                            <span className="text-[9px] font-black rounded px-1.5 py-0.5 leading-none shrink-0 bg-(--secondary) text-(--background-primary)">
                                OFFICIAL
                            </span>
                        )}
                    </div>
                    {release.description && (
                        <div className="text-[12px] text-(--text-secondary)">{release.description}</div>
                    )}
                </div>
            </div>

            {error && (
                <div className="mx-4 mt-2 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5 shrink-0">
                    {error}
                </div>
            )}

            <Tabs.Root
                value={activeEditionId ?? undefined}
                onValueChange={id => {
                    const edition = release.editions.find(e => e.id === id);
                    if (edition) onEditionChange(edition.slug);
                }}
                className="flex flex-col flex-1 min-h-0"
            >
                <div className="flex items-center gap-3 px-4 pt-2 bg-(--background-secondary) shrink-0">
                    <span className="text-[10px] font-bold text-(--text-tertiary) uppercase tracking-wide shrink-0">Editions</span>
                    <Tabs.List className="flex items-center gap-x-3 border-b border-(--divider) flex-1 min-w-0 overflow-x-auto">
                        {release.editions.map(edition => (
                            <Tabs.Trigger key={edition.id} value={edition.id} className={EDITION_TAB_CLASS}>
                                {edition.name}
                                <span className="ml-1.5 text-[10px] text-(--text-tertiary) font-normal py-0.5 bg-(--background-primary) px-1 rounded-md">{edition.card_count}</span>
                            </Tabs.Trigger>
                        ))}
                        {!readOnly && (
                            <button
                                type="button"
                                onClick={() => openEditionForm('create')}
                                className="flex items-center gap-1 px-2 py-2.5 text-[13px] font-semibold text-(--text-tertiary) hover:text-(--text-secondary) transition-colors shrink-0 cursor-pointer"
                            >
                                <FaPlus className="text-[10px]" /> Edition
                            </button>
                        )}
                        {!readOnly && activeEditionId && (
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
                </div>

                {editionForm && (
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
                            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
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

                {release.editions.length === 0 && !editionForm ? (
                    <p className="text-[13px] text-(--text-tertiary) py-8 text-center">
                        {readOnly ? 'This release has no editions yet.' : 'Add an edition to start building your player pool.'}
                    </p>
                ) : (
                    release.editions.map(edition => (
                        <Tabs.Content
                            key={edition.id}
                            value={edition.id}
                            // Kept mounted once loaded (just hidden) so each edition's builder state survives tab switches.
                            forceMount
                            className="flex-1 min-h-0 flex flex-col focus:outline-none data-[state=inactive]:hidden"
                        >
                            {!editionCache[edition.id] ? (
                                edition.id === activeEditionId && (
                                    <div className="flex justify-center py-12">
                                        <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
                                    </div>
                                )
                            ) : (
                                <EditionBuilder
                                    releaseId={release.id}
                                    edition={editionCache[edition.id]}
                                    readOnly={readOnly}
                                    token={token}
                                    defaultShowdownSet={release.default_showdown_set}
                                    onEditionUpdated={handleEditionUpdated}
                                />
                            )}
                        </Tabs.Content>
                    ))
                )}
            </Tabs.Root>
        </div>
    );
}
