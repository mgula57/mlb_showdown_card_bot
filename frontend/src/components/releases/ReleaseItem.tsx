import type { CSSProperties } from 'react';
import type { Release, ReleasePreviewImage } from '../../api/releases';
import { cardImagePublicUrl } from '../../api/supabase';
import { SetBadgeRow } from '../shared/SetBadge';
import { FaHeart, FaLayerGroup } from 'react-icons/fa6';
import { SLANT_ROOM_CLASS } from '../shared/headingStyles';
import { Plate } from '../shared/Plate';
import { FrameCorners } from '../shared/FrameCorners';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';

/** Tile frame shared by ReleaseItem and its skeleton — sized like TeamPreviewCard's 'md' tile on
 *  wider screens, filling a 2-column grid cell on phones. */
const TILE_FRAME = 'w-full sm:w-52 aspect-3/4 rounded-card';

/** Fan placement per image count: index 0 (first edition's highest-points card) sits in front. */
const FAN_LAYOUTS: Record<number, FanPlacement[]> = {
    1: [{ x: 0, y: 12, rotate: 0 }],
    2: [{ x: 28, y: 12, rotate: 6 }, { x: -28, y: 20, rotate: -6 }],
    3: [{ x: 0, y: 12, rotate: 0 }, { x: -58, y: 20, rotate: -10 }, { x: 58, y: 20, rotate: 10 }],
};

type FanPlacement = { x: number; y: number; rotate: number };

/** Hovering a tile fans its cards open a little: side cards spread and tilt further, every card
 *  lifts and grows slightly, and a lone card tips to one side. */
const FAN_HOVER = { spread: 1.18, tilt: 1.5, lift: 6, scale: 1.04, loneCardTilt: -3, staggerMs: 40 };

const fanTransform = ({ x, y, rotate }: FanPlacement, scale = 1): string =>
    `translateX(calc(-50% + ${x}%)) translateY(${y}%) rotate(${rotate}deg) scale(${scale})`;

function hoveredPlacement(placement: FanPlacement, cardCount: number): FanPlacement {
    return {
        x: placement.x * FAN_HOVER.spread,
        y: placement.y - FAN_HOVER.lift,
        rotate: cardCount === 1 ? FAN_HOVER.loneCardTilt : placement.rotate * FAN_HOVER.tilt,
    };
}

type ReleaseItemProps = {
    release: Release;
    /** Leave out for a display-only tile (e.g. the Review step's preview). */
    onClick?: () => void;
    /** Show the Draft/Published pill — only meaningful on the owner's own releases. */
    showPublishStatus?: boolean;
};

/** Release tile for the Release Builder list: a fan of the release's rendered card images under the
 *  logos of every set it includes, over its name, creator, and edition/card counts. With nothing
 *  rendered yet, a draft shows blank cards dealing into the fan and a published release a set icon. */
export function ReleaseItem({ release, onClick, showPublishStatus = false }: ReleaseItemProps) {
    const totalCards = release.editions.reduce((sum, e) => sum + e.card_count, 0);
    const editionCount = release.editions.length;
    // Matches the public list: a release is visible to others once any edition is published
    const isPublished = release.editions.some(e => e.is_published);
    const images = (release.preview_images ?? []).slice(0, 3);
    // Sets actually in the release's cards; before any cards are added, the default set it was created with
    const sets = release.showdown_sets?.length ? release.showdown_sets : [release.default_showdown_set];

    const Frame = onClick ? 'button' : 'div';
    return (
        <Frame
            {...(onClick ? { type: 'button' as const, onClick } : {})}
            className={`
                ${TILE_FRAME} group relative p-0.75 text-left
                border-2 border-(--rule-strong) bg-(--background-secondary)
                ${onClick ? `
                    [@media(hover:hover)]:hover:scale-[1.025] [@media(hover:hover)]:active:scale-[0.975]
                    [@media(hover:hover)]:transition-transform [@media(hover:hover)]:duration-150
                    cursor-pointer
                ` : ''}
            `}
        >
            {/* Double-rule frame from the 2001 card back: outer rule on the button, hairline here, bases on the corners */}
            <FrameCorners />
            <div className="relative h-full flex flex-col overflow-hidden rounded-plate border border-(--divider)">
                {/* Official plate + every included set, wrapping onto a second row when there are many */}
                <div className="absolute top-0.5 inset-x-0.5 z-1 flex items-start justify-between gap-1 pointer-events-none">
                    {release.is_official ? <Plate variant="navy" size="sm">Official</Plate> : <span />}
                    <SetBadgeRow
                        sets={sets}
                        className="flex flex-wrap items-center justify-end gap-1 p-0.5"
                    />
                </div>

                {/* Card fan on the silver card-back field */}
                <div className="relative flex-1 min-h-0 bg-(--background-tertiary) bg-pinstripe">
                    {images.length > 0 ? (
                        images.map((image, i) => (
                            <FannedCardImage key={image.thumbnail_path} image={image} index={i} cardCount={images.length} />
                        ))
                    ) : !isPublished ? (
                        <BuildingFan />
                    ) : (
                        <div className="absolute inset-0 flex items-center justify-center text-(--text-tertiary)">
                            <FaLayerGroup className="text-5xl opacity-30" />
                        </div>
                    )}
                </div>

                {/* Details */}
                <div className="relative z-20 flex flex-col gap-1 px-2 pt-2 pb-2 border-t border-(--divider) bg-(--background-secondary)">
                    <div className={`font-display text-[21px] leading-[0.95] uppercase text-(--text-primary) line-clamp-2 ${SLANT_ROOM_CLASS}`}>
                        {release.name}
                    </div>
                    {release.description && (
                        <div className="text-[10px] font-semibold text-(--text-secondary) line-clamp-1">
                            {release.description}
                        </div>
                    )}
                    <div className="flex items-center justify-between gap-1.5 min-w-0">
                        <span className="flex items-center gap-1 min-w-0 text-[11px] font-medium text-(--text-tertiary)">
                            <span className="truncate">{release.creator_username ? `by ${release.creator_username}` : ''}</span>
                            {release.like_count > 0 && (
                                <span className="flex items-center gap-0.5 shrink-0 tabular-nums" title={`${release.like_count} like${release.like_count === 1 ? '' : 's'}`}>
                                    <FaHeart className="text-[9px]" />{release.like_count}
                                </span>
                            )}
                        </span>
                        <span className="shrink-0 text-[11px] font-semibold tabular-nums text-(--text-tertiary)">
                            {editionCount} ed. · {totalCards} card{totalCards === 1 ? '' : 's'}
                        </span>
                    </div>
                    {showPublishStatus && (
                        <div className="flex flex-wrap gap-1">
                            <Plate variant={isPublished ? 'success' : 'outline'} size="sm">
                                {isPublished ? 'Published' : 'Draft'}
                            </Plate>
                            {isPublished && !release.is_listed && <Plate variant="outline" size="sm">Link only</Plate>}
                            {release.has_pending_changes && <Plate variant="outline" size="sm">Unpublished changes</Plate>}
                        </div>
                    )}
                </div>
            </div>
        </Frame>
    );
}

