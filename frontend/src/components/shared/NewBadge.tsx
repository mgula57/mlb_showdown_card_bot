export function NewBadge({ className }: { className?: string }) {
    return (
        <span className={`inline-flex items-center text-[9px] font-bold uppercase tracking-wide leading-none px-1.5 py-0.5 rounded-full border border-amber-500/30 bg-amber-500/15 text-amber-600 dark:text-amber-400 ${className ?? ''}`}>
            New
        </span>
    );
}
