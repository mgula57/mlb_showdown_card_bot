/**
 * @fileoverview Loading state for `GameDetail` — a skeleton of the real three-state shell (mobile
 * tab strip, `md` 50/50 split, `lg` three columns) so the page keeps its shape while the boxscore
 * and cards load, then settles into place instead of popping in from a spinner.
 */
import BackButton from "../shared/BackButton";

/** One pulsing placeholder block. Lives inside an `animate-pulse` ancestor, so it doesn't animate
 * on its own — that keeps every block in a group in phase. */
function Bar({ className = "" }: { className?: string }) {
    return <div className={`rounded bg-(--background-quaternary) ${className}`} />;
}

/** Scoreboard placeholder — two team rows and a state line, matching `ScoreHeader`. */
function ScoreHeaderSkeleton() {
    return (
        <div className="animate-pulse rounded-xl border border-(--divider) bg-(--background-secondary) p-4 space-y-3">
            {[0, 1].map((i) => (
                <div key={i} className="flex items-center gap-3">
                    <Bar className="h-7 w-7 rounded-full" />
                    <Bar className="h-4 flex-1 max-w-40" />
                    <Bar className="h-6 w-8" />
                </div>
            ))}
            <Bar className="h-3 w-24 mx-auto" />
        </div>
    );
}

/** Stack of card-shaped rows — stands in for the play-by-play log and the matchup cards. */
function CardRowsSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="animate-pulse space-y-3">
            {Array.from({ length: rows }, (_, i) => (
                <div key={i} className="flex items-start gap-3 rounded-xl border border-(--divider)/50 bg-primary p-3">
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

/** Box score placeholder — a couple of stat tables' worth of rows. */
function BoxScoreSkeleton() {
    return (
        <div className="animate-pulse space-y-4">
            <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3 space-y-2">
                <Bar className="h-4 w-32" />
                {Array.from({ length: 9 }, (_, i) => <Bar key={i} className="h-3 w-full" />)}
            </div>
            <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3 space-y-2">
                <Bar className="h-4 w-24" />
                {Array.from({ length: 4 }, (_, i) => <Bar key={i} className="h-3 w-full" />)}
            </div>
        </div>
    );
}

export default function GameDetailSkeleton({ className, onBack }: { className?: string; onBack: () => void }) {
    return (
        <div className={`flex flex-col md:h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
            <div className="relative z-50 px-4 py-2 border-b border-(--divider) bg-(--background-primary) shrink-0 flex items-center gap-3">
                <BackButton onBack={onBack} />
                <div className="ml-auto flex items-center gap-2 animate-pulse">
                    <Bar className="h-7 w-20 rounded-lg" />
                    <Bar className="h-7 w-24 rounded-lg" />
                </div>
            </div>

            {/* Mobile tab strip placeholder — mirrors `MOBILE_TABS`. */}
            <div className="flex md:hidden shrink-0 px-2 py-2 gap-2 animate-pulse">
                <Bar className="h-8 flex-1 rounded-lg" />
                <Bar className="h-8 flex-1 rounded-lg" />
                <Bar className="h-8 flex-1 rounded-lg" />
            </div>

            <div className="flex-1 min-h-0 md:grid md:grid-cols-2 md:gap-4 md:px-4 md:overflow-hidden lg:grid-cols-[3fr_4fr_3fr]">
                {/* Box score column — its own column only at `lg`. */}
                <div className="hidden lg:block lg:order-1 h-full overflow-y-auto py-4 scrollbar-hide">
                    <BoxScoreSkeleton />
                </div>

                {/* Spotlight column — scoreboard, field, matchup. */}
                <div className="h-full overflow-y-auto space-y-4 p-4 md:px-0 md:py-4 scrollbar-hide md:order-1 lg:order-2">
                    <ScoreHeaderSkeleton />
                    <div className="animate-pulse rounded-xl border border-(--divider) bg-(--background-secondary) aspect-4/3 w-full" />
                    <div className="@container">
                        <CardRowsSkeleton rows={1} />
                    </div>
                </div>

                {/* Box score + play-by-play — flow with the mobile strip below `md`, a column with
                    its own strip between `md` and `lg`, back to the outer grid at `lg`. */}
                <div className="contents md:flex md:flex-col md:order-2 md:min-h-0 md:overflow-hidden lg:contents">
                    <div className="hidden md:flex lg:hidden shrink-0 pt-4 gap-2 animate-pulse">
                        <Bar className="h-8 flex-1 rounded-lg" />
                        <Bar className="h-8 flex-1 rounded-lg" />
                    </div>
                    <div className="h-full min-w-0 overflow-y-auto p-4 md:px-0 md:py-4 md:h-auto md:flex-1 md:min-h-0 scrollbar-hide @container lg:order-3">
                        <CardRowsSkeleton />
                    </div>
                </div>
            </div>
        </div>
    );
}