/** One card in the fan. Rest/hover transforms are passed as CSS variables so the tile's hover
 *  (`group-hover`) can animate between them; only on devices that hover, and not with reduced motion. */
function FannedCardImage({ image, index, cardCount }: { image: ReleasePreviewImage; index: number; cardCount: number }) {
    const placement = FAN_LAYOUTS[cardCount][index];
    const style = {
        zIndex: cardCount - index,
        '--fan-rest': fanTransform(placement),
        '--fan-hover': fanTransform(hoveredPlacement(placement, cardCount), FAN_HOVER.scale),
        transitionDelay: `${index * FAN_HOVER.staggerMs}ms`,
    } as CSSProperties;
    return (
        <img
            src={cardImagePublicUrl(image.thumbnail_path)}
            alt={image.name ?? ''}
            loading="lazy"
            draggable={false}
            className="
                absolute left-1/2 top-[10%] w-[48%] h-auto select-none drop-shadow-[0_2px_0_rgb(0_0_0/0.25)]
                transform-(--fan-rest) transition-transform duration-300 ease-out motion-reduce:transition-none
                [@media(hover:hover)]:motion-safe:group-hover:transform-(--fan-hover)
            "
            style={style}
        />
    );
}

/** Delay between each blank card dealing into the building fan. */
const BUILDING_DEAL_STAGGER_MS = 220;

/** Draft with no rendered images: blank cards deal into the 3-card fan back to front on a loop
 *  (`release-building-card` in index.css), the front one labeled "Building". */
function BuildingFan() {
    const layout = FAN_LAYOUTS[3];
    // Back cards first, the front card (index 0) last
    const dealOrder = [1, 2, 0];
    return (
        <>
            {dealOrder.map((index, turn) => (
                <div
                    key={index}
                    aria-hidden
                    className="
                        release-building-card absolute left-1/2 top-[10%] w-[48%] aspect-5/7 p-0.75
                        rounded-plate border border-(--rule-strong) bg-(--background-secondary)
                        drop-shadow-[0_2px_0_rgb(0_0_0/0.25)]
                    "
                    style={{
                        zIndex: layout.length - index,
                        '--fan-rest': fanTransform(layout[index]),
                        animationDelay: `${turn * BUILDING_DEAL_STAGGER_MS}ms`,
                    } as CSSProperties}
                >
                    <div className="h-full flex items-center justify-center rounded-plate border border-(--divider)">
                        {index === 0 && <span className={`text-(--text-tertiary) ${CAPS_LABEL_CLASS}`}>Building</span>}
                    </div>
                </div>
            ))}
        </>
    );
}

/** Loading placeholder sized to match ReleaseItem. */
export function ReleaseItemSkeleton() {
    return <div aria-hidden className={`${TILE_FRAME} border-2 border-(--divider) bg-(--background-tertiary) animate-pulse`} />;
}

export default ReleaseItem;
