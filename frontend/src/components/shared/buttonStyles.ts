/**
 * @fileoverview Class-string builder for the app's buttons and button-styled links (see
 * frontend/DESIGN.md). `primary` is the navy action with the hard raised edge, `secondary` the
 * bordered surface button, `ghost` a quiet text button, `danger` a destructive confirm. Kept
 * component-free so it works on `<button>`, `<Link>` and `<a>` alike.
 */
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md';

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
    primary: 'bg-(--showdown-blue) text-white shadow-raised hover:brightness-110 active:translate-y-px active:shadow-none',
    secondary: 'bg-(--background-secondary) text-(--text-primary) border border-(--rule-strong) hover:bg-(--background-tertiary)',
    ghost: 'text-(--text-secondary) hover:bg-(--background-tertiary) hover:text-(--text-primary)',
    danger: 'bg-(--showdown-red) text-white shadow-raised hover:brightness-110 active:translate-y-px active:shadow-none',
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
    sm: 'px-3 py-1.5 text-[13px]',
    md: 'px-4 py-2 text-sm',
};

export function buttonClass(variant: ButtonVariant = 'secondary', size: ButtonSize = 'md', className = ''): string {
    return `inline-flex items-center justify-center gap-2 shrink-0 rounded-control font-semibold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${SIZE_CLASSES[size]} ${VARIANT_CLASSES[variant]} ${className}`;
}
