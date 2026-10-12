import { showdownSets, imageForSet } from './SiteSettingsContext';

type ShowdownSetLogosProps = {
    /** Set values in any order, duplicates allowed (e.g. one per card). */
    sets: Iterable<string | null | undefined>;
    /** Logo height when there's a single set (full logo). */
    heightClass: string;
    /** Logo height when there are several sets (abbreviated logos, so they fit side by side). */
    abbreviatedHeightClass: string;
    className?: string;
};

/** Logos for the distinct Showdown sets given, in the site's set order. Renders nothing for no sets. */
export function ShowdownSetLogos({ sets, heightClass, abbreviatedHeightClass, className }: ShowdownSetLogosProps) {
    const present = new Set(sets);
    const ordered = showdownSets.map(s => s.value).filter(set => present.has(set));
    if (ordered.length === 0) return null;

    const isAbbreviated = ordered.length >= 2;
    return (
        <div className={className}>
            {ordered.map(set => {
                const image = imageForSet(set, isAbbreviated);
                return image ? (
                    <img
                        key={set}
                        src={image}
                        alt={set}
                        title={set}
                        loading="lazy"
                        className={`${isAbbreviated ? abbreviatedHeightClass : heightClass} w-auto object-contain`}
                    />
                ) : null;
            })}
        </div>
    );
}

export default ShowdownSetLogos;
