import { useState } from "react";
import type { CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { cardImagePublicUrl } from "../../api/supabase";
import { getLastName } from "../../functions/names";
import { getContrastTextColor, NEUTRAL_TEAM_COLOR } from "../../functions/colors";
import { SetBadge } from "../shared/SetBadge";
import { CardActionButton } from "./CardItem";
import type { CardItemActionButton } from "./CardItemCompact";
import PointsBadge from "./card_elements/PointsBadge";

type CardThumbnailProps = {
    /** Rendered card image (thumbnail preferred). Falls back to a team-color placeholder when missing or broken. */
    imageUrl?: string | null;
    name?: string;
    points?: number;
    team?: string;
    showdownSet?: string;
    primaryColor?: string | null;
    secondaryColor?: string | null;

    onClick?: () => void;
    className?: string;
    isSelected?: boolean;
    /** Same corner actions as `CardItem` */
    actionButton?: CardItemActionButton;
    secondaryActionButton?: CardItemActionButton;
};

/**
 * CardThumbnail - image-first alternative to `CardItem` for card grids. Shows the card's rendered
 * image with a bottom banner (last name + points) laid over it, and the same corner action buttons.
 */
export const CardThumbnail = ({
    imageUrl, name, points, team, showdownSet, primaryColor, secondaryColor,
    onClick, className, isSelected, actionButton, secondaryActionButton,
}: CardThumbnailProps) => {
    // Track which URL failed so a recycled grid cell with a new card retries its image
    const [failedUrl, setFailedUrl] = useState<string | null>(null);
    const showImage = !!imageUrl && failedUrl !== imageUrl;

    const bannerColor = primaryColor || NEUTRAL_TEAM_COLOR;
    const isClickable = onClick !== undefined;
    // Same frame as CardItem: neutral hairline; selection is a navy outline (see frontend/DESIGN.md)
    const borderSettings = isSelected
        ? 'border-(--showdown-blue) ring-1 ring-(--showdown-blue)'
        : `border-(--divider)${isClickable ? ' hover:border-(--rule-strong)' : ''}`;

    return (
        <div className={`${className ?? ''} relative ${actionButton?.variant === 'prominent' || secondaryActionButton?.variant === 'prominent' ? '@container' : ''}`}>
            {actionButton && <CardActionButton action={actionButton} />}
            {secondaryActionButton && <CardActionButton action={secondaryActionButton} />}
            <div
                className={`
                    relative aspect-[5/7] overflow-hidden
                    rounded-trading-card border bg-secondary
                    ${isClickable ? 'cursor-pointer' : ''}
                    ${borderSettings}
                `}
                onClick={onClick}
            >
                {showImage ? (
                    <img
                        src={imageUrl!}
                        alt={name ?? 'Card'}
                        loading="lazy"
                        className="absolute inset-0 w-full h-full object-cover"
                        onError={() => setFailedUrl(imageUrl!)}
                    />
                ) : (
                    // No rendered image yet - team-color tile with the set badge
                    <div
                        className="absolute inset-0 flex items-center justify-center"
                        style={{ background: `linear-gradient(160deg, ${bannerColor}, ${secondaryColor || bannerColor})` }}
                    >
                        <SetBadge set={showdownSet || '2005'} size="lg" onField className="opacity-60" />
                    </div>
                )}

                {/* Bottom banner: last name + points */}
                <div
                    className="absolute bottom-0 inset-x-0 flex items-center justify-between gap-1 px-2 py-1"
                    style={{ backgroundColor: bannerColor, color: getContrastTextColor(bannerColor) }}
                    title={team ? `${name} (${team})` : name}
                >
                    <span className="font-bold text-xs truncate">{getLastName(name).toUpperCase()}</span>
                    {points != null && <PointsBadge points={points} bg_color={secondaryColor} className="shrink-0" />}
                </div>
            </div>
        </div>
    );
};

type CardThumbnailFromCardDatabaseRecordProps = Omit<CardThumbnailProps, 'imageUrl' | 'name' | 'points' | 'team' | 'showdownSet' | 'primaryColor' | 'secondaryColor'> & {
    card: CardDatabaseRecord;
};

/** Thumbnail for a release card record - prefers the 200px thumbnail, then the full render. */
export const CardThumbnailFromCardDatabaseRecord = ({ card, ...props }: CardThumbnailFromCardDatabaseRecordProps) => {
    const imagePath = card.release_thumbnail_path || card.release_image_path;
    return (
        <CardThumbnail
            imageUrl={imagePath ? cardImagePublicUrl(imagePath) : null}
            name={card.name}
            points={card.points}
            team={card.wbc_team || card.team}
            showdownSet={card.showdown_set}
            primaryColor={card.color_primary}
            secondaryColor={card.color_secondary}
            {...props}
        />
    );
};

export function CardThumbnailSkeleton({ className }: { className?: string }) {
    return (
        <div className={`${className ?? ''} relative aspect-[5/7] rounded-trading-card border border-(--divider) bg-(--background-tertiary)/40 animate-pulse overflow-hidden`}>
            <div className="absolute bottom-0 inset-x-0 h-7 bg-(--background-tertiary)" />
        </div>
    );
}
