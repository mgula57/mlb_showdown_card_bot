/**
 * @fileoverview PlayerSearchInput - Advanced player search and autocomplete component
 * 
 * Provides a sophisticated search interface for finding MLB players with features like
 * autocomplete, filtering by year/team/type, award highlights, and advanced search options.
 * Integrates with the player database API to provide real-time search results with
 * comprehensive player information and statistics.
 */

import { useState, useEffect, useRef, useId } from 'react';
import { FaSearch } from 'react-icons/fa';
import { FaXmark } from 'react-icons/fa6';
import { createPortal } from 'react-dom';
import { SearchFrame } from '../shared/SearchFrame';
import { Plate } from '../shared/Plate';

import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { choiceClass } from '../shared/choiceStyles';
import { PLAYER_VERSION_LABELS, versionFormFields, type PlayerVersion } from '../../domain/twoWay';
import { mergeTwoWayRows, isTwoWayRow, playerTypeKey, type PlayerSearchRow } from './playerSearch';
export type PlayerSearchSelection = {
    name: string;
    year: string;
    player_id: string;
    player_type_override?: string;
    /** Two-way players only: build one card with both sides */
    two_way?: boolean;
};

/**
 * Props for the PlayerSearchInput component
 */
interface PlayerSearchInputProps {
    /** Display label for the search input */
    label?: string;
    /** Current search query value */
    value: string;
    /** Callback when player is selected from search results */
    onChange: (selection: PlayerSearchSelection) => void;
    /** Optional CSS class names for styling */
    className?: string;
    /** Offer the Two-Way version on two-way players' rows (the Custom Card Builder). Otherwise
     *  their rows offer Hitter and Pitcher only. */
    offerTwoWay?: boolean;
    /** Optional search filter options */
    searchOptions?: {
        exclude_multi_year?: boolean;
        exclude_career?: boolean;
        min_bwar?: number;
        limit?: number;
        include_mlb_api_current_season?: boolean; // TEMP: Option to include current season active players from MLB API for better results on active players
    };
}

/** Minimum dropdown width in px (the input itself can be narrower) */
const MENU_MIN_WIDTH = 380;
/** Minimum gap in px between the dropdown and the viewport edges */
const MENU_VIEWPORT_MARGIN = 8;

/** Mouse/trackpad devices, where typing then Enter picks the top result. Touch devices get no auto-highlight. */
const isFinePointer = () => typeof window !== 'undefined' && !!window.matchMedia?.('(pointer: fine)').matches;

/**
 * Example search queries to cycle through in placeholder text
 * Demonstrates various search capabilities and formats
 */
const PLACEHOLDER_EXAMPLES = [
    "Search for a player…",
    "Try: Aaron Judge",
    "Try: 2025",
    "Try: NYM",
    "Try: Career",
    "Try: 1998-2002",
    "Try: Barry Bonds",
    "Try: Tarik Skubal",
    "Try: Rodriguez NYY",
];

/**
 * PlayerSearchInput - Advanced player search with autocomplete
 * 
 * Provides a comprehensive player search interface with real-time autocomplete,
 * advanced filtering options, and rich result display. Supports searching by
 * player name, year, team, player type, and special designations like "Career".
 * Results include player statistics, awards, and team information.
 * 
 * Search Features:
 * - Real-time autocomplete with debounced API calls
 * - Multi-criteria search (name, year, team, type)
 * - Hall of Fame and award indicators
 * - Career vs season-specific results
 * - Player type disambiguation (pitcher/hitter)
 * 
 * @example
 * ```tsx
 * <PlayerSearchInput
 *   label="Find Player"
 *   value={searchQuery}
 *   onChange={(selection) => {
 *     setForm({
 *       ...form,
 *       name: selection.name,
 *       year: selection.year,
 *       player_id: selection.player_id
 *     });
 *   }}
 * />
 * ```
 * 
 * @param label - Input field label
 * @param value - Current search query
 * @param onChange - Player selection handler
 * @param className - Additional styling classes
 * @returns Advanced player search component
 */
