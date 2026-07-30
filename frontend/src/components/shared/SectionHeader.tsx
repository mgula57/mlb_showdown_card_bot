/**
 * @fileoverview Section header with a label, filled/total count, points total, and an optional
 * KPI strip — was implemented twice (`FieldView.FieldViewSectionHeader` and
 * `DepthChartPanel.SectionHeader`), identical except for outer container styling.
 */
import type { KpiTile } from '../team_builder/TeamKpiUtils';

type SectionHeaderVariant = 'overlay' | 'plain';

type SectionHeaderProps = {
    label: string;
    filledCount: number;
    maxPlayers?: number;
    total: number;
    kpis?: KpiTile[];
    /** 'overlay' sits atop the field background art (FieldView); 'plain' is an inline list header (DepthChartPanel). */
    variant?: SectionHeaderVariant;
};

const VARIANT_CLASSES: Record<SectionHeaderVariant, { container: string; row: string; label: string; total: string }> = {
    overlay: {
        container: 'px-3 py-1.5 backdrop-blur-xs bg-(--background)/40',
        row: 'flex items-center gap-1.5 opacity-75',
        label: 'text-[11px] font-bold text-(--text-secondary) uppercase tracking-wide',
        total: 'ml-auto text-[11px] font-semibold text-(--text-tertiary)',
    },
    plain: {
        container: 'pt-3 pb-1',
        row: 'flex items-center gap-1.5',
        label: 'text-[10px] font-semibold text-(--text-secondary) uppercase tracking-widest',
        total: 'ml-auto text-[10px] font-semibold text-(--text-tertiary)',
    },
};

export function SectionHeader({ label, filledCount, maxPlayers, total, kpis, variant = 'plain' }: SectionHeaderProps) {
    const classes = VARIANT_CLASSES[variant];
    return (
        <div className={classes.container}>
            <div className={classes.row}>
                <span className={classes.label}>{label}</span>
                <span className="text-[10px] text-(--text-tertiary)">{filledCount}{maxPlayers !== undefined ? `/${maxPlayers}` : ''}</span>
                {total > 0 && (
                    <span className={classes.total}>{total} pts</span>
                )}
            </div>
            {kpis && kpis.length > 0 && (
                <div className="flex items-center gap-3 mt-1.5 overflow-x-auto pb-0.5">
                    {kpis.map(({ label: kLabel, value }) => (
                        <div key={kLabel} className="flex flex-col items-center shrink-0">
                            <span className="text-[8px] text-(--text-tertiary) uppercase tracking-wider opacity-75">{kLabel}</span>
                            <span className="text-[11px] font-bold text-(--text-secondary)">{value}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default SectionHeader;
