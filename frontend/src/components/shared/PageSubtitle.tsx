import type { ReactNode } from 'react';

const SIZE_CLASSES = { sm: 'text-[12px]', md: 'text-[13px]' } as const;

type PageSubtitleProps = {
    children: ReactNode;
    /** `sm` for a count or short note under the title, `md` for a one-line description. */
    size?: keyof typeof SIZE_CLASSES;
    className?: string;
};

/** The line under a `Heading level="page"` (see frontend/DESIGN.md, "Type"). Tight leading, so a
 *  description that wraps on a phone reads as one block under the title. */
export function PageSubtitle({ children, size = 'md', className = '' }: PageSubtitleProps) {
    return <p className={`${SIZE_CLASSES[size]} leading-tight text-(--text-secondary) ${className}`}>{children}</p>;
}

export default PageSubtitle;
