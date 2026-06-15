import { useState, useEffect, useRef, useCallback, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { FaBolt, FaTrash, FaCheck, FaTimes, FaPlus, FaLock, FaPencilAlt } from 'react-icons/fa';
import { FaFloppyDisk } from 'react-icons/fa6';
import { LoadingStatusToast } from '../shared/LoadingStatusToast';
import { CardSource } from '../../types/cardSource';
import {
    type QuickFilter,
    getUserQuickFilters,
    createUserQuickFilter,
    updateUserQuickFilter,
    deleteUserQuickFilter,
} from '../../api/userQuickFilters';
import { LoginModal } from '../auth/LoginModal';

function Tip({ label, children }: { label: string; children: ReactNode }) {
    return (
        <div className="relative group/tip shrink-0">
            {children}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 z-100 pointer-events-none
                            opacity-0 group-hover/tip:opacity-100 transition-opacity duration-150">
                <div className="bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap shadow-lg">
                    {label}
                </div>
            </div>
        </div>
    );
}

type Props = {
    source: CardSource;
    defaultPresets: QuickFilter[];
    currentFilters: Record<string, unknown>;
    onApply: (filters: Record<string, unknown>) => void;
    token: string | null;
};

export function QuickFiltersDropdown({ source, defaultPresets, currentFilters, onApply, token }: Props) {
    const [isOpen, setIsOpen] = useState(false);
    const [userFilters, setUserFilters] = useState<QuickFilter[]>([]);
    const [isLoadingFilters, setIsLoadingFilters] = useState(false);
    const [saveMode, setSaveMode] = useState(false);
    const [saveName, setSaveName] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [renamingId, setRenamingId] = useState<string | null>(null);
    const [renameValue, setRenameValue] = useState('');
    const [toast, setToast] = useState<{ message: string; color: string } | null>(null);
    const [toastExiting, setToastExiting] = useState(false);
    const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [alignRight, setAlignRight] = useState(false);
    const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const saveInputRef = useRef<HTMLInputElement>(null);
    const renameInputRef = useRef<HTMLInputElement>(null);
    // Snapshot of currentFilters captured after parent processes onApply
    const appliedSnapshotRef = useRef<Record<string, unknown> | null>(null);
    const captureNextFiltersRef = useRef(false);

    const isLoggedIn = !!token;

    // Capture the resolved filter state on the next render after onApply fires
    useEffect(() => {
        if (captureNextFiltersRef.current) {
            appliedSnapshotRef.current = currentFilters;
            captureNextFiltersRef.current = false;
        }
    }, [currentFilters]);

    // True only when the selected preset's applied state still exactly matches current filters
    const selectedPresetFiltersMatch =
        selectedPresetId !== null &&
        appliedSnapshotRef.current !== null &&
        JSON.stringify(currentFilters) === JSON.stringify(appliedSnapshotRef.current);

    const showToast = (message: string, color: string) => {
        if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
        setToast({ message, color });
        setToastExiting(false);
        toastTimerRef.current = setTimeout(() => {
            setToastExiting(true);
            setTimeout(() => setToast(null), 300);
        }, 2500);
    };

    const loadUserFilters = useCallback(async () => {
        if (!token) return;
        setIsLoadingFilters(true);
        const data = await getUserQuickFilters(token, source);
        setUserFilters(data);
        setIsLoadingFilters(false);
    }, [token, source]);

    useEffect(() => {
        if (isOpen && isLoggedIn) {
            loadUserFilters();
        }
        if (!isOpen) {
            setSaveMode(false);
            setSaveName('');
        }
    }, [isOpen, isLoggedIn]);

    // Close on outside click; also compute left/right alignment on open
    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setIsOpen(false);
            }
        };
        if (isOpen) {
            document.addEventListener('mousedown', handleClick);
            // Decide alignment: flip to right-anchored if button is in the right half of the viewport
            if (containerRef.current) {
                const rect = containerRef.current.getBoundingClientRect();
                const dropdownWidth = 320; // max-w-80 = 20rem = 320px
                setAlignRight(rect.left + dropdownWidth > window.innerWidth - 16);
            }
        }
        return () => document.removeEventListener('mousedown', handleClick);
    }, [isOpen]);

    // Focus save input when save mode opens
    useEffect(() => {
        if (saveMode) saveInputRef.current?.focus();
    }, [saveMode]);

    // Focus rename input when rename mode opens
    useEffect(() => {
        if (renamingId) renameInputRef.current?.focus();
    }, [renamingId]);

    const handleApply = (filters: Record<string, unknown>, presetId?: string) => {
        onApply(filters);
        setSelectedPresetId(presetId ?? null);
        captureNextFiltersRef.current = !!presetId;
        if (!presetId) appliedSnapshotRef.current = null;
        setIsOpen(false);
    };

    const handleSave = async () => {
        if (!token || !saveName.trim()) return;
        setIsSaving(true);
        const newFilter: QuickFilter = {
            id: crypto.randomUUID(),
            name: saveName.trim(),
            filters: currentFilters,
        };
        await createUserQuickFilter(token, source, newFilter);
        setUserFilters(prev => [...prev, newFilter]);
        setSelectedPresetId(newFilter.id);
        appliedSnapshotRef.current = currentFilters;
        setSaveMode(false);
        setSaveName('');
        setIsSaving(false);
        showToast('Filter saved!', 'rgb(34, 197, 94)');
    };

    const handleDelete = async (id: string) => {
        if (!token) return;
        setUserFilters(prev => prev.filter(f => f.id !== id));
        await deleteUserQuickFilter(token, id);
        showToast('Filter deleted', 'rgb(156, 163, 175)');
    };

    const handleRenameCommit = async () => {
        if (!token || !renamingId || !renameValue.trim()) return;
        const trimmed = renameValue.trim();
        setUserFilters(prev => prev.map(f => f.id === renamingId ? { ...f, name: trimmed } : f));
        setRenamingId(null);
        await updateUserQuickFilter(token, renamingId, { name: trimmed });
        showToast('Filter renamed!', 'rgb(34, 197, 94)');
    };

    const handleRenameCancel = () => {
        setRenamingId(null);
        setRenameValue('');
    };

    const handleUpdateFilters = async (id: string) => {
        if (!token) return;
        setUserFilters(prev => prev.map(f => f.id === id ? { ...f, filters: currentFilters } : f));
        await updateUserQuickFilter(token, id, { filters: currentFilters });
        showToast('Preset updated!', 'rgb(34, 197, 94)');
    };

    return (
        <div ref={containerRef} className="relative">
            <button
                onClick={() => setIsOpen(prev => !prev)}
                className={`
                    px-3 h-11 rounded-xl border-2 flex items-center gap-2
                    ${isOpen
                        ? 'bg-(--background-secondary-hover) border-form-element'
                        : 'bg-(--background-secondary) border-form-element hover:bg-(--background-secondary-hover)'}
                `}
            >
                <FaBolt className={selectedPresetFiltersMatch ? 'text-(--success)' : 'text-primary'} />
                <span className="hidden sm:inline font-medium">
                    {selectedPresetFiltersMatch
                        ? ([...userFilters, ...defaultPresets].find(p => p.id === selectedPresetId)?.name ?? 'Presets')
                        : 'Presets'}
                </span>
            </button>

            {isOpen && (
                <div className={`
                    absolute top-full mt-1 z-50
                    ${alignRight ? 'right-0' : 'left-0'}
                    min-w-64 w-max max-w-80
                    bg-(--background-secondary)/95 backdrop-blur-2xl border-2 border-form-element
                    rounded-xl shadow-xl
                `}>
                    {/* Defaults */}
                    {defaultPresets.length > 0 && (
                        <section className="px-3 pt-3 pb-2">
                            <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-1">Defaults</p>
                            <ul className="flex flex-col gap-1">
                                {defaultPresets.map(preset => (
                                    <li key={preset.id}>
                                        <button
                                            onClick={() => handleApply(preset.filters, preset.id)}
                                            className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-(--background-quaternary) text-sm font-medium transition-colors cursor-pointer flex items-center justify-between gap-2"
                                        >
                                            <span>{preset.name}</span>
                                            {selectedPresetId === preset.id && selectedPresetFiltersMatch && <FaCheck className="text-(--success) text-xs shrink-0" />}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}

                    <div className="border-t border-form-element" />

                    {/* My Filters */}
                    <section className="px-3 pt-2 pb-3">
                        <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-1">My Filters</p>

                        {!isLoggedIn ? (
                            <button
                                onClick={() => { setIsOpen(false); setShowLoginModal(true); }}
                                className="flex items-center gap-2 text-sm text-secondary hover:text-primary transition-colors py-1 cursor-pointer"
                            >
                                <FaLock className="text-xs" />
                                <span>Sign in to save filters</span>
                            </button>
                        ) : isLoadingFilters ? (
                            <p className="text-xs text-secondary py-1">Loading...</p>
                        ) : userFilters.length === 0 ? (
                            <p className="text-xs text-secondary py-1">No saved filters yet.</p>
                        ) : (
                            <ul className="flex flex-col gap-1 mb-2">
                                {userFilters.map(f => (
                                    <li key={f.id} className="flex items-center gap-1">
                                        {renamingId === f.id ? (
                                            <>
                                                <input
                                                    ref={renameInputRef}
                                                    type="text"
                                                    value={renameValue}
                                                    onChange={e => setRenameValue(e.target.value)}
                                                    onKeyDown={e => {
                                                        if (e.key === 'Enter') handleRenameCommit();
                                                        if (e.key === 'Escape') handleRenameCancel();
                                                    }}
                                                    className="flex-1 text-sm px-2 py-1 rounded-lg border border-form-element bg-(--background-primary) focus:outline-none focus:border-blue-500 min-w-0"
                                                    maxLength={40}
                                                />
                                                <Tip label="Save rename">
                                                    <button
                                                        onClick={handleRenameCommit}
                                                        disabled={!renameValue.trim()}
                                                        className="p-1.5 rounded-lg bg-(--success) text-white disabled:opacity-40 cursor-pointer"
                                                        aria-label="Confirm rename"
                                                    >
                                                        <FaCheck className="text-xs" />
                                                    </button>
                                                </Tip>
                                                <Tip label="Cancel">
                                                    <button
                                                        onClick={handleRenameCancel}
                                                        className="p-1.5 rounded-lg hover:bg-(--background-secondary-hover) text-secondary cursor-pointer"
                                                        aria-label="Cancel rename"
                                                    >
                                                        <FaTimes className="text-xs" />
                                                    </button>
                                                </Tip>
                                            </>
                                        ) : (
                                            <>
                                                <button
                                                    onClick={() => handleApply(f.filters, f.id)}
                                                    className="flex-1 text-left px-2 py-1.5 rounded-lg hover:bg-(--background-quaternary) text-sm font-medium transition-colors cursor-pointer flex items-center justify-between gap-2 min-w-0"
                                                >
                                                    <span className="truncate">{f.name}</span>
                                                    {selectedPresetId === f.id && selectedPresetFiltersMatch && <FaCheck className="text-(--success) text-xs shrink-0" />}
                                                </button>
                                                {selectedPresetId === f.id && !selectedPresetFiltersMatch && (
                                                    <Tip label="Update with current filters">
                                                        <button
                                                            onClick={() => handleUpdateFilters(f.id)}
                                                            className="p-1.5 rounded-lg hover:bg-(--background-secondary-hover) text-secondary hover:text-primary transition-colors cursor-pointer"
                                                            aria-label={`Update ${f.name} with current filters`}
                                                        >
                                                            <FaFloppyDisk className="text-xs" />
                                                        </button>
                                                    </Tip>
                                                )}
                                                <Tip label="Rename">
                                                    <button
                                                        onClick={() => { setRenamingId(f.id); setRenameValue(f.name); }}
                                                        className="p-1.5 rounded-lg hover:bg-(--background-secondary-hover) text-secondary hover:text-primary transition-colors cursor-pointer"
                                                        aria-label={`Rename ${f.name}`}
                                                    >
                                                        <FaPencilAlt className="text-xs" />
                                                    </button>
                                                </Tip>
                                                <Tip label="Delete">
                                                    <button
                                                        onClick={() => handleDelete(f.id)}
                                                        className="p-1.5 rounded-lg hover:bg-(--background-secondary-hover) text-secondary hover:text-red-500 transition-colors cursor-pointer"
                                                        aria-label={`Delete ${f.name}`}
                                                    >
                                                        <FaTrash className="text-xs" />
                                                    </button>
                                                </Tip>
                                            </>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        )}

                        {/* Save current filters */}
                        {isLoggedIn && !saveMode && (
                            <button
                                onClick={() => setSaveMode(true)}
                                className="flex items-center gap-1.5 text-sm text-secondary hover:text-primary transition-colors mt-1 cursor-pointer"
                            >
                                <FaPlus className="text-xs" />
                                <span>Save current filters</span>
                            </button>
                        )}

                        {isLoggedIn && saveMode && (
                            <div className="flex items-center gap-1 mt-1">
                                <input
                                    ref={saveInputRef}
                                    type="text"
                                    placeholder="Filter name…"
                                    value={saveName}
                                    onChange={e => setSaveName(e.target.value)}
                                    onKeyDown={e => {
                                        if (e.key === 'Enter') handleSave();
                                        if (e.key === 'Escape') { setSaveMode(false); setSaveName(''); }
                                    }}
                                    className="flex-1 text-sm px-2 py-1 rounded-lg border border-form-element bg-(--background-primary) focus:outline-none focus:border-blue-500 min-w-0"
                                    maxLength={40}
                                />
                                <Tip label="Save">
                                    <button
                                        onClick={handleSave}
                                        disabled={!saveName.trim() || isSaving}
                                        className="p-1.5 rounded-lg bg-(--success) text-white disabled:opacity-40 transition-opacity cursor-pointer"
                                        aria-label="Save"
                                    >
                                        <FaCheck className="text-xs" />
                                    </button>
                                </Tip>
                                <Tip label="Cancel">
                                    <button
                                        onClick={() => { setSaveMode(false); setSaveName(''); }}
                                        className="p-1.5 rounded-lg hover:bg-(--background-secondary-hover) text-secondary cursor-pointer"
                                        aria-label="Cancel"
                                    >
                                        <FaTimes className="text-xs" />
                                    </button>
                                </Tip>
                            </div>
                        )}
                    </section>
                </div>
            )}

            {showLoginModal && <LoginModal onClose={() => setShowLoginModal(false)} />}

            {createPortal(
                <LoadingStatusToast
                    loadingStatus={toast ? { message: toast.message, backgroundColor: toast.color } : null}
                    isExiting={toastExiting}
                />,
                document.body
            )}
        </div>
    );
}
