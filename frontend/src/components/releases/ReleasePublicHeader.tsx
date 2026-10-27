import { useState, type ReactNode } from 'react';
import { FaArrowLeft, FaHeart, FaRegHeart, FaShareNodes } from 'react-icons/fa6';
import { toggleReleaseLike, type Release } from '../../api/releases';
import { formatShortDate } from '../../functions/formatters';
import { Heading } from '../shared/Heading';
import { Eyebrow } from '../shared/Eyebrow';
import { Plate } from '../shared/Plate';
import { ReleaseHeaderButton } from './ReleaseHeaderButton';
import { ReleaseVersionHistory } from './ReleaseVersionHistory';

type ReleasePublicHeaderProps = {
    release: Release;
    /** Cards and editions the viewer can see (published ones, unless it's the owner). */
    cardCount: number;
    editionCount: number;
    isOwner: boolean;
    token?: string;
    onBack: () => void;
    onShare: () => void;
    onReleaseUpdated: (release: Release) => void;
    /** Owner-only actions, e.g. Edit. */
    children?: ReactNode;
};

/** The top of a published release when browsing it: what it is, who made it, which version this is,
 *  and the visitor's actions (like, share). Editing uses the builder's compact header instead. */
export function ReleasePublicHeader({ release, cardCount, editionCount, isOwner, token, onBack, onShare, onReleaseUpdated, children }: ReleasePublicHeaderProps) {
    const [liking, setLiking] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    // Owners can't like their own release, and liking needs an account
    const canLike = !!token && !isOwner;
    const versionDate = release.version_published_at ?? release.published_at;

    async function handleToggleLike() {
        if (!token || liking) return;
        setLiking(true);
        try {
            const { liked, like_count } = await toggleReleaseLike(release.id, token);
            onReleaseUpdated({ ...release, liked_by_me: liked, like_count });
        } catch {
            // The count just stays where it was
        } finally {
            setLiking(false);
        }
    }

    return (
        <>
        <header className="relative isolate shrink-0 border-b border-(--divider) bg-(--background-secondary)">
            <div aria-hidden className="absolute inset-0 -z-10 bg-pinstripe" />
            <div className="flex flex-col gap-2 px-4 pt-3 pb-3.5">
                <div className="flex items-center gap-3">
                    <button type="button" onClick={onBack} aria-label="Back" className="text-(--text-tertiary) opacity-70 hover:text-(--text-primary) transition-colors cursor-pointer">
                        <FaArrowLeft />
                    </button>
                    <Eyebrow>{release.is_official ? 'Official release' : 'Community release'}</Eyebrow>
                </div>
                <div className="flex flex-wrap items-end gap-x-4 gap-y-3">
                    <div className="flex flex-col gap-1.5 min-w-0 flex-1 basis-72">
                        <div className="flex items-center gap-2 min-w-0">
                            <Heading level="page" as="h1" fit>{release.name}</Heading>
                            {release.is_official && <Plate variant="navy" size="sm">Official</Plate>}
                            {isOwner && !release.is_listed && <Plate variant="outline" size="sm" title="Opens from its link but isn't listed in Community or search">Link only</Plate>}
                        </div>
                        <div className="flex flex-wrap items-center gap-x-1.5 text-[13px] text-(--text-secondary)">
                            {release.creator_username && (
                                <>
                                    <span>by <span className="font-semibold text-(--text-primary)">{release.creator_username}</span></span>
                                    <span aria-hidden className="text-(--text-tertiary)">·</span>
                                </>
                            )}
                            <span className="tabular-nums">
                                v{release.published_version}{versionDate ? `, ${release.published_version > 1 ? 'updated' : 'published'} ${formatShortDate(versionDate)}` : ''}
                            </span>
                            <span aria-hidden className="text-(--text-tertiary)">·</span>
                            <button type="button" onClick={() => setShowHistory(true)} className="font-semibold text-(--showdown-blue) hover:underline cursor-pointer">
                                History
                            </button>
                        </div>
                        {release.description && (
                            <p className="text-[13px] text-(--text-secondary) max-w-prose">{release.description}</p>
                        )}
                        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                            <Plate size="sm">{cardCount} card{cardCount === 1 ? '' : 's'}</Plate>
                            <Plate size="sm">{editionCount} edition{editionCount === 1 ? '' : 's'}</Plate>
                            <Plate variant="outline" size="sm">{release.view_count} view{release.view_count === 1 ? '' : 's'}</Plate>
                            {!canLike && <Plate variant="outline" size="sm">{release.like_count} like{release.like_count === 1 ? '' : 's'}</Plate>}
                        </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                        {canLike && (
                            <ReleaseHeaderButton
                                icon={release.liked_by_me ? <FaHeart /> : <FaRegHeart />}
                                label={release.liked_by_me ? 'Liked' : 'Like'}
                                tone={release.liked_by_me ? 'liked' : 'neutral'}
                                count={release.like_count}
                                busy={liking}
                                onClick={handleToggleLike}
                                title={release.liked_by_me ? `Unlike ${release.name}` : `Like ${release.name}`}
                            />
                        )}
                        <ReleaseHeaderButton icon={<FaShareNodes />} label="Share" onClick={onShare} />
                        {children}
                    </div>
                </div>
            </div>
        </header>
        {/* Outside the header: its `isolate` stacking context would trap the modal under the page below */}
        {showHistory && <ReleaseVersionHistory release={release} token={token} onClose={() => setShowHistory(false)} />}
        </>
    );
}
