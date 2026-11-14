/**
 * @fileoverview Loading state for the game screen: a skeleton of `GameStage`'s shell, the board
 * above the rail on a phone and beside it from `md` up, so the page keeps its shape while the
 * boxscore and cards load instead of popping in from a spinner.
 */
import BackButton from "../shared/BackButton";

/** One pulsing placeholder block. Lives inside an `animate-pulse` ancestor, so it doesn't animate
 * on its own — that keeps every block in a group in phase. */
function Bar({ className = "" }: { className?: string }) {
    return <div className={`rounded-plate bg-(--background-tertiary) ${className}`} />;
}

/** Stack of card-shaped rows — stands in for the play-by-play log. */
function CardRowsSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="animate-pulse space-y-3">
            {Array.from({ length: rows }, (_, i) => (
                <div key={i} className="flex items-start gap-3 rounded-card border border-(--divider)/50 bg-primary p-3">
                    <div className="grid grid-cols-1 @[500px]:grid-cols-2 gap-1 min-w-24 @[300px]:min-w-32">
                        <Bar className="h-11" />
                        <Bar className="h-11 hidden @[500px]:block" />
                    </div>
                    <div className="min-w-0 flex-1 space-y-2 pt-0.5">
                        <Bar className="h-4 w-20" />
                        <Bar className="h-3 w-full" />
                        <Bar className="h-3 w-2/3" />
                    </div>
                </div>
            ))}
        </div>
    );
}

export default function GameDetailSkeleton({ className, onBack }: { className?: string; onBack: () => void }) {
    return (
        <div className={`flex flex-col tall:h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
            <div className="relative z-50 px-4 py-2 border-b border-(--divider) bg-(--background-primary) shrink-0 flex items-center gap-3">
                <BackButton onBack={onBack} />
                <div className="ml-auto flex items-center gap-2 animate-pulse">
                    <Bar className="h-7 w-20 rounded-card" />
                    <Bar className="h-7 w-24 rounded-card" />
                </div>
            </div>

            <div className="flex min-h-0 flex-1 flex-col short:flex-none short:h-[calc(100dvh-2.5rem)] md:flex-row">
                {/* The board: score track, field, and the two cards along the bottom. */}
                <div className="flex h-96 shrink-0 animate-pulse flex-col gap-3 bg-(--background-secondary) p-3 md:h-auto md:min-w-0 md:flex-1">
                    <Bar className="h-14 w-full rounded-card" />
                    <div className="min-h-0 flex-1 rounded-card bg-(--background-tertiary)" />
                    <div className="grid shrink-0 grid-cols-2 gap-3">
                        <Bar className="h-20 rounded-card md:h-32" />
                        <Bar className="h-20 rounded-card md:h-32" />
                    </div>
                </div>

                {/* The rail: its tabs over the play-by-play. */}
                <div className="flex min-h-0 min-w-0 flex-1 flex-col border-t border-(--divider) md:w-80 md:flex-none md:border-l md:border-t-0 xl:w-90">
                    <div className="flex shrink-0 gap-2 p-2 animate-pulse">
                        <Bar className="h-8 flex-1 rounded-card" />
                        <Bar className="h-8 flex-1 rounded-card" />
                        <Bar className="h-8 flex-1 rounded-card" />
                    </div>
                    <div className="@container min-h-0 flex-1 overflow-hidden p-4">
                        <CardRowsSkeleton />
                    </div>
                </div>
            </div>
        </div>
    );
}
