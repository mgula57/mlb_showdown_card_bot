import type { FaceoffSide, FaceoffSummary } from '../../../api/faceoff';
import { relativeTime } from '../../../functions/formatters';

type Props = {
    faceoff: FaceoffSummary;
    onOpen: () => void;
};

function TeamLine({ name, color, isWinner }: { name: string; color?: string | null; isWinner: boolean }) {
    return (
        <span className="flex min-w-0 items-center gap-1.5">
            <span className="w-1.5 h-3 rounded-full shrink-0" style={{ backgroundColor: color ?? 'var(--divider)' }} />
            <span className={`truncate text-[13px] ${isWinner ? 'font-bold text-(--text-primary)' : 'text-(--text-secondary)'}`}>{name}</span>
        </span>
    );
}

/** One Faceoff as a clickable row. A single game reads as its score, a series as its wins. */
export function FaceoffRow({ faceoff, onOpen }: Props) {
    const isSeries = faceoff.best_of > 1;
    const game = faceoff.game_scores[0];
    const score = (side: FaceoffSide) => {
        if (isSeries) return side === 'challenger' ? faceoff.challenger_wins : faceoff.opponent_wins;
        return side === 'challenger' ? game?.challenger_score : game?.opponent_score;
    };
    return (
        <button
            type="button"
            onClick={onOpen}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-control text-left bg-(--background-tertiary) cursor-pointer hover:bg-(--divider) transition-colors"
        >
            <span className="min-w-0 flex-1 space-y-0.5">
                <TeamLine name={faceoff.challenger_identity.name} color={faceoff.challenger_identity.primary_color} isWinner={faceoff.winner_side === 'challenger'} />
                <TeamLine name={faceoff.opponent_identity.name} color={faceoff.opponent_identity.primary_color} isWinner={faceoff.winner_side === 'opponent'} />
            </span>
            <span className="text-right shrink-0">
                <span className="block font-display-upright text-[17px] leading-none text-(--text-primary) tabular-nums">
                    {score('challenger')}<span className="text-(--text-tertiary)">–</span>{score('opponent')}
                </span>
                <span className="block text-[11px] text-(--text-tertiary)">{relativeTime(faceoff.created_at)}</span>
            </span>
        </button>
    );
}
