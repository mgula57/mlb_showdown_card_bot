import type { Release } from '../../api/releases';
import { Plate } from '../shared/Plate';
import { RELEASE_VISIBILITY } from './releaseVisibility';

/** "Link only" or "Private" beside a release the owner restricted. Nothing for a listed release. */
export function ReleaseVisibilityPlate({ release, show = true }: { release: Pick<Release, 'visibility'>; show?: boolean }) {
    const plate = RELEASE_VISIBILITY[release.visibility]?.plate;
    if (!show || !plate) return null;
    return <Plate variant="outline" size="sm" title={plate.title}>{plate.label}</Plate>;
}
