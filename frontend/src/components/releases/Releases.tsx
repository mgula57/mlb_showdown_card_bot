import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import {
    fetchMyReleases,
    fetchPublicReleases,
    fetchRelease,
    createRelease,
    createEdition,
    type Release,
} from '../../api/releases';
import { ReleaseCard } from './ReleaseCard';
import { ReleaseDetail } from './ReleaseDetail';
import { NewReleaseModal } from './NewReleaseModal';
import { FaPlus, FaSpinner } from 'react-icons/fa6';
import type { ReleaseCreatePayload } from '../../api/releases';

/** A release that has been opened in this session. Each one keeps its own mounted ReleaseDetail
 *  (hidden when not addressed by the URL) so unsaved builder progress survives navigation. */
type OpenRelease = {
    release: Release;
    readOnly: boolean;
    /** Last edition slug viewed in this release — restored when navigating back to it. */
    editionSlug: string | null;
};

export default function Releases() {
    const { session } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const token = session?.access_token;

    const [userReleases, setUserReleases] = useState<Release[]>([]);
    const [officialReleases, setOfficialReleases] = useState<Release[]>([]);
    const [openReleases, setOpenReleases] = useState<Record<string, OpenRelease>>({});
    const [loading, setLoading] = useState(true);
    const [listLoaded, setListLoaded] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);

    // UX Spacing — matches TeamBuilder
    const px = 'px-4 sm:px-8';

    // URL shape: /release-builder/:releaseId/:editionSlug
    const isOnReleaseBuilder = location.pathname === '/release-builder' || location.pathname.startsWith('/release-builder/');
    const [, , releaseIdFromUrl = null, editionSlugFromUrl = null] = isOnReleaseBuilder
        ? location.pathname.split('/')
        : [];

    // Auth change invalidates the cached list
    useEffect(() => { setListLoaded(false); }, [token]);

    // Load the releases list lazily — only when viewing the list, so a direct visit to a
    // release URL opens the release without first loading every release.
    useEffect(() => {
        if (!isOnReleaseBuilder || releaseIdFromUrl || listLoaded) return;
        loadReleases();
    }, [isOnReleaseBuilder, releaseIdFromUrl, listLoaded, token]);

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

    // When the URL addresses a release that isn't mounted yet, fetch and mount it.
    useEffect(() => {
        // This page stays mounted while hidden, so leaving the route must not touch open releases.
        if (!isOnReleaseBuilder || !releaseIdFromUrl || openReleases[releaseIdFromUrl]) return;

        fetchRelease(releaseIdFromUrl, token ?? undefined)
            .then(release => {
                const readOnly = !token || release.created_by !== session?.user?.id;
                mountRelease(release, readOnly);
            })
            .catch(() => {
                navigate('/release-builder', { replace: true });
            });
    }, [releaseIdFromUrl, isOnReleaseBuilder, token]);

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
            const [publicReleases, myReleases] = await Promise.all([
                fetchPublicReleases(100),
                token ? fetchMyReleases(token) : Promise.resolve([]),
            ]);
            setOfficialReleases(publicReleases.filter(r => r.created_by !== session?.user?.id));
            setUserReleases(myReleases);
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
                { id: mainEdition.id, name: mainEdition.name, attributes: mainEdition.attributes, slug: mainEdition.slug, is_published: mainEdition.is_published, card_count: 0 },
            ],
        };
        setUserReleases(prev => [newRelease, ...prev]);
        setShowCreateModal(false);
        mountRelease(newRelease, false, mainEdition.slug);
        navigate(`/release-builder/${newRelease.id}/${mainEdition.slug}`);
    }

    function handleReleaseUpdated(updated: Release) {
        setUserReleases(prev => prev.map(r => r.id === updated.id ? updated : r));
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
                            onBack={goBack}
                            onReleaseUpdated={handleReleaseUpdated}
                            token={token}
                        />
                    </div>
                );
            })}

            {releaseIdFromUrl && !activeOpenRelease && <ReleaseDetailSkeleton />}

            {!releaseIdFromUrl && renderList()}
        </>
    );

    function renderList() {
        return (
        <div className="@container w-full">
        <div className="flex flex-col gap-6 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
            {/* Header */}
            <div className={`flex items-center ${px} justify-between`}>
                <div>
                    <h1 className="text-[20px] font-black text-(--text-primary)">Release Builder</h1>
                    <p className="text-[13px] text-(--text-secondary)">
                        Browse official card sets or build your own
                    </p>
                </div>
                {token && (
                    <button
                        type="button"
                        onClick={() => setShowCreateModal(true)}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity cursor-pointer"
                    >
                        <FaPlus className="text-[10px]" />
                        New
                        <span className="hidden sm:inline">Release</span>
                    </button>
                )}
            </div>

            {showCreateModal && (
                <NewReleaseModal
                    onConfirm={handleCreate}
                    onCancel={() => setShowCreateModal(false)}
                />
            )}

            {error && (
                <div className={px}>
                    <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                        {error}
                    </div>
                </div>
            )}

            {loading ? (
                <div className="flex justify-center py-12">
                    <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
                </div>
            ) : (
                <>
                    {/* My Releases */}
                    {token && (
                        <section className={px}>
                            <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide mb-2">
                                My Releases
                            </div>
                            {userReleases.length === 0 ? (
                                <p className="text-[13px] text-(--text-tertiary) py-4">
                                    You haven't created any releases yet.
                                </p>
                            ) : (
                                <div className="flex flex-col gap-2">
                                    {userReleases.map(release => (
                                        <ReleaseCard
                                            key={release.id}
                                            release={release}
                                            onClick={() => openRelease(release, false)}
                                        />
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {/* Official Releases */}
                    {officialReleases.length > 0 && (
                        <section className={px}>
                            <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide mb-2">
                                Official Releases
                            </div>
                            <div className="flex flex-col gap-2">
                                {officialReleases.map(release => (
                                    <ReleaseCard
                                        key={release.id}
                                        release={release}
                                        onClick={() => openRelease(release, true)}
                                    />
                                ))}
                            </div>
                        </section>
                    )}

                    {!token && officialReleases.length === 0 && (
                        <p className="text-[13px] text-(--text-tertiary) py-4 text-center">
                            Sign in to create your own releases.
                        </p>
                    )}
                </>
            )}
        </div>
        </div>
        );
    }
}

/** Placeholder shaped like ReleaseDetail's header + edition tab bar while a release loads. */
function ReleaseDetailSkeleton() {
    return (
        <div className="flex flex-col h-[calc(100dvh-2.5rem)] overflow-hidden animate-pulse">
            <div className="flex items-start gap-3 px-4 py-2.5 border-b border-(--divider)">
                <div className="h-4 w-4 rounded bg-(--background-secondary) mt-1" />
                <div className="flex-1 space-y-2">
                    <div className="h-6 w-56 rounded bg-(--background-secondary)" />
                    <div className="h-3 w-80 max-w-full rounded bg-(--background-secondary)" />
                </div>
            </div>
            <div className="flex items-center gap-3 px-4 py-3 bg-(--background-secondary)">
                <div className="h-3 w-14 rounded bg-(--background-primary)" />
                <div className="h-4 w-20 rounded bg-(--background-primary)" />
                <div className="h-4 w-20 rounded bg-(--background-primary)" />
            </div>
            <div className="flex-1 p-4">
                <div className="h-full rounded-lg bg-(--background-secondary)" />
            </div>
        </div>
    );
}
