import { showdownSets } from './SiteSettingsContext';

export type SetBadgeSize = 'sm' | 'md' | 'lg';

/** Set color: red for the early sets (2000, 2001, Classic), navy for the later ones. */
const TONE_CLASSES = {
    red: 'text-(--showdown-red)',
    blue: 'text-(--showdown-blue)',
};

/** Matched to the old set logos: `sm` for card corners and inline rows, `md` for fields and menus, `lg` for the header and builder pickers. */
const SIZE_CLASSES: Record<SetBadgeSize, string> = {
    sm: 'text-[16px]',
    md: 'text-[22px]',
    lg: 'text-[28px]',
};

type SetBadgeProps = {
    /** Set value (e.g. "2001", "CLASSIC") */
    set: string;
    /** Short form ('01, CLS) for tight rows */
    abbreviated?: boolean;
    size?: SetBadgeSize;
    /** On a team-color field: keeps the white outline in both themes */
    onField?: boolean;
    className?: string;
};

/**
 * A Showdown set's name the way the cards print it: display italic caps in the set's color with an
 * outline (`--set-outline`, dark gray in light and white in dark). Renders nothing for an unknown set.
 */
export function SetBadge({ set, abbreviated = false, size = 'md', onField = false, className = '' }: SetBadgeProps) {
    const found = showdownSets.find(s => s.value === set);
    if (!found) return null;
    return (
        <span
            title={found.name}
            className={`inline-flex items-center justify-center shrink-0 pl-[0.1em] pr-[0.18em] py-[0.08em] font-display uppercase leading-none whitespace-nowrap text-outline-set ${onField ? '[--set-badge-outline:white]' : ''} ${SIZE_CLASSES[size]} ${TONE_CLASSES[found.tone]} ${className}`}
        >
            {abbreviated ? found.abbr : found.name}
        </span>
    );
}

type SetBadgeRowProps = {
    /** Set values in any order, duplicates allowed (e.g. one per card). */
    sets: Iterable<string | null | undefined>;
    size?: SetBadgeSize;
    onField?: boolean;
    className?: string;
};

/** Badges for the distinct sets given, in site order: full names for one set, abbreviated for several. Renders nothing for no sets. */
export function SetBadgeRow({ sets, size = 'sm', onField, className }: SetBadgeRowProps) {
    const present = new Set(sets);
    const ordered = showdownSets.map(s => s.value).filter(set => present.has(set));
    if (ordered.length === 0) return null;

    const abbreviated = ordered.length >= 2;
    return (
        <div className={className}>
            {ordered.map(set => <SetBadge key={set} set={set} abbreviated={abbreviated} size={size} onField={onField} />)}
        </div>
    );
}

/**
 * A set as a `CustomSelect` / `MultiSelect` option. `compact` adds the abbreviated badge for the
 * button at narrow widths; only use it inside an `@container`, since the swap is a container query.
 */
export const setSelectOption = (set: string, { label = '', compact = false, size = 'md' }: { label?: string; compact?: boolean; size?: SetBadgeSize } = {}) => ({
    value: set,
    label,
    icon: <SetBadge set={set} size={size} />,
    ...(compact && { iconCompact: <SetBadge set={set} size={size} abbreviated /> }),
});

/** Every set as `CustomSelect` options, in site order. */
export const SET_SELECT_OPTIONS = showdownSets.map(s => setSelectOption(s.value));
/** Large badges, for the header and account set pickers. */
export const SET_SELECT_OPTIONS_LG = showdownSets.map(s => setSelectOption(s.value, { size: 'lg' }));

export default SetBadge;
