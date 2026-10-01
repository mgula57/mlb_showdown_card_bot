import type { AlgorithmPointBucket } from '../../api/releases';

export const bucketLabel = (bucket: AlgorithmPointBucket) => `${bucket.min_points}–${bucket.max_points}`;

/** Mirrors `PointBucket.validate_list` on the backend. Returns a message for the first problem found, or null. */
export function validatePointBuckets(buckets: AlgorithmPointBucket[]): string | null {
    const invalidRange = buckets.find(b => b.min_points > b.max_points);
    if (invalidRange) return `Bucket ${bucketLabel(invalidRange)}: min points must be at or below max points.`;

    const ordered = [...buckets].sort((a, b) => a.min_points - b.min_points);
    for (let i = 1; i < ordered.length; i++) {
        if (ordered[i].min_points <= ordered[i - 1].max_points) {
            return `Buckets ${bucketLabel(ordered[i - 1])} and ${bucketLabel(ordered[i])} overlap.`;
        }
    }

    const totalPercent = Math.round(buckets.reduce((sum, b) => sum + b.percentage, 0) * 100);
    if (totalPercent > 100) return `Bucket targets add up to ${totalPercent}% — they can't exceed 100%.`;
    return null;
}
