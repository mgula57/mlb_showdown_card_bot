/**
 * @fileoverview Class-string builder for the app's buttons and button-styled links (see
 * frontend/DESIGN.md). `feature` is the one headline action on a screen (navy with a hard red
 * edge, label in the display face), `primary` the navy action with the hard raised edge,
 * `secondary` the bordered surface button, `ghost` a quiet text button, `danger` a destructive
 * confirm. Kept component-free so it works on `<button>`, `<Link>` and `<a>` alike.
 */
export type ButtonVariant = 'feature' | 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

// design-ok-start: these are the button primitives the custom-button rule points to
const VARIANT_CLASSES: Record<ButtonVariant, string> = {
    feature: 'bg-(--showdown-blue-fill) text-white shadow-feature hover:brightness-110 active:translate-y-0.5 active:shadow-none font-display uppercase leading-none',
    primary: 'bg-(--showdown-blue-fill) text-white shadow-raised hover:brightness-110 active:translate-y-px active:shadow-none',
    secondary: 'bg-(--background-secondary) text-(--text-primary) border border-(--rule-strong) hover:bg-(--background-tertiary)',
    ghost: 'text-(--text-secondary) hover:bg-(--background-tertiary) hover:text-(--text-primary)',
    danger: 'bg-(--showdown-red-fill) text-white shadow-raised hover:brightness-110 active:translate-y-px active:shadow-none',
};
// design-ok-end

const SIZE_CLASSES: Record<ButtonSize, string> = {
    sm: 'px-3 py-1.5 text-[13px]',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-3 text-base',
};

/** The display face runs small next to body text, so `feature` labels step up a size. */
const FEATURE_SIZE_CLASSES: Record<ButtonSize, string> = {
    sm: 'px-3 py-2 text-[15px]',
    md: 'px-4 py-2.5 text-[17px]',
    lg: 'px-5 py-3 text-[22px]',
};

/** Just a variant's colors, edge and states, for buttons that size themselves (a top-bar button,
 *  an icon overlay on a card). Pair with `rounded-control` and the caller's own padding. */
export function buttonVariantClass(variant: ButtonVariant): string {
    return `transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]}`;
}

export function buttonClass(variant: ButtonVariant = 'secondary', size: ButtonSize = 'md', className = ''): string {
    const sizeClass = variant === 'feature' ? FEATURE_SIZE_CLASSES[size] : `${SIZE_CLASSES[size]} font-semibold`;
    return `inline-flex items-center justify-center gap-2 shrink-0 rounded-control transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${sizeClass} ${VARIANT_CLASSES[variant]} ${className}`;
}
