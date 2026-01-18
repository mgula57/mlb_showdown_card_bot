/**
 * @fileoverview PlayerSearchInput - Advanced player search and autocomplete component
 * 
 * Provides a sophisticated search interface for finding MLB players with features like
 * autocomplete, filtering by year/team/type, award highlights, and advanced search options.
 * Integrates with the player database API to provide real-time search results with
 * comprehensive player information and statistics.
 */

import { useState, useEffect, useRef } from 'react';
import { FaSearch } from 'react-icons/fa';
import { FaXmark } from 'react-icons/fa6';
import { createPortal } from 'react-dom';

/**
 * Player search result option with comprehensive metadata
 */
interface PlayerSearchOption {
    /** Player's full name */
    name: string;
    /** Season year or special designation (CAREER, etc.) */
    year: number | string;
    /** Formatted year display (e.g., "2020-2024" for multi-year) */
    year_display?: string | null;
    /** Baseball Reference player ID */
    bref_id: string;
    /** Whether player is in Hall of Fame */
    is_hof: boolean;
    /** Summary of major awards (MVP, Cy Young, etc.) */
    award_summary?: string | null;
    /** Baseball WAR (Wins Above Replacement) value */
    bwar: number;
    /** Team abbreviation for the season */
    team?: string | null;
    /** Override for player type (Hitter/Pitcher) if ambiguous */
    player_type_override?: string | null;
}

export type PlayerSearchSelection = {
    name: string;
    year: string;
    bref_id: string;
    player_type_override?: string;
};

/**
 * Props for the PlayerSearchInput component
 */
interface PlayerSearchInputProps {
    /** Display label for the search input */
    label: string;
    /** Current search query value */
    value: string;
    /** Callback when player is selected from search results */
    onChange: (selection: PlayerSearchSelection) => void;
    /** Optional CSS class names for styling */
    className?: string;
    /** Optional search filter options */
    searchOptions?: {
        exclude_multi_year?: boolean;
        exclude_career?: boolean;
        min_bwar?: number;
        limit?: number;
    };
}

/**
 * Example search queries to cycle through in placeholder text
 * Demonstrates various search capabilities and formats
 */
