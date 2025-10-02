import { useState, useEffect, useRef } from 'react';
import { FaSearch } from 'react-icons/fa';
import { FaXmark } from 'react-icons/fa6';
import { createPortal } from 'react-dom';

interface PlayerSearchOption {
    name: string;
    year: number | string;
    year_display?: string | null;
    bref_id: string;
    is_hof: boolean;
    award_summary?: string | null;
    bwar: number;
    team?: string | null;
    player_type_override?: string | null;
}

interface PlayerSearchInputProps {
    label: string;
    value: string;
    onChange: (selection: {
        name: string;
        year: string;
        bref_id: string;
    }) => void;
    className?: string;
}

// Add placeholder examples array
const PLACEHOLDER_EXAMPLES = [
    "Search for a player...",
    "Try: Aaron Judge",
    "Try: 2025",
    "Try: NYM",
    "Try: Career",
    "Try: 1998-2002",
    "Try: Barry Bonds",
    "Try: Tarik Skubal",
    "Try: Shohei Hitting"
];

export function PlayerSearchInput({
    label,
    value,
    onChange,
    className = ''
}: PlayerSearchInputProps) {

    const [query, setQuery] = useState(value);
    const [options, setOptions] = useState<PlayerSearchOption[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const [placeholderIndex, setPlaceholderIndex] = useState(0);
    const [isFocused, setIsFocused] = useState(false);

    // Positioning
    const [menuPos, setMenuPos] = useState<{ left: number; top: number; width: number }>({ left: 0, top: 0, width: 0 });

    // Refs
    const inputRef = useRef<HTMLInputElement>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const programmaticChange = useRef(false);
    const placeholderInterval = useRef<ReturnType<typeof setInterval> | null>(null);

    /** Measure the dropdown position and set direction based on available space */
    const measureAndSetDirection = () => {
        if (!inputRef.current) return;
        const inputRect = inputRef.current.getBoundingClientRect();

        setMenuPos({
            left: inputRect.left,
            top: inputRect.bottom,
            width: inputRect.width
        });
    };

    /** Close dropdown when clicking outside */
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
                const response = await fetch('/api/players/search?q=' + encodeURIComponent(query));
                console.log(response);
                const results = await response.json();
                
                setOptions(results);

                console.log(options.length)
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
            bref_id: option.bref_id.toString()
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
                            absolute z-[1000]
                            left-0 transform
                            bg-secondary rounded-xl shadow-lg
                            text-nowrap overflow-auto max-h-[40vh]
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
                                        {option.bwar !== undefined && <div>bWAR: {option.bwar.toFixed(1)}</div>}
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