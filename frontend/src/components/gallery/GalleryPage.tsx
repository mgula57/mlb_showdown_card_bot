import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';
import { FaImages, FaTrash, FaSpinner } from 'react-icons/fa';
import { fetchUserGallery, deleteGalleryCard, type GalleryImageRecord } from '../../api/gallery';

const PAGE_SIZE = 50;

const GalleryCard: React.FC<{
    item: GalleryImageRecord;
    onDelete: (id: number) => void;
    isDeleting: boolean;
}> = ({ item, onDelete, isDeleting }) => {
    const [isHovered, setIsHovered] = useState(false);

    const imageUrl = item.public_url ?? item.storage_path;
    const label = [item.player_name, item.year, item.set_name].filter(Boolean).join(' · ');

    return (
        <div
            className="flex flex-col gap-1"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <div className="relative rounded-md overflow-hidden bg-(--background-secondary)" style={{ aspectRatio: '2.5 / 3.5' }}>
                {imageUrl ? (
                    <img
                        src={imageUrl}
                        alt={label}
                        loading="lazy"
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-secondary text-xs">No image</div>
                )}

                {/* Delete overlay on hover */}
                {isHovered && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                        <button
                            onClick={() => onDelete(item.id)}
                            disabled={isDeleting}
                            className="p-2 rounded-full bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50"
                            title="Delete from gallery"
                        >
                            {isDeleting ? <FaSpinner className="animate-spin" size={16} /> : <FaTrash size={16} />}
                        </button>
                    </div>
                )}
            </div>
            {label && (
                <p className="text-xs text-secondary text-center truncate px-1">{label}</p>
            )}
        </div>
    );
};

const GalleryPage: React.FC = () => {
    const { user, session, loading } = useAuth();
    const navigate = useNavigate();

    const [gallery, setGallery] = useState<GalleryImageRecord[]>([]);
    const [hasMore, setHasMore] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<number | null>(null);

    // Redirect if not logged in (matches AccountPage pattern)
    useEffect(() => {
        if (!loading && !user) {
            navigate('/');
        }
    }, [user, loading, navigate]);

    const loadGallery = useCallback(async (offset: number, append: boolean) => {
        if (!session?.access_token) return;
        if (append) setIsLoadingMore(true);
        else setIsLoading(true);
        setError(null);
        try {
            const data = await fetchUserGallery(session.access_token, PAGE_SIZE, offset);
            setGallery(prev => append ? [...prev, ...data.gallery] : data.gallery);
            setHasMore(data.has_more);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load gallery');
        } finally {
            setIsLoading(false);
            setIsLoadingMore(false);
        }
    }, [session?.access_token]);

    useEffect(() => {
        if (user && session?.access_token) {
            loadGallery(0, false);
        }
    }, [user, session?.access_token, loadGallery]);

    const handleDelete = async (id: number) => {
        if (!session?.access_token) return;
        setDeletingId(id);
        try {
            await deleteGalleryCard(session.access_token, id);
            setGallery(prev => prev.filter(item => item.id !== id));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete card');
        } finally {
            setDeletingId(null);
        }
    };

    const handleLoadMore = () => {
        loadGallery(gallery.length, true);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-secondary text-xl">Loading...</div>
            </div>
        );
    }

    if (!user) return null;

    return (
        <div className="min-h-screen bg-(--background-primary) p-6 md:p-8">
            <div className="max-w-7xl mx-auto">

                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-2">
                        <FaImages className="text-primary" size={24} />
                        <h1 className="text-2xl font-bold text-primary">My Gallery</h1>
                    </div>
                    <p className="text-secondary text-sm">Cards you've generated while signed in</p>
                </div>

                {/* Error banner */}
                {error && (
                    <div className="mb-6 p-3 rounded-md bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
                        {error}
                    </div>
                )}

                {/* Loading state */}
                {isLoading ? (
                    <div className="flex items-center justify-center py-24">
                        <FaSpinner className="animate-spin text-secondary" size={32} />
                    </div>
                ) : gallery.length === 0 ? (
                    /* Empty state */
                    <div className="flex flex-col items-center justify-center py-24 gap-4 text-secondary">
                        <FaImages size={48} className="opacity-30" />
                        <p className="text-lg font-medium">No cards yet</p>
                        <p className="text-sm text-center max-w-xs">
                            Cards you generate while signed in will appear here automatically.
                        </p>
                    </div>
                ) : (
                    <>
                        {/* Card grid */}
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                            {gallery.map(item => (
                                <GalleryCard
                                    key={item.id}
                                    item={item}
                                    onDelete={handleDelete}
                                    isDeleting={deletingId === item.id}
                                />
                            ))}
                        </div>

                        {/* Load more */}
                        {hasMore && (
                            <div className="flex justify-center mt-8">
                                <button
                                    onClick={handleLoadMore}
                                    disabled={isLoadingMore}
                                    className="px-6 py-2 rounded-md bg-(--background-secondary) hover:bg-(--background-tertiary) text-primary font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                                >
                                    {isLoadingMore && <FaSpinner className="animate-spin" size={14} />}
                                    {isLoadingMore ? 'Loading...' : 'Load More'}
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default GalleryPage;
