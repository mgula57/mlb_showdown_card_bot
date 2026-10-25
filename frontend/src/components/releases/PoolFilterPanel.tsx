import { useMemo } from 'react';
import type { ReleaseCard } from '../../api/releases';
import MultiSelect from '../shared/MultiSelect';
import { POOL_FILTER_OPTIONS, poolFilterValueOptions, type PoolFilters } from './poolGrouping';

type PoolFilterPanelProps = {
    /** The full (unfiltered) pool — options and counts come from here so selecting one value doesn't hide the others. */
    cards: ReleaseCard[];
    filters: PoolFilters;
    onChange: (filters: PoolFilters) => void;
};

/** One multi-select per grouping dimension. Dimensions with a single value in the pool are hidden
 * (nothing to narrow), unless they already have a selection that needs clearing. */
export function PoolFilterPanel({ cards, filters, onChange }: PoolFilterPanelProps) {
    const dimensions = useMemo(
        () => POOL_FILTER_OPTIONS
            .map(dimension => ({ ...dimension, options: poolFilterValueOptions(cards, dimension.value) }))
            .filter(dimension => dimension.options.length > 1 || (filters[dimension.value]?.length ?? 0) > 0),
        [cards, filters]
    );

    return (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(min(200px,100%),1fr))] gap-3 px-3 py-3 border-b border-(--divider) bg-(--background-secondary) shrink-0">
            {dimensions.map(dimension => (
                <MultiSelect
                    key={dimension.value}
                    label={dimension.label}
                    options={dimension.options}
                    selections={filters[dimension.value] ?? []}
                    onChange={values => onChange({ ...filters, [dimension.value]: values })}
                    placeholder="Any"
                    className="text-[13px]"
                />
            ))}
        </div>
    );
}
