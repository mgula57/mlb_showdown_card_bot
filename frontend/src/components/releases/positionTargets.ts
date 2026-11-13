import type { AlgorithmPlayerTypeDistribution, AlgorithmPositionTarget } from '../../api/releases';

export const POSITION_LABELS: Record<string, string> = { STARTER: 'SP', RELIEVER: 'RP', CLOSER: 'CL' };

/** Splits `total` across targets by share (largest remainder), mirroring `PositionTarget.allocate_counts` on the backend. */
export function allocateCounts(targets: AlgorithmPositionTarget[], total: number): number[] {
    const shareTotal = targets.reduce((sum, t) => sum + t.percentage, 0);
    if (shareTotal <= 0 || total <= 0) return targets.map(() => 0);
    const exact = targets.map(t => (total * t.percentage) / shareTotal);
    const counts = exact.map(Math.floor);
    const leftover = total - counts.reduce((sum, c) => sum + c, 0);
    exact
        .map((value, index) => ({ index, remainder: value - counts[index] }))
        .sort((a, b) => b.remainder - a.remainder)
        .slice(0, leftover)
        .forEach(({ index }) => counts[index]++);
    return counts;
}

/** Hitter / starter / reliever split implied by a set of position targets. */
export function distributionFromPositionTargets(targets: AlgorithmPositionTarget[]): AlgorithmPlayerTypeDistribution {
    const shareOf = (positions: string[]) => targets.filter(t => positions.includes(t.position)).reduce((sum, t) => sum + t.percentage, 0);
    const total = shareOf(targets.map(t => t.position)) || 1;
    const starters = shareOf(['STARTER']) / total;
    const relievers = shareOf(['RELIEVER', 'CLOSER']) / total;
    return { hitters_percentage: 1 - starters - relievers, starters_percentage: starters, relievers_percentage: relievers };
}
