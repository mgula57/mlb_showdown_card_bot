import React from 'react';
import { FaGoogleDrive, FaLink, FaRobot, FaUpload } from 'react-icons/fa';
import type { ShowdownBotCardImageSource } from '../../../api/showdownBotCard';
import ImageLibraryName from '../../account/ImageLibraryName';

const SHOWDOWN_BOT_LIBRARY_NAME = 'Showdown Bot'; // Matches ImageLibrary.showdown_bot() in images.py

/** Icon + label describing where a card's player image came from, or null if there's nothing to show. */
const describeImageSource = (source: ShowdownBotCardImageSource | null | undefined): { icon: React.ReactNode; label: React.ReactNode; title: string } | null => {
    if (!source) return null;
    if (source.type === 'Upload') return { icon: <FaUpload />, label: 'Uploaded image', title: 'Player image uploaded in the card builder' };
    if (source.type === 'Link') return { icon: <FaLink />, label: 'Image link', title: 'Player image from a link' };
    if (!source.library_name) return null;
    if (source.library_name === SHOWDOWN_BOT_LIBRARY_NAME) {
        return { icon: <FaRobot />, label: <ImageLibraryName name={source.library_name} isShowdownBot />, title: 'Player image from the official Showdown Bot image library' };
    }
    return { icon: <FaGoogleDrive />, label: source.library_name, title: `Player image from your Google Drive library "${source.library_name}"` };
};

/** Pill showing the player image's source (Showdown Bot library, a user's Drive library, upload, or link). */
export const ImageSourceBadge: React.FC<{ source?: ShowdownBotCardImageSource | null }> = ({ source }) => {
    const description = describeImageSource(source);
    if (!description) return null;
    return (
        <div
            title={description.title}
            className="
                flex items-center gap-1.5 max-w-56
                py-1 px-3 rounded-2xl
                border border-(--divider)
                text-xs font-semibold text-(--text-secondary)
            "
        >
            <span className="shrink-0 w-3 h-3 flex items-center">{description.icon}</span>
            <span className="min-w-0 truncate">{description.label}</span>
        </div>
    );
};

export default ImageSourceBadge;
