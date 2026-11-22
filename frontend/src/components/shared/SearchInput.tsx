/**
 * @fileoverview A compact, label-less search field for filter rows (e.g. the Seasons Transactions
 * tab): the navy-to-red search frame around an `sm` field-height input, a magnifying glass, and a
 * clear button once there's text. Forms with a label above the field use `FormInput` with
 * `showSearchIcon` instead.
 */
import { FaMagnifyingGlass, FaXmark } from "react-icons/fa6";

import { SearchFrame } from "./SearchFrame";

type SearchInputProps = {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    /** Accessible name, since there's no visible label. Defaults to the placeholder. */
    ariaLabel?: string;
    /** Width and placement of the frame. */
    className?: string;
};

export function SearchInput({ value, onChange, placeholder = "Search", ariaLabel, className = "" }: SearchInputProps) {
    return (
        <SearchFrame rounded="rounded-control" className={className}>
            <div className="flex h-7 items-center gap-2 rounded-plate bg-(--background-secondary) pl-2.5 text-[12px] text-(--text-primary)">
                <FaMagnifyingGlass className="h-3 w-3 shrink-0 text-(--text-tertiary)" aria-hidden />
                <input
                    type="search"
                    inputMode="search"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Escape" && value) onChange(""); }}
                    placeholder={placeholder}
                    aria-label={ariaLabel ?? placeholder}
                    autoComplete="off"
                    spellCheck="false"
                    className="min-w-0 flex-1 bg-transparent focus:outline-none placeholder:text-(--text-tertiary) [&::-webkit-search-cancel-button]:hidden"
                />
                {value ? (
                    <button
                        type="button"
                        onClick={() => onChange("")}
                        aria-label="Clear search"
                        className="flex h-full items-center px-2 text-(--text-tertiary) hover:text-(--text-primary) cursor-pointer"
                    >
                        <FaXmark className="h-3 w-3" aria-hidden />
                    </button>
                ) : (
                    <span className="w-1" aria-hidden />
                )}
            </div>
        </SearchFrame>
    );
}
