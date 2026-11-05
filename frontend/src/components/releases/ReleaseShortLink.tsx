import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { fetchReleaseBySlug } from '../../api/releases';
import { EmptyState } from '../shared/EmptyState';
import { EditionBuilderSkeleton } from './EditionBuilder';
import { buttonClass } from '../shared/buttonStyles';

/** A release's short link, `/r/<slug>[/<edition slug>[/<card>]]`: looks the release up by slug and replaces
 *  the URL with its Release Builder page. Link previews for these paths are served by Flask. */
export default function ReleaseShortLink() {
    const { session, loading: authLoading } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [, , slug = '', editionSlug = '', cardRef = ''] = location.pathname.split('/');
    const [missing, setMissing] = useState(false);

    useEffect(() => {
        // Wait for the session so an owner's unpublished release resolves too
        if (authLoading || !slug) return;
        let cancelled = false;
        fetchReleaseBySlug(slug, session?.access_token)
            .then(release => {
                if (cancelled) return;
                const editionPath = editionSlug ? `/${editionSlug}${cardRef ? `/${cardRef}` : ''}` : '';
                navigate(`/release-builder/${release.id}${editionPath}`, { replace: true });
            })
            .catch(() => { if (!cancelled) setMissing(true); });
        return () => { cancelled = true; };
    }, [authLoading, slug, editionSlug, cardRef, session?.access_token, navigate]);

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
