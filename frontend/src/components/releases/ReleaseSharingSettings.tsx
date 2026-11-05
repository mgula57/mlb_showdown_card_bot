import { useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import { updateRelease, type Release, type ReleaseUpdatePayload } from '../../api/releases';
import FormEnabler from '../customs/FormEnabler';
import { choiceClass } from '../shared/choiceStyles';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { InlineError } from '../shared/InlineError';

const OPTIONS = [
    { isListed: true, label: 'Listed', detail: 'Shows in Community and search' },
    { isListed: false, label: 'Link only', detail: 'Anyone with the link, not listed' },
] as const;

type SharingField = 'is_listed' | 'allow_remix' | 'is_wip';

type ReleaseSharingSettingsProps = {
    release: Release;
    token: string;
    onReleaseUpdated: (release: Release) => void;
};

/** Listed or link-only, whether others may remix it, and its WIP tag. Saved to the release right away (like its
 *  description), so both can be picked before publishing and switched at any time after, and the
 *  link stays the same either way. Turning remixes off keeps the remixes already made. */
export function ReleaseSharingSettings({ release, token, onReleaseUpdated }: ReleaseSharingSettingsProps) {
    // The field being saved, and the value it's being saved as
    const [saving, setSaving] = useState<{ field: SharingField; value: boolean } | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function save(field: SharingField, value: boolean) {
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
            <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Who can find it">
                {OPTIONS.map(option => (
                    <button
                        key={option.label}
                        type="button"
                        role="radio"
                        aria-checked={release.is_listed === option.isListed}
                        onClick={() => save('is_listed', option.isListed)}
                        disabled={saving !== null}
                        className={choiceClass(release.is_listed === option.isListed, 'md', 'flex-col items-start! text-left h-auto min-w-0 py-2 whitespace-normal!')}
                    >
                        <span className="flex items-center gap-1.5">
                            {saving?.field === 'is_listed' && saving.value === option.isListed && <FaSpinner className="animate-spin text-[10px]" />}
                            {option.label}
                        </span>
                        <span className="text-[11px] font-normal text-(--text-tertiary)">{option.detail}</span>
                    </button>
                ))}
            </div>
            <FormEnabler
                label={<span className="flex items-center gap-1.5">{saving?.field === 'allow_remix' && <FaSpinner className="animate-spin text-[10px]" />}Allow remixes</span>}
                description="Others can start their own release from this one. Theirs credits yours."
                isEnabled={release.allow_remix}
                onChange={enabled => save('allow_remix', !enabled)}
                isDisabled={saving !== null}
            />
            <FormEnabler
                label={<span className="flex items-center gap-1.5">{saving?.field === 'is_wip' && <FaSpinner className="animate-spin text-[10px]" />}Mark as work in progress</span>}
                description="Shows a WIP tag so people know more cards or changes are coming."
                isEnabled={release.is_wip}
                onChange={enabled => save('is_wip', !enabled)}
                isDisabled={saving !== null}
            />
            {error && <InlineError size="sm">{error}</InlineError>}
        </div>
    );
}
