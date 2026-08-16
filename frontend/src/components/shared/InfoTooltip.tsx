import { useEffect, useRef, useState } from 'react';
import { FaCircleInfo } from 'react-icons/fa6';

/** A small (i) icon that reveals an explanatory tooltip on click/tap — for a label that needs
 * more context than fits inline. Click-triggered rather than hover-only so it works on touch
 * devices, and closes on an outside click or Escape. */
export function InfoTooltip({ text, className = '' }: { text: string; className?: string }) {
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open) return;
        const close = (e: MouseEvent | KeyboardEvent) => {
            if (e instanceof KeyboardEvent) {
                if (e.key === 'Escape') setOpen(false);
                return;
            }
            if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
        };
        document.addEventListener('mousedown', close);
        document.addEventListener('keydown', close);
        return () => {
            document.removeEventListener('mousedown', close);
            document.removeEventListener('keydown', close);
        };
    }, [open]);

    return (
        <div ref={ref} className={`relative inline-flex ${className}`}>
            <button
                type="button"
                onClick={() => setOpen(o => !o)}
                aria-label="More info"
                aria-expanded={open}
                className="cursor-pointer flex items-center text-(--text-tertiary) hover:text-(--text-primary) transition-colors"
            >
                <FaCircleInfo className="text-[11px]" />
            </button>
            {open && (
                <div
                    role="tooltip"
                    className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 rounded-lg bg-(--background-tertiary) border border-(--divider) shadow-xl text-[11px] font-normal normal-case text-(--text-secondary) text-left z-50"
                >
                    {text}
                </div>
            )}
        </div>
    );
}
