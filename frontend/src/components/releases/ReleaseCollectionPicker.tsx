import { useEffect, useState } from 'react';
import { FaPen, FaSpinner } from 'react-icons/fa6';
import {
    fetchAllReleaseCollections, saveReleaseCollection, setReleaseCollection,
    type Release, type ReleaseCollection,
} from '../../api/releases';
import CustomSelect, { type SelectOption } from '../shared/CustomSelect';
import FormEnabler from '../customs/FormEnabler';
import { buttonClass } from '../shared/buttonStyles';
import { fieldClass, FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { InlineError } from '../shared/InlineError';
import { notifyReleaseCollectionsChanged } from './useReleaseLibrary';

const NO_COLLECTION = '';
const NEW_COLLECTION = '__new__';

const slugify = (title: string) => title.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

/** The collection form's fields: a new collection (no `slug` yet) or an existing one being edited. */
type CollectionForm = { slug: string | null; title: string; description: string; sortIndex: string; isVisible: boolean };

type ReleaseCollectionPickerProps = {
    release: Release;
    token: string;
    onReleaseUpdated: (release: Release) => void;
};

/** Admin only, on an official release: which Release Builder shelf it's grouped under (the 2027 sets, say),
 *  plus making a new shelf or editing the selected one's title, description, position and visibility. Saved
 *  right away; visitors see it the next time the list loads. */
export function ReleaseCollectionPicker({ release, token, onReleaseUpdated }: ReleaseCollectionPickerProps) {
    const [collections, setCollections] = useState<ReleaseCollection[]>([]);
    const [form, setForm] = useState<CollectionForm | null>(null);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchAllReleaseCollections(token).then(setCollections).catch(err => setError(err.message));
    }, [token]);

    const selected = collections.find(c => c.slug === release.collection_slug) ?? null;

    async function assign(slug: string | null) {
        const updated = await setReleaseCollection(release.id, slug, token);
        onReleaseUpdated({ ...release, collection_slug: updated.collection_slug, collection_sort_index: updated.collection_sort_index });
        notifyReleaseCollectionsChanged();
    }

    async function run(action: () => Promise<void>, failure: string) {
        setSaving(true);
        setError(null);
        try {
            await action();
        } catch (err) {
            setError(err instanceof Error ? err.message : failure);
        } finally {
            setSaving(false);
        }
    }

    function openEdit(collection: ReleaseCollection) {
        setForm({
            slug: collection.slug, title: collection.title, description: collection.description ?? '',
            sortIndex: String(collection.sort_index), isVisible: collection.is_visible,
        });
    }

    const patchForm = (patch: Partial<CollectionForm>) => setForm(prev => prev && { ...prev, ...patch });

    function submit() {
        if (!form) return;
        const slug = form.slug ?? slugify(form.title);
        if (!slug || !form.title.trim()) return;
        const isNew = form.slug === null;
        run(async () => {
            // New shelves go after the existing ones
            const sortIndex = isNew
                ? collections.reduce((max, c) => Math.max(max, c.sort_index), 0) + 1
                : Number.parseInt(form.sortIndex, 10);
            const saved = await saveReleaseCollection({
                slug, title: form.title.trim(), description: form.description.trim(),
                sort_index: Number.isNaN(sortIndex) ? undefined : sortIndex, is_visible: form.isVisible,
            }, token);
            setCollections(prev => [...prev.filter(c => c.slug !== saved.slug), saved].sort((a, b) => a.sort_index - b.sort_index || a.title.localeCompare(b.title)));
            setForm(null);
            if (isNew) await assign(saved.slug);
            else notifyReleaseCollectionsChanged();
        }, "Couldn't save the collection. Try again.");
    }

    const options: SelectOption[] = [
        { value: NO_COLLECTION, label: 'None (in "More releases")' },
        ...collections.map(c => ({ value: c.slug, label: c.is_visible ? c.title : `${c.title} (hidden)` })),
        { value: NEW_COLLECTION, label: 'New collection…' },
    ];
    const isNewForm = form !== null && form.slug === null;

    return (
        <div className="flex flex-col gap-1.5">
            <span className={`${FIELD_LABEL_CLASS} flex items-center gap-1.5`}>
                Collection {saving && <FaSpinner className="animate-spin text-[10px]" />}
            </span>
            <CustomSelect
                value={isNewForm ? NEW_COLLECTION : release.collection_slug ?? NO_COLLECTION}
                onChange={value => {
                    if (value === NEW_COLLECTION) {
                        setForm({ slug: null, title: '', description: '', sortIndex: '', isVisible: true });
                        return;
                    }
                    setForm(null);
                    run(() => assign(value || null), "Couldn't save the collection. Try again.");
                }}
                options={options}
                disabled={saving}
            />
            <div className="flex items-start justify-between gap-3">
                <p className="text-[11px] text-(--text-tertiary)">Groups it with other official releases in one carousel on the Release Builder page.</p>
                {selected && form === null && (
                    <button type="button" onClick={() => openEdit(selected)} className={buttonClass('ghost', 'sm', 'shrink-0')}>
                        <FaPen className="text-[10px]" /> Edit
                    </button>
                )}
            </div>
            {form && (
                <div className="flex flex-col gap-2">
                    <input value={form.title} onChange={e => patchForm({ title: e.target.value })} placeholder="Title (e.g. 2027 Release)" className={fieldClass('md')} />
                    <textarea value={form.description} onChange={e => patchForm({ description: e.target.value })} rows={3} placeholder="Description shown under the title" className={fieldClass('md')} />
                    {!isNewForm && (
                        <>
                            <label className="flex items-center gap-2 text-[12px] text-(--text-secondary)">
                                Position
                                <input
                                    type="number" value={form.sortIndex} onChange={e => patchForm({ sortIndex: e.target.value })}
                                    className={fieldClass('sm', 'w-20')} aria-label="Position among collections, lowest first"
                                />
                                <span className="text-[11px] text-(--text-tertiary)">Lowest shows first</span>
                            </label>
                            <FormEnabler
                                label="Show on the Release Builder page"
                                description="Hide it to take the carousel down without removing its releases."
                                isEnabled={form.isVisible}
                                onChange={enabled => patchForm({ isVisible: !enabled })}
                            />
                        </>
                    )}
                    <div className="flex gap-2">
                        <button type="button" onClick={submit} disabled={saving || !form.title.trim()} className={buttonClass('primary', 'sm')}>
                            {isNewForm ? 'Create and add' : 'Save changes'}
                        </button>
                        <button type="button" onClick={() => setForm(null)} disabled={saving} className={buttonClass('ghost', 'sm')}>Cancel</button>
                    </div>
                </div>
            )}
            {error && <InlineError size="sm">{error}</InlineError>}
        </div>
    );
}
