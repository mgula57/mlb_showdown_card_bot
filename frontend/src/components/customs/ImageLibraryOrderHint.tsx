import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FaGoogleDrive, FaRobot } from 'react-icons/fa';
import { IMAGE_LIBRARIES_PATH, useImageLibraries } from '../account/useImageLibraries';
import { NewBadge } from '../shared/NewBadge';
import ImageLibraryName from '../account/ImageLibraryName';
import { LoginModal } from '../auth/LoginModal';

const linkClass = 'text-tertiary hover:underline cursor-pointer';

/**
 * Shows signed-in users which image libraries "Auto" player images search, in order, with a link
 * to manage them in Account settings. Users without libraries get a link to connect one, and
 * signed-out users get a button to sign in first.
 */
export const ImageLibraryOrderHint: React.FC<{ className?: string }> = ({ className = '' }) => {
    const { token, overview, ordered, isLoading } = useImageLibraries();
    const [isLoginOpen, setIsLoginOpen] = useState(false);

    if (!token) {
        return (
            <>
                <button
                    type="button"
                    onClick={() => setIsLoginOpen(true)}
                    className={`flex items-center gap-1.5 text-xs ${linkClass} ${className}`}
                >
                    <FaGoogleDrive className="shrink-0" />
                    Sign in to link your Google Drive
                    <NewBadge />
                </button>
                {isLoginOpen && <LoginModal onClose={() => setIsLoginOpen(false)} />}
            </>
        );
    }

    if (isLoading) {
        return (
            <div className={`space-y-1.5 animate-pulse ${className}`}>
                <div className="h-3 w-28 rounded bg-background-tertiary" />
                <div className="h-3 w-36 rounded bg-background-tertiary" />
            </div>
        );
    }
    if (!overview) return null;

    if (overview.libraries.length === 0) {
        return (
            <Link to={IMAGE_LIBRARIES_PATH} className={`flex items-center gap-1.5 text-xs ${linkClass} ${className}`}>
                <FaGoogleDrive className="shrink-0" />
                Use your own images from Google Drive
                <NewBadge />
            </Link>
        );
    }

    return (
        <div className={`text-xs ${className}`}>
            <div className="flex items-center justify-between gap-2 mb-1">
                <span className="flex items-center gap-1.5 text-gray-500">Image search order <NewBadge /></span>
                <Link to={IMAGE_LIBRARIES_PATH} className={linkClass}>Manage</Link>
            </div>
            <ol className="space-y-0.5">
                {ordered.map((entry, index) => (
                    <li key={entry.id} className="flex items-center gap-1.5 min-w-0 text-secondary">
                        <span className="w-3 shrink-0 text-right text-gray-500">{index + 1}</span>
                        {entry.isShowdownBot
                            ? <FaRobot className="shrink-0 text-gray-500" />
                            : <FaGoogleDrive className="shrink-0 text-gray-500" />}
                        <ImageLibraryName name={entry.name} isShowdownBot={entry.isShowdownBot} />
                    </li>
                ))}
            </ol>
        </div>
    );
};

export default ImageLibraryOrderHint;
