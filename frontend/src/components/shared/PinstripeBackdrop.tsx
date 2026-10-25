/**
 * Card-back pinstripes behind the top of a page, fading out as the page scrolls into content
 * (see frontend/DESIGN.md). Render it inside a `relative isolate` page container; it sits behind
 * the page's content and above the container's own background.
 */
export function PinstripeBackdrop({ heightClass = 'h-[720px]' }: { heightClass?: string }) {
    return (
        <div
            aria-hidden
            className={`
                pointer-events-none absolute inset-x-0 top-0 -z-10 ${heightClass}
                bg-pinstripe
                mask-[linear-gradient(to_bottom,black_40%,transparent)]
            `}
        />
    );
}

export default PinstripeBackdrop;
