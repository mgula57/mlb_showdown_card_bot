import type { ReactNode } from 'react';
import { Heading } from './Heading';

type SectionBandProps = {
    /** Background utility, e.g. `bg-(--background-secondary)`; alternate tones to tell neighboring bands apart. */
    tone: string;
    /** CSS variable name for the icon and its watermark, e.g. `--challenge-legendary`. */
    accent: string;
    icon: ReactNode;
    title: string;
    description: string;
    /** Horizontal page padding applied to the title and description. */
    horizontalPadding: string;
    children: ReactNode;
};

/** Full-bleed colored band around one section of a browse page, with a large title + description and a
 *  faint oversized icon watermark tied to the section's accent color. Breaks out to the true
 *  edge of the nearest `@container` ancestor (ignoring the page's centered max-width), then
 *  re-centers its content with the same max-width so it still lines up with the header/tabs. */
export function SectionBand({ tone, accent, icon, title, description, horizontalPadding, children }: SectionBandProps) {
    return (
        <div
            className={`relative overflow-hidden ${tone}`}
            style={{ marginLeft: 'calc((100% - 100cqw) / 2)', marginRight: 'calc((100% - 100cqw) / 2)' }}
        >
            <div
                aria-hidden
                className="pointer-events-none absolute -top-8 -right-8 text-[160px] leading-none opacity-[0.06] select-none"
                style={{ color: `var(${accent})` }}
            >
                {icon}
            </div>
            <div className="relative max-w-4xl lg:max-w-7xl mx-auto w-full flex flex-col gap-3 py-6">
                <div className={horizontalPadding}>
                    <div className="flex items-center gap-2">
                        <span className="text-[18px]" style={{ color: `var(${accent})` }}>{icon}</span>
                        <Heading level="section">{title}</Heading>
                    </div>
                    <p className="text-[12px] text-(--text-secondary) mt-0.5 max-w-2xl">{description}</p>
                </div>
                {children}
            </div>
        </div>
    );
}
