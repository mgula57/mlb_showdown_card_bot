import { useState } from 'react';
import { FaChevronDown } from 'react-icons/fa6';
import { headingClass } from '../shared/headingStyles';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';

const sectionOpenStorageKey = (id: string) => `releaseBuilder.algorithmSection.${id}`;

function loadSectionOpen(id: string, defaultOpen: boolean): boolean {
    try {
        const saved = localStorage.getItem(sectionOpenStorageKey(id));
        return saved === null ? defaultOpen : saved === 'open';
    } catch {
        return defaultOpen;
    }
}

/** Lightweight collapsible group — used instead of FormSection so the build panel's settings keep
 * as much of the narrow panel as possible. Shows `summary` while collapsed so the whole
 * config stays readable at a glance; open/closed is remembered per section. */
export function SettingsGroup({ id, title, summary, children, defaultOpen = true }: { id: string; title: string; summary?: string; children: React.ReactNode; defaultOpen?: boolean }) {
    const [isOpen, setIsOpen] = useState(() => loadSectionOpen(id, defaultOpen));

    function toggle() {
        const next = !isOpen;
        setIsOpen(next);
        try { localStorage.setItem(sectionOpenStorageKey(id), next ? 'open' : 'closed'); } catch { /* storage unavailable */ }
    }

    return (
        <section className="flex flex-col gap-2.5 shrink-0 border-t border-(--divider) pt-4">
            <button
                type="button"
                onClick={toggle}
                aria-expanded={isOpen}
                className="group flex items-center justify-between gap-3 text-left cursor-pointer"
            >
                <span className={`shrink-0 ${headingClass('panel')}`}>{title}</span>
                <span className="flex items-center gap-2 min-w-0">
                    {!isOpen && summary && (
                        <span title={summary} className="text-[11px] font-semibold text-(--text-tertiary) truncate">{summary}</span>
                    )}
                    <FaChevronDown className={`shrink-0 text-[10px] text-(--text-tertiary) opacity-60 group-hover:opacity-100 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                </span>
            </button>
            {isOpen && children}
        </section>
    );
}

/** Field-style caps label for a sub-part of a SettingsGroup. */
export function SettingsLabel({ children }: { children: React.ReactNode }) {
    return <span className={FIELD_LABEL_CLASS}>{children}</span>;
}
