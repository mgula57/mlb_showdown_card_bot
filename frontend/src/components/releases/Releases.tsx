import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import {
    fetchMyReleases,
    fetchPublicReleases,
    fetchSavedReleases,
    fetchRelease,
    createRelease,
    createEdition,
    editionSummaryOf,
    type Release,
    type PublicReleaseSort,
} from '../../api/releases';
import { useCommunityReleases } from './useCommunityReleases';
import { TeamSearchInput } from '../team_builder/TeamSearchInput';
import { choiceClass } from '../shared/choiceStyles';
import { ReleaseItem, ReleaseItemSkeleton } from './ReleaseItem';
import { ReleaseDetail } from './ReleaseDetail';
import { NewReleaseModal } from './NewReleaseModal';
import { FaPlus, FaSpinner } from 'react-icons/fa6';
import type { ReleaseCreatePayload } from '../../api/releases';

import { InlineError } from '../shared/InlineError';
import { Heading } from '../shared/Heading';
import { BetaBadge } from '../shared/BetaBadge';
import { buttonClass } from '../shared/buttonStyles';
import { EmptyState } from '../shared/EmptyState';
import { PinstripeBackdrop } from '../shared/PinstripeBackdrop';
/** A release that has been opened in this session. Each one keeps its own mounted ReleaseDetail
 *  (hidden when not addressed by the URL) so unsaved builder progress survives navigation. */
/** Release tiles: two per row on phones, fixed-width tiles that wrap on wider screens. */
const RELEASE_GRID = 'grid grid-cols-2 sm:flex sm:flex-wrap gap-3';

type OpenRelease = {
    release: Release;
    readOnly: boolean;
    /** Last edition slug viewed in this release — restored when navigating back to it. */
    editionSlug: string | null;
};

