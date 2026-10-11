/**
 * @fileoverview FormSectionSummary - Chips summarizing a collapsed FormSection's non-default values.
 */

import type { SelectOption } from '../shared/CustomSelect';

/** Returns the summary chips for a FormSection's `childrenWhenClosed`, or undefined when there's nothing to show. */
export function formSectionSummary(summaryItems: SelectOption[]) {
    if (summaryItems.length === 0) {
        return undefined;
    }
    return (
        <div className="text-xs font-bold flex flex-wrap items-center gap-x-1.5 gap-y-1 text-(--tertiary)">
            {summaryItems.map(item => (
                <div key={item.label} className={`flex shrink-0 items-center whitespace-nowrap rounded-md px-1 border ${item.borderColor || 'border-(--tertiary)/65'}`}>
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
                            case "coloring": suffix = " COLOR"; break;
                            case "glow": suffix = "X"; prefix = "GLOW "; break;
                            case "nickname": prefix = "NICKNAME "; break;
                            case "chart version": prefix = "CHART "; break;
                            case "real stats": prefix = "SHOW "; suffix = " STATS"; break;
                        }
                        return <span className={`${item.borderColor || 'text-(--tertiary)'}`}>{prefix}{value}{suffix}</span>;
                    })()}
                </div>
            ))}
        </div>
    );
}
