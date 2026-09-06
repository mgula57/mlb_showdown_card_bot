import { useEffect, useMemo, useState } from 'react';
import { Modal } from '../shared/Modal';
import CustomSelect, { type SelectOption } from '../shared/CustomSelect';
import {
    fetchAdminCollections, upsertAdminCollection, publishTeam,
    type Team, type TeamCollection,
} from '../../api/userTeams';
import { FaSpinner } from 'react-icons/fa6';

type PublishToFeaturedModalProps = {
    token: string;
    /** The team being published (the admin's working copy — left untouched, deep-copied server-side). */
    team: Team;
    onClose: () => void;
    onPublished: (published: Team) => void;
};

const NEW = '__new__';

const inputClass =
    'w-full rounded-lg border border-(--divider) bg-(--background-secondary) px-3 py-2 text-[13px] text-(--text-primary) placeholder:text-(--text-tertiary)';

export function PublishToFeaturedModal({ token, team, onClose, onPublished }: PublishToFeaturedModalProps) {
    const [collections, setCollections] = useState<TeamCollection[] | null>(null);
    const [collectionSlug, setCollectionSlug] = useState<string>('');
    const [newSlug, setNewSlug] = useState('');
    const [newTitle, setNewTitle] = useState('');
    const [newEmoji, setNewEmoji] = useState('');
    const [subtitle, setSubtitle] = useState(team.subtitle ?? '');
    const [credit, setCredit] = useState(team.credit ?? '');
    const [sortIndex, setSortIndex] = useState<string>('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchAdminCollections(token)
            .then(list => {
                setCollections(list);
                setCollectionSlug(list[0]?.slug ?? NEW);
            })
            .catch(err => setError(err.message ?? 'Failed to load collections.'));
    }, [token]);

    const options: SelectOption[] = useMemo(() => [
        ...(collections ?? []).map(c => ({ value: c.slug, label: `${c.cover_emoji ? c.cover_emoji + ' ' : ''}${c.title}` })),
        { value: NEW, label: '+ New collection…' },
    ], [collections]);

    const creatingNew = collectionSlug === NEW;

    async function handlePublish() {
        setBusy(true);
        setError(null);
        try {
            let slug = collectionSlug;
            if (creatingNew) {
                const cleanSlug = newSlug.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
                if (!cleanSlug || !newTitle.trim()) throw new Error('New collection needs a slug and title.');
                await upsertAdminCollection(token, {
                    slug: cleanSlug, title: newTitle.trim(), cover_emoji: newEmoji.trim() || undefined,
                });
                slug = cleanSlug;
            }
            const published = await publishTeam(token, {
                source_team_id: team.team_id,
                collection_slug: slug,
                subtitle: subtitle.trim() || null,
                credit: credit.trim() || null,
                collection_sort_index: sortIndex.trim() ? Number(sortIndex) : null,
                strategy_deck: team.strategy_deck ?? null,
            });
            onPublished(published);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to publish.');
            setBusy(false);
        }
    }

    return (
        <Modal
            title="Publish to Featured"
            subtitle="Deep-copies this roster into a public, curated collection. Your working copy stays editable."
            size="md"
            onClose={onClose}
            footer={
                <div className="flex justify-end gap-2">
                    <button type="button" onClick={onClose}
                        className="px-3 py-2 rounded-lg text-[13px] font-semibold text-(--text-secondary) hover:bg-(--divider) cursor-pointer">
                        Cancel
                    </button>
                    <button type="button" onClick={handlePublish} disabled={busy || collections === null}
                        className="px-3 py-2 rounded-lg text-[13px] font-bold text-(--background-primary) bg-(--secondary) hover:opacity-90 disabled:opacity-50 cursor-pointer flex items-center gap-1.5">
                        {busy && <FaSpinner className="animate-spin" />} Publish
                    </button>
                </div>
            }
        >
            {collections === null ? (
                <div className="flex justify-center py-8"><FaSpinner className="animate-spin text-(--text-tertiary)" /></div>
            ) : (
                <div className="flex flex-col gap-3 p-4">
                    <label className="flex flex-col gap-1">
                        <span className="text-[12px] font-semibold text-(--text-secondary)">Collection</span>
                        <CustomSelect
                            value={collectionSlug}
                            onChange={setCollectionSlug}
                            options={options}
                            buttonClassName={inputClass + ' flex items-center justify-between cursor-pointer'}
                        />
                    </label>

                    {creatingNew && (
                        <div className="grid grid-cols-3 gap-2">
                            <label className="flex flex-col gap-1 col-span-2">
                                <span className="text-[12px] font-semibold text-(--text-secondary)">New collection title</span>
                                <input className={inputClass} value={newTitle} onChange={e => setNewTitle(e.target.value)} placeholder="All-Time Lineups" />
                            </label>
                            <label className="flex flex-col gap-1">
                                <span className="text-[12px] font-semibold text-(--text-secondary)">Emoji</span>
                                <input className={inputClass} value={newEmoji} onChange={e => setNewEmoji(e.target.value)} placeholder="🏆" />
                            </label>
                            <label className="flex flex-col gap-1 col-span-3">
                                <span className="text-[12px] font-semibold text-(--text-secondary)">Slug</span>
                                <input className={inputClass} value={newSlug} onChange={e => setNewSlug(e.target.value)} placeholder="all-time-lineups" />
                            </label>
                        </div>
                    )}

                    <label className="flex flex-col gap-1">
                        <span className="text-[12px] font-semibold text-(--text-secondary)">Subtitle <span className="text-(--text-tertiary)">(shown on the tile)</span></span>
                        <input className={inputClass} value={subtitle} onChange={e => setSubtitle(e.target.value)} placeholder="1996 World Champions" />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span className="text-[12px] font-semibold text-(--text-secondary)">Credit</span>
                        <input className={inputClass} value={credit} onChange={e => setCredit(e.target.value)} placeholder="Built by Gary Quinn" />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span className="text-[12px] font-semibold text-(--text-secondary)">Sort index <span className="text-(--text-tertiary)">(lower shows first)</span></span>
                        <input className={inputClass} type="number" value={sortIndex} onChange={e => setSortIndex(e.target.value)} placeholder="0" />
                    </label>

                    {error && <p className="text-[12px] text-red-400">{error}</p>}
                </div>
            )}
        </Modal>
    );
}

export default PublishToFeaturedModal;
