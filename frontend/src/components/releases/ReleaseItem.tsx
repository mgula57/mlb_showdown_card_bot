import type { ReactNode } from 'react';
import type { Release, ReleasePreviewImage } from '../../api/releases';
import { cardImagePublicUrl } from '../../api/supabase';
import { ShowdownSetLogos } from '../shared/ShowdownSetLogos';
import { FaLayerGroup } from 'react-icons/fa6';

/** Tile frame shared by ReleaseItem and its skeleton — sized like TeamPreviewCard's 'md' tile on
 *  wider screens, filling a 2-column grid cell on phones. */
const TILE_FRAME = 'w-full sm:w-52 aspect-3/4 rounded-xl';

/** Fan placement per image count: index 0 (first edition's highest-points card) sits in front. */
const FAN_LAYOUTS: Record<number, Array<{ x: number; y: number; rotate: number }>> = {
    1: [{ x: 0, y: 12, rotate: 0 }],
    2: [{ x: 28, y: 12, rotate: 6 }, { x: -28, y: 20, rotate: -6 }],
    3: [{ x: 0, y: 12, rotate: 0 }, { x: -58, y: 20, rotate: -10 }, { x: 58, y: 20, rotate: 10 }],
};

type ReleaseItemProps = {
    release: Release;
    onClick: () => void;
};

/** Release tile for the Release Builder list: a fan of the release's rendered card images under the
 *  logos of every set it includes, over its name, creator, and edition/card counts. Falls back to a
 *  set icon when nothing is rendered yet. */
export function ReleaseItem({ release, onClick }: ReleaseItemProps) {
    const totalCards = release.editions.reduce((sum, e) => sum + e.card_count, 0);
    const editionCount = release.editions.length;
    const images = (release.preview_images ?? []).slice(0, 3);
    // Sets actually in the release's cards; before any cards are added, the default set it was created with
    const sets = release.showdown_sets?.length ? release.showdown_sets : [release.default_showdown_set];

    return (
        <button
            type="button"
            onClick={onClick}
            className={`
                ${TILE_FRAME} relative overflow-hidden flex flex-col text-left
                border-2 border-(--divider) bg-(--background-secondary)
                [@media(hover:hover)]:hover:scale-[1.025] [@media(hover:hover)]:active:scale-[0.975]
                [@media(hover:hover)]:transition-transform [@media(hover:hover)]:duration-150
                cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1
            `}
        >
            {/* Official badge + every included set, wrapping onto a second row when there are many */}
            <div className="absolute top-0 inset-x-0 z-30 flex items-start justify-between gap-1 pointer-events-none">
                {release.is_official ? (
                    <span className="shrink-0 text-[9px] font-black rounded-br-md px-1.5 py-0.5 leading-none tracking-wide bg-(--secondary) text-(--background-primary)">
                        OFFICIAL
                    </span>
                ) : <span />}
                <ShowdownSetLogos
                    sets={sets}
                    heightClass="h-5"
                    abbreviatedHeightClass="h-4"
                    className="flex flex-wrap items-center justify-end gap-1 rounded-bl-md p-1 bg-black/20"
                />
            </div>

            {/* Card fan */}
            <div className="relative flex-1 min-h-0">
                {images.length > 0 ? (
                    images.map((image, i) => (
                        <FannedCardImage key={image.thumbnail_path} image={image} placement={FAN_LAYOUTS[images.length][i]} zIndex={images.length - i} />
                    ))
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-(--text-tertiary)">
                        <FaLayerGroup className="text-5xl opacity-30" />
                    </div>
                )}
            </div>

            {/* Fade the bottom of the fan into the details */}
            <div
                aria-hidden
                className="absolute inset-0 z-10 pointer-events-none"
                style={{ background: 'linear-gradient(to top, var(--background-secondary) 30%, transparent 55%)' }}
            />

            {/* Details */}
            <div className="relative z-20 flex flex-col gap-1 p-2.5 pt-0">
                <div className="text-[18px] leading-[1.05] font-black uppercase tracking-tight text-(--text-primary) line-clamp-2">
                    {release.name}
                </div>
                {release.creator_username && (
                    <div className="text-[11px] font-semibold text-(--text-tertiary) truncate">
                        by {release.creator_username}
                    </div>
                )}
                {release.description && (
                    <div className="text-[10px] font-semibold text-(--text-secondary) line-clamp-1">
                        {release.description}
                    </div>
                )}
                <div className="flex items-center gap-1 flex-wrap text-[10px]">
                    <StatPill>{editionCount} edition{editionCount === 1 ? '' : 's'}</StatPill>
                    <StatPill>{totalCards} card{totalCards === 1 ? '' : 's'}</StatPill>
                </div>
            </div>
        </button>
    );
}

function FannedCardImage({ image, placement, zIndex }: { image: ReleasePreviewImage; placement: { x: number; y: number; rotate: number }; zIndex: number }) {
    return (
        <img
            src={cardImagePublicUrl(image.thumbnail_path)}
            alt={image.name ?? ''}
            loading="lazy"
            draggable={false}
            className="absolute left-1/2 top-[8%] w-[48%] h-auto select-none drop-shadow-lg"
            style={{
                zIndex,
                transform: `translateX(calc(-50% + ${placement.x}%)) translateY(${placement.y}%) rotate(${placement.rotate}deg)`,
            }}
        />
    );
}

function StatPill({ children }: { children: ReactNode }) {
    return (
        <span className="font-bold rounded px-1.5 py-0.5 leading-none bg-(--background-tertiary) text-(--text-secondary)">
            {children}
        </span>
    );
}

/** Loading placeholder sized to match ReleaseItem. */
export function ReleaseItemSkeleton() {
    return <div aria-hidden className={`${TILE_FRAME} bg-(--background-secondary) animate-pulse`} />;
}

export default ReleaseItem;
