import { useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import { updateRelease, type Release, type ReleaseUpdatePayload, type ReleaseVisibility } from '../../api/releases';
import FormEnabler from '../customs/FormEnabler';
import { choiceClass } from '../shared/choiceStyles';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { InlineError } from '../shared/InlineError';
import { useAuth } from '../auth/AuthContext';
import { ReleaseCollectionPicker } from './ReleaseCollectionPicker';
import { RELEASE_VISIBILITY, RELEASE_VISIBILITY_ORDER } from './releaseVisibility';

type SharingField = 'visibility' | 'allow_remix' | 'allow_comments' | 'is_wip';
type SharingValue = ReleaseVisibility | boolean;

type ReleaseSharingSettingsProps = {
    release: Release;
    token: string;
    onReleaseUpdated: (release: Release) => void;
};

/** Who can find it (listed, link-only or only the owner), whether others may remix it or comment on it, and its WIP tag. Saved
 *  to the release right away (like its description), so all can be picked before publishing and switched at
 *  any time after, and the link stays the same either way. Turning remixes off keeps the remixes already
 *  made; turning comments off hides them until they're turned back on; going private keeps others' saves, which come back if it's shared again. */
export function ReleaseSharingSettings({ release, token, onReleaseUpdated }: ReleaseSharingSettingsProps) {
    // The field being saved, and the value it's being saved as
    const { isAdmin } = useAuth();
    const [saving, setSaving] = useState<{ field: SharingField; value: SharingValue } | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function save(field: SharingField, value: SharingValue) {
        if (value === release[field] || saving !== null) return;
        setSaving({ field, value });
        setError(null);
        try {
            const payload: ReleaseUpdatePayload = { [field]: value };
            const updated = await updateRelease(release.id, payload, token);
            onReleaseUpdated({ ...release, [field]: updated[field] });
        } catch (err) {
            setError(err instanceof Error ? err.message : "Couldn't save that setting. Try again.");
        } finally {
            setSaving(null);
        }
    }

    return (
        <div className="flex flex-col gap-1.5">
            <span className={FIELD_LABEL_CLASS}>Who can find it</span>
            <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Who can find it">
                {RELEASE_VISIBILITY_ORDER.map(visibility => (
                    <button
                        key={visibility}
                        type="button"
                        role="radio"
                        aria-checked={release.visibility === visibility}
                        onClick={() => save('visibility', visibility)}
                        disabled={saving !== null}
                        className={choiceClass(release.visibility === visibility, 'md', 'flex-col items-start! justify-start! text-left h-auto min-w-0 py-2 whitespace-normal!')}
                    >
                        <span className="flex items-center gap-1.5">
                            {saving?.field === 'visibility' && saving.value === visibility && <FaSpinner className="animate-spin text-[10px]" />}
                            {RELEASE_VISIBILITY[visibility].label}
                        </span>
                        <span className="text-[11px] font-normal text-(--text-tertiary)">{RELEASE_VISIBILITY[visibility].detail}</span>
                    </button>
                ))}
            </div>
            {/* Nobody else can open a private release, so remixing, comments and the WIP tag don't apply */}
            {release.visibility !== 'private' && (
            <>
            <FormEnabler
                label={<span className="flex items-center gap-1.5">{saving?.field === 'allow_remix' && <FaSpinner className="animate-spin text-[10px]" />}Allow remixes</span>}
                description="Others can start their own release from this one. Theirs credits yours."
                isEnabled={release.allow_remix}
                onChange={enabled => save('allow_remix', !enabled)}
                isDisabled={saving !== null}
            />
            <FormEnabler
                label={<span className="flex items-center gap-1.5">{saving?.field === 'allow_comments' && <FaSpinner className="animate-spin text-[10px]" />}Allow comments</span>}
                description="People can comment on it and reply to each other. You can delete any comment on it."
                isEnabled={release.allow_comments}
                onChange={enabled => save('allow_comments', !enabled)}
                isDisabled={saving !== null}
            />
            <FormEnabler
                label={<span className="flex items-center gap-1.5">{saving?.field === 'is_wip' && <FaSpinner className="animate-spin text-[10px]" />}Mark as work in progress</span>}
                description="Shows a WIP tag so people know more cards or changes are coming."
                isEnabled={release.is_wip}
                onChange={enabled => save('is_wip', !enabled)}
                isDisabled={saving !== null}
            />
            </>
            )}
            {isAdmin && release.is_official && (
                <ReleaseCollectionPicker release={release} token={token} onReleaseUpdated={onReleaseUpdated} />
            )}
            {error && <InlineError size="sm">{error}</InlineError>}
        </div>
    );
}
