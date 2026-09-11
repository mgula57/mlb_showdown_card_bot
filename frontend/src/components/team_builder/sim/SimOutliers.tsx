import type { OutlierEntry, OutlierGroup, SimStatLine, SimTeamIdentity } from '../../../api/sim';
import { SectionCard } from './SectionCard';
import { SimStatsTable } from './SimStatsTable';

const OUTLIER_COLUMNS = ['ops', 'real_ops', 'ops_diff'];

function toStatLine(entry: OutlierEntry): SimStatLine {
    return {
        id: entry.id,
        name: entry.name,
        team: entry.team,
        position: null,
        points: 0,
        command: 0,
        player_type: entry.player_type,
        card_source: entry.card_source,
        stats: { ops: entry.sim_ops, real_ops: entry.real_ops, ops_diff: entry.diff },
    };
}

type Props = {
    /** Keyed by PlayerType value ('Hitter'/'Pitcher') — `SeasonSimSummary.outliers`. */
    outliers: Record<string, OutlierGroup>;
    identities: Record<string, SimTeamIdentity>;
};

/**
 * Biggest sim-vs-real-life OPS gaps, split into overperformers/underperformers — the web
 * equivalent of the CLI's `--show_outliers`. Reuses `SimStatsTable` (each entry reshaped into a
 * `SimStatLine`) so these rows get the same card-linking/team-branding as every other sim table.
 */
export function SimOutliers({ outliers, identities }: Props) {
    const hitters = outliers['Hitter'];
    const pitchers = outliers['Pitcher'];
    const hasAny = [hitters?.positive, hitters?.negative, pitchers?.positive, pitchers?.negative]
        .some(list => (list?.length ?? 0) > 0);
    if (!hasAny) return null;

    const subTable = (label: string, entries: OutlierEntry[] | undefined) => (entries?.length ?? 0) > 0 && (
        <div>
            <p className="text-[11px] text-(--text-tertiary) mb-1">{label}</p>
            <SimStatsTable rows={entries!.map(toStatLine)} columns={OUTLIER_COLUMNS} emptyLabel="" cardsEnabled identities={identities} />
        </div>
    );

    return (
        <SectionCard title="Outliers vs. Real Life">
            <div className="flex flex-col gap-4">
                <div>
                    <p className="text-[11px] font-bold text-(--success) uppercase tracking-wide mb-1.5">Overperformers</p>
                    <div className="flex flex-col gap-3">
                        {subTable('Hitters', hitters?.positive)}
                        {subTable('Pitchers', pitchers?.positive)}
                    </div>
                </div>
                <div>
                    <p className="text-[11px] font-bold text-(--error) uppercase tracking-wide mb-1.5">Underperformers</p>
                    <div className="flex flex-col gap-3">
                        {subTable('Hitters', hitters?.negative)}
                        {subTable('Pitchers', pitchers?.negative)}
                    </div>
                </div>
            </div>
        </SectionCard>
    );
}
