import { useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { FaArrowLeft, FaBookmark, FaCodeFork, FaHeart, FaRegBookmark, FaRegHeart, FaShareNodes } from 'react-icons/fa6';
import { toggleReleaseLike, toggleReleaseSave, type Release } from '../../api/releases';
import { formatShortDate } from '../../functions/formatters';
import { Heading } from '../shared/Heading';
import { Eyebrow } from '../shared/Eyebrow';
import { Plate } from '../shared/Plate';
import { ReleaseHeaderButton } from './ReleaseHeaderButton';
import { ReleaseVersionHistory } from './ReleaseVersionHistory';
import { ReleaseRemixModal } from './ReleaseRemixModal';
import { ReleaseCardFan } from './ReleaseItem';

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
    /** Opens the viewer's new remix of this release. Without it there's no Remix button. */
    onRemixed?: (release: Release) => void;
    /** Owner-only actions, e.g. Edit. */
    children?: ReactNode;
};

/** The top of a published release when browsing it: what it is, who made it (and what it was remixed
 *  from), which version this is, and the visitor's actions (like, save, remix, share). Editing uses the builder's compact header instead. */
export function ReleasePublicHeader({ release, cardCount, editionCount, isOwner, token, onBack, onShare, onReleaseUpdated, onRemixed, children }: ReleasePublicHeaderProps) {
    const [liking, setLiking] = useState(false);
    const [saving, setSaving] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [showRemix, setShowRemix] = useState(false);
    // Touch screens can't hover, so a tap toggles the featured cards open instead
    const [cardsFanned, setCardsFanned] = useState(false);
    // Owners can't like their own release, and liking needs an account
    const canLike = !!token && !isOwner;
    // Same audience as liking, while the owner allows remixes
    const canRemix = canLike && release.allow_remix && !!onRemixed;
    const forkParent = release.fork_parent;
    const versionDate = release.version_published_at ?? release.published_at;
    const previewImages = release.preview_images ?? [];

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

    async function handleToggleSave() {
        if (!token || saving) return;
        setSaving(true);
        try {
            const { saved } = await toggleReleaseSave(release.id, token);
            onReleaseUpdated({ ...release, saved_by_me: saved });
        } catch {
            // Stays as it was
        } finally {
            setSaving(false);
        }
    }

    return (
        <>
        <header className="relative isolate shrink-0 border-b border-(--divider) bg-(--background-secondary)">
            <div aria-hidden className="absolute inset-0 -z-10 bg-pinstripe" />
            {/* Info, the featured cards, then the actions. Below md the cards are hidden and the actions wrap under the info;
                from md to lg there's no room for all three side by side, so the cards sit behind the actions instead. */}
            <div className="flex flex-wrap md:flex-nowrap items-stretch">
            <div className="relative z-1 flex flex-col gap-2 basis-full md:basis-auto md:flex-1 min-w-0 px-4 pt-3 pb-3 md:pb-3.5">
                <div className="flex items-center gap-3">
                    <button type="button" onClick={onBack} aria-label="Back" className="text-(--text-tertiary) opacity-70 hover:text-(--text-primary) transition-colors cursor-pointer">
                        <FaArrowLeft />
                    </button>
                    <Eyebrow>{release.is_official ? 'Official release' : 'Community release'}</Eyebrow>
                </div>
                <div className="flex flex-col gap-1.5 min-w-0">
                    <div className="flex items-center gap-2 min-w-0">
                        <Heading level="page" as="h1" fit>{release.name}</Heading>
                        {release.is_official && <Plate variant="navy" size="sm">Official</Plate>}
                        {release.is_wip && <Plate variant="outline" size="sm" title="Work in progress: more cards or changes are coming">WIP</Plate>}
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
                    {forkParent && (
                        <div className="flex items-center gap-1.5 text-[13px] text-(--text-secondary) min-w-0">
                            <FaCodeFork aria-hidden className="shrink-0 text-[11px] text-(--text-tertiary)" />
                            <span className="min-w-0">
                                Remixed from{' '}
                                {forkParent.is_linkable
                                    ? <Link to={`/release-builder/${forkParent.id}`} className="font-semibold text-(--showdown-blue) hover:underline cursor-pointer">{forkParent.name}</Link>
                                    : <span className="font-semibold text-(--text-primary)">{forkParent.name}</span>}
                                {forkParent.creator_username && <> by <span className="font-semibold text-(--text-primary)">{forkParent.creator_username}</span></>}
                            </span>
                        </div>
                    )}
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
            </div>
            {/* The release's featured cards, dealt up from the header's bottom edge (which crops them). The
                side cards spill past the box sideways, under the info and actions (above the pinstripes). Info and actions sit at z-1 rather than the fan at -z-1, which would put it under the row for hit-testing and kill its hover.
                Its z-0 keeps the cards' own z-indexes inside the fan, so none of them climb over the z-1 info or actions.
                Below lg it's pulled out of the row and pinned to the right edge, behind the actions. */}
            {previewImages.length > 0 && (
                <div
                    aria-hidden
                    data-fanned={cardsFanned || undefined}
                    onPointerDown={e => { if (e.pointerType !== 'mouse') setCardsFanned(f => !f); }}
                    className="group hidden md:block z-0 absolute inset-y-0 right-0 lg:relative lg:inset-auto lg:-ml-10 w-72 lg:w-64 shrink-0 overflow-y-clip"
                >
                    <ReleaseCardFan images={previewImages} />
                </div>
            )}
            {/* From md to lg it's at least as wide as the cards behind it, so they never slide under the info */}
            <div className="relative z-1 flex items-center justify-end gap-1.5 shrink-0 self-end md:max-lg:min-w-72 px-4 pb-3.5">
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
                {/* Same rule as liking: your own releases are always in your card search */}
                {canLike && (
                    <ReleaseHeaderButton
                        icon={release.saved_by_me ? <FaBookmark /> : <FaRegBookmark />}
                        label={release.saved_by_me ? 'Saved' : 'Save'}
                        tone={release.saved_by_me ? 'primary' : 'neutral'}
                        busy={saving}
                        onClick={handleToggleSave}
                        title={release.saved_by_me ? `Remove ${release.name} from your card search` : `Save ${release.name} to search its cards in the Card Explorer`}
                    />
                )}
                {canRemix && (
                    <ReleaseHeaderButton
                        icon={<FaCodeFork />}
                        label="Remix"
                        collapseLabel
                        onClick={() => setShowRemix(true)}
                        title={`Start your own release from ${release.name}`}
                    />
                )}
                <ReleaseHeaderButton icon={<FaShareNodes />} label="Share" onClick={onShare} />
                {children}
            </div>
            </div>
        </header>
        {/* Outside the header: its `isolate` stacking context would trap the modal under the page below */}
        {showHistory && <ReleaseVersionHistory release={release} token={token} onClose={() => setShowHistory(false)} />}
        {showRemix && token && onRemixed && (
            <ReleaseRemixModal release={release} token={token} onClose={() => setShowRemix(false)} onRemixed={onRemixed} />
        )}
        </>
    );
}
