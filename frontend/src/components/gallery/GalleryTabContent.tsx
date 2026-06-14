import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FaImages, FaSpinner, FaExpand, FaEyeSlash, FaEye, FaChevronUp } from 'react-icons/fa';
import { SignInPrompt } from '../shared/SignInPrompt';
import { FaPencil } from 'react-icons/fa6';
import { fetchUserGallery, deleteGalleryCard, unhideGalleryCard, type GalleryImageRecord, type GalleryFilters } from '../../api/gallery';
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

// ----------------------------------------------------------------
// Stack grouping — consecutive items with same player/year/set
// ----------------------------------------------------------------
interface GalleryStack {
    stackId: number; // first item's id — stable key for expanded state
    items: GalleryImageRecord[];
}

function groupIntoStacks(gallery: GalleryImageRecord[]): GalleryStack[] {
    const stacks: GalleryStack[] = [];
    for (const item of gallery) {
        const last = stacks[stacks.length - 1];
        const sameGroup =
            last &&
            last.items[0].player_name === item.player_name &&
            last.items[0].year === item.year &&
            last.items[0].set_name === item.set_name;
        if (sameGroup) {
            last.items.push(item);
        } else {
            stacks.push({ stackId: item.id, items: [item] });
        }
    }
    return stacks;
}

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
// GalleryStackCell — collapsed multi-card stack with expand toggle
// ----------------------------------------------------------------
const GalleryStackCell: React.FC<{
    stack: GalleryStack;
    isExpanded: boolean;
    onToggle: () => void;
    onDeleteRequest: (id: number) => void;
    onUnhideRequest: (id: number) => void;
    onPreview: (cardResult: ShowdownBotCard) => void;
    onReload?: (userInputs: Record<string, unknown>, cardResult: ShowdownBotCard) => void;
    deletingId: number | null;
    showingHidden: boolean;
    isDimmed?: boolean;
}> = ({ stack, isExpanded, onToggle, onDeleteRequest, onUnhideRequest, onPreview, onReload, deletingId, showingHidden, isDimmed }) => {
    const { items } = stack;
    const top = items[0];
    const count = items.length;
    const thumbUrl = top.thumbnail_public_url ?? top.public_url ?? top.storage_path;
    const label = [top.player_name, top.year, top.set_name].filter(Boolean).join(' · ');

    if (isExpanded) {
        return (
            <>
                {items.map(item => (
                    <GalleryCard
                        key={item.id}
                        item={item}
                        onDeleteRequest={onDeleteRequest}
                        onUnhideRequest={onUnhideRequest}
                        onPreview={onPreview}
                        onReload={onReload}
                        isDeleting={deletingId === item.id}
                        showingHidden={showingHidden}
                    />
                ))}
                {/* Collapse button spanning the whole row width */}
                <div className="col-span-full flex justify-center mt-1 mb-2">
                    <button
                        onClick={onToggle}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-(--background-secondary) hover:bg-(--background-tertiary) text-secondary hover:text-primary text-xs font-medium transition-colors border border-form-element"
                    >
                        <FaChevronUp size={10} />
                        Collapse {label}
                    </button>
                </div>
            </>
        );
    }

    const [isHovered, setIsHovered] = useState(false);
    const thumb2 = items[1] ? (items[1].thumbnail_public_url ?? items[1].public_url ?? items[1].storage_path) : null;

    const t = 'transform 0.2s ease';
    const topT = isHovered ? 'translateY(-6px)' : 'none';
    const ghost2T = isHovered ? 'translate(9px, 12px) rotate(3deg)' : 'translate(5px, 7px) rotate(1.2deg)';

    return (
        <div className={`flex flex-col gap-2 transition-all duration-200 ${isDimmed ? 'opacity-30 grayscale pointer-events-none' : ''}`} style={{ paddingBottom: count >= 3 ? '14px' : count >= 2 ? '8px' : '0' }}>
            <button
                onClick={onToggle}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                className="relative rounded-md overflow-visible bg-transparent text-left"
                style={{ aspectRatio: '2.5 / 3.5' }}
                title={`${count} versions — click to expand`}
            >

                {/* Ghost card 2 — middle of pile */}
                {count >= 2 && (
                    <div
                        className="absolute inset-0 rounded-md overflow-hidden shadow-sm"
                        style={{ transform: ghost2T, transition: t, zIndex: 1, transformOrigin: 'top left' }}
                    >
                        {thumb2 ? (
                            <img src={thumb2} alt="" loading="lazy" className="w-full h-full object-cover grayscale-60 brightness-75" />
                        ) : (
                            <div className="w-full h-full bg-(--background-tertiary) border border-form-element rounded-md" />
                        )}
                        <div className="absolute inset-0 bg-black/25" />
                    </div>
                )}
                {/* Top card */}
                <div
                    className="absolute inset-0 rounded-md overflow-hidden shadow-md"
                    style={{ transform: topT, transition: t, zIndex: 2 }}
                >
                    {thumbUrl ? (
                        <img src={thumbUrl} alt={label} loading="lazy" className={`w-full h-full object-cover transition-transform duration-200 ${isHovered ? 'scale-105' : 'scale-100'}`} />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-secondary text-xs bg-(--background-secondary)">No image</div>
                    )}
                </div>
                {/* Count badge */}
                <div
                    className="absolute top-1.5 left-1.5 bg-blue-600 text-white text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center leading-none shadow"
                    style={{ zIndex: 3 }}
                >
                    {count}
                </div>
            </button>
            <div className="flex flex-col space-y-0.5">
                {label && (
                    <p className="text-[10px] font-bold text-secondary text-center truncate px-1">{label}</p>
                )}
            </div>
        </div>
    );
};

