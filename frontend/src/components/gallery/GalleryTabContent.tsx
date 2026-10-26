import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FaImages, FaSpinner, FaExpand, FaEyeSlash, FaEye, FaChevronUp, FaBaseballBall } from 'react-icons/fa';
import { SignInPrompt } from '../shared/SignInPrompt';
import { FaPencil } from 'react-icons/fa6';
import { fetchUserGallery, deleteGalleryCard, unhideGalleryCard, type GalleryImageRecord, type GalleryFilters } from '../../api/gallery';
import { fetchTeamHierarchy } from '../../api/card_db/cardDatabase';
import { Modal } from '../shared/Modal';
import FormInput from '../customs/FormInput';
import CustomSelect from '../shared/CustomSelect';
import { expansionOptions, editionOptions } from '../customs/cardStyle';
import { buttonClass } from '../shared/buttonStyles';
import { choiceClass } from '../shared/choiceStyles';
import { SetBadge, SET_SELECT_OPTIONS } from '../shared/SetBadge';

/** Editions offered as gallery filters (the rest of `editionOptions` rarely appear in a gallery). */
const GALLERY_EDITION_FILTERS = new Set(['CC', 'SS', 'RS', 'ASG', 'WBC', 'POST']);
import { type ShowdownBotCard, type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import { CardDetail } from '../cards/CardDetail';

import { Heading } from '../shared/Heading';
import { EmptyState } from '../shared/EmptyState';
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
    const stackTextLabel = [top.player_name, top.year].filter(Boolean).join(' · ');

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
                        type="button"
                        onClick={onToggle}
                        className={buttonClass('secondary', 'sm')}
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
                className="relative rounded-control overflow-visible bg-transparent text-left cursor-pointer"
                style={{ aspectRatio: '2.5 / 3.5' }}
                title={`${count} versions — click to expand`}
            >

                {/* Ghost card 2 — middle of pile */}
                {count >= 2 && (
                    <div
                        className="absolute inset-0 rounded-[3px] overflow-hidden shadow-raised"
                        style={{ transform: ghost2T, transition: t, zIndex: 1, transformOrigin: 'top left' }}
                    >
                        {thumb2 ? (
                            <img src={thumb2} alt="" loading="lazy" className="w-full h-full object-cover grayscale-60 brightness-75" />
                        ) : (
                            <div className="w-full h-full bg-(--background-tertiary) border border-(--divider) rounded-card" />
                        )}
                        <div className="absolute inset-0 bg-black/25" />
                    </div>
                )}
                {/* Top card */}
                <div
                    className="absolute inset-0 rounded-[3px] overflow-hidden shadow-raised"
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
                    className="absolute top-1.5 left-1.5 bg-(--showdown-blue-fill) text-white text-[10px] font-bold tabular-nums rounded-plate min-w-5 h-5 px-1 flex items-center justify-center leading-none"
                    style={{ zIndex: 3 }}
                >
                    {count}
                </div>
            </button>
            <div className="flex flex-col items-center gap-0.5">
                {stackTextLabel && (
                    <p className="text-[10px] font-bold text-secondary text-center truncate px-1 w-full">{stackTextLabel}</p>
                )}
                {top.set_name && <SetBadge set={top.set_name} size="sm" />}
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
    const textLabel = [item.player_name, item.year].filter(Boolean).join(' · ');

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
                className="relative rounded-card overflow-hidden bg-(--background-secondary)"
                style={{ aspectRatio: '2.5 / 3.5' }}
            >
                {thumbUrl ? (
                    <img src={thumbUrl} alt={label} loading="lazy" className={`w-full h-full object-cover transition-transform duration-200`} />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-secondary text-xs">No image</div>
                )}

                {isHovered && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center gap-2 pb-3">
                        <button
                            onClick={() => { if (item.card_result) onPreview(item.card_result); }}
                            className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors cursor-pointer"
                            title="View"
                        >
                            <FaExpand size={16} />
                        </button>

                        {!showingHidden && onReload && item.user_inputs && (
                            <button
                                onClick={() => onReload(item.user_inputs!, item.card_result!)}
                                className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors cursor-pointer"
                                title="Reload into form"
                            >
                                <FaPencil size={16} />
                            </button>
                        )}

                        {showingHidden ? (
                            <button
                                onClick={() => onUnhideRequest(item.id)}
                                disabled={isDeleting}
                                className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                                title="Restore to gallery"
                            >
                                <FaEye size={16} />
                            </button>
                        ) : (
                            <button
                                onClick={() => onDeleteRequest(item.id)}
                                disabled={isDeleting}
                                className="p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                                title="Hide from gallery"
                            >
                                <FaEyeSlash size={16} />
                            </button>
                        )}
                    </div>
                )}
            </div>
            <div className='flex flex-col items-center gap-0.5'>
                {textLabel && (
                    <p className="text-[10px] font-bold text-secondary text-center truncate px-1 w-full">{textLabel}</p>
                )}
                {item.set_name && <SetBadge set={item.set_name} size="sm" />}
                {badges.length > 0 && (
                    <div className="flex flex-wrap justify-center">
                        {badges.map(badge => (
                            <span key={badge} className="text-[10px] leading-tight px-1 rounded-plate bg-(--background-secondary) text-secondary truncate max-w-full">
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
    const [isLoadingMore, setIsLoadingMore] = useState(false);
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
                { value: '', label: 'My Teams' },
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

    const loadGallery = useCallback(async (pageOffset: number, activeFilters: GalleryFilters, showHidden: boolean = false, append: boolean = false) => {
        if (!token) {
            console.warn('Attempted to load gallery without token');
            return;
        }
        if (append) {
            setIsLoadingMore(true);
        } else {
            setIsLoading(true);
        }
        try {
            const data = await fetchUserGallery(token, PAGE_SIZE, pageOffset, activeFilters, showHidden);
            setGallery(prev => append ? [...prev, ...data.gallery] : data.gallery);
            setOffset(pageOffset);
            setHasMore(data.has_more);
        } catch (err) {
            console.error('Failed to load gallery:', err);
        } finally {
            setIsLoading(false);
            setIsLoadingMore(false);
        }
    }, [token]);

    const observerRef = useRef<IntersectionObserver | null>(null);
    const lastItemRef = useCallback((node: HTMLDivElement | null) => {
        if (observerRef.current) observerRef.current.disconnect();
        if (!node) return;
        observerRef.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && hasMore && !isLoadingMore && !isLoading) {
                loadGallery(offset + PAGE_SIZE, filters, showingHidden, true);
            }
        });
        observerRef.current.observe(node);
    }, [hasMore, isLoadingMore, isLoading, offset, filters, showingHidden, loadGallery]);

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
                            <Heading level="section">Remove card?</Heading>
                            <p className="text-sm text-secondary">This card will be hidden from your gallery. You can unhide it later if you change your mind by using the "Active/Hidden" toggle.</p>
                        </div>
                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => setPendingDeleteId(null)}
                                className={buttonClass('secondary')}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleConfirmDelete}
                                className={buttonClass('danger')}
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
                    showSearchIcon={true}
                />

                {/* Row 2: Set + Expansion + Edition + Team + Year + Hidden toggle */}
                <div className="flex items-end gap-1.5 w-full overflow-x-scroll scrollbar-hide">
                    <CustomSelect
                        options={[{ value: '', label: 'All Sets', textColor: 'text-secondary' }, ...SET_SELECT_OPTIONS]}
                        value={filters.set_name ?? ''}
                        onChange={handleSetChange}
                        size="lg"
                    />
                    <CustomSelect
                        options={[
                            { value: '', label: 'All Expansions', textColor: 'text-secondary' },
                            ...expansionOptions,
                        ]}
                        value={filters.expansion ?? ''}
                        onChange={handleExpansionChange}
                        size="lg"
                    />
                    <CustomSelect
                        options={[
                            { value: '', label: 'All Editions', textColor: 'text-secondary' },
                            ...editionOptions.filter(option => GALLERY_EDITION_FILTERS.has(option.value)),
                        ]}
                        value={filters.edition ?? ''}
                        onChange={handleEditionChange}
                        size="lg"
                    />
                    <CustomSelect
                        options={teamOptions}
                        value={filters.team ?? ''}
                        onChange={handleTeamChange}
                        size="lg"
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
                        type="button"
                        className={choiceClass(showingHidden, 'md', 'h-11')}
                        title={showingHidden ? 'Show active cards' : 'Show hidden cards'}
                    >
                        <FaEyeSlash size={13} />
                        {showingHidden ? 'Hidden only' : 'Active only'}
                    </button>
                </div>
            </div>

            {/* Grid */}
            <div className="p-3">
                {gallery.length === 0 && !isLoading ? (
                    hasActiveFilters ? (
                        <EmptyState size="inline">No cards match these filters.</EmptyState>
                    ) : showingHidden ? (
                        <EmptyState size="panel" title="Nothing hidden.">Cards you hide from your gallery show up here.</EmptyState>
                    ) : (
                        <EmptyState title="No cards yet.">Cards you build while signed in land here.</EmptyState>
                    )
                ) : (
                    <>
                        <div className="relative">
                            {isLoading && gallery.length > 0 && (
                                <div className="absolute z-50 flex items-center justify-center w-full h-full bg-(--background-primary)/60 rounded-card">
                                    <FaSpinner className="inset-10 animate-spin text-secondary" size={24} />
                                </div>
                            )}
                            <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(135px, 1fr))' }}>
                                {(() => {
                                    // First load: card-shaped skeleton tiles in the grid's own footprint
                                    if (gallery.length === 0) return Array.from({ length: 8 }, (_, i) => (
                                        <div key={i} className="rounded-card bg-(--background-tertiary) animate-pulse" style={{ aspectRatio: '2.5 / 3.5' }} />
                                    ));
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

                            {/* Infinite scroll sentinel */}
                            <div ref={lastItemRef} />

                            {isLoadingMore && (
                                <div className="flex justify-center py-4">
                                    <FaBaseballBall
                                        className="text-secondary animate-bounce"
                                        style={{ animationDuration: '0.7s' }}
                                        size={24}
                                    />
                                </div>
                            )}

                            {!hasMore && gallery.length > PAGE_SIZE && (
                                <div className="flex justify-center p-6 text-secondary">
                                    <span className="text-sm">No more cards to load</span>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </>
    );
};
