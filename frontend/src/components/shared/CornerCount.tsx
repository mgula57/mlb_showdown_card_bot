/**
 * A small navy count plate pinned to a button's top-right corner (active filters, new sims).
 * The parent must be `relative`. Renders nothing for 0 and caps at 99+.
 */
export function CornerCount({ count }: { count: number }) {
    if (count <= 0) return null;
    return (
        <span className="absolute -top-1.5 -right-1.5 min-w-4 h-4 px-1 flex items-center justify-center rounded-plate bg-(--showdown-blue) text-white text-[10px] font-semibold leading-none tabular-nums pointer-events-none">
            {count > 99 ? '99+' : count}
        </span>
    );
}

export default CornerCount;
