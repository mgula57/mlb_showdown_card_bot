/**
 * @fileoverview FormSectionSummary - Chips summarizing a collapsed FormSection's non-default values.
 */

import type { SelectOption } from '../shared/CustomSelect';

/** A summary chip for a dropdown value, showing the option's readable label instead of its raw value
 * (e.g. "Last Team" rather than LAST_TEAM). `label` overrides the chip's label, which drives prefixes/suffixes below. */
export function optionSummaryItem(options: SelectOption[], value: string, label?: string): SelectOption {
    const option = options.find(opt => opt.value === value);
    return { ...option, value: option?.label ?? value, label: label ?? option?.label };
}

/** Returns the summary chips for a FormSection's `childrenWhenClosed`, or undefined when there's nothing to show. */
export function formSectionSummary(summaryItems: SelectOption[]) {
    if (summaryItems.length === 0) {
        return undefined;
    }
    return (
        <div className="text-xs font-bold flex flex-wrap items-center gap-x-1.5 gap-y-1 text-(--tertiary)">
            {summaryItems.map(item => (
                <div key={item.label ?? item.value}className={`flex shrink-0 items-center whitespace-nowrap rounded-plate px-1 border ${item.borderColor || 'border-(--tertiary)/65'}`}>
                    <span className="font-semibold">{item.icon}</span>
                    {(() => {
                        const label = item.label?.toLowerCase()
                        let prefix = "";
                        let suffix = "";
                        const value = item.value || "";
                        if (label === "name") {
                            return <span style={{ textTransform: 'capitalize' }}>{item.value}</span>;
                        }
                        if (item.image && item.label === "Showdown Set") {
                            return <img src={item.image} alt={item.label} className="w-12 object-contain h-5" />;
                        }
                        if (item.image) {
                            return <img src={item.image} alt={item.label} className="w-5 h-5" />;
                        }
                        if (item.icon) {
                            return <span className="w-5 h-5" >{item.icon}</span>;
                        }
                        if (item.symbol) {
                            return <span className="w-5 h-5" >{item.symbol}</span>;
                        }
                        switch (label) {
                            case "set number": prefix = "#"; break;
                            case "chart version": prefix = "Chart "; break;
                            case "real stats": prefix = "Show "; suffix = " Stats"; break;
                        }
                        return <span className={`${item.borderColor || 'text-(--tertiary)'}`}>{prefix}{value}{suffix}</span>;
                    })()}
                </div>
            ))}
        </div>
    );
}
