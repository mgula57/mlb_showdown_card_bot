/**
 * @fileoverview Image Library Settings
 *
 * Account section for connecting Google Drive folders as player image libraries and choosing
 * the order libraries are searched when a card uses "Auto" player images. Its pieces
 * (`ConnectDriveButton`, `ImageLibraryList`) are also used by `ImageLibrariesModal`.
 */

import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { FaArrowDown, FaArrowUp, FaGoogleDrive, FaImages, FaPlus, FaRobot, FaSpinner, FaSyncAlt, FaTrash } from 'react-icons/fa';
import AccountSection from './AccountSection';
import ImageLibraryName from './ImageLibraryName';
import DriveLibrarySetupModal from './DriveLibrarySetupModal';
import ImageLibraryGuideLink from './ImageLibraryGuideLink';
import { IMAGE_LIBRARIES_SECTION_ID, useImageLibraries } from './useImageLibraries';
import type { OrderedImageLibrary } from './useImageLibraries';
import { deleteImageLibrary, saveImageLibrary, updateImageLibraryOrder } from '../../api/imageLibraries';

import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { buttonClass } from '../shared/buttonStyles';
import { smoothScrollBehavior } from '../../hooks/usePrefersReducedMotion';
import { EmptyState } from '../shared/EmptyState';
const MAX_LIBRARIES = 5; // Matches UserImageLibraries.MAX_LIBRARIES

const iconButton = 'p-1.5 rounded-control text-(--text-tertiary) hover:text-(--text-secondary) hover:bg-(--background-tertiary) cursor-pointer disabled:cursor-not-allowed disabled:opacity-30';

const formatDate = (iso: string | null) => iso
    ? new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : 'never';

const LibraryRowSkeleton: React.FC = () => (
    <div className="flex items-center gap-3 rounded-card border border-form-element p-3 animate-pulse">
        <div className="w-6 h-6 rounded-plate bg-(--background-tertiary)" />
        <div className="flex-1 space-y-1.5">
            <div className="h-4 w-40 rounded-plate bg-(--background-tertiary)" />
            <div className="h-3 w-56 rounded-plate bg-(--background-tertiary)" />
        </div>
    </div>
);

type LibraryRowProps = {
    entry: OrderedImageLibrary;
    rank: number;
    isFirst: boolean;
    isLast: boolean;
    isBusy: boolean;
    rowError: string | null;
    onMove: (direction: -1 | 1) => void;
    onRetest: () => void;
    onRemove: () => void;
};

const LibraryRow: React.FC<LibraryRowProps> = ({ entry, rank, isFirst, isLast, isBusy, rowError, onMove, onRetest, onRemove }) => {
    const { library } = entry;
    const subtitle = library
        ? `${library.recognized_image_count} of ${library.image_count} images usable · verified ${formatDate(library.verified_at)}`
        : 'Official Showdown Bot player images';
    return (
        <div className="rounded-card border border-form-element p-3">
            <div className="flex items-center gap-3">
                <span className="w-6 h-6 shrink-0 rounded-plate bg-(--showdown-blue-fill) text-white text-xs font-bold tabular-nums flex items-center justify-center">{rank}</span>
                {entry.isShowdownBot
                    ? <FaRobot className="shrink-0 text-(--text-tertiary)" />
                    : <FaGoogleDrive className="shrink-0 text-(--text-tertiary)" />}
                <div className="flex-1 min-w-0">
                    <ImageLibraryName name={entry.name} isShowdownBot={entry.isShowdownBot} className="text-secondary font-medium" />
                    <p className="text-xs text-(--text-tertiary) truncate">{subtitle}</p>
                </div>
                <div className="flex items-center shrink-0">
                    {library && (
                        <>
                            <button type="button" className={iconButton} onClick={onRetest} disabled={isBusy} title="Re-test connection">
                                {isBusy ? <FaSpinner className="animate-spin" /> : <FaSyncAlt />}
                            </button>
                            <button type="button" className={iconButton} onClick={onRemove} disabled={isBusy} title="Remove library">
                                <FaTrash />
                            </button>
                        </>
                    )}
                    <button type="button" className={iconButton} onClick={() => onMove(-1)} disabled={isFirst} title="Search earlier">
                        <FaArrowUp />
                    </button>
                    <button type="button" className={iconButton} onClick={() => onMove(1)} disabled={isLast} title="Search later">
                        <FaArrowDown />
                    </button>
                </div>
            </div>
            {rowError && <p className="text-xs text-(--red) mt-2 pl-9">{rowError}</p>}
        </div>
    );
};

/** One line on what image libraries do, with a link to the image guide. */
export const ImageLibrariesDescription: React.FC = () => (
    <>Use player images from your own Google Drive folders when a card's Player Image is set to Auto. <ImageLibraryGuideLink>How to make images</ImageLibraryGuideLink></>
);