// ----------------------------------------------------------------
// GalleryCard
// ----------------------------------------------------------------
const GalleryCard: React.FC<{
    item: GalleryImageRecord;
    onDeleteRequest: (id: number) => void;
    onUnhideRequest: (id: number) => void;
    onPreview: (cardResult: ShowdownBotCard) => void;
    onReload?: (userInputs: Record<string, unknown>, cardResult: ShowdownBotCard) => void;
    isDeleting: boolean;
    showingHidden: boolean;
    isDimmed?: boolean;
}> = ({ item, onDeleteRequest, onUnhideRequest, onPreview, onReload, isDeleting, showingHidden, isDimmed }) => {
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
            className={`flex flex-col gap-2 transition-all duration-200 ${isDimmed ? 'opacity-30 grayscale pointer-events-none' : ''}`}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <div
                className="relative rounded-md overflow-hidden bg-(--background-secondary)"
                style={{ aspectRatio: '2.5 / 3.5' }}
            >
                {thumbUrl ? (
                    <img src={thumbUrl} alt={label} loading="lazy" className={`w-full h-full object-cover transition-transform duration-200 ${isHovered ? 'scale-105' : 'scale-100'}`} />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-secondary text-xs">No image</div>
                )}

                {isHovered && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center gap-2 pb-3">
                        <button
                            onClick={() => { if (item.card_result) onPreview(item.card_result); }}
                            className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors"
                            title="View"
                        >
                            <FaExpand size={16} />
                        </button>

                        {!showingHidden && onReload && item.user_inputs && (
                            <button
                                onClick={() => onReload(item.user_inputs!, item.card_result!)}
                                className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors"
                                title="Reload into form"
                            >
                                <FaPencil size={16} />
                            </button>
                        )}

                        {showingHidden ? (
                            <button
                                onClick={() => onUnhideRequest(item.id)}
                                disabled={isDeleting}
                                className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors disabled:opacity-40"
                                title="Restore to gallery"
                            >
                                <FaEye size={16} />
                            </button>
                        ) : (
                            <button
                                onClick={() => onDeleteRequest(item.id)}
                                disabled={isDeleting}
                                className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors disabled:opacity-40"
                                title="Hide from gallery"
                            >
                                <FaEyeSlash size={16} />
                            </button>
                        )}
                    </div>
                )}
            </div>
            <div className='flex flex-col space-y-0.5'>
                {label && (
                    <p className="text-[10px] font-bold text-secondary text-center truncate px-1">{label}</p>
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
    const [showingHidden, setShowingHidden] = useState(false);
    const [expandedStacks, setExpandedStacks] = useState<Set<number>>(new Set());

    const toggleStack = (stackId: number) => {
        setExpandedStacks(prev => {
            const next = new Set(prev);
            if (next.has(stackId)) next.delete(stackId);
            else next.add(stackId);
            return next;
        });
    };

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
    const filterTextClassName = "h-11 text-xs md:text-sm w-full leading-tight border-2 border-form-element rounded-xl px-3 bg-(--background-secondary) text-primary focus:outline-none cursor-pointer";

    const hasActiveFilters = !!(filters.set_name || filters.player_name || filters.year || filters.player_type || filters.edition || filters.expansion || filters.team);

    const loadGallery = useCallback(async (pageOffset: number, activeFilters: GalleryFilters, showHidden: boolean = false) => {
        if (!token) {
            console.warn('Attempted to load gallery without token');
            return;
        }
        setIsLoading(true);
        try {
            const data = await fetchUserGallery(token, PAGE_SIZE, pageOffset, activeFilters, showHidden);
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
        loadGallery(0, next, showingHidden);
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

    const handleUnhide = async (id: number) => {
        if (!token) return;
        setDeletingId(id);
        try {
            await unhideGalleryCard(token, id);
            setGallery(prev => prev.filter(item => item.id !== id));
        } catch (err) {
            console.error('Failed to unhide gallery card:', err);
        } finally {
            setDeletingId(null);
        }
    };

    const handleToggleHidden = () => {
        const next = !showingHidden;
        setShowingHidden(next);
        loadGallery(0, filters, next);
    };

    if (!user) {
        return (
            <SignInPrompt
                icon={<FaImages size={28} />}
                title="Your Gallery"
                message="Sign in to save and browse your cards."
                className="h-full mt-12"
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
                            <p className="text-sm text-secondary">This card will be hidden from your gallery. You can unhide it later if you change your mind by using the "Active/Hidden" toggle.</p>
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

                {/* Row 2: Set + Expansion + Edition + Team + Year + Hidden toggle */}
                <div className="flex items-end gap-1.5 w-full overflow-x-scroll">
                    <CustomSelect
                        options={[{ value: '', label: 'All Sets', image: undefined, textColor: 'text-secondary' }, ...showdownSets]}
                        value={filters.set_name ?? ''}
                        onChange={handleSetChange}
                        buttonClassName={filterTextClassName}
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
                        buttonClassName={filterTextClassName}
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
                        buttonClassName={filterTextClassName}
                    />
                    <CustomSelect
                        options={teamOptions}
                        value={filters.team ?? ''}
                        onChange={handleTeamChange}
                        buttonClassName={filterTextClassName}
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
                    <button
                        onClick={handleToggleHidden}
                        className={`
                            shrink-0 flex items-center gap-1.5 px-3 h-11 
                            rounded-xl border-2 
                            text-xs font-medium 
                            transition-colors 
                            ${showingHidden ? 'border-primary text-primary' : 'border-form-element text-secondary hover:text-primary'} 
                            bg-(--background-secondary)
                            cursor-pointer
                        `}
                        title={showingHidden ? 'Show active cards' : 'Show hidden cards'}
                    >
                        <FaEyeSlash size={13} />
                        {showingHidden ? 'Hidden Only' : 'Active Only'}
                    </button>
                </div>
            </div>

            {/* Grid */}
            <div className="p-3">
                {gallery.length === 0 && !isLoading ? (
                    <div className="flex flex-col items-center justify-center py-16 gap-3 text-secondary">
                        <FaImages size={36} className="opacity-30" />
                        <p className="text-sm font-medium">
                            {hasActiveFilters ? 'No cards match these filters' : showingHidden ? 'No hidden cards' : 'No cards yet'}
                        </p>
                        {!hasActiveFilters && !showingHidden && (
                            <p className="text-xs text-center max-w-xs">Cards you generate while signed in will appear here.</p>
                        )}
                    </div>
                ) : (
                    <>
                        <div className="relative">
                            {isLoading && (
                                <div className="absolute inset-10 z-50 flex items-center justify-center bg-(--background-primary)/60 backdrop-blur-[2px] rounded-xl">
                                    <FaSpinner className="animate-spin text-secondary" size={24} />
                                </div>
                            )}
                            <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(135px, 1fr))' }}>
                                {(() => {
                                    const stacks = groupIntoStacks(gallery);
                                    const anyExpanded = expandedStacks.size > 0;
                                    return stacks.map(stack => {
                                        const isExpanded = expandedStacks.has(stack.stackId);
                                        const isDimmed = anyExpanded && !isExpanded;
                                        return stack.items.length === 1 ? (
                                            <GalleryCard
                                                key={stack.stackId}
                                                item={stack.items[0]}
                                                onDeleteRequest={setPendingDeleteId}
                                                onUnhideRequest={handleUnhide}
                                                onPreview={setSelectedCard}
                                                onReload={onReload}
                                                isDeleting={deletingId === stack.items[0].id}
                                                showingHidden={showingHidden}
                                                isDimmed={isDimmed}
                                            />
                                        ) : (
                                            <GalleryStackCell
                                                key={stack.stackId}
                                                stack={stack}
                                                isExpanded={isExpanded}
                                                onToggle={() => toggleStack(stack.stackId)}
                                                onDeleteRequest={setPendingDeleteId}
                                                onUnhideRequest={handleUnhide}
                                                onPreview={setSelectedCard}
                                                onReload={onReload}
                                                deletingId={deletingId}
                                                showingHidden={showingHidden}
                                                isDimmed={isDimmed}
                                            />
                                        );
                                    });
                                })()}
                            </div>

                            {(currentPage > 1 || hasMore) && (
                                <div className="flex items-center justify-center gap-3 mt-4">
                                    <button
                                        onClick={() => loadGallery(offset - PAGE_SIZE, filters, showingHidden)}
                                        disabled={isLoading || currentPage === 1}
                                        className="px-4 py-2 rounded-md bg-(--background-secondary) hover:bg-(--background-tertiary) text-primary text-sm font-medium transition-colors disabled:opacity-40"
                                    >
                                        ← Prev
                                    </button>
                                    <span className="text-sm text-secondary min-w-16 text-center">
                                        {isLoading ? <FaSpinner className="animate-spin inline" size={12} /> : `Page ${currentPage}`}
                                    </span>
                                    <button
                                        onClick={() => loadGallery(offset + PAGE_SIZE, filters, showingHidden)}
                                        disabled={isLoading || !hasMore}
                                        className="px-4 py-2 rounded-md bg-(--background-secondary) hover:bg-(--background-tertiary) text-primary text-sm font-medium transition-colors disabled:opacity-40"
                                    >
                                        Next →
                                    </button>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </>
    );
};
