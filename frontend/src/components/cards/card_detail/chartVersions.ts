/**
 * @fileoverview Chart version ordering shared by the Chart Selection breakdown and the chart
 * version picker in the Card Style editor.
 */

/** Charts in chart version order, `rank` 1 = version 1: by accuracy, except a curated combo
 * (`pickedChart`, ex: '13-8') is promoted to version 1, pushing the rest down. Matches the
 * backend's chart version order. */
export function rankChartsByVersion<T extends { chart: string; accuracy: number }>(rows: T[], pickedChart: string | null): (T & { rank: number })[] {
    const byAccuracy = [...rows].sort((a, b) => b.accuracy - a.accuracy);
    return [
        ...byAccuracy.filter(row => row.chart === pickedChart),
        ...byAccuracy.filter(row => row.chart !== pickedChart),
    ].map((row, index) => ({ ...row, rank: index + 1 }));
}
