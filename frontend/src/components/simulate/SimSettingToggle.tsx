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
    /** Dependent controls. Always mounted; dimmed and `inert` (non-interactive, unfocusable)
     *  while the toggle is off, so nothing appears or disappears on flip. */
    children?: React.ReactNode;
    className?: string;
};

/**
 * The single row shape every option in `SeasonSimSetupForm` uses: a toggle, an always-visible
 * one-line description, and an indented panel of dependent settings that stays in the DOM
 * (just disabled) when the toggle is off. Uniform look + no layout jump.
 */
export default function SimSettingToggle({ label, description, isEnabled, onToggle, children, className = '' }: Props) {
    return (
        <div className={`flex flex-col gap-2 rounded-xl border border-form-element bg-secondary p-3 ${className}`}>
            <FormEnabler label={label} isEnabled={isEnabled} onChange={onToggle} className="self-start" />
            {description && <p className="text-[11px] text-(--text-tertiary)">{description}</p>}
            {children && (
                <div
                    className="flex flex-col gap-3 border-l-2 border-form-element pl-3 transition-opacity"
                    style={isEnabled ? undefined : { opacity: 0.45 }}
                    inert={!isEnabled}
                >
                    {children}
                </div>
            )}
        </div>
    );
}
