import { FaPlus, FaXmark } from 'react-icons/fa6';
import type { AlgorithmPointBucket } from '../../api/releases';
import FormInput from '../customs/FormInput';
import PercentageSlider from '../shared/PercentageSlider';
import IconButton from '../shared/IconButton';
import InlineWarning from '../shared/InlineWarning';
import { bucketLabel, validatePointBuckets } from './pointBuckets';

/** Bucket added by "Add Bucket" — starts just above the highest existing bucket so it never overlaps. */
function nextBucket(buckets: AlgorithmPointBucket[]): AlgorithmPointBucket {
    if (buckets.length === 0) return { min_points: 10, max_points: 50, percentage: 0.2 };
    const highestMax = Math.max(...buckets.map(b => b.max_points));
    return { min_points: highestMax + 10, max_points: highestMax + 50, percentage: 0.1 };
}

type PointBucketsEditorProps = {
    buckets: AlgorithmPointBucket[];
    onChange: (buckets: AlgorithmPointBucket[]) => void;
};

export default function PointBucketsEditor({ buckets, onChange }: PointBucketsEditorProps) {
    const validationError = validatePointBuckets(buckets);

    function updateBucket(index: number, patch: Partial<AlgorithmPointBucket>) {
        onChange(buckets.map((bucket, i) => (i === index ? { ...bucket, ...patch } : bucket)));
    }

    return (
        <div className="flex flex-col gap-2.5">
            {buckets.map((bucket, index) => (
                <div key={index} className="flex flex-col gap-1.5 rounded-lg border border-(--divider) p-2">
                    <div className="flex items-end gap-2">
                        <FormInput
                            label="Min Points"
                            type="number"
                            step="10"
                            value={bucket.min_points}
                            onChange={value => updateBucket(index, { min_points: parseInt(value || '0', 10) || 0 })}
                        />
                        <FormInput
                            label="Max Points"
                            type="number"
                            step="10"
                            value={bucket.max_points}
                            onChange={value => updateBucket(index, { max_points: parseInt(value || '0', 10) || 0 })}
                        />
                        <IconButton
                            icon={<FaXmark className="text-[12px]" />}
                            label={`Remove ${bucketLabel(bucket)} bucket`}
                            onClick={() => onChange(buckets.filter((_, i) => i !== index))}
                            className="mb-1.5 shrink-0"
                        />
                    </div>
                    <PercentageSlider
                        label="Target"
                        fillClassName="bg-(--secondary)"
                        value={Math.round(bucket.percentage * 100)}
                        onChange={percent => updateBucket(index, { percentage: percent / 100 })}
                    />
                </div>
            ))}

            {validationError && <InlineWarning>{validationError}</InlineWarning>}

            <button
                type="button"
                onClick={() => onChange([...buckets, nextBucket(buckets)])}
                className="self-start flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-(--divider) text-[12px] font-semibold
                    text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--background-secondary) transition-colors cursor-pointer"
            >
                <FaPlus className="text-[10px]" /> Add Bucket
            </button>

            <p className="text-[11px] text-(--text-tertiary)">
                {buckets.length > 0
                    ? `Aims for ${buckets.map(b => `${Math.round(b.percentage * 100)}% at ${bucketLabel(b)} pts`).join(', ')} within each of hitters, starters and relievers, so rosters have affordable depth.`
                    : 'No buckets — the set is filled purely by player priority, which tends to favor high-point stars.'}
            </p>
        </div>
    );
}
