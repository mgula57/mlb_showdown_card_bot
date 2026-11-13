import React from 'react';
import { Modal } from '../shared/Modal';
import { ConnectDriveButton, ImageLibrariesDescription, ImageLibraryList } from './ImageLibrarySettings';

/** Manage image libraries without leaving the current page (ex: the Release Builder). Same
 * controls as the Account page's Image Libraries section. */
export const ImageLibrariesModal: React.FC<{ onClose: () => void }> = ({ onClose }) => (
    <Modal title="Image Libraries" subtitle="Where Auto player images come from" size="md" onClose={onClose}>
        <div className="px-4 py-4 flex flex-col gap-4">
            <div className="flex items-start justify-between gap-4">
                <p className="text-sm text-(--text-tertiary)"><ImageLibrariesDescription /></p>
                <ConnectDriveButton />
            </div>
            <ImageLibraryList />
        </div>
    </Modal>
);

export default ImageLibrariesModal;
