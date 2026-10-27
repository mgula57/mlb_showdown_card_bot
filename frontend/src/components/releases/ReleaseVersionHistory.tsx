import { useEffect, useState } from 'react';
import { fetchReleaseVersions, type Release, type ReleaseVersion } from '../../api/releases';
import { formatShortDate } from '../../functions/formatters';
import { Modal } from '../shared/Modal';
import { Plate } from '../shared/Plate';
import { InlineError } from '../shared/InlineError';
import { EmptyState } from '../shared/EmptyState';
import { headingClass } from '../shared/headingStyles';

type ReleaseVersionHistoryProps = {
    release: Release;
    token?: string;
    onClose: () => void;
};

/** Every published version of a release, newest first: when, the owner's note, and what changed. */
export function ReleaseVersionHistory({ release, token, onClose }: ReleaseVersionHistoryProps) {
    const [versions, setVersions] = useState<ReleaseVersion[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        fetchReleaseVersions(release.id, token)
            .then(result => { if (!cancelled) setVersions(result); })
            .catch(err => { if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load version history.'); });
        return () => { cancelled = true; };
    }, [release.id, token]);

    return (
        <Modal size="md" onClose={onClose} title="Version history" subtitle={release.name}>
            <div className="flex flex-col p-4">
                {error && <InlineError size="md">{error}</InlineError>}
                {!versions && !error && <VersionHistorySkeleton />}
                {versions && versions.length === 0 && (
                    // Releases published before versions were recorded
                    <EmptyState size="inline">No version history yet. It starts with the next update.</EmptyState>
                )}
                {versions && versions.length > 0 && (
                    <ol className="flex flex-col">
                        {versions.map((version, i) => (
                            <li key={version.version} className="flex flex-col gap-1.5 py-3 border-t border-(--divider) first:border-t-0 first:pt-0">
                                <div className="flex items-center gap-2">
                                    <span className={headingClass('panel')}>v{version.version}</span>
                                    {i === 0 && <Plate variant="success" size="sm">Current</Plate>}
                                    {version.published_at && (
                                        <span className="text-[12px] text-(--text-tertiary)">{formatShortDate(version.published_at)}</span>
                                    )}
                                </div>
                                {version.note && <p className="text-[13px] text-(--text-secondary)">{version.note}</p>}
                                <VersionChanges version={version} />
                            </li>
                        ))}
                    </ol>
                )}
            </div>
        </Modal>
    );
}

function VersionChanges({ version }: { version: ReleaseVersion }) {
    if (version.changes.length === 0) {
        return <span className="text-[12px] text-(--text-tertiary)">{version.version === 1 ? 'First published.' : 'Republished with no card changes.'}</span>;
    }
    return (
        <ul className="flex flex-col gap-1">
            {version.changes.map(change => {
                const parts = change.is_new
                    ? [`new edition, ${change.added} card${change.added === 1 ? '' : 's'}`]
                    : [
                        change.renamed_from && `renamed from ${change.renamed_from}`,
                        change.added > 0 && `+${change.added} added`,
                        change.removed > 0 && `−${change.removed} removed`,
                        change.changed > 0 && `${change.changed} changed`,
                        change.renumbered > 0 && `${change.renumbered} renumbered`,
                    ].filter(Boolean);
                return (
                    <li key={change.name} className="text-[12px] text-(--text-secondary)">
                        <span className="font-semibold text-(--text-primary)">{change.name}</span>
                        {parts.length > 0 ? ` · ${parts.join(' · ')}` : ' · style or card details'}
                    </li>
                );
            })}
        </ul>
    );
}

function VersionHistorySkeleton() {
    return (
        <div aria-label="Loading version history" className="flex flex-col animate-pulse">
            {[0, 1, 2].map(row => (
                <div key={row} className="flex flex-col gap-2 py-3 border-t border-(--divider) first:border-t-0 first:pt-0">
                    <div className="h-4 w-24 rounded-plate bg-(--background-tertiary)" />
                    <div className="h-3 w-2/3 rounded-plate bg-(--background-tertiary)" />
                </div>
            ))}
        </div>
    );
}
