import { useEffect, useState } from 'react';
import { fetchMyFaceoffs, type FaceoffSummary } from '../../../api/faceoff';
import { Heading } from '../../shared/Heading';
import { FaceoffRow } from './FaceoffRow';

const RECENT_COUNT = 6;

type Props = {
    token: string;
    onOpenFaceoff: (faceoffId: string) => void;
};

/** The signed-in user's latest Faceoffs on the My Teams tab, including games between their own
 *  teams. Renders nothing until there's at least one, so it never flashes an empty section. */
export function RecentFaceoffsShelf({ token, onOpenFaceoff }: Props) {
    const [faceoffs, setFaceoffs] = useState<FaceoffSummary[]>([]);

    useEffect(() => {
        let stale = false;
        fetchMyFaceoffs(token, RECENT_COUNT)
            .then(data => { if (!stale) setFaceoffs(data); })
            .catch(() => { if (!stale) setFaceoffs([]); });
        return () => { stale = true; };
    }, [token]);

    if (faceoffs.length === 0) return null;

    return (
        <div className="flex flex-col gap-2">
            <Heading level="panel">Recent Faceoffs</Heading>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
                {faceoffs.map(faceoff => (
                    <FaceoffRow key={faceoff.faceoff_id} faceoff={faceoff} onOpen={() => onOpenFaceoff(faceoff.faceoff_id)} />
                ))}
            </div>
        </div>
    );
}
