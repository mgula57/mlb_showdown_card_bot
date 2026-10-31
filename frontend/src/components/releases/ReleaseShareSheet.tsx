import { useCallback, useEffect, useState } from 'react';
import { FaCheck, FaDownload, FaLink, FaShareNodes, FaSpinner } from 'react-icons/fa6';
import { ensureReleaseShareImage, type Release } from '../../api/releases';
import { cardImagePublicUrl } from '../../api/supabase';
import { Modal } from '../shared/Modal';
import { Eyebrow } from '../shared/Eyebrow';
import { InlineError } from '../shared/InlineError';
import { buttonClass } from '../shared/buttonStyles';
import { fieldClass } from '../shared/fieldStyles';
import { useCopyReleaseLink } from './useCopyReleaseLink';
import { ReleaseSharingSettings } from './ReleaseSharingSettings';

type ReleaseShareSheetProps = {
    release: Release;
    onClose: () => void;
    /** Shown above the title, e.g. "Published · v1" right after publishing. */
    eyebrow?: string;
    /** The owner's session, to switch between listed and link-only from here. */
    ownerToken?: string;
    onReleaseUpdated?: (release: Release) => void;
};

/** The release's preview image, asked for when the sheet opens: the server renders it if it's missing
 *  or out of date (e.g. a release published before share images, or a render that failed at publish). */
function useShareImage(release: Release) {
    const [path, setPath] = useState<string | null>(release.share_image_path);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            setPath(await ensureReleaseShareImage(release.id));
        } catch (err) {
            setError(err instanceof Error ? err.message : "Couldn't make the preview image.");
        } finally {
            setLoading(false);
        }
    }, [release.id]);

    useEffect(() => { load(); }, [load]);

    return { path, loading, error, retry: load };
}

/** Everything for sending a release to someone: its short link (copied, or handed to the phone's
 *  share sheet) and the preview image chat apps show for it, which can also be saved. */
export function ReleaseShareSheet({ release, onClose, eyebrow, ownerToken, onReleaseUpdated }: ReleaseShareSheetProps) {
    const link = useCopyReleaseLink(release.slug);
    const [downloading, setDownloading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const shareImage = useShareImage(release);
    const imageUrl = shareImage.path ? cardImagePublicUrl(shareImage.path) : null;
    const canShareNatively = typeof navigator.share === 'function';

    async function handleNativeShare() {
        try {
            await navigator.share({ title: release.name, text: release.description ?? undefined, url: link.url });
        } catch (err) {
            // Closing the share sheet rejects with AbortError, which isn't a failure
            if (!(err instanceof DOMException && err.name === 'AbortError')) setError("Couldn't open sharing. Copy the link instead.");
        }
    }

    async function handleDownloadImage() {
        if (!imageUrl) return;
        setDownloading(true);
        setError(null);
        try {
            const blob = await fetch(imageUrl).then(res => {
                if (!res.ok) throw new Error();
                return res.blob();
            });
            const objectUrl = URL.createObjectURL(blob);
            const anchor = document.createElement('a');
            anchor.href = objectUrl;
            anchor.download = `${release.slug}.jpg`;
            anchor.click();
            URL.revokeObjectURL(objectUrl);
        } catch {
            setError("Couldn't download the image. Try again in a moment.");
        } finally {
            setDownloading(false);
        }
    }

    return (
        <Modal
            size="md"
            onClose={onClose}
            title={
                <div className="flex flex-col gap-1">
                    {eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}
                    <span>Share {release.name}</span>
                </div>
            }
        >
            <div className="flex flex-col gap-4 p-4">
                {imageUrl ? (
                    <img
                        src={imageUrl}
                        alt={`Link preview for ${release.name}`}
                        className="w-full aspect-[1200/630] object-cover rounded-card border border-(--divider)"
                    />
                ) : shareImage.error ? (
                    <div className="flex flex-col items-start gap-2">
                        <InlineError size="md" icon>{shareImage.error}</InlineError>
                        <button type="button" onClick={shareImage.retry} className={buttonClass('secondary', 'sm')}>Try again</button>
                    </div>
                ) : (
                    <div className="flex flex-col gap-1.5">
                        <div aria-hidden className={`w-full aspect-[1200/630] rounded-card bg-(--background-tertiary) ${shareImage.loading ? 'animate-pulse' : ''}`} />
                        <span className="text-[12px] text-(--text-tertiary)">Making the preview image…</span>
                    </div>
                )}

                <div className="flex gap-2">
                    <input
                        type="text"
                        readOnly
                        value={link.url}
                        aria-label="Release link"
                        onFocus={e => e.currentTarget.select()}
                        className={fieldClass('md', 'flex-1 min-w-0 tabular-nums')}
                    />
                    <button type="button" onClick={link.copy} className={buttonClass('primary', 'md')}>
                        {link.copied ? <FaCheck className="text-[11px]" /> : <FaLink className="text-[11px]" />}
                        {link.copied ? 'Copied' : 'Copy link'}
                    </button>
                </div>

                <div className="flex flex-wrap gap-2">
                    {canShareNatively && (
                        <button type="button" onClick={handleNativeShare} className={buttonClass('secondary', 'md', 'flex-1')}>
                            <FaShareNodes className="text-[11px]" /> Share…
                        </button>
                    )}
                    {imageUrl && (
                        <button type="button" onClick={handleDownloadImage} disabled={downloading} className={buttonClass('secondary', 'md', 'flex-1')}>
                            {downloading ? <FaSpinner className="animate-spin text-[11px]" /> : <FaDownload className="text-[11px]" />} Download image
                        </button>
                    )}
                </div>

                {ownerToken && onReleaseUpdated && (
                    <ReleaseSharingSettings release={release} token={ownerToken} onReleaseUpdated={onReleaseUpdated} />
                )}

                {(error || link.error) && <InlineError size="md">{error ?? link.error}</InlineError>}
            </div>
        </Modal>
    );
}
