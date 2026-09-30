import { useState, useEffect } from 'react';
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

type ViewState =
    | { mode: 'list' }
    | { mode: 'editor'; release: Release; readOnly: boolean };

export default function Releases() {
    const { session } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const token = session?.access_token;

    const [userReleases, setUserReleases] = useState<Release[]>([]);
    const [officialReleases, setOfficialReleases] = useState<Release[]>([]);
    const [view, setView] = useState<ViewState>({ mode: 'list' });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);

    // Extract releaseId from URL: /release-builder/:releaseId — only when actually on a /release-builder/ path
    const releaseIdFromUrl = location.pathname.startsWith('/release-builder/')
        ? (location.pathname.split('/')[2] ?? null)
        : null;

    useEffect(() => {
        loadReleases();
    }, [token]);

    // When URL contains a release ID, fetch and open that release
    useEffect(() => {
        if (!releaseIdFromUrl) {
            setView({ mode: 'list' });
            return;
        }
        if (view.mode === 'editor' && view.release.id === releaseIdFromUrl) return;

        fetchRelease(releaseIdFromUrl, token ?? undefined)
            .then(release => {
                const readOnly = !token || release.created_by !== session?.user?.id;
                setView({ mode: 'editor', release, readOnly });
            })
            .catch(() => {
                navigate('/release-builder', { replace: true });
            });
    }, [releaseIdFromUrl, token]);

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
        } catch (err: any) {
            setError(err.message ?? 'Failed to load releases.');
        } finally {
            setLoading(false);
        }
    }

    function openRelease(release: Release, readOnly: boolean) {
        navigate('/release-builder/' + release.id);
        setView({ mode: 'editor', release, readOnly });
    }

    function goBack() {
        navigate('/release-builder');
        setView({ mode: 'list' });
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
        navigate('/release-builder/' + newRelease.id);
        setView({ mode: 'editor', release: newRelease, readOnly: false });
    }

    function handleReleaseUpdated(updated: Release) {
        setUserReleases(prev => prev.map(r => r.id === updated.id ? updated : r));
        setView(prev => prev.mode === 'editor' && prev.release.id === updated.id
            ? { ...prev, release: updated }
            : prev
        );
    }

    if (view.mode === 'editor') {
        const { release, readOnly } = view;
        return (
            <div className="flex flex-col h-full">
                <ReleaseDetail
                    release={release}
                    readOnly={readOnly}
                    onBack={goBack}
                    onReleaseUpdated={handleReleaseUpdated}
                    token={token}
                />
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6 py-4 max-w-4xl mx-auto w-full">
            {/* Header */}
            <div className="flex items-center px-4 justify-between">
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
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity"
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
                <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                    {error}
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
                        <section className="px-4">
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
                        <section className="px-4">
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
    );
}
