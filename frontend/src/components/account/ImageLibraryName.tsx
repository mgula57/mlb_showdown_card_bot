import React from 'react';
import { MdVerified } from 'react-icons/md';

/** Display name for the built-in library. The backend's stable library_name stays 'Showdown Bot'. */
const SHOWDOWN_BOT_DISPLAY_NAME = 'Showdown Bot (Official)';

/** Image library name, showing the built-in library as "Showdown Bot (Official)" with a verified check. */
export const ImageLibraryName: React.FC<{ name: string; isShowdownBot: boolean; className?: string }> = ({ name, isShowdownBot, className = '' }) => (
    <span className={`flex items-center gap-1 min-w-0 ${className}`}>
        <span className="truncate">{isShowdownBot ? SHOWDOWN_BOT_DISPLAY_NAME : name}</span>
        {isShowdownBot && <MdVerified className="shrink-0 text-blue-500" aria-label="Official" />}
    </span>
);

export default ImageLibraryName;
