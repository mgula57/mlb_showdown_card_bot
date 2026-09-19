import React from 'react';
import FormEnabler from '../customs/FormEnabler';

type Props = {
    /** Toggle label. */
    label: string;
    /** One-line explanation shown under the label. Always rendered, so it never causes the
     *  form to jump when the toggle flips. */
    description?: string;
    isEnabled: boolean;
    /** Called to flip the value — absorbs `FormEnabler`'s current-value callback so callers
     *  just pass `() => setX(v => !v)`. */
    onToggle: () => void;
    /** Dependent controls, only rendered while the toggle is on. */
    children?: React.ReactNode;
    className?: string;
};

/**
 * The single card shape every option in `SeasonSimSetupForm` uses: a toggle, an always-visible
 * one-line description, and — only while enabled — an indented panel of dependent settings.
 */
export default function SimSettingToggle({ label, description, isEnabled, onToggle, children, className = '' }: Props) {
    return (
        <div className={`flex flex-col gap-2 rounded-xl border border-form-element bg-secondary p-3 ${className}`}>
            <FormEnabler label={label} isEnabled={isEnabled} onChange={onToggle} className="self-start" />
            {description && <p className="text-[11px] text-(--text-tertiary)">{description}</p>}
            {isEnabled && children && (
                <div className="flex flex-col gap-3 border-l-2 border-form-element pl-3">
                    {children}
                </div>
            )}
        </div>
    );
}
