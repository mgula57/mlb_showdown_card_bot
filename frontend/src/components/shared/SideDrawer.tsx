import { useEffect, type ReactNode } from 'react';
import { FaXmark } from 'react-icons/fa6';
import { Heading } from './Heading';

type SideDrawerProps = {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    subtitle?: string;
    /** Pinned under the title, outside the scrolling body (e.g. a section switcher). */
    headerContent?: ReactNode;
    /** Pinned to the bottom edge, outside the scrolling body. */
    footer?: ReactNode;
    children: ReactNode;
};

/**
 * Desktop (lg+) reference panel docked to the right edge, under the app header. Non-modal: no
 * scrim and no scroll lock, so the page beside it stays usable while it's open. Escape or the X
 * closes it. Hidden below lg; pair it with `SlideOver` there.
 */
export function SideDrawer({ isOpen, onClose, title, subtitle, headerContent, footer, children }: SideDrawerProps) {
    useEffect(() => {
        if (!isOpen) return;
        const handleEscape = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose]);

    return (
        <aside
            aria-label={title}
            aria-hidden={!isOpen}
            inert={!isOpen}
            className={`
                hidden lg:flex flex-col fixed top-10 bottom-0 right-0 z-30 w-96
                bg-(--background-primary) border-l border-(--divider)
                transition-[translate,box-shadow] motion-reduce:duration-[1ms]
                ${isOpen
                    ? 'translate-x-0 shadow-overlay duration-300 ease-(--side-menu-ease)'
                    : 'translate-x-full shadow-none duration-200 ease-[cubic-bezier(0.32,0,0.67,0)]'}
            `}
        >
            <div className="flex flex-col gap-3 px-4 pt-3 pb-3 border-b border-(--divider) shrink-0">
                <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                        <Heading level="section" fit>{title}</Heading>
                        {subtitle && <p className="text-[12px] text-(--text-secondary) mt-0.5">{subtitle}</p>}
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close"
                        className="text-(--text-secondary) hover:text-(--text-primary) text-xl cursor-pointer"
                    >
                        <FaXmark />
                    </button>
                </div>
                {headerContent}
            </div>
            <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain">
                {children}
            </div>
            {footer && <div className="shrink-0 border-t border-(--divider) px-4 py-3">{footer}</div>}
        </aside>
    );
}
