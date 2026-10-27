/**
 * @fileoverview User tags on a Release Builder card (e.g. "FOIL" to track which cards will be
 * printed as foils): a read-only chip list for the pool grid and an editor for the card detail modal.
 */

import { useState } from 'react';
import { FaPlus, FaXmark } from 'react-icons/fa6';
import { FIELD_LABEL_CLASS, fieldClass } from '../shared/fieldStyles';
import { choiceClass } from '../shared/choiceStyles';

/** Always offered in the editor, even before any card in the edition uses them. */
const DEFAULT_TAG_SUGGESTIONS = ['FOIL'];
/** Mirrors the backend's `_RELEASE_CARD_TAG_MAX_LENGTH`. */
const TAG_MAX_LENGTH = 24;

/** Tags are stored uppercase and trimmed so "foil" and "FOIL " are the same tag. */
function normalizeReleaseCardTag(value: string): string {
    return value.trim().toUpperCase().slice(0, TAG_MAX_LENGTH);
}

const CHIP_CLASS = 'inline-flex items-center gap-1 rounded-plate bg-(--warning) text-(--field-ink) font-semibold uppercase leading-none';

export function ReleaseCardTagChips({ tags, onRemove }: { tags: string[]; onRemove?: (tag: string) => void }) {
    if (tags.length === 0) return null;
    return (
        <div className="flex flex-wrap gap-1">
            {tags.map(tag => (
                <span key={tag} className={`${CHIP_CLASS} ${onRemove ? 'text-[11px] py-1 pl-2 pr-1' : 'text-[9px] py-0.5 px-1.5'}`}>
                    {tag}
                    {onRemove && (
                        <button
                            type="button"
                            onClick={() => onRemove(tag)}
                            aria-label={`Remove ${tag} tag`}
                            className="flex items-center justify-center w-4 h-4 rounded-full hover:bg-(--red)/90 hover:text-white transition-colors cursor-pointer"
                        >
                            <FaXmark className="text-[10px]" />
                        </button>
                    )}
                </span>
            ))}
        </div>
    );
}

type ReleaseCardTagsEditorProps = {
    tags: string[];
    /** Tags already used elsewhere in the edition, offered as one-click adds. */
    editionTags: string[];
    readOnly: boolean;
    onChange: (tags: string[]) => void;
};

export function ReleaseCardTagsEditor({ tags, editionTags, readOnly, onChange }: ReleaseCardTagsEditorProps) {
    const [draft, setDraft] = useState('');

    if (readOnly) {
        return tags.length > 0 ? <ReleaseCardTagChips tags={tags} /> : null;
    }

    const suggestions = [...new Set([...DEFAULT_TAG_SUGGESTIONS, ...editionTags])].filter(t => !tags.includes(t));

    function addTag(value: string) {
        const tag = normalizeReleaseCardTag(value);
        setDraft('');
        if (!tag || tags.includes(tag)) return;
        onChange([...tags, tag]);
    }

    return (
        <div className="flex flex-wrap items-center gap-2 min-w-0">
            <span className={FIELD_LABEL_CLASS}>Tags</span>
            <ReleaseCardTagChips tags={tags} onRemove={tag => onChange(tags.filter(t => t !== tag))} />
            <input
                type="text"
                value={draft}
                onChange={e => setDraft(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addTag(draft); } }}
                maxLength={TAG_MAX_LENGTH}
                placeholder="Add tag…"
                className={fieldClass('sm', 'w-28 uppercase focus:outline-none')}
            />
            {suggestions.map(tag => (
                <button
                    key={tag}
                    type="button"
                    onClick={() => addTag(tag)}
                    className={choiceClass(false, 'sm', 'border-dashed uppercase')}
                >
                    <FaPlus className="text-[9px]" />
                    {tag}
                </button>
            ))}
        </div>
    );
}