const PLACEHOLDER_EXAMPLES = [
    "Search for a player...",
    "Try: Aaron Judge",
    "Try: 2025",
    "Try: NYM",
    "Try: Career",
    "Try: 1998-2002",
    "Try: Barry Bonds",
    "Try: Tarik Skubal",
    "Try: Shohei Hitting",
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
 *       player_id: selection.bref_id
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
    label,
    value,
    onChange,
    className = '',
    searchOptions = {}
}: PlayerSearchInputProps) {

    // =============================================================================
    // STATE MANAGEMENT
    // =============================================================================

    /** Current search query text */
    const [query, setQuery] = useState(value);
    /** Available player search options from API */
    const [options, setOptions] = useState<PlayerSearchOption[]>([]);
    /** Whether the dropdown menu is visible */
    const [isOpen, setIsOpen] = useState(false);
    /** Whether API search is in progress */
    const [isLoading, setIsLoading] = useState(false);
    /** Currently highlighted option index for keyboard navigation */
    const [selectedIndex, setSelectedIndex] = useState(-1);
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

    /**
     * Calculate and set dropdown positioning relative to input field
     * Measures the input bounds and positions dropdown accordingly
     */
    const measureAndSetDirection = () => {
        if (!inputRef.current) return;
        const inputRect = inputRef.current.getBoundingClientRect();

        setMenuPos({
            left: inputRect.left,
            top: inputRect.bottom + 4, // Add small gap below input
            width: inputRect.width
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
            setOptions([]);
            setIsOpen(false);
            return;
        }
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

                const response = await fetch(`/api/players/search?${params.toString()}`);
                const results = await response.json();
                
                setOptions(results);
                setIsOpen(results.length > 0);
                setSelectedIndex(-1);
            } catch (error) {
                console.error('Error searching players:', error);
                setOptions([]);
                setIsOpen(false);
            } finally {
                setIsLoading(false);
            }
        }, 300);

        return () => {
            if (debounceRef.current) {
                clearTimeout(debounceRef.current);
            }
        };
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

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isOpen) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex(prev => 
                    prev < options.length - 1 ? prev + 1 : prev
                );
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && selectedIndex < options.length) {
                    handleSelect(options[selectedIndex]);
                }
                break;
            case 'Escape':
                setIsOpen(false);
                setSelectedIndex(-1);
                break;
        }
    };

    const handleSelect = (option: PlayerSearchOption) => {
        programmaticChange.current = true;
        const nameAndYear = `${option.name} ${option.year}`;
        setQuery(nameAndYear);
        setIsOpen(false);
        setSelectedIndex(-1);

        const typeOverride = option.player_type_override ? ` ${option.player_type_override.toUpperCase()}` : '';

        // Call onChange with the selected option
        onChange({
            name: `${option.name}${typeOverride}`,
            year: option.year.toString(),
            bref_id: option.bref_id.toString(),
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
    const currentPlaceholder = (isFocused || query) ? "Search for a player..." : PLACEHOLDER_EXAMPLES[placeholderIndex];

    return (
        <div className={`relative ${className}`}>
            <label className="block text-sm font-medium text-secondary mb-1">
                {label}
            </label>

            <div className="relative bg-gradient-to-r from-blue-500 to-red-500 p-[2px] rounded-lg">

                <div className="bg-primary rounded-[calc(0.5rem-2px)] relative">
                    <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-primary">
                        <FaSearch className="w-4 h-4" />
                    </div>
                    
                    <input
                        ref={inputRef}
                        type="text"
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
                        }}
                        placeholder={currentPlaceholder}
                        autoComplete="off"
                        spellCheck="false"
                        className={`
                            w-full pl-10 pr-6 py-2
                            text-primary
                            focus:outline-none
                            placeholder-gray-500
                            transition-opacity duration-300 ease-in-out
                            font-bold
                            ${isFocused || query ? 'opacity-100' : 'animate-pulse // Optional: adds subtle pulse effect'}
                        `}
                    />
                    
                    {/* Loading indicator */}
                    {isLoading && (
                        <div className="absolute right-8 top-1/2 transform -translate-y-1/2">
                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
                        </div>
                    )}

                    {/* Clear button */}
                    {query && !isLoading && (
                        <button
                            type="button"
                            onClick={handleClear}
                            className="
                                absolute right-2 top-1/2 transform -translate-y-1/2
                                text-secondary hover:text-gray-600
                                w-4 h-4 flex items-center justify-center
                                text-lg
                            "
                        >
                            <FaXmark />
                        </button>
                    )}
            
                </div>
            </div>

            {isOpen && options.length > 0 && typeof document !== 'undefined' && (
                createPortal(
                    <div 
                        ref={dropdownRef}
                        className="
                            fixed z-[5]
                            transform
                            bg-secondary rounded-xl shadow-lg
                            text-nowrap overflow-auto max-h-[40vh]
                            border-2 border-form-element
                        "
                        style={{ left: menuPos.left, top: menuPos.top, width: menuPos.width }}
                    >
                        {options.map((option, index) => (
                            <div
                                key={`${option.year.toString()}-${option.bref_id}`}
                                onClick={() => handleSelect(option)}
                                className={`
                                    px-3 py-3 cursor-pointer border-b border-form-element last:border-b-0
                                    hover:bg-[var(--background-tertiary)]
                                    ${index === 0 ? 'rounded-t-lg' : ''}
                                    ${index === options.length - 1 ? 'rounded-b-lg' : ''}
                                `}
                            >
                                <div className="flex-col items-center gap-2">
                                    {/* Name and Year */}
                                    <div className='flex flex-row items-center gap-2'>
                                        <div className="font-medium" style={{ textTransform: 'capitalize' }}>{option.name}</div>

                                        <div className={`flex items-center gap-1 text-sm ${index === selectedIndex ? 'text-blue-100' : 'text-gray-400'}`}>
                                            <div className='text-xs'>{option.year_display ? option.year_display : option.year} </div>
                                            {option.team && <div className="text-xs">{option.team}</div>}
                                            {option.award_summary?.includes('AS') && option.year.toString().length < 5 && <div className="text-xs">★</div>}
                                        </div>
                                        
                                        {option.is_hof && <div className="bg-yellow-300 rounded-md text-xs p-1 text-black">HOF</div>}
                                    </div>
                                    {/* Contextual info */}
                                    <div className="text-xs text-gray-500">
                                        {option.player_type_override && <div className='font-bold'>{option.player_type_override.toUpperCase()}</div>}
                                        {option.award_summary && <div>Awards: {option.award_summary}</div>}
                                        {option.bwar !== undefined && option.bwar !== null && <div>bWAR: {option.bwar.toFixed(1)}</div>}
                                    </div>
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