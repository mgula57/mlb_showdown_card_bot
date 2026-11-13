import { createPortal } from 'react-dom';
import { FaXmark } from 'react-icons/fa6';
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock';
import { UnderToolbarFill } from './UnderToolbarFill';

type ImageLightboxProps = {
    src: string;
    alt?: string;
    onClose: () => void;
};

/** Full-screen view of a single image (e.g. a card) over a dark scrim. Click anywhere outside the image to close. */
export function ImageLightbox({ src, alt = 'Card full view', onClose }: ImageLightboxProps) {
    useBodyScrollLock(true);
    return createPortal(
        <>
            <div
                className="fixed top-0 left-0 w-screen h-lvh z-9999 flex items-center justify-center bg-black/80"
                onClick={onClose}
            >
                <button
                    type="button"
                    aria-label="Close"
                    className="absolute top-4 right-4 text-white/70 hover:text-white transition-colors text-xl cursor-pointer"
                    onClick={onClose}
                >
                    <FaXmark />
                </button>
                <img
                    src={src}
                    alt={alt}
                    className="max-h-[90vh] max-w-[90vw] object-contain rounded-trading-card shadow-overlay"
                    onClick={(e) => e.stopPropagation()}
                />
            </div>
            <UnderToolbarFill zIndex={9999} className="left-0 w-full bg-black/80" />
        </>,
        document.body,
    );
}
