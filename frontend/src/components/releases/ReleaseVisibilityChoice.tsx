import { useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import { updateRelease, type Release } from '../../api/releases';
import { choiceClass } from '../shared/choiceStyles';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { InlineError } from '../shared/InlineError';

const OPTIONS = [
    { isListed: true, label: 'Listed', detail: 'Shows in Community and search' },
    { isListed: false, label: 'Link only', detail: 'Anyone with the link, not listed' },
] as const;

type ReleaseVisibilityChoiceProps = {
    release: Release;
    token: string;
    onReleaseUpdated: (release: Release) => void;
};

/** Listed or link-only. Saved to the release right away (like its description), so it can be picked
 *  before publishing and switched at any time after, and the link stays the same either way. */
export function ReleaseVisibilityChoice({ release, token, onReleaseUpdated }: ReleaseVisibilityChoiceProps) {
    const [saving, setSaving] = useState<boolean | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function handleChange(isListed: boolean) {
        if (isListed === release.is_listed || saving !== null) return;
        setSaving(isListed);
        setError(null);
        try {
            const updated = await updateRelease(release.id, { is_listed: isListed }, token);
            onReleaseUpdated({ ...release, is_listed: updated.is_listed });
        } catch (err) {
            setError(err instanceof Error ? err.message : "Couldn't change who can find it.");
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
                        onClick={() => handleChange(option.isListed)}
                        disabled={saving !== null}
                        className={choiceClass(release.is_listed === option.isListed, 'md', 'flex-col items-start! text-left h-auto min-w-0 py-2 whitespace-normal!')}
                    >
                        <span className="flex items-center gap-1.5">
                            {saving === option.isListed && <FaSpinner className="animate-spin text-[10px]" />}
                            {option.label}
                        </span>
                        <span className="text-[11px] font-normal text-(--text-tertiary)">{option.detail}</span>
                    </button>
                ))}
            </div>
            {error && <InlineError size="sm">{error}</InlineError>}
        </div>
    );
}