/** Opens the Google Drive folder setup flow. */
export const ConnectDriveButton: React.FC<{ size?: 'sm' | 'md' }> = ({ size = 'md' }) => {
    const { token, overview, isLoading, setOverview } = useImageLibraries();
    const [isSetupOpen, setIsSetupOpen] = useState(false);

    const libraryCount = overview?.libraries.length ?? 0;
    const isUnavailable = !!overview && !overview.service_account_email;

    return (
        <>
            <button
                type="button"
                onClick={() => setIsSetupOpen(true)}
                disabled={isLoading || isUnavailable || libraryCount >= MAX_LIBRARIES}
                title={libraryCount >= MAX_LIBRARIES ? `You can connect up to ${MAX_LIBRARIES} folders` : undefined}
                className={buttonClass('primary', size)}
            >
                <FaPlus className="w-3 h-3" />
                <span className="hidden sm:inline">Connect Google Drive</span>
                <span className="sm:hidden">Connect</span>
            </button>
            {isSetupOpen && token && overview?.service_account_email && (
                <DriveLibrarySetupModal
                    token={token}
                    serviceAccountEmail={overview.service_account_email}
                    onClose={() => setIsSetupOpen(false)}
                    onSaved={setOverview}
                />
            )}
        </>
    );
};

/** The user's libraries in search order, with reorder, re-test and remove controls. */
export const ImageLibraryList: React.FC = () => {
    const { token, overview, ordered, error, isLoading, setOverview } = useImageLibraries();
    const [busyId, setBusyId] = useState<string | null>(null);
    const [rowErrors, setRowErrors] = useState<Record<string, string>>({});
    const [orderError, setOrderError] = useState<string | null>(null);

    const libraryCount = overview?.libraries.length ?? 0;
    const isUnavailable = !!overview && !overview.service_account_email;
    const setRowError = (id: string, message: string | null) => setRowErrors(prev => {
        const next = { ...prev };
        if (message) next[id] = message; else delete next[id];
        return next;
    });

    const handleMove = async (index: number, direction: -1 | 1) => {
        if (!token || !overview) return;
        const order = [...overview.order];
        [order[index], order[index + direction]] = [order[index + direction], order[index]];
        const previous = overview;
        setOverview({ ...overview, order }); // optimistic
        setOrderError(null);
        try {
            setOverview(await updateImageLibraryOrder(token, order));
        } catch (err) {
            setOverview(previous);
            setOrderError((err as Error).message);
        }
    };

    const handleRetest = async (entry: OrderedImageLibrary) => {
        if (!token || !entry.library) return;
        setBusyId(entry.id);
        setRowError(entry.id, null);
        try {
            setOverview(await saveImageLibrary(token, entry.library.folder_id));
        } catch (err) {
            setRowError(entry.id, (err as Error).message);
        } finally {
            setBusyId(null);
        }
    };

    const handleRemove = async (entry: OrderedImageLibrary) => {
        if (!token || !entry.library) return;
        if (!window.confirm(`Remove "${entry.name}"? Showdown Bot will stop using its images. To fully revoke access, also unshare the folder in Google Drive.`)) return;
        setBusyId(entry.id);
        setRowError(entry.id, null);
        try {
            setOverview(await deleteImageLibrary(token, entry.id));
        } catch (err) {
            setRowError(entry.id, (err as Error).message);
        } finally {
            setBusyId(null);
        }
    };

    return (
        <>
            {error && <p className="text-sm text-(--red)">{error}</p>}
            {isUnavailable && <p className="text-sm text-(--text-tertiary) mb-3">Google Drive libraries are temporarily unavailable.</p>}

            {isLoading ? (
                <div className="space-y-2">
                    <LibraryRowSkeleton />
                    <LibraryRowSkeleton />
                </div>
            ) : overview && (
                <div className="space-y-2">
                    <p className={FIELD_LABEL_CLASS}>Search order</p>
                    <p className="text-xs text-(--text-tertiary) -mt-1 mb-2">
                        Libraries are checked top to bottom and the first one with a matching image is used.
                    </p>
                    {ordered.map((entry, index) => (
                        <LibraryRow
                            key={entry.id}
                            entry={entry}
                            rank={index + 1}
                            isFirst={index === 0}
                            isLast={index === ordered.length - 1}
                            isBusy={busyId === entry.id}
                            rowError={rowErrors[entry.id] ?? null}
                            onMove={direction => handleMove(index, direction)}
                            onRetest={() => handleRetest(entry)}
                            onRemove={() => handleRemove(entry)}
                        />
                    ))}
                    {orderError && <p className="text-xs text-(--red)">{orderError}</p>}
                    {libraryCount === 0 && (
                        <EmptyState size="panel" title="No folders yet.">
                            Connect a Google Drive folder to use your own player images on cards.
                        </EmptyState>
                    )}
                </div>
            )}
        </>
    );
};

export const ImageLibrarySettings: React.FC = () => {
    const location = useLocation();

    // Pages stay mounted (hidden) across routes, so the browser won't jump to the hash on its own
    useEffect(() => {
        if (location.pathname !== '/account' || location.hash !== `#${IMAGE_LIBRARIES_SECTION_ID}`) return;
        const timeout = setTimeout(() => {
            document.getElementById(IMAGE_LIBRARIES_SECTION_ID)?.scrollIntoView({ behavior: smoothScrollBehavior(), block: 'start' });
        }, 50);
        return () => clearTimeout(timeout);
    }, [location.pathname, location.hash, location.key]);

    return (
        <AccountSection
            id={IMAGE_LIBRARIES_SECTION_ID}
            title="Image Libraries"
            icon={<FaImages />}
            description={<ImageLibrariesDescription />}
            action={<ConnectDriveButton />}
        >
            <ImageLibraryList />
        </AccountSection>
    );
};

export default ImageLibrarySettings;
