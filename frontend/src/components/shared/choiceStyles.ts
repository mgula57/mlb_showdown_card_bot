/**
 * @fileoverview Class-string builder for choice chips: a row of options where one (or several) is
 * picked, like the numbering mode, the algorithm templates or a filter preset (see
 * frontend/DESIGN.md). A bordered surface in the control corner; the picked option gets the
 * app-wide selection treatment, a navy outline, rather than an inverted fill, so it never reads
 * as a primary button. Kept component-free so it works on any `<button>`.
 */
export type ChoiceSize = 'sm' | 'md';

const SIZE_CLASSES: Record<ChoiceSize, string> = {
    sm: 'min-h-8 px-2.5 py-1 text-[12px]',
    md: 'min-h-9 px-3 py-2 text-[13px]',
};

export function choiceClass(selected: boolean, size: ChoiceSize = 'md', className = ''): string {
    return `inline-flex items-center justify-center gap-1.5 shrink-0 whitespace-nowrap rounded-control border bg-(--background-secondary) transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${SIZE_CLASSES[size]} ${
        selected
            ? 'border-(--showdown-blue) ring-1 ring-(--showdown-blue) text-(--text-primary) font-semibold'
            : 'border-(--divider) text-(--text-secondary) font-medium hover:border-(--rule-strong) hover:text-(--text-primary)'
    } ${className}`;
}
