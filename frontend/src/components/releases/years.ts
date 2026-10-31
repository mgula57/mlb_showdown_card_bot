/**
 * @fileoverview Parsing, validation and serialization for the Release Builder's years setting.
 * The backend takes one string (`convert_year_string_to_list`): "2023", "2000-2004" (a range) or
 * "2006+2014" (specific years). A range and a list can't be mixed.
 */

export type YearsMode = 'single' | 'range' | 'list';

/** What the form fields hold - strings while typing, so partial entries survive. */
export type YearsDraft = {
    mode: YearsMode;
    single: string;
    from: string;
    to: string;
    list: number[];
};

export const MIN_YEAR = 1900;
export const MAX_YEAR = new Date().getFullYear();

const isYear = (text: string) => /^\d{4}$/.test(text) && Number(text) >= MIN_YEAR && Number(text) <= MAX_YEAR;

/** Reads a stored years string into form fields. Anything unrecognized lands as an empty single year. */
export function parseYearsValue(value: string): YearsDraft {
    const text = (value ?? '').trim();
    const empty: YearsDraft = { mode: 'single', single: '', from: '', to: '', list: [] };
    if (/^\d+$/.test(text)) return { ...empty, single: text, from: text, to: text, list: [Number(text)] };
    const range = text.match(/^(\d+)\s*-\s*(\d+)$/);
    if (range) return { ...empty, mode: 'range', from: range[1], to: range[2], single: range[1], list: [Number(range[1])] };
    if (/^\d+(\s*\+\s*\d+)+$/.test(text)) {
        const list = [...new Set(text.split('+').map(part => Number(part.trim())))].sort((a, b) => a - b);
        return { ...empty, mode: 'list', list, single: String(list[0]), from: String(list[0]), to: String(list[0]) };
    }
    return empty;
}

/** `isBlank` is true while the entry is still being typed (empty or under 4 digits), so there's nothing to flag yet. */
export type YearsValidation = { error: string | null; isBlank: boolean };

export function validateYears(draft: YearsDraft): YearsValidation {
    const range = `${MIN_YEAR}-${MAX_YEAR}`;
    if (draft.mode === 'single') {
        if (!draft.single) return { error: 'Enter a year.', isBlank: true };
        if (draft.single.length < 4) return { error: 'Enter a 4-digit year.', isBlank: true };
        return isYear(draft.single) ? { error: null, isBlank: false } : { error: `Enter a year between ${range}.`, isBlank: false };
    }
    if (draft.mode === 'range') {
        if (!draft.from && !draft.to) return { error: 'Enter a start and end year.', isBlank: true };
        if (draft.from.length < 4 || draft.to.length < 4) return { error: 'Enter both a start and end year.', isBlank: true };
        if (!isYear(draft.from) || !isYear(draft.to)) return { error: `Years must be 4 digits between ${range}.`, isBlank: false };
        if (Number(draft.from) > Number(draft.to)) return { error: 'The start year must come before the end year.', isBlank: false };
        return { error: null, isBlank: false };
    }
    return draft.list.length === 0
        ? { error: 'Add at least one year.', isBlank: true }
        : { error: null, isBlank: false };
}

/** Backend string for a valid draft. Collapses one-year ranges and one-year lists to a plain year. */
export function serializeYears(draft: YearsDraft): string {
    if (draft.mode === 'single') return draft.single;
    if (draft.mode === 'range') return draft.from === draft.to ? draft.from : `${draft.from}-${draft.to}`;
    return draft.list.join('+');
}
