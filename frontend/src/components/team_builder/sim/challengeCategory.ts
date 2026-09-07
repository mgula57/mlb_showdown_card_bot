import type { ReactNode } from 'react';
import { createElement } from 'react';
import { FaCrown, FaSackDollar, FaPalette } from 'react-icons/fa6';
import type { ChallengeCategory } from '../../../api/sim';

type CategoryMeta = {
    label: string;
    /** CSS custom property name (defined in index.css, light + dark). Use via
     *  `style={{ color: \`var(${cssVar})\` }}` — the value can't be a static Tailwind class
     *  because the category isn't known at build time. */
    cssVar: string;
    icon: ReactNode;
    /** Display order so a week's challenges read as "one of each". */
    order: number;
};

const META: Record<ChallengeCategory, CategoryMeta> = {
    legendary: { label: 'Legendary', cssVar: '--challenge-legendary', icon: createElement(FaCrown), order: 0 },
    budget_cap: { label: 'Budget Cap', cssVar: '--challenge-budget', icon: createElement(FaSackDollar), order: 1 },
    themed: { label: 'Themed', cssVar: '--challenge-themed', icon: createElement(FaPalette), order: 2 },
};

const FALLBACK: CategoryMeta = META.themed;

export function challengeCategoryMeta(category: ChallengeCategory | null | undefined): CategoryMeta {
    return (category && META[category]) || FALLBACK;
}

/** Sort comparator for challenge cards — legendary, then budget cap, then themed. */
export function byChallengeCategory<T extends { category?: ChallengeCategory | null }>(a: T, b: T): number {
    return challengeCategoryMeta(a.category).order - challengeCategoryMeta(b.category).order;
}