export function PlayerSearchInput({
    label='',
    value,
    onChange,
    className = '',
    offerTwoWay = false,
    searchOptions = {}
}: PlayerSearchInputProps) {

    const rowVersions: PlayerVersion[] = offerTwoWay ? ['TWO_WAY', 'HITTER', 'PITCHER'] : ['HITTER', 'PITCHER'];
    const defaultVersion = rowVersions[0];

    // =============================================================================
    // STATE MANAGEMENT
    // =============================================================================

    /** Current search query text */
    const [query, setQuery] = useState(value);
    /** Available player search options from API */
    const [options, setOptions] = useState<PlayerSearchRow[]>([]);
    /** Whether the dropdown menu is visible */
    const [isOpen, setIsOpen] = useState(false);
    /** Whether API search is in progress */
    const [isLoading, setIsLoading] = useState(false);
    /** Currently highlighted option index for keyboard navigation */
    const [selectedIndex, setSelectedIndex] = useState(-1);
    /** Version picked with ←/→ on a two-way row. Only counts while that row is still highlighted */
    const [versionPick, setVersionPick] = useState<{ index: number; version: PlayerVersion } | null>(null);
    const highlightedVersion = versionPick?.index === selectedIndex ? versionPick.version : defaultVersion;
    /** Index for cycling placeholder examples */
    const [placeholderIndex, setPlaceholderIndex] = useState(0);
    /** Whether input field has focus */
    const [isFocused, setIsFocused] = useState(false);

    /** Dropdown positioning coordinates */
    const [menuPos, setMenuPos] = useState<{ left: number; top: number; width: number }>({ left: 0, top: 0, width: 0 });

    // =============================================================================
    // REFS FOR DOM MANIPULATION AND TIMERS
    // =============================================================================

    /** Reference to the search input element */
    const inputRef = useRef<HTMLInputElement>(null);
    /** Reference to the dropdown menu element */
    const dropdownRef = useRef<HTMLDivElement>(null);
    /** Timer for debouncing search API calls */
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    /** Flag to prevent search when setting value programmatically */
    const programmaticChange = useRef(false);
    /** Timer for cycling placeholder text examples */
    const placeholderInterval = useRef<ReturnType<typeof setInterval> | null>(null);
    /** True from a keystroke until its search resolves, so Enter can't fall through to a page-level handler mid-search */
    const isSearchPending = useRef(false);

    /** Listbox id for combobox ARIA wiring; each row's id is `${listboxId}-${index}` */
    const listboxId = useId();

    /**
     * Calculate and set dropdown positioning relative to input field
     * Measures the input bounds and positions dropdown accordingly
     */
    const measureAndSetDirection = () => {
        if (!inputRef.current) return;
        const inputRect = inputRef.current.getBoundingClientRect();

        // Menu may be wider than the input, but never wider than the viewport
        const width = Math.min(Math.max(inputRect.width, MENU_MIN_WIDTH), window.innerWidth - 2 * MENU_VIEWPORT_MARGIN);
        // Keep the menu left-aligned with the input unless that would overflow the right edge
        const left = Math.max(
            MENU_VIEWPORT_MARGIN,
            Math.min(inputRect.left, window.innerWidth - width - MENU_VIEWPORT_MARGIN)
        );

        setMenuPos({
            left,
            top: inputRect.bottom + 4, // Add small gap below input
            width
        });
    };

    /**
     * Handle clicks outside the component to close dropdown
     * Used for proper focus management and UX
     */
    const handleClickOutside = (event: MouseEvent) => {
        const target = event.target;
        if (!(target instanceof Node)) return;

        if (
            dropdownRef.current &&
            !dropdownRef.current.contains(target) &&
            inputRef.current &&
            !inputRef.current.contains(target)
        ) {
            setIsOpen(false);
        }
    };

    // Listen for up and down arrow keys
    useEffect(() => {
        if (!isOpen) return;
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isOpen]);

    // Handle positioning when dropdown opens
    useEffect(() => {
        if (!isOpen) return;

        measureAndSetDirection();
        const handleUpdate = () => measureAndSetDirection();
        window.addEventListener('resize', handleUpdate);
        window.addEventListener('scroll', handleUpdate, true);

        return () => {
            window.removeEventListener('resize', handleUpdate);
            window.removeEventListener('scroll', handleUpdate, true);
        };
    }, [isOpen, options.length]);

    // Debounced search
    useEffect(() => {
        if (debounceRef.current) {
            clearTimeout(debounceRef.current);
        }

        // Don't search if this was a programmatic change
        if (programmaticChange.current) {
            programmaticChange.current = false;
            return;
        }

        if (query.length < 2) {
            isSearchPending.current = false;
            setOptions([]);
            setIsOpen(false);
            return;
        }
        isSearchPending.current = true;
        debounceRef.current = setTimeout(async () => {
            setIsLoading(true);
            try {
                // Build query params
                const params = new URLSearchParams({ q: query });
                
                if (searchOptions.exclude_multi_year) {
                    params.append('exclude_multi_year', 'true');
                }
                if (searchOptions.exclude_career) {
                    params.append('exclude_career', 'true');
                }
                if (searchOptions.min_bwar !== undefined) {
                    params.append('min_bwar', searchOptions.min_bwar.toString());
                }
                if (searchOptions.limit !== undefined) {
                    params.append('limit', searchOptions.limit.toString());
                }
                if (searchOptions.include_mlb_api_current_season) {
                    params.append('include_mlb_api_current_season', 'true');
                }

                const response = await fetch(`/api/players/search?${params.toString()}`);
                const results = mergeTwoWayRows(await response.json());

                setOptions(results);
                setIsOpen(results.length > 0);
                // On desktop, pre-highlight the top hit so type → Enter selects it
                setSelectedIndex(results.length > 0 && isFinePointer() ? 0 : -1);
            } catch (error) {
                console.error('Error searching players:', error);
                setOptions([]);
                setIsOpen(false);
            } finally {
                isSearchPending.current = false;
                setIsLoading(false);
            }
        }, 800); // Debounce delay of 800ms

        return () => {
            if (debounceRef.current) {
                clearTimeout(debounceRef.current);
            }
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [query]);

    // Rotate placeholder examples
    useEffect(() => {
        // Only rotate when not focused and no query
        if (!isFocused && !query) {
            placeholderInterval.current = setInterval(() => {
                setPlaceholderIndex(prev => (prev + 1) % PLACEHOLDER_EXAMPLES.length);
            }, 5000); // Change every 5 seconds
        } else {
            if (placeholderInterval.current) {
                clearInterval(placeholderInterval.current);
                placeholderInterval.current = null;
            }
        }

        return () => {
            if (placeholderInterval.current) {
                clearInterval(placeholderInterval.current);
            }
        };
    }, [isFocused, query]);

    // Keep the highlighted row visible as the keyboard moves through a scrolling list
    useEffect(() => {
        if (!isOpen || selectedIndex < 0) return;
        dropdownRef.current?.children[selectedIndex]?.scrollIntoView({ block: 'nearest' });
    }, [isOpen, selectedIndex]);

    /** Swallow a key so page-level listeners (e.g. the builder's Enter-to-build) never see it */
    const consumeKey = (e: React.KeyboardEvent) => {
        e.preventDefault();
        e.stopPropagation();
        e.nativeEvent.stopImmediatePropagation();
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        const hasMenu = isOpen && options.length > 0;

        // Enter picks the highlighted row. While results are open or a search is still pending it
        // never falls through, so it can't build a card from the previous selection.
        if (e.key === 'Enter') {
            if (hasMenu) {
                consumeKey(e);
                if (selectedIndex >= 0 && selectedIndex < options.length) {
                    handleSelect(options[selectedIndex], highlightedVersion);
                }
            } else if (isSearchPending.current) {
                consumeKey(e);
            }
            return;
        }

        if (!hasMenu) return;

        const last = options.length - 1;
        // ←/→ pick the version on a highlighted two-way row
        if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && isTwoWayRow(options[selectedIndex])) {
            e.preventDefault();
            const step = e.key === 'ArrowRight' ? 1 : -1;
            const next = rowVersions[Math.min(Math.max(rowVersions.indexOf(highlightedVersion) + step, 0), rowVersions.length - 1)];
            setVersionPick({ index: selectedIndex, version: next });
            return;
        }
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex(prev => Math.min(prev + 1, last));
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
                break;
            case 'Tab':
                // Tab / Shift+Tab step through results (wrapping) instead of leaving the field
                e.preventDefault();
                setSelectedIndex(prev => e.shiftKey
                    ? (prev <= 0 ? last : prev - 1)
                    : (prev >= last ? 0 : prev + 1)
                );
                break;
            case 'Escape':
                setIsOpen(false);
                setSelectedIndex(-1);
                break;
        }
    };

    const handleSelect = (row: PlayerSearchRow, version: PlayerVersion = defaultVersion) => {
        // A two-way row picks the chosen side's result (Two-Way builds from the hitting side's)
        const option = isTwoWayRow(row) ? row.versions![version === 'PITCHER' ? 'PITCHER' : 'HITTER']! : row;
        programmaticChange.current = true;
        const nameAndYear = `${option.name} ${option.year}`;
        setQuery(nameAndYear);
        setIsOpen(false);
        setSelectedIndex(-1);

        const typeOverride = option.player_type_override ? ` ${option.player_type_override.toUpperCase()}` : '';

        if (isTwoWayRow(row)) {
            onChange({
                ...versionFormFields(option.name, version),
                year: option.year.toString(),
                player_id: option.player_id.toString(),
            });
            return;
        }

        // Call onChange with the selected option
        onChange({
            name: `${option.name}${typeOverride}`,
            year: option.year.toString(),
            player_id: option.player_id.toString(),
            player_type_override: option.player_type_override ? option.player_type_override.toUpperCase().replace("(", "").replace(")", "") : undefined,
        });
        
    };

    const handleClear = () => {
        setQuery('');
        setOptions([]);
        setIsOpen(false);
        
        inputRef.current?.focus();
    };

    // Get current placeholder text
    const currentPlaceholder = (isFocused || query) ? "Search for a player…" : PLACEHOLDER_EXAMPLES[placeholderIndex];

    return (
        <div className={`relative ${className}`}>
            <label className={FIELD_LABEL_CLASS}>
                {label}
            </label>

            <SearchFrame className="relative">

                <div className="bg-primary rounded-[3px] relative">
                    <div className="absolute left-2 top-1/2 transform -translate-y-1/2 text-primary">
                        <FaSearch className="w-4 h-4" />
                    </div>
                    
                    <input
                        ref={inputRef}
                        type="text"
                        role="combobox"
                        aria-autocomplete="list"
                        aria-expanded={isOpen && options.length > 0}
                        aria-controls={listboxId}
                        aria-activedescendant={isOpen && selectedIndex >= 0 ? `${listboxId}-${selectedIndex}` : undefined}
                        style={{ textTransform: 'capitalize' }}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onFocus={() => {
                            setIsFocused(true);
                            if (options.length > 0) setIsOpen(true);
                        }}
                        onBlur={() => {
                            setIsFocused(false);
                            // Rows keep focus on the input (see the menu's onMouseDown), so any blur means focus left the search
                            setIsOpen(false);
                        }}
                        placeholder={currentPlaceholder}
                        autoComplete="off"
                        spellCheck="false"
                        className={`
                            w-full pl-8 py-2
                            text-primary
                            focus:outline-none
                            placeholder:text-(--text-tertiary)
                            transition-opacity duration-300 ease-in-out
                            font-bold
                            ${isFocused || query ? 'opacity-100' : 'animate-pulse'}
                        `}
                    />
                    
                    {/* Loading indicator */}
                    {isLoading && (
                        <div className="absolute right-8 top-1/2 transform -translate-y-1/2">
                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-(--showdown-blue) border-t-transparent"></div>
                        </div>
                    )}

                    {/* Clear button */}
                    {query && !isLoading && (
                        <button
                            type="button"
                            onClick={handleClear}
                            aria-label="Clear search"
                            className="
                                absolute right-0 top-1/2 transform -translate-y-1/2
                                text-secondary hover:text-(--text-secondary)/80
                                w-6 h-10 flex items-center justify-center
                                rounded-r-control p-1 cursor-pointer
                                text-lg
                            "
                        >
                            <FaXmark />
                        </button>
                    )}

                </div>
            </SearchFrame>

            {isOpen && options.length > 0 && typeof document !== 'undefined' && (
                createPortal(
                    <div 
                        ref={dropdownRef}
                        id={listboxId}
                        role="listbox"
                        // Keep focus on the input so clicking a row doesn't blur-close the menu before the click lands
                        onMouseDown={(e) => e.preventDefault()}
                        className="
                            fixed z-5
                            transform
                            bg-secondary rounded-card shadow-overlay
                            text-nowrap overflow-auto scrollbar-hide max-h-[40vh]
                            border-2 border-form-element
                        "
                        style={{ left: menuPos.left, top: menuPos.top, width: menuPos.width }}
                    >
                        {options.map((option, index) => (
                            <div
                                key={`${option.year.toString()}-${option.player_id}-${isTwoWayRow(option) ? 'TWP' : playerTypeKey(option.player_type_override) ?? ''}`}
                                id={`${listboxId}-${index}`}
                                role="option"
                                aria-selected={index === selectedIndex}
                                onClick={() => handleSelect(option)}
                                // mousemove (not mouseenter) so keyboard scrolling under a still pointer doesn't steal the highlight
                                onMouseMove={() => { if (index !== selectedIndex) setSelectedIndex(index); }}
                                className={`
                                    pl-3 py-3 cursor-pointer border-b border-form-element last:border-b-0
                                    ${index === selectedIndex ? 'bg-(--background-tertiary)' : ''}
                                    ${index === 0 ? 'rounded-t-card' : ''}
                                    ${index === options.length - 1 ? 'rounded-b-card' : ''}
                                `}
                            >
                                <div className="flex-col items-center gap-2">
                                    {/* Name and Year */}
                                    <div className='flex flex-row items-center gap-2'>
                                        <div className="font-medium" style={{ textTransform: 'capitalize' }}>{option.name}</div>

                                        <div className={`flex items-center gap-1 text-sm ${index === selectedIndex ? 'text-(--text-secondary)' : 'text-(--text-tertiary)'}`}>
                                            <div className='text-xs'>{option.year_display ? option.year_display : option.year} </div>
                                            {option.team && <div className="text-xs">{option.team}</div>}
                                            {option.award_summary?.includes('AS') && option.year.toString().length < 5 && <div className="text-xs">★</div>}
                                        </div>
                                        
                                        {option.is_hof && <Plate variant="custom" size="sm" className="bg-(--gold) text-(--field-ink)">HOF</Plate>}
                                    </div>
                                    {/* Contextual info */}
                                    <div className="text-xs text-(--text-tertiary)">
                                        {option.player_type_override && !isTwoWayRow(option) && <div className='font-bold'>{option.player_type_override.toUpperCase()}</div>}
                                        {option.award_summary && <div>Awards: {option.award_summary}</div>}
                                        {isTwoWayRow(option) ? (
                                            <div>{option.war_type}: {option.versions!.HITTER!.war?.toFixed(1)} hitting · {option.versions!.PITCHER!.war?.toFixed(1)} pitching</div>
                                        ) : option.war !== undefined && option.war !== null && <div>{option.war_type}: {option.war.toFixed(1)}</div>}
                                    </div>

                                    {/* Two-way: which card to build. Clicking the row picks the highlighted one */}
                                    {isTwoWayRow(option) && (
                                        <div className="flex gap-1 pt-2" role="group" aria-label="Card version">
                                            {rowVersions.map(version => (
                                                <button
                                                    key={version}
                                                    type="button"
                                                    aria-pressed={index === selectedIndex && version === highlightedVersion}
                                                    onClick={(e) => { e.stopPropagation(); handleSelect(option, version); }}
                                                    className={choiceClass(index === selectedIndex ? version === highlightedVersion : version === defaultVersion, 'xs')}
                                                >
                                                    {PLAYER_VERSION_LABELS[version]}
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>,
                    document.body
                )
            )}

        </div>
    );
}