export default function Releases() {
    const { session, loading: authLoading } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const token = session?.access_token;

    const [userReleases, setUserReleases] = useState<Release[]>([]);
    const [savedReleases, setSavedReleases] = useState<Release[]>([]);
    const [officialReleases, setOfficialReleases] = useState<Release[]>([]);
    const [openReleases, setOpenReleases] = useState<Record<string, OpenRelease>>({});
    const [loading, setLoading] = useState(true);
    const [listLoaded, setListLoaded] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [communitySort, setCommunitySort] = useState<PublicReleaseSort>('popular');
    const [communitySearch, setCommunitySearch] = useState('');

    // UX Spacing — matches TeamBuilder
    const px = 'px-4 sm:px-8';

    // URL shape: /release-builder/:releaseId/:editionSlug[/:releaseCardId] (a card link opens that card)
    const isOnReleaseBuilder = location.pathname === '/release-builder' || location.pathname.startsWith('/release-builder/');
    const [, , releaseIdFromUrl = null, editionSlugFromUrl = null, cardRefFromUrl = null] = isOnReleaseBuilder
        ? location.pathname.split('/')
        : [];
    // Only fetched while the list is on screen
    const community = useCommunityReleases(communitySort, communitySearch, isOnReleaseBuilder && !releaseIdFromUrl);

    // Auth change invalidates the cached list
    useEffect(() => { setListLoaded(false); }, [token]);

    // Load the releases list lazily — only when viewing the list, so a direct visit to a
    // release URL opens the release without first loading every release.
    useEffect(() => {
        if (authLoading || !isOnReleaseBuilder || releaseIdFromUrl || listLoaded) return;
        loadReleases();
    }, [authLoading, isOnReleaseBuilder, releaseIdFromUrl, listLoaded, token]);

    const activeOpenRelease = releaseIdFromUrl ? openReleases[releaseIdFromUrl] : undefined;
    const isActiveReleaseMounted = !!activeOpenRelease;

    // readOnly is resolved per release when it mounts, so a different signed-in user needs fresh
    // mounts. Keyed on the user id (not the token) so routine token refreshes keep progress.
    const userId = session?.user?.id;
    const mountedForUserRef = useRef(userId);
    useEffect(() => {
        if (mountedForUserRef.current === userId) return;
        mountedForUserRef.current = userId;
        setOpenReleases({});
    }, [userId]);

    // When the URL addresses a release that isn't mounted yet, fetch and mount it. Waits for the
    // auth session to restore first — on a page reload the token isn't available on the first
    // render, and an unpublished release fetched anonymously 404s and bounces back to the list.
    useEffect(() => {
        // This page stays mounted while hidden, so leaving the route must not touch open releases.
        if (authLoading || !isOnReleaseBuilder || !releaseIdFromUrl || openReleases[releaseIdFromUrl]) return;

        let cancelled = false;
        fetchRelease(releaseIdFromUrl, token ?? undefined)
            .then(release => {
                if (cancelled) return;
                const readOnly = !token || release.created_by !== session?.user?.id;
                mountRelease(release, readOnly);
            })
            .catch(() => {
                if (!cancelled) navigate('/release-builder', { replace: true });
            });
        return () => { cancelled = true; };
    }, [authLoading, releaseIdFromUrl, isOnReleaseBuilder, token]);

    // Bare release URL (no edition slug) → restore the edition last viewed in that release.
    useEffect(() => {
        if (!isOnReleaseBuilder || !activeOpenRelease || editionSlugFromUrl || !activeOpenRelease.editionSlug) return;
        navigate(`/release-builder/${activeOpenRelease.release.id}/${activeOpenRelease.editionSlug}`, { replace: true });
    }, [releaseIdFromUrl, editionSlugFromUrl, isOnReleaseBuilder, isActiveReleaseMounted]);

    // Remember the edition being viewed so returning to this release lands on it.
    useEffect(() => {
        if (!isOnReleaseBuilder || !releaseIdFromUrl || !editionSlugFromUrl) return;
        setOpenReleases(prev => !prev[releaseIdFromUrl] || prev[releaseIdFromUrl].editionSlug === editionSlugFromUrl
            ? prev
            : { ...prev, [releaseIdFromUrl]: { ...prev[releaseIdFromUrl], editionSlug: editionSlugFromUrl } }
        );
    }, [releaseIdFromUrl, editionSlugFromUrl, isOnReleaseBuilder, isActiveReleaseMounted]);

    function mountRelease(release: Release, readOnly: boolean, editionSlug: string | null = null) {
        setOpenReleases(prev => prev[release.id] ? prev : { ...prev, [release.id]: { release, readOnly, editionSlug } });
    }

    async function loadReleases() {
        setLoading(true);
        setError(null);
        try {
            const [publicReleases, myReleases, saved] = await Promise.all([
                fetchPublicReleases(100, 0, { section: 'official', sort: 'new' }),
                token ? fetchMyReleases(token) : Promise.resolve([]),
                token ? fetchSavedReleases(token) : Promise.resolve([]),
            ]);
            setOfficialReleases(publicReleases.filter(r => r.created_by !== session?.user?.id));
            setUserReleases(myReleases);
            setSavedReleases(saved);
            setListLoaded(true);
        } catch (err: any) {
            setError(err.message ?? 'Failed to load releases.');
        } finally {
            setLoading(false);
        }
    }

    function openRelease(release: Release, readOnly: boolean) {
        mountRelease(release, readOnly);
        navigate('/release-builder/' + release.id);
        // List tiles lack the viewer's like/save state, which the header's buttons need
        if (readOnly && token && release.liked_by_me === undefined) {
            fetchRelease(release.id, token)
                .then(full => handleReleaseUpdated({ ...release, liked_by_me: full.liked_by_me, saved_by_me: full.saved_by_me }))
                .catch(() => {});
        }
    }

    function goBack() {
        navigate('/release-builder');
    }

    async function handleCreate(payload: ReleaseCreatePayload) {
        if (!token) return;
        const created = await createRelease(payload, token);
        // Every release starts with a single "main" edition — no need to make the user create one manually.
        const mainEdition = await createEdition(created.id, { name: 'main' }, token);
        const newRelease: Release = {
            ...created,
            editions: [
                editionSummaryOf(mainEdition),
            ],
        };
        setUserReleases(prev => [newRelease, ...prev]);
        setShowCreateModal(false);
        mountRelease(newRelease, false, mainEdition.slug);
        navigate(`/release-builder/${newRelease.id}/${mainEdition.slug}`);
    }

    function handleReleaseUpdated(updated: Release) {
        setUserReleases(prev => prev.map(r => r.id === updated.id ? updated : r));
        // Saving or unsaving in the release's header adds it to (or drops it from) the Saved section
        if (updated.saved_by_me !== undefined) {
            setSavedReleases(prev => {
                const rest = prev.filter(r => r.id !== updated.id);
                if (!updated.saved_by_me) return rest;
                return prev.some(r => r.id === updated.id) ? prev.map(r => r.id === updated.id ? updated : r) : [updated, ...rest];
            });
        }
        setOpenReleases(prev => prev[updated.id]
            ? { ...prev, [updated.id]: { ...prev[updated.id], release: updated } }
            : prev
        );
    }

    return (
        <>
            {/* One mounted ReleaseDetail per opened release; only the one in the URL is visible. */}
            {Object.values(openReleases).map(({ release, readOnly, editionSlug }) => {
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
                            token={token}
                        />
                    </div>
                );
            })}

            {releaseIdFromUrl && !activeOpenRelease && <ReleaseDetailSkeleton />}

            {!releaseIdFromUrl && renderList()}

            {/* Outside the list's @container: container-type makes it the containing block for fixed
                descendants, which would clip the modal to the list's height. */}
            {showCreateModal && (
                <NewReleaseModal
                    onConfirm={handleCreate}
                    onCancel={() => setShowCreateModal(false)}
                />
            )}
        </>
    );

    function renderList() {
        return (
        <div className="@container w-full relative isolate">
        {/* Card-back pinstripes behind the page header, echoing the release tiles' card fields */}
        <PinstripeBackdrop heightClass="h-72" />
        <div className="flex flex-col gap-6 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
            {/* Header */}
            <div className={`flex items-center ${px} justify-between`}>
                <div>
                    <Heading level="page" className="flex items-center gap-2">
                        Release Builder
                        <BetaBadge />
                    </Heading>
                    <p className="text-[13px] text-(--text-secondary)">
                        Browse official card sets or build your own
                    </p>
                </div>
                {token && (
                    <button
                        type="button"
                        onClick={() => setShowCreateModal(true)}
                        className={buttonClass('primary', 'sm')}
                    >
                        <FaPlus className="text-[10px]" />
                        <span>New<span className="hidden sm:inline"> release</span></span>
                    </button>
                )}
            </div>

            {error && (
                <div className={px}>
                    <InlineError size="md">
                        {error}
                    </InlineError>
                </div>
            )}

            {loading ? (
                <section className={px}>
                    <div className="h-3 w-24 rounded-plate bg-(--background-tertiary) animate-pulse mb-2" />
                    <ReleaseSkeletonRow />
                </section>
            ) : (
                <>
                    {/* My Releases */}
                    {token && (
                        <section className={px}>
                            <Heading level="section" as="h2" className="mb-3">My Releases</Heading>
                            {userReleases.length === 0 ? (
                                <EmptyState
                                    size="panel"
                                    title="No releases yet."
                                    action={<button type="button" onClick={() => setShowCreateModal(true)} className={buttonClass('primary')}><FaPlus className="text-[11px]" /> New release</button>}
                                >
                                    Build your own set: pick the players, the editions and the point values.
                                </EmptyState>
                            ) : (
                                <div className={RELEASE_GRID}>
                                    {userReleases.map(release => (
                                        <ReleaseItem
                                            key={release.id}
                                            release={release}
                                            onClick={() => openRelease(release, false)}
                                            showPublishStatus
                                        />
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {/* Saved - other users' releases whose cards the user searches in the Card Explorer */}
                    {savedReleases.length > 0 && (
                        <section className={px}>
                            <Heading level="section" as="h2" className="mb-3">Saved</Heading>
                            <div className={RELEASE_GRID}>
                                {savedReleases.map(release => (
                                    <ReleaseItem
                                        key={release.id}
                                        release={release}
                                        onClick={() => openRelease(release, true)}
                                    />
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Official Releases */}
                    {officialReleases.length > 0 && (
                        <section className={px}>
                            <Heading level="section" as="h2" className="mb-3">Official</Heading>
                            <div className={RELEASE_GRID}>
                                {officialReleases.map(release => (
                                    <ReleaseItem
                                        key={release.id}
                                        release={release}
                                        onClick={() => openRelease(release, true)}
                                    />
                                ))}
                            </div>
                        </section>
                    )}

                    {!token && (
                        <p className="text-[13px] text-(--text-tertiary) text-center">
                            Sign in to create your own releases.
                        </p>
                    )}
                </>
            )}

            {renderCommunity()}
        </div>
        </div>
        );
    }

    /** Every listed community release, the user's own included: sorted and searched on the server, a page at a time. */
    function renderCommunity() {
        const { releases, loading: loadingCommunity, hasMore, error: communityError, loadMore, searching } = community;
        return (
            <section className={`${px} flex flex-col gap-3`}>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                    <Heading level="section" as="h2">Community</Heading>
                    <div className="flex gap-1.5" role="group" aria-label="Sort community releases">
                        {COMMUNITY_SORTS.map(option => (
                            <button
                                key={option.value}
                                type="button"
                                aria-pressed={communitySort === option.value}
                                onClick={() => setCommunitySort(option.value)}
                                className={choiceClass(communitySort === option.value, 'sm')}
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                    <TeamSearchInput
                        value={communitySearch}
                        onChange={setCommunitySearch}
                        placeholder="Search by name or creator…"
                        className="w-full sm:w-72 sm:ml-auto"
                    />
                </div>

                {communityError && <InlineError size="md">{communityError}</InlineError>}

                {releases === null ? (
                    <ReleaseSkeletonRow />
                ) : releases.length === 0 ? (
                    searching ? (
                        <EmptyState size="inline">No releases match “{communitySearch.trim()}”.</EmptyState>
                    ) : (
                        <EmptyState size="panel" title="No community releases yet.">
                            Publish one of your releases and it shows up here.
                        </EmptyState>
                    )
                ) : (
                    <>
                        <div className={`${RELEASE_GRID} ${loadingCommunity ? 'opacity-60' : ''} transition-opacity`}>
                            {releases.map(release => (
                                // The user's own open in the builder, as from My Releases
                                <ReleaseItem key={release.id} release={release} onClick={() => openRelease(release, release.created_by !== userId)} />
                            ))}
                        </div>
                        {hasMore && (
                            <button type="button" onClick={loadMore} disabled={loadingCommunity} className={buttonClass('secondary', 'md', 'self-center')}>
                                {loadingCommunity && <FaSpinner className="animate-spin text-[11px]" />} Load more
                            </button>
                        )}
                    </>
                )}
            </section>
        );
    }
}

const COMMUNITY_SORTS: { value: PublicReleaseSort; label: string }[] = [
    { value: 'popular', label: 'Popular' },
    { value: 'new', label: 'New' },
];

/** A single row of tile skeletons: two on phones; on wider screens the row is clipped to one tile
 *  height (sm:w-52 at 3/4 aspect), so tiles that would wrap stay hidden. */
function ReleaseSkeletonRow() {
    return (
        <div className={`${RELEASE_GRID} sm:h-[calc(13rem*4/3)] sm:overflow-hidden`}>
            {Array.from({ length: 8 }, (_, i) => (
                <div key={i} className={i >= 2 ? 'max-sm:hidden' : undefined}>
                    <ReleaseItemSkeleton />
                </div>
            ))}
        </div>
    );
}

/** Placeholder shaped like ReleaseDetail's header + edition tab bar while a release loads. */
function ReleaseDetailSkeleton() {
    return (
        <div className="flex flex-col md:h-[calc(100dvh-2.5rem)] md:overflow-hidden animate-pulse">
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
