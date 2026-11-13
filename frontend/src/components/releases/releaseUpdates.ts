import type { Release, ReleaseEditionSummary, ReleaseVersionChange } from '../../api/releases';

/** How long a release tile flags an update that added cards. */
const TILE_UPDATE_DAYS = 14;
/** How long an edition added by an update keeps its "New" tab plate. */
const NEW_EDITION_DAYS = 30;

const DAY_MS = 24 * 60 * 60 * 1000;

const isWithinDays = (iso: string | null, days: number): boolean =>
    !!iso && Date.now() - new Date(iso).getTime() < days * DAY_MS;

const plural = (count: number, noun: string) => `${count} ${noun}${count === 1 ? '' : 's'}`;

/** The tile's update plate: "New edition" or "New cards" while a recent update added cards, else null. */
export function releaseUpdateLabel(release: Release): string | null {
    if (!isWithinDays(release.cards_added_at, TILE_UPDATE_DAYS)) return null;
    return release.latest_version_changes?.some(change => change.is_new) ? 'New edition' : 'New cards';
}

/** An edition that a recent update added to an already-published release. */
export const isNewEdition = (edition: ReleaseEditionSummary): boolean =>
    edition.added_in_update && isWithinDays(edition.published_at, NEW_EDITION_DAYS);

/** What a version did to one edition, e.g. ["new edition, 7 cards"] or ["+3 added", "1 changed"].
 *  Empty when only style or card details changed. */
export function describeEditionChange(change: ReleaseVersionChange): string[] {
    if (change.is_new) return [`new edition, ${plural(change.added, 'card')}`];
    if (change.is_removed) return [`edition removed, ${plural(change.removed, 'card')} retired`];
    return [
        change.renamed_from && `renamed from ${change.renamed_from}`,
        change.added > 0 && `+${change.added} added`,
        change.removed > 0 && `−${change.removed} removed`,
        change.changed > 0 && `${change.changed} changed`,
        change.renumbered > 0 && `${change.renumbered} renumbered`,
    ].filter((part): part is string => !!part);
}
