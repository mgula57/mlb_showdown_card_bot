/**
 * @fileoverview The strip above the pool grid while an unsaved preview is showing (an Algorithm run,
 * foil suggestions): a title in the preview accent, a "not saved yet" line, and the actions to keep it.
 */

import type { ReactNode } from 'react';
import { FaWandMagicSparkles } from 'react-icons/fa6';
import { headingClass } from '../shared/headingStyles';

type PoolPreviewBannerProps = {
    title: ReactNode;
    description: ReactNode;
    children: ReactNode;
};

export function PoolPreviewBanner({ title, description, children }: PoolPreviewBannerProps) {
    return (
        <div className="flex flex-col gap-2 px-3 py-2.5 border-b border-(--preview-accent)/30 bg-(--preview-accent)/10 shrink-0">
            <div className="flex flex-col gap-0.5">
                <div className={`flex items-center gap-1.5 ${headingClass('panel')} text-(--preview-accent)!`}>
                    <FaWandMagicSparkles />
                    {title}
                </div>
                <span className="text-[11px] text-(--text-secondary)">{description}</span>
            </div>
            {children}
        </div>
    );
}
