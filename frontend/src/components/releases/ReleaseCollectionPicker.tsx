import { useEffect, useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import {
    fetchAllReleaseCollections, saveReleaseCollection, setReleaseCollection,
    type Release, type ReleaseCollection,
} from '../../api/releases';
import CustomSelect, { type SelectOption } from '../shared/CustomSelect';
import { buttonClass } from '../shared/buttonStyles';
import { fieldClass, FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { InlineError } from '../shared/InlineError';

const NO_COLLECTION = '';
const NEW_COLLECTION = '__new__';

const slugify = (title: string) => title.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

type ReleaseCollectionPickerProps = {
    release: Release;
    token: string;
    onReleaseUpdated: (release: Release) => void;
};

/** Admin only, on an official release: which Release Builder shelf it's grouped under (the 2027 sets, say),
 *  or a new shelf with its own title and description. Saved right away; visitors see it on their next load
 *  of the list. */
export function ReleaseCollectionPicker({ release, token, onReleaseUpdated }: ReleaseCollectionPickerProps) {
    const [collections, setCollections] = useState<ReleaseCollection[]>([]);
    const [creating, setCreating] = useState(false);
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchAllReleaseCollections(token).then(setCollections).catch(err => setError(err.message));
    }, [token]);

    async function assign(slug: string | null) {
        setSaving(true);
        setError(null);
        try {
            const updated = await setReleaseCollection(release.id, slug, token);
            onReleaseUpdated({ ...release, collection_slug: updated.collection_slug, collection_sort_index: updated.collection_sort_index });
            return true;
        } catch (err) {
            setError(err instanceof Error ? err.message : "Couldn't save the collection. Try again.");
            return false;
        } finally {
            setSaving(false);
        }
    }

    async function create() {
        const slug = slugify(title);
        if (!slug) return;
        setSaving(true);
        setError(null);
        try {
            // New shelves go after the existing ones
            const sortIndex = collections.reduce((max, c) => Math.max(max, c.sort_index), 0) + 1;
            const collection = await saveReleaseCollection({ slug, title: title.trim(), description: description.trim() || null, sort_index: sortIndex }, token);
            setCollections(prev => [...prev.filter(c => c.slug !== collection.slug), collection]);
            setCreating(false);
            setTitle('');
            setDescription('');
            setSaving(false);
            await assign(collection.slug);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Couldn't create the collection. Try again.");
            setSaving(false);
        }
    }

    const options: SelectOption[] = [
        { value: NO_COLLECTION, label: 'None (plain Official list)' },
        ...collections.map(c => ({ value: c.slug, label: c.title })),
        { value: NEW_COLLECTION, label: 'New collection…' },
    ];

    return (
        <div className="flex flex-col gap-1.5">
            <span className={`${FIELD_LABEL_CLASS} flex items-center gap-1.5`}>
                Collection {saving && <FaSpinner className="animate-spin text-[10px]" />}
            </span>
            <CustomSelect
                value={creating ? NEW_COLLECTION : release.collection_slug ?? NO_COLLECTION}
                onChange={value => {
                    if (value === NEW_COLLECTION) { setCreating(true); return; }
                    setCreating(false);
                    assign(value || null);
                }}
                options={options}
                disabled={saving}
            />
            <p className="text-[11px] text-(--text-tertiary)">Groups it with other official releases in one carousel on the Release Builder page.</p>
            {creating && (
                <div className="flex flex-col gap-2">
                    <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title (e.g. 2027 Release)" className={fieldClass('md')} />
                    <textarea value={description} onChange={e => setDescription(e.target.value)} rows={2} placeholder="Description shown under the title" className={fieldClass('md')} />
                    <div className="flex gap-2">
                        <button type="button" onClick={create} disabled={saving || !slugify(title)} className={buttonClass('primary', 'sm')}>Create and add</button>
                        <button type="button" onClick={() => setCreating(false)} disabled={saving} className={buttonClass('ghost', 'sm')}>Cancel</button>
                    </div>
                </div>
            )}
            {error && <InlineError size="sm">{error}</InlineError>}
        </div>
    );
}
