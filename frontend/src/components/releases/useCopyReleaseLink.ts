import { useState } from 'react';
import { releaseShareUrl } from '../../api/releases';

/** Copies a release's short link, flipping `copied` on for a moment. When the clipboard is refused
 * the link comes back in `error` so it can still be copied by hand. */
export function useCopyReleaseLink(slug: string, editionSlug?: string | null, releaseCardId?: string | null) {
    const [copied, setCopied] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const url = releaseShareUrl(slug, editionSlug, releaseCardId);

    async function copy() {
        setError(null);
        try {
            await navigator.clipboard.writeText(url);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            setError(`Couldn't copy. The link is ${url}`);
        }
    }

    return { url, copied, error, copy };
}
