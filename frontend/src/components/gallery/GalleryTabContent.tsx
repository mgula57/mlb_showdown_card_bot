import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FaImages, FaTrash, FaSpinner, FaExpand, FaTimes } from 'react-icons/fa';
import { FaRotateLeft } from 'react-icons/fa6';
import { fetchUserGallery, deleteGalleryCard, type GalleryImageRecord, type GalleryFilters } from '../../api/gallery';
import { Modal } from '../shared/Modal';
import FormInput from '../customs/FormInput';
import FormDropdown from '../customs/FormDropdown';
import CustomSelect from '../shared/CustomSelect';
import { showdownSets } from '../shared/SiteSettingsContext';

type User = { id: string } | null | undefined;

interface GalleryTabContentProps {
    user: User;
    token: string | null;
    onReload?: (userInputs: Record<string, unknown>) => void;
    refreshKey?: number;
}

const PAGE_SIZE = 50;

// ----------------------------------------------------------------
// GalleryCard
// ----------------------------------------------------------------
const GalleryCard: React.FC<{
    item: GalleryImageRecord;
    onDeleteRequest: (id: number) => void;
    onPreview: (url: string, label: string) => void;
    onReload?: (userInputs: Record<string, unknown>) => void;
    isDeleting: boolean;
}> = ({ item, onDeleteRequest, onPreview, onReload, isDeleting }) => {
    const [isHovered, setIsHovered] = useState(false);
    const fullUrl = item.public_url ?? item.storage_path;
    const thumbUrl = item.thumbnail_public_url ?? fullUrl;
    const label = [item.player_name, item.year, item.set_name].filter(Boolean).join(' · ');

    return (
        <div
            className="flex flex-col gap-1"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <div
                className="relative rounded-md overflow-hidden bg-(--background-secondary)"
                style={{ aspectRatio: '2.5 / 3.5' }}
            >
                {thumbUrl ? (
                    <img src={thumbUrl} alt={label} loading="lazy" className="w-full h-full object-cover" />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-secondary text-xs">No image</div>
                )}

                {isHovered && (
                    <div className="absolute inset-0 bg-black/50 flex items-end justify-center gap-2 pb-3">
                        <button
                            onClick={() => fullUrl && onPreview(fullUrl, label)}
                            className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors"
                            title="View"
                        >
                            <FaExpand size={13} />
                        </button>

                        {onReload && item.user_inputs && (
                            <button
                                onClick={() => onReload(item.user_inputs!)}
                                className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors"
                                title="Reload into form"
                            >
                                <FaRotateLeft size={13} />
                            </button>
                        )}

                        <button
                            onClick={() => onDeleteRequest(item.id)}
                            disabled={isDeleting}
                            className="p-2 rounded-full bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50"
                            title="Remove from gallery"
                        >
                            {isDeleting ? <FaSpinner className="animate-spin" size={13} /> : <FaTrash size={13} />}
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

// ----------------------------------------------------------------
// LightboxImage
// ----------------------------------------------------------------
const LightboxImage: React.FC<{ url: string; label: string }> = ({ url, label }) => {
    const [loaded, setLoaded] = useState(false);
    return (
        <div className="relative rounded-md overflow-hidden bg-(--background-secondary)" style={{ height: '75dvh', aspectRatio: '2.5 / 3.5' }}>
            {!loaded && (
                <div className="absolute inset-0 flex items-center justify-center">
                    <FaSpinner className="animate-spin text-secondary" size={24} />
                </div>
            )}
            <img
                src={url}
                alt={label}
                onLoad={() => setLoaded(true)}
                className={`w-full h-full object-contain transition-opacity duration-200 ${loaded ? 'opacity-100' : 'opacity-0'}`}
            />
        </div>
    );
};

// ----------------------------------------------------------------
// GalleryTabContent
// ----------------------------------------------------------------
export const GalleryTabContent: React.FC<GalleryTabContentProps> = ({ user, token, onReload, refreshKey }) => {
    const [gallery, setGallery] = useState<GalleryImageRecord[]>([]);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);
    const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null);
    const [lightbox, setLightbox] = useState<{ url: string; label: string } | null>(null);

    // Filter state
    const [nameInput, setNameInput] = useState('');
    const [yearInput, setYearInput] = useState('');
    const [filters, setFilters] = useState<GalleryFilters>({});
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const hasActiveFilters = !!(filters.set_name || filters.player_name || filters.year || filters.player_type);

    const loadGallery = useCallback(async (reset: boolean, activeFilters: GalleryFilters) => {
        if (!token) return;
        const currentOffset = reset ? 0 : offset;
        setIsLoading(true);
        try {
            const data = await fetchUserGallery(token, PAGE_SIZE, currentOffset, activeFilters);
            setGallery(prev => reset ? data.gallery : [...prev, ...data.gallery]);
            setOffset(currentOffset + data.gallery.length);
            setHasMore(data.has_more);
        } catch (err) {
            console.error('Failed to load gallery:', err);
        } finally {
            setIsLoading(false);
        }
    }, [token, offset]);

    // Initial load when user/token become available; re-runs when refreshKey changes
    useEffect(() => {
        if (user && token) {
            loadGallery(true, filters);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user, token, refreshKey]);

    const applyFilters = (next: GalleryFilters) => {
        setFilters(next);
        setOffset(0);
        loadGallery(true, next);
    };

    const handleNameInputChange = (value: string) => {
        setNameInput(value);
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
            applyFilters({ ...filters, player_name: value || undefined });
        }, 300);
    };

    const handleSetChange = (value: string) => {
        applyFilters({ ...filters, set_name: value || undefined });
    };

    const handleYearChange = (value: string) => {
        setYearInput(value);
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
            applyFilters({ ...filters, year: value || undefined });
        }, 400);
    };

    const handleConfirmDelete = async () => {
        const id = pendingDeleteId;
        if (!id || !token) return;
        setPendingDeleteId(null);
        setDeletingId(id);
        try {
            await deleteGalleryCard(token, id);
            setGallery(prev => prev.filter(item => item.id !== id));
        } catch (err) {
            console.error('Failed to delete gallery card:', err);
        } finally {
            setDeletingId(null);
        }
    };

    if (!user) {
        return (
            <div className="flex flex-col items-center justify-center h-48 gap-3 text-secondary">
                <FaImages size={28} className="opacity-40" />
                <p className="text-sm">Sign in to save and browse your cards.</p>
            </div>
        );
    }

    return (
        <>
            {/* Delete confirmation */}
            {pendingDeleteId !== null && (
                <Modal size="sm" onClose={() => setPendingDeleteId(null)}>
                    <div className="p-6 flex flex-col gap-5">
                        <div className="flex flex-col gap-1">
                            <h2 className="text-lg font-semibold text-primary">Remove card?</h2>
                            <p className="text-sm text-secondary">This card will be hidden from your gallery.</p>
                        </div>
                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => setPendingDeleteId(null)}
                                className="px-4 py-2 rounded-lg bg-(--background-secondary) hover:bg-(--background-tertiary) text-primary text-sm font-medium transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleConfirmDelete}
                                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors"
                            >
                                Remove
                            </button>
                        </div>
                    </div>
                </Modal>
            )}

            {/* Lightbox */}
            {lightbox && (
                <Modal size="lg" onClose={() => setLightbox(null)}>
                    <div className="py-8 px-8 flex flex-col items-center gap-3">
                        <LightboxImage url={lightbox.url} label={lightbox.label} />
                        {lightbox.label && <p className="text-sm text-secondary">{lightbox.label}</p>}
                    </div>
                </Modal>
            )}

            {/* Filter bar */}
            <div className="px-3 pt-3 pb-2 flex gap-2 border-b border-form-element">
                {/* Row 1: player name search + clear */}
                <div className="flex-1">
                    <FormInput
                        label=""
                        value={nameInput}
                        placeholder="Search player…"
                        onChange={value => handleNameInputChange(value || '')}
                        isClearable={true}
                    />
                </div>                

                {/* Row 2: Set, Year, Player type */}
                <div className="flex items-end gap-1.5">
                    {/* Set dropdown */}

                    <CustomSelect
                        options={[{ value: '', label: 'All Sets', image: undefined, textColor: 'text-secondary' },...showdownSets]}
                        value={filters.set_name ?? ''}
                        onChange={handleSetChange}
                        buttonClassName="h-11 w-full border-2 border-form-element rounded-xl px-3 bg-(--background-secondary) text-primary focus:outline-none cursor-pointer"
                        imageClassName="max-w-18 object-contain object-center"
                    />

                    {/* Year input */}
                    <div className="w-24 shrink-0">
                        <FormInput
                            label=""
                            value={yearInput}
                            placeholder="Year"
                            inputMode="numeric"
                            onChange={value => handleYearChange((value ?? '').slice(0, 4))}
                        />
                    </div>

                </div>
            </div>

            {/* Grid */}
            <div className="p-3">
                {isLoading && gallery.length === 0 ? (
                    <div className="flex items-center justify-center py-16">
                        <FaSpinner className="animate-spin text-secondary" size={24} />
                    </div>
                ) : gallery.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-16 gap-3 text-secondary">
                        <FaImages size={36} className="opacity-30" />
                        <p className="text-sm font-medium">
                            {hasActiveFilters ? 'No cards match these filters' : 'No cards yet'}
                        </p>
                        {!hasActiveFilters && (
                            <p className="text-xs text-center max-w-xs">Cards you generate while signed in will appear here.</p>
                        )}
                    </div>
                ) : (
                    <>
                        <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(min(175px, 100%), 1fr))' }}>
                            {gallery.map(item => (
                                <GalleryCard
                                    key={item.id}
                                    item={item}
                                    onDeleteRequest={setPendingDeleteId}
                                    onPreview={(url, label) => setLightbox({ url, label })}
                                    onReload={onReload}
                                    isDeleting={deletingId === item.id}
                                />
                            ))}
                        </div>

                        {hasMore && (
                            <div className="flex justify-center mt-4">
                                <button
                                    onClick={() => loadGallery(false, filters)}
                                    disabled={isLoading}
                                    className="px-5 py-2 rounded-md bg-(--background-secondary) hover:bg-(--background-tertiary) text-primary text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                                >
                                    {isLoading && <FaSpinner className="animate-spin" size={12} />}
                                    {isLoading ? 'Loading…' : 'Load More'}
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </>
    );
};
