import React from 'react';
import { Link } from 'react-router-dom';
import { FaLayerGroup } from 'react-icons/fa6';
import { SOURCE_BADGE_CLASS } from './ImageSourceBadge';

/** The Release Builder edition a card came from, and the path that opens the card there. */
export type CardReleaseSource = {
    releaseName: string;
    editionName: string;
    /** `/release-builder/:releaseId/:editionSlug/:releaseCardId` */
    path: string;
};

/** Source tag linking a release card back to its edition in the Release Builder. */
export const ReleaseSourceBadge: React.FC<{ source?: CardReleaseSource | null }> = ({ source }) => {
    if (!source) return null;
    const label = `${source.releaseName} · ${source.editionName}`;
    return (
        <Link
            to={source.path}
            title={`Open this card in ${label}`}
            className={`${SOURCE_BADGE_CLASS} cursor-pointer transition-colors hover:border-(--showdown-blue) hover:text-(--showdown-blue)`}
        >
            <span className="shrink-0 w-3 h-3 flex items-center"><FaLayerGroup /></span>
            <span className="min-w-0 truncate">{label}</span>
        </Link>
    );
};

export default ReleaseSourceBadge;
