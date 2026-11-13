import { FaMagnifyingGlass, FaXmark } from 'react-icons/fa6';
import { SearchFrame } from '../shared/SearchFrame';

type TeamSearchInputProps = {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
    autoFocus?: boolean;
};

/** Shared search field used by the team lists — logo frame, icon, clear button, consistent styling. */
export function TeamSearchInput({ value, onChange, placeholder, className, autoFocus }: TeamSearchInputProps) {
    return (
        <SearchFrame className={className}>
            <div className="relative bg-(--background-secondary) rounded-[3px]">
                <FaMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 text-[12px] text-(--text-tertiary)" />
                <input
                    type="text"
                    value={value}
                    onChange={e => onChange(e.target.value)}
                    autoFocus={autoFocus}
                    placeholder={placeholder ?? 'Search teams by name or set…'}
                    className="w-full pl-9 pr-9 py-2 rounded-control bg-transparent text-[13px] text-(--text-primary) placeholder:text-(--text-tertiary) focus:outline-none"
                />
                {value && (
                    <button
                        type="button"
                        onClick={() => onChange('')}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-full text-(--text-tertiary) hover:bg-(--divider) cursor-pointer"
                        aria-label="Clear search"
                    >
                        <FaXmark className="text-[12px]" />
                    </button>
                )}
            </div>
        </SearchFrame>
    );
}

export default TeamSearchInput;
