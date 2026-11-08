import type { Release, ReleaseVisibility } from '../../api/releases';

/** Each "Who can find it" option: its picker label and detail, and the owner-only plate for the
 *  restricted ones (a listed release needs no plate). */
export const RELEASE_VISIBILITY: Record<ReleaseVisibility, { label: string; detail: string; plate?: { label: string; title: string } }> = {
    listed: {
        label: 'Listed',
        detail: 'Shows in Community and search',
    },
    link: {
        label: 'Link only',
        detail: 'Anyone with the link, not listed',
        plate: { label: 'Link only', title: "Opens from its link but isn't listed in Community or search" },
    },
    private: {
        label: 'Only me',
        detail: 'For your own teams and card search',
        plate: { label: 'Private', title: 'Published for your own use. Nobody else can open it' },
    },
};

export const RELEASE_VISIBILITY_ORDER: ReleaseVisibility[] = ['listed', 'link', 'private'];

export function isPrivateRelease(release: Pick<Release, 'visibility'>): boolean {
    return release.visibility === 'private';
}

/** Who sees the live version, as a sentence for publish status lines. */
export function releaseAudience(visibility: ReleaseVisibility): string {
    switch (visibility) {
        case 'listed': return 'Anyone can browse it and use its cards.';
        case 'link': return 'Anyone with the link can browse it and use its cards.';
        case 'private': return 'Only you can see it and use its cards.';
    }
}
