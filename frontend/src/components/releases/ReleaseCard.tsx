import type { Release } from '../../api/releases';
import { FaLayerGroup } from 'react-icons/fa6';

type ReleaseCardProps = {
    release: Release;
    onClick?: () => void;
};

export function ReleaseCard({ release, onClick }: ReleaseCardProps) {
    const totalCards = release.editions.reduce((sum, e) => sum + e.card_count, 0);

    return (
        <button
            type="button"
            onClick={onClick}
            className={`
                relative w-full text-left flex items-center gap-3
                rounded-lg px-3 py-2 border-2 border-(--divider)
                ${onClick ? 'cursor-pointer hover:opacity-90' : 'cursor-default'}
                transition-opacity
            `}
        >
            <div className="shrink-0 w-10 h-10 rounded-md flex items-center justify-center bg-(--background-tertiary) text-(--text-secondary)">
                <FaLayerGroup className="text-[16px]" />
            </div>

            <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                    <span className="text-[13px] font-bold text-(--text-primary) truncate">
                        {release.name}
                    </span>
                    {release.is_official && (
                        <span className="text-[9px] font-black rounded px-1 py-0.5 leading-none bg-(--secondary) text-(--background-primary)">
                            OFFICIAL
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                    {release.description && (
                        <span className="text-[11px] text-(--text-secondary) truncate">
                            {release.description}
                        </span>
                    )}
                    {release.editions.length > 0 && (
                        <span className="text-[10px] text-(--text-tertiary) shrink-0">
                            {release.editions.length} edition{release.editions.length === 1 ? '' : 's'} · {totalCards} card{totalCards === 1 ? '' : 's'}
                        </span>
                    )}
                </div>
            </div>
        </button>
    );
}
