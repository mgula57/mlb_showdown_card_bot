import { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { fetchRelease, createRelease, type Release, type ReleaseCreatePayload } from '../../api/releases';
import { useCommunityReleases } from './useCommunityReleases';
import { useReleaseLibrary, withEngagement } from './useReleaseLibrary';
import { useOpenReleases, useReleaseBuilderRoute } from './useOpenReleases';
import { ReleaseList } from './ReleaseList';
import { ReleaseDetail } from './ReleaseDetail';
import { NewReleaseModal } from './NewReleaseModal';
import { ReleaseGuide } from './ReleaseGuide';
import type { ReleaseGuideSectionId } from './releaseGuideContent';
import { isInCommunity } from './releaseVisibility';
import { RetryableError } from '../shared/RetryableError';
import { buttonClass } from '../shared/buttonStyles';

export default function Releases() {
    const { session, loading: authLoading } = useAuth();
    const navigate = useNavigate();
    const token = session?.access_token;
    const userId = session?.user?.id;

    const route = useReleaseBuilderRoute();
    const { releaseId: releaseIdFromUrl, editionSlug: editionSlugFromUrl, cardRef: cardRefFromUrl } = route;
    const isListShown = route.isOnReleaseBuilder && !releaseIdFromUrl;

    const [showCreateModal, setShowCreateModal] = useState(false);
    const [guideSection, setGuideSection] = useState<ReleaseGuideSectionId | null>(null);
    /** Why the list was opened in place of a release link (it's private or gone). */
    const [releaseNotice, setReleaseNotice] = useState<string | null>(null);

    // Both lists are only fetched while on screen, once the session restores (they depend on the viewer)
    const library = useReleaseLibrary(isListShown && !authLoading, token, userId);
    const community = useCommunityReleases(isListShown && !authLoading, token, userId);
    const openReleases = useOpenReleases({
        route, authLoading, token, userId,
        onNotFound: () => setReleaseNotice('That release is private or no longer exists.'),
    });
    const listRef = useListScrollMemory(isListShown);

    // Opening a release (from a tile, a link or history) clears the note about the last link that
    // couldn't be opened. Adjusted during render, so the note never flashes on the next screen.
    const [noticeReleaseId, setNoticeReleaseId] = useState(releaseIdFromUrl);
    if (noticeReleaseId !== releaseIdFromUrl) {
        setNoticeReleaseId(releaseIdFromUrl);
        if (releaseIdFromUrl) setReleaseNotice(null);
    }

    function openRelease(release: Release, readOnly: boolean) {
        setGuideSection(null);
        openReleases.mount(release, readOnly);
        navigate('/release-builder/' + release.id);
        // List tiles lack the viewer's like/save state, which the header's buttons need
        if (readOnly && token && release.liked_by_me === undefined) {
            fetchRelease(release.id, token)
                .then(full => handleReleaseUpdated({ ...release, liked_by_me: full.liked_by_me, saved_by_me: full.saved_by_me }))
                .catch(() => {});
        }
    }

    /** Community tiles show every release as visitors see it (published editions only). The user's
     *  own open in the builder, so they mount the full copy from My Releases, or fetch it. */
    function openCommunityRelease(release: Release) {
        if (release.created_by !== userId) {
            openRelease(release, true);
            return;
        }
        const own = library.mine.find(r => r.id === release.id);
        if (own) {
            openRelease(own, false);
            return;
        }
        setGuideSection(null);
        // Mounting happens once the URL's release is fetched (see useOpenReleases)
        navigate('/release-builder/' + release.id);
    }

    function goBack() {
        navigate('/release-builder');
    }

    function handleReleaseDeleted(releaseId: string) {
        library.remove(releaseId);
        community.mapReleases(r => r.id === releaseId ? null : r);
        openReleases.remove(releaseId);
        navigate('/release-builder', { replace: true });
    }

    async function handleCreate(payload: ReleaseCreatePayload) {
        if (!token) return;
        // Created with its "main" edition in one request, so a failure never leaves a release without one
        const created = await createRelease(payload, token);
        setShowCreateModal(false);
        openNewRelease(created);
    }

    /** Opens a release the user just made (new or remixed) in the builder, at its first edition. */
    function openNewRelease(created: Release) {
        setGuideSection(null);
        const firstSlug = created.editions[0]?.slug ?? null;
        library.addMine(created);
        openReleases.mount(created, false, firstSlug);
        navigate(`/release-builder/${created.id}${firstSlug ? `/${firstSlug}` : ''}`);
    }

    function handleReleaseUpdated(updated: Release) {
        // One of the user's releases newly published or listed: Community reloads when next shown,
        // since it's sorted and paged on the server and can't just be added to the loaded pages
        if (updated.created_by === userId && isInCommunity(updated)) {
            const previous = openReleases.get(updated.id) ?? library.mine.find(r => r.id === updated.id);
            if (!previous || !isInCommunity(previous)) community.invalidate();
        }
        library.applyUpdate(updated);
        // Unpublished, or made link-only or private: it leaves Community right away, not on the next
        // load. Otherwise a like from the release's header shows on its tile.
        community.mapReleases(r => r.id !== updated.id ? r
            : updated.visibility && !isInCommunity(updated) ? null
            : withEngagement(r, updated));
        openReleases.update(updated);
    }

    return (
        <>
            {/* One mounted ReleaseDetail per opened release; only the one in the URL is visible. */}
            {openReleases.releases.map(({ release, readOnly, editionSlug }) => {
                const isActive = release.id === releaseIdFromUrl;
                return (
                    <div key={release.id} className={isActive ? 'flex flex-col h-full' : 'hidden'}>
                        <ReleaseDetail
                            release={release}
                            readOnly={readOnly}
                            editionSlug={isActive ? (editionSlugFromUrl ?? editionSlug) : editionSlug}
                            onEditionChange={slug => navigate(`/release-builder/${release.id}/${slug}`, { replace: true })}
                            cardRef={isActive ? cardRefFromUrl : null}
                            // Once opened, drop the card from the URL so closing it (or a reload) doesn't reopen it
                            onCardLinkOpened={() => editionSlugFromUrl && navigate(`/release-builder/${release.id}/${editionSlugFromUrl}`, { replace: true })}
                            onBack={goBack}
                            onReleaseUpdated={handleReleaseUpdated}
                            onDeleted={handleReleaseDeleted}
                            onRemixed={openNewRelease}
                            token={token}
                        />
                    </div>
                );
            })}

            {releaseIdFromUrl && !openReleases.active && (openReleases.error ? (
                <div className="px-4 sm:px-8 py-6">
                    <RetryableError
                        onRetry={openReleases.retry}
                        actions={<button type="button" onClick={goBack} className={buttonClass('ghost', 'sm')}>Back to releases</button>}
                    >
                        {openReleases.error}
                    </RetryableError>
                </div>
            ) : <ReleaseDetailSkeleton />)}

            {!releaseIdFromUrl && (
                <ReleaseList
                    listRef={listRef}
                    signedIn={!!token}
                    library={library}
                    community={community}
                    notice={releaseNotice}
                    onOpen={openRelease}
                    onOpenCommunity={openCommunityRelease}
                    onCreate={() => setShowCreateModal(true)}
                    onOpenGuide={() => setGuideSection('plan')}
                />
            )}

            {/* Outside the list's @container: container-type makes it the containing block for fixed
                descendants, which would clip the modal and the guide to the list's height. */}
            {!releaseIdFromUrl && <ReleaseGuide section={guideSection} onClose={() => setGuideSection(null)} />}
            {showCreateModal && (
                <NewReleaseModal
                    onConfirm={handleCreate}
                    onCancel={() => setShowCreateModal(false)}
                />
            )}
        </>
    );
}

/** The list unmounts while a release is open, so this remembers where it was scrolled and goes
 *  back there on return (its tiles and loaded Community pages are still in state, so it's that tall
 *  again right away). Only records while the list is on screen, since this page stays mounted hidden.
 *  Returns the ref for the list's root. */
function useListScrollMemory(isListShown: boolean) {
    const listRef = useRef<HTMLDivElement>(null);
    const scrollY = useRef(0);
    useEffect(() => {
        const onScroll = () => {
            if (listRef.current?.offsetParent) scrollY.current = window.scrollY;
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        return () => window.removeEventListener('scroll', onScroll);
    }, []);
    useLayoutEffect(() => {
        if (isListShown) window.scrollTo(0, scrollY.current);
    }, [isListShown]);
    return listRef;
}

/** Placeholder shaped like ReleaseDetail's header + edition tab bar while a release loads. */
function ReleaseDetailSkeleton() {
    return (
        <div className="flex flex-col md:tall:h-[calc(100dvh-2.5rem)] md:tall:overflow-hidden animate-pulse">
            <div className="flex items-start gap-3 px-4 py-2.5 border-b border-(--divider)">
                <div className="h-4 w-4 rounded-plate bg-(--background-tertiary) mt-1" />
                <div className="flex-1 space-y-2">
                    <div className="h-6 w-56 rounded-plate bg-(--background-tertiary)" />
                    <div className="h-3 w-80 max-w-full rounded-plate bg-(--background-tertiary)" />
                </div>
            </div>
            <div className="flex items-center gap-3 px-4 py-3 bg-(--background-secondary)">
                <div className="h-3 w-14 rounded-plate bg-(--background-tertiary)" />
                <div className="h-4 w-20 rounded-plate bg-(--background-tertiary)" />
                <div className="h-4 w-20 rounded-plate bg-(--background-tertiary)" />
            </div>
            <div className="flex-1 p-4">
                <div className="h-full rounded-card bg-(--background-secondary)" />
            </div>
        </div>
    );
}
