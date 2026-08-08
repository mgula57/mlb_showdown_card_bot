import { useState } from 'react';
import { SimLeaderboard } from './SimLeaderboard';
import { SimHistory } from './SimHistory';

type View = 'leaderboard' | 'mine';

type Props = {
    token?: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
};

/**
 * Home for everything about played seasons: a global leaderboard and the signed-in user's own
 * history, switched by a segmented control so both live under one "Simulations" tab rather than
 * competing for a top-level slot each.
 */
export function SimulationsTab({ token, onOpenSeason }: Props) {
    const [view, setView] = useState<View>('leaderboard');

    return (
        <div className="flex flex-col gap-4">
            <div className="px-4">
                <div className="inline-flex gap-1 rounded-lg bg-(--background-tertiary) p-1">
                    {([
                        { id: 'leaderboard', label: 'Leaderboard' },
                        { id: 'mine', label: 'My Seasons' },
                    ] as const).map(tab => (
                        <button
                            key={tab.id}
                            type="button"
                            onClick={() => setView(tab.id)}
                            className={`px-3 py-1.5 text-[12px] font-semibold rounded-md whitespace-nowrap transition-colors cursor-pointer ${
                                view === tab.id
                                    ? 'bg-(--showdown-blue) text-white shadow-sm'
                                    : 'text-(--text-tertiary) hover:text-(--text-secondary)'
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {view === 'leaderboard' ? (
                <SimLeaderboard token={token} onOpenSeason={onOpenSeason} />
            ) : (
                <SimHistory token={token} onOpenSeason={onOpenSeason} />
            )}
        </div>
    );
}
