import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FaImages, FaSpinner, FaExpand, FaStar } from 'react-icons/fa';
import { SignInPrompt } from '../shared/SignInPrompt';
import { FaPencil } from 'react-icons/fa6';
import { fetchUserGallery, deleteGalleryCard, type GalleryImageRecord, type GalleryFilters } from '../../api/gallery';
import { fetchTeamHierarchy } from '../../api/card_db/cardDatabase';
import { Modal } from '../shared/Modal';
import FormInput from '../customs/FormInput';
import CustomSelect from '../shared/CustomSelect';
import { showdownSets } from '../shared/SiteSettingsContext';

const cardImagePath = (name: string) => `/images/card/${name}.png`;
import { type ShowdownBotCard, type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import { CardDetail } from '../cards/CardDetail';

type User = { id: string } | null | undefined;

interface GalleryTabContentProps {
    user: User;
    token: string | null;
    onReload?: (userInputs: Record<string, unknown>, cardResult: ShowdownBotCard) => void;
    refreshKey?: number;
}

const PAGE_SIZE = 50;

const EDITION_LABELS: Record<string, string> = {
    CC: 'Cooperstown',
    SS: 'Super Season',
    RS: 'Rookie Season',
    ASG: 'All-Star Game',
    WBC: 'WBC',
    POST: 'Postseason',
};

const PARALLEL_LABELS: Record<string, string> = {
    RF: 'Rainbow Foil',
    TCB: 'Team Color Blast',
    GALAXY: 'Galaxy',
    GOLD: 'Gold',
    GOLDRUSH: 'Gold Rush',
    GF: 'Gold Frame',
    SPH: 'Sapphire',
    'B&W': 'Black & White',
    RAD: 'Radial',
    CB: 'Comic Book Hero',
    WS: 'White Smoke',
    FLAMES: 'Flames',
    MYSTERY: 'Mystery',
};

const STATS_PERIOD_LABELS: Record<string, string> = {
    CAREER: 'Career',
    SPLIT: 'Split',
    DATES: 'Date Range',
    POST: 'Postseason',
};

// ----------------------------------------------------------------
// GalleryCard
// ----------------------------------------------------------------
const GalleryCard: React.FC<{
    item: GalleryImageRecord;
    onDeleteRequest: (id: number) => void;
    onPreview: (cardResult: ShowdownBotCard) => void;
    onReload?: (userInputs: Record<string, unknown>, cardResult: ShowdownBotCard) => void;
    isDeleting: boolean;
}> = ({ item, onDeleteRequest, onPreview, onReload, isDeleting }) => {
    const [isHovered, setIsHovered] = useState(false);
    const fullUrl = item.public_url ?? item.storage_path;
    const thumbUrl = item.thumbnail_public_url ?? fullUrl;
    const label = [item.player_name, item.year, item.set_name].filter(Boolean).join(' · ');

    const inputs = item.user_inputs ?? {};
    const badges = [
        EDITION_LABELS[inputs.edition as string],
        PARALLEL_LABELS[inputs.image_parallel as string],
        STATS_PERIOD_LABELS[inputs.stats_period_type as string],
        inputs.chart_version !== '1' ? `v${inputs.chart_version}` : undefined,
        inputs.set_number ? `#${inputs.set_number}` : undefined,
    ].filter(Boolean) as string[];
    
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
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center gap-2 pb-3">
                        <button
                            onClick={
                                () => {
                                    if (item.card_result) {
                                        onPreview(item.card_result);
                                    }
                                    console.log("Preview card result:", item.card_result);
                                }
                            }
                            className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors"
                            title="View"
                        >
                            <FaExpand size={16} />
                        </button>

                        {onReload && item.user_inputs && (
                            <button
                                onClick={() => onReload(item.user_inputs!, item.card_result!)}
                                className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors"
                                title="Reload into form"
                            >
                                <FaPencil size={16} />
                            </button>
                        )}

                    </div>
                )}
            </div>
            <div className='flex flex-col space-y-0.5'>
                {label && (
                    <p className="text-xs font-bold text-secondary text-center truncate px-1">{label}</p>
                )}
                {badges.length > 0 && (
                    <div className="flex flex-wrap justify-center">
                        {badges.map(badge => (
                            <span key={badge} className="text-[10px] leading-tight px-1 rounded-full bg-(--background-secondary) text-secondary truncate max-w-full">
                                {badge}
                            </span>
                        ))}
                    </div>
                )}
            </div>
            
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
    const [selectedCard, setSelectedCard] = useState<ShowdownBotCard | null>(null);

    // Team options for dropdown
    const [teamOptions, setTeamOptions] = useState<{ value: string; label: string }[]>([]);
    useEffect(() => {
        fetchTeamHierarchy().then(data => {
            const mlbTeams = [...new Set(
                data.filter(r => r.organization === 'MLB').map(r => r.team)
            )].sort();
            setTeamOptions([
                { value: '', label: 'All Teams' },
                ...mlbTeams.map(t => ({ value: t, label: t })),
            ]);
        });
    }, []);

    // Filter state
    const [nameInput, setNameInput] = useState('');
    const [yearInput, setYearInput] = useState('');
    const [filters, setFilters] = useState<GalleryFilters>({});
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const hasActiveFilters = !!(filters.set_name || filters.player_name || filters.year || filters.player_type || filters.edition || filters.expansion || filters.team);

    const loadGallery = useCallback(async (pageOffset: number, activeFilters: GalleryFilters) => {
        if (!token) return;
        setIsLoading(true);
        try {
            const data = await fetchUserGallery(token, PAGE_SIZE, pageOffset, activeFilters);
            setGallery(data.gallery);
            setOffset(pageOffset);
            setHasMore(data.has_more);
        } catch (err) {
            console.error('Failed to load gallery:', err);
        } finally {
            setIsLoading(false);
        }
    }, [token]);

    // Initial load when user/token become available; re-runs when refreshKey changes
    useEffect(() => {
        if (user && token) {
            loadGallery(0, filters);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user, token, refreshKey]);

    const applyFilters = (next: GalleryFilters) => {
        setFilters(next);
        loadGallery(0, next);
    };

    const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

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

    const handleEditionChange = (value: string) => {
        applyFilters({ ...filters, edition: value || undefined });
    };

    const handleExpansionChange = (value: string) => {
        applyFilters({ ...filters, expansion: value || undefined });
    };

    const handleTeamChange = (value: string) => {
        applyFilters({ ...filters, team: value || undefined });
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
            <SignInPrompt
                icon={<FaImages size={28} />}
                title="Your Gallery"
                message="Sign in to save and browse your cards."
                className="h-48 mt-12"
            />
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

            {/* Modal for selected card */}
            <div className={!!selectedCard ? '' : 'hidden pointer-events-none'}>
                <Modal isVisible={!!selectedCard} onClose={() => setSelectedCard(null)} size="lg">
                    <CardDetail
                        showdownBotCardData={selectedCard ? { card: selectedCard } as ShowdownBotCardAPIResponse : undefined}
                        hideTrendGraphs={true}
                        context='explore'
                        parent="modal"
                    />
                </Modal>
            </div>

            {/* Filter bar */}
            <div className="px-3 pt-3 pb-2 flex flex-col gap-2 border-b border-form-element">
                {/* Row 1: player name search */}
                <FormInput
                    label=""
                    value={nameInput}
                    placeholder="Search for player…"
                    onChange={value => handleNameInputChange(value || '')}
                    isClearable={true}
                />

                {/* Row 2: Set + Expansion + Edition + Team + Year */}
                <div className="flex items-end gap-1.5 w-full overflow-x-scroll">
                    <CustomSelect
                        options={[{ value: '', label: 'All Sets', image: undefined, textColor: 'text-secondary' }, ...showdownSets]}
                        value={filters.set_name ?? ''}
                        onChange={handleSetChange}
                        buttonClassName="h-11 w-full leading-tight border-2 border-form-element rounded-xl px-3 bg-(--background-secondary) text-primary focus:outline-none cursor-pointer"
                        imageClassName="max-w-18 object-contain object-center"
                    />
                    <CustomSelect
                        options={[
                            { value: '', label: 'All Expansions', textColor: 'text-secondary' },
                            { value: 'BS', label: 'Base Set', image: cardImagePath('expansion-bs') },
                            { value: 'TD', label: 'Trading Deadline', image: cardImagePath('expansion-td'), borderColor: 'border-red-600' },
                            { value: 'PR', label: 'Pennant Run', image: cardImagePath('expansion-pr'), borderColor: 'border-blue-900' },
                        ]}
                        value={filters.expansion ?? ''}
                        onChange={handleExpansionChange}
                        buttonClassName="h-11 w-full leading-tight border-2 border-form-element rounded-xl px-3 bg-(--background-secondary) text-primary focus:outline-none cursor-pointer"
                    />
                    <CustomSelect
                        options={[
                            { value: '', label: 'All Editions', textColor: 'text-secondary' },
                            { value: 'CC', label: 'Cooperstown', image: cardImagePath('edition-cc'), borderColor: 'border-amber-800' },
                            { value: 'SS', label: 'Super Season', image: cardImagePath('edition-ss'), borderColor: 'border-red-500' },
                            { value: 'RS', label: 'Rookie Season', image: cardImagePath('edition-rs'), borderColor: 'border-red-800' },
                            { value: 'ASG', label: 'All-Star Game', symbol: '⭐', borderColor: 'border-yellow-400' },
                            { value: 'WBC', label: 'WBC', image: cardImagePath('edition-wbc'), borderColor: 'border-red-700' },
                            { value: 'POST', label: 'Postseason', image: cardImagePath('edition-post'), borderColor: 'border-blue-800' },
                        ]}
                        value={filters.edition ?? ''}
                        onChange={handleEditionChange}
                        buttonClassName="h-11 w-full leading-tight border-2 border-form-element rounded-xl px-3 bg-(--background-secondary) text-primary focus:outline-none cursor-pointer"
                    />
                    <CustomSelect
                        options={teamOptions}
                        value={filters.team ?? ''}
                        onChange={handleTeamChange}
                        buttonClassName="h-11 w-full leading-tight border-2 border-form-element rounded-xl px-3 bg-(--background-secondary) text-primary focus:outline-none cursor-pointer"
                    />
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
                        <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(175px, 1fr))' }}>
                            {gallery.map(item => (
                                <GalleryCard
                                    key={item.id}
                                    item={item}
                                    onDeleteRequest={setPendingDeleteId}
                                    onPreview={(cardResult) => setSelectedCard(cardResult)}
                                    onReload={onReload}
                                    isDeleting={deletingId === item.id}
                                />
                            ))}
                        </div>

                        {(currentPage > 1 || hasMore) && (
                            <div className="flex items-center justify-center gap-3 mt-4">
                                <button
                                    onClick={() => loadGallery(offset - PAGE_SIZE, filters)}
                                    disabled={isLoading || currentPage === 1}
                                    className="px-4 py-2 rounded-md bg-(--background-secondary) hover:bg-(--background-tertiary) text-primary text-sm font-medium transition-colors disabled:opacity-40"
                                >
                                    ← Prev
                                </button>
                                <span className="text-sm text-secondary min-w-16 text-center">
                                    {isLoading ? <FaSpinner className="animate-spin inline" size={12} /> : `Page ${currentPage}`}
                                </span>
                                <button
                                    onClick={() => loadGallery(offset + PAGE_SIZE, filters)}
                                    disabled={isLoading || !hasMore}
                                    className="px-4 py-2 rounded-md bg-(--background-secondary) hover:bg-(--background-tertiary) text-primary text-sm font-medium transition-colors disabled:opacity-40"
                                >
                                    Next →
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </>
    );
};
