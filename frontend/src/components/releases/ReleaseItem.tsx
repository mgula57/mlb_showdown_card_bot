import type { ReactNode } from 'react';
import type { Release, ReleasePreviewImage } from '../../api/releases';
import { cardImagePublicUrl } from '../../api/supabase';
import { imageForSet } from '../shared/SiteSettingsContext';
import { FaLayerGroup } from 'react-icons/fa6';

/** Tile frame shared by ReleaseItem and its skeleton — sized like TeamPreviewCard's 'md' tile on
 *  wider screens, filling a 2-column grid cell on phones. */
const TILE_FRAME = 'w-full sm:w-52 aspect-3/4 rounded-xl';

/** Fan placement per image count: index 0 (first edition's highest-points card) sits in front. */
const FAN_LAYOUTS: Record<number, Array<{ x: number; y: number; rotate: number }>> = {
    1: [{ x: 0, y: 0, rotate: 0 }],
    2: [{ x: 28, y: 0, rotate: 6 }, { x: -28, y: 4, rotate: -6 }],
    3: [{ x: 0, y: 0, rotate: 0 }, { x: -58, y: 7, rotate: -10 }, { x: 58, y: 7, rotate: 10 }],
};

type ReleaseItemProps = {
    release: Release;
    onClick: () => void;
};

/** Release tile for the Release Builder list: a fan of the release's rendered card images over its
 *  name, default set, and edition/card counts. Falls back to a set icon when nothing is rendered yet. */
export function ReleaseItem({ release, onClick }: ReleaseItemProps) {
    const totalCards = release.editions.reduce((sum, e) => sum + e.card_count, 0);
    const editionCount = release.editions.length;
    const images = (release.preview_images ?? []).slice(0, 3);
    const setImage = release.default_showdown_set ? imageForSet(release.default_showdown_set) : undefined;

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
            {release.is_official && (
                <span className="absolute top-0 left-0 z-30 text-[9px] font-black rounded-br-md px-1.5 py-0.5 leading-none tracking-wide bg-(--secondary) text-(--background-primary)">
                    OFFICIAL
                </span>
            )}
            {setImage && (
                <div className="absolute top-0 right-0 z-30 rounded-bl-md p-1 bg-black/50">
                    <img src={setImage} alt={release.default_showdown_set ?? ''} loading="lazy" className="h-4 w-auto object-contain" />
                </div>
            )}

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
                <div className="text-[15px] leading-tight font-black text-(--text-primary) line-clamp-2">
                    {release.name}
                </div>
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
