/**
 * @fileoverview Home's season band: a bordered block whose header is a navy band over a red rule
 * (from the Showdown logo) with a title, a short meta line and a link out. Today's Games uses it
 * during the season and Hot Stove in the offseason, in the same spot under the hero.
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { FaChevronRight } from 'react-icons/fa';

import { Heading } from '../shared/Heading';

type HomeBandProps = {
    title: string;
    /** Sits before the title, e.g. the live dot. */
    icon?: ReactNode;
    meta?: ReactNode;
    link: { label: string; to: string };
    children: ReactNode;
};

export function HomeBand({ title, icon, meta, link, children }: HomeBandProps) {
    return (
        <div className="rounded-card border border-(--divider) overflow-hidden max-w-7xl mx-auto bg-(--background-secondary)">
            <div className="flex items-center justify-between gap-4 px-4 md:px-6 py-2.5 bg-(--showdown-blue-fill) border-b-2 border-(--showdown-red)">
                <p className="flex items-center gap-2 text-white min-w-0">
                    {icon}
                    <Heading level="section" as="h2" className="whitespace-nowrap" style={{ color: 'white' }}>{title}</Heading>
                    {/* Meta gives way on a phone so the title and the link stay on one line */}
                    {meta && <span className="hidden sm:inline text-xs text-white/70 truncate">{meta}</span>}
                </p>
                <Link to={link.to} className="text-xs font-semibold text-white/80 hover:text-white flex items-center gap-1 shrink-0">
                    {link.label} <FaChevronRight className="text-[10px]" />
                </Link>
            </div>
            {children}
        </div>
    );
}

export default HomeBand;
