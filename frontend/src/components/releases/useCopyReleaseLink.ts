import { releaseShareUrl } from '../../api/releases';
import { useCopyLink } from '../../hooks/useCopyLink';

/** Copies a release's short link (see `useCopyLink`). */
export function useCopyReleaseLink(sharePath: string, editionSlug?: string | null, releaseCardId?: string | null) {
    return useCopyLink(releaseShareUrl(sharePath, editionSlug, releaseCardId));
}
