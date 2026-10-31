import { useState, type ImgHTMLAttributes, type SyntheticEvent } from 'react';

/** Printable border around a bordered render (`Set.card_border_padding`), and the card inside it. */
const CARD_BORDER_PX = 72;
const CARD_SIZE_PX = { width: 1500, height: 2100 };

/** Transparent image with the card's aspect ratio, so a wrapper holding only a cropped image sizes
 * like a plain card image. */
const CARD_ASPECT_SIZER_SRC = `data:image/svg+xml;utf8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="${CARD_SIZE_PX.width}" height="${CARD_SIZE_PX.height}"/>`)}`;

// A card with its border is wider (and relatively less tall) than the 5:7 card alone, so the aspect
// ratio tells them apart; the cutoff sits between the two.
const PLAIN_ASPECT = CARD_SIZE_PX.width / CARD_SIZE_PX.height;
const BORDERED_ASPECT = (CARD_SIZE_PX.width + 2 * CARD_BORDER_PX) / (CARD_SIZE_PX.height + 2 * CARD_BORDER_PX);
const isBorderedAspect = (width: number, height: number) =>
    height > 0 && width / height > (PLAIN_ASPECT + BORDERED_ASPECT) / 2;

/** Sizes and offsets an absolutely positioned image so its border falls outside the parent. */
const BORDER_CROP_STYLE = {
    width: `${(1 + 2 * CARD_BORDER_PX / CARD_SIZE_PX.width) * 100}%`,
    left: `${-CARD_BORDER_PX / CARD_SIZE_PX.width * 100}%`,
    top: `${-CARD_BORDER_PX / CARD_SIZE_PX.height * 100}%`,
} as const;

type BorderCroppedImageProps = Omit<ImgHTMLAttributes<HTMLImageElement>, 'style'> & {
    /** Whether the image includes the border. Detected from the loaded image when omitted. */
    isBordered?: boolean;
};

/**
 * A card image that hides the printable border of bordered renders, showing just the 1500x2100 card.
 * The parent must be `relative overflow-hidden` with the card's 5:7 aspect ratio. `className` styles
 * the plain (unbordered) image; a bordered one is positioned by the crop instead.
 */
export function BorderCroppedImage({ isBordered, className = '', onLoad, ...props }: BorderCroppedImageProps) {
    const [detected, setDetected] = useState(false);
    const cropped = isBordered ?? detected;

    function handleLoad(event: SyntheticEvent<HTMLImageElement>) {
        const { naturalWidth, naturalHeight } = event.currentTarget;
        setDetected(isBorderedAspect(naturalWidth, naturalHeight));
        onLoad?.(event);
    }

    return (
        <img
            {...props}
            onLoad={handleLoad}
            className={cropped ? 'absolute max-w-none' : className}
            style={cropped ? BORDER_CROP_STYLE : undefined}
        />
    );
}

/** Gives a wrapper holding only a cropped image the size of a plain card image (see `BorderCroppedImage`). */
export const CardAspectSizer = ({ className = '' }: { className?: string }) => (
    <img src={CARD_ASPECT_SIZER_SRC} alt="" aria-hidden className={className} />
);
