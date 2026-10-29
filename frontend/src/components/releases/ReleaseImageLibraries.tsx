import { useState, type ReactNode } from 'react';
import { FaGoogleDrive } from 'react-icons/fa';
import { FaXmark } from 'react-icons/fa6';
import { useImageLibraries } from '../account/useImageLibraries';
import { ImageLibrariesModal } from '../account/ImageLibrariesModal';
import ImageLibraryGuideLink from '../account/ImageLibraryGuideLink';
import { buttonClass } from '../shared/buttonStyles';
import { Heading } from '../shared/Heading';
import { ReleaseTip } from './ReleaseOnboarding';

/** Release card images search the owner's image libraries. True once loaded with no Drive folder connected. */
function useHasNoDriveLibrary(): boolean {
    const { token, overview } = useImageLibraries();
    return !!token && !!overview && overview.libraries.length === 0;
}

type ReleaseDriveNoticeProps = {
    /** Shown on the right, ex: a Connect button. */
    action?: ReactNode;
    onDismiss?: () => void;
    /** Extra line under the explanation. */
    footnote?: ReactNode;
    className?: string;
};

/** Explains that a release's player images come from the owner's Google Drive. Renders nothing
 * once a Drive folder is connected (or while libraries load). */
export function ReleaseDriveNotice({ action, onDismiss, footnote, className = '' }: ReleaseDriveNoticeProps) {
    if (!useHasNoDriveLibrary()) return null;
    return (
        <div className={`flex items-start gap-3 rounded-card border border-(--divider) bg-(--background-secondary) px-3 py-2.5 text-xs leading-snug ${className}`}>
            <FaGoogleDrive className="shrink-0 mt-0.5 text-(--text-secondary)" />
            <div className="flex-1 min-w-0">
                <Heading level="panel" as="h3">Player images come from Google Drive</Heading>
                <p className="mt-0.5 text-secondary">
                    Cards in your release use your image libraries. Without a Google Drive folder connected,
                    only players with an official Showdown Bot image get a photo.{' '}
                    <ImageLibraryGuideLink>How to make images</ImageLibraryGuideLink>
                </p>
                {footnote && <p className="mt-1 text-(--text-tertiary)">{footnote}</p>}
            </div>
            {action}
            {onDismiss && (
                <button
                    type="button"
                    onClick={onDismiss}
                    aria-label="Dismiss"
                    className="shrink-0 text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer"
                >
                    <FaXmark size={16} />
                </button>
            )}
        </div>
    );
}

/** Step bar button that opens image library settings in place, so the builder keeps its state.
 * `onClose` lets the builder re-check image matches against any library changes. `tipMoment` is
 * when the first-build tour may point here (until a Drive folder is connected). */
export function ImageLibrariesButton({ onClose, tipMoment = false }: { onClose?: () => void; tipMoment?: boolean }) {
    const [isOpen, setIsOpen] = useState(false);
    const [button, setButton] = useState<HTMLButtonElement | null>(null);
    const { overview } = useImageLibraries();
    const hasNoDriveLibrary = useHasNoDriveLibrary();
    const driveCount = overview?.libraries.length ?? 0;
    return (
        <>
            <ReleaseTip id="imageLibraries" show={tipMoment && hasNoDriveLibrary && !isOpen} anchor={button} placement="bottom-end" />
            <button
                ref={setButton}
                type="button"
                onClick={() => setIsOpen(true)}
                title="Google Drive folders your card images come from"
                className={buttonClass('secondary', 'sm', 'min-h-5')}
            >
                <FaGoogleDrive className="text-[12px] shrink-0" />
                <span><span className="hidden sm:inline">Image </span>Libraries</span>
                {overview && <span className="hidden sm:inline text-(--text-tertiary) tabular-nums">{driveCount}</span>}
            </button>
            {isOpen && (
                <ImageLibrariesModal
                    onClose={() => {
                        setIsOpen(false);
                        onClose?.();
                    }}
                />
            )}
        </>
    );
}
