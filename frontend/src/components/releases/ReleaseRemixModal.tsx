import { FaCodeFork } from 'react-icons/fa6';
import { remixRelease, type Release, type ReleaseCreatePayload } from '../../api/releases';
import { NewReleaseModal } from './NewReleaseModal';

type ReleaseRemixModalProps = {
    /** Someone else's published release, as a visitor sees it (published editions only). */
    release: Release;
    token: string;
    onClose: () => void;
    /** The new release, owned by the viewer and not yet published. */
    onRemixed: (release: Release) => void;
};

/** Names a remix: a new release of the viewer's own, started from this one's editions, cards, card
 *  styles and algorithm settings, and credited to it on its public page. */
export function ReleaseRemixModal({ release, token, onClose, onRemixed }: ReleaseRemixModalProps) {
    const editionCount = release.editions.length;

    async function handleConfirm(payload: ReleaseCreatePayload) {
        onRemixed(await remixRelease(release.id, payload, token));
    }

    return (
        <NewReleaseModal
            title="Remix Release"
            subtitle={`Start your own set from ${release.name}`}
            initial={{
                name: `${release.name} Remix`,
                description: release.description ?? '',
                ...(release.default_showdown_set ? { default_showdown_set: release.default_showdown_set } : {}),
            }}
            confirmLabel="Start remix"
            confirmIcon={<FaCodeFork className="text-[11px]" />}
            onConfirm={handleConfirm}
            onCancel={onClose}
        >
            <p className="text-[12px] text-(--text-secondary)">
                Copies its {editionCount} edition{editionCount === 1 ? '' : 's'} with their cards, card styles and
                algorithm settings into a new release you own. Nothing changes on the original, and yours stays
                private until you publish it, credited as remixed from {release.name}
                {release.creator_username ? ` by ${release.creator_username}` : ''}.
            </p>
        </NewReleaseModal>
    );
}
