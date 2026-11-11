import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { fetchReleaseByLink } from '../../api/releases';
import { EmptyState } from '../shared/EmptyState';
import { EditionBuilderSkeleton } from './EditionBuilder';
import { buttonClass } from '../shared/buttonStyles';

/** A release's short link, `/r/<owner>/<release>[/<edition slug>[/<card>]]` (or the older
 *  `/r/<release>[/...]`): the server works out which release, edition and card it means, and this
 *  replaces the URL with its Release Builder page. Link previews for these paths are served by Flask. */
export default function ReleaseShortLink() {
    const { session, loading: authLoading } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const linkPath = location.pathname.replace(/^\/r\//, '').replace(/\/+$/, '');
    const [missing, setMissing] = useState(false);

    useEffect(() => {
        // Wait for the session so an owner's unpublished release resolves too
        if (authLoading || !linkPath) return;
        let cancelled = false;
        fetchReleaseByLink(linkPath, session?.access_token)
            .then(({ release, edition_slug, card_ref }) => {
                if (cancelled) return;
                const editionPath = edition_slug ? `/${edition_slug}${card_ref ? `/${card_ref}` : ''}` : '';
                navigate(`/release-builder/${release.id}${editionPath}`, { replace: true });
            })
            .catch(() => { if (!cancelled) setMissing(true); });
        return () => { cancelled = true; };
    }, [authLoading, linkPath, session?.access_token, navigate]);

    if (missing) {
        return (
            <EmptyState
                size="page"
                title="Release not found."
                action={<Link to="/release-builder" className={buttonClass('primary')}>Browse releases</Link>}
            >
                It may have been unpublished, or the link is mistyped.
            </EmptyState>
        );
    }
    return (
        <div className="flex flex-col h-[calc(100dvh-2.5rem)]">
            <EditionBuilderSkeleton />
        </div>
    );
}
