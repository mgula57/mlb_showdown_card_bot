export function BetaBadge({ className }: { className?: string }) {
    return (
        <span className={`inline-flex items-center text-[9px] font-bold uppercase tracking-wide leading-none px-1.5 py-0.5 rounded-full border border-violet-500/30 bg-violet-500/15 text-violet-600 dark:text-violet-400 ${className ?? ''}`}>
            Beta
        </span>
    );
}
