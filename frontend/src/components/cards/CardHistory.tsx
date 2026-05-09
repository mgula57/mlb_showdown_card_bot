import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { type CustomCardLogRecord } from "../../api/card_db/cardDatabase";
import { FaCircleCheck, FaCircleXmark, FaShuffle, FaImage, FaXmark, FaExpand } from "react-icons/fa6";
import { imageForSet } from "../shared/SiteSettingsContext";
import type { CustomCardFormState } from "../customs/CustomCardBuilder";
import { titleCase } from "../../functions/text";
import { useAuth } from "../auth/AuthContext";

type CardHistoryProps = {
    history?: CustomCardLogRecord[];
    onSelectCard?: (userInputs: CustomCardFormState) => void;
};

export const CardHistory = ({ history, onSelectCard }: CardHistoryProps) => {
    const { user } = useAuth();
    const [modalImageUrl, setModalImageUrl] = useState<string | null>(null);

    useEffect(() => {
        if (!modalImageUrl) return;
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setModalImageUrl(null); };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [modalImageUrl]);

    // Group only consecutive records with the same card (name + year + set)
    const groupConsecutiveRecords = () => {
        if (!history || history.length === 0) return [];
        
        const groups: Array<{ record: CustomCardLogRecord; timestamps: Array<{ created_on: string; error_for_user?: string | null, user_inputs?: CustomCardFormState | null }> }> = [];
        let currentGroup: { record: CustomCardLogRecord; timestamps: Array<{ created_on: string; error_for_user?: string | null, user_inputs?: CustomCardFormState | null }> } | null = null;
        
        history.forEach((record) => {
            const expansion = record.user_inputs?.expansion !== undefined ? record.user_inputs.expansion : 'BS';
            const set_number = record.user_inputs?.set_number !== undefined ? record.user_inputs.set_number : '0';
            const edition = record.user_inputs?.edition && record.user_inputs.edition !== 'NONE' ? record.user_inputs.edition : 'NONE';
            const key = `${record.name}-${record.year}-${record.set}-${expansion}-${set_number}-${edition}`;
            
            const currentExpansion = currentGroup?.record.user_inputs?.expansion !== undefined ? currentGroup.record.user_inputs.expansion : 'BS';
            const currentSetNumber = currentGroup?.record.user_inputs?.set_number !== undefined ? currentGroup.record.user_inputs.set_number : '0';
            const currentEdition = currentGroup?.record.user_inputs?.edition && currentGroup.record.user_inputs.edition !== 'NONE' ? currentGroup.record.user_inputs.edition : 'NONE';
            const currentKey = currentGroup ? `${currentGroup.record.name}-${currentGroup.record.year}-${currentGroup.record.set}-${currentExpansion}-${currentSetNumber}-${currentEdition}` : null;
            
            if (key === currentKey) {
                // Same card, add to current group
                currentGroup!.timestamps.push({
                    created_on: record.created_on,
                    error_for_user: record.error_for_user,
                    user_inputs: record.user_inputs
                });
            } else {
                // Different card, start new group
                currentGroup = {
                    record,
                    timestamps: [{
                        created_on: record.created_on,
                        error_for_user: record.error_for_user,
                        user_inputs: record.user_inputs
                    }]
                };
                groups.push(currentGroup);
            }
        });
        
        return groups;
    };

    const groupedArray = groupConsecutiveRecords();

    // Or create a helper function:
    const formatTimeUTC = (utcTimestamp: string | number) => {
        return new Date(utcTimestamp.toString().endsWith('Z') ? utcTimestamp : utcTimestamp + 'Z').toLocaleString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const getImageUrl = (record: CustomCardLogRecord): string | null => {
        const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
        if (record.thumbnail_storage_path) return `${supabaseUrl}/storage/v1/object/public/card_images/${record.thumbnail_storage_path}`;
        if (record.storage_path) return `${supabaseUrl}/storage/v1/object/public/card_images/${record.storage_path}`;
        if (record.img_url) return record.img_url;
        if (record.img_name) return `static/output/${record.img_name}`;
        return null;
    };

    const getFullImageUrl = (record: CustomCardLogRecord): string | null => {
        const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
        if (record.storage_path) return `${supabaseUrl}/storage/v1/object/public/card_images/${record.storage_path}`;
        if (record.thumbnail_storage_path) return `${supabaseUrl}/storage/v1/object/public/card_images/${record.thumbnail_storage_path}`;
        if (record.img_url) return record.img_url;
        if (record.img_name) return `static/output/${record.img_name}`;
        return null;
    };

    const editionLabel: Record<string, string> = {
        CC: 'Cooperstown',
        SS: 'Super Season',
        RS: 'Rookie Season',
        WBC: 'WBC',
        POST: 'Postseason',
        ASG: 'All-Star',
    };

    return (
        <div className="h-full pb-20">
            <ul className="list-inside space-y-4  px-4">
                {!history || history.length === 0 ? (
                    <li className="py-4">
                        {user ? "No history available." : "No history available. Login to start tracking your cards."}
                    </li>
                ) : (
                    <>
                        {groupedArray.map((group, index) => {
                            const inputs = group.record.user_inputs;
                            const edition = inputs?.edition && inputs.edition !== 'NONE' ? (editionLabel[inputs.edition] ?? inputs.edition) : null;
                            const split = inputs?.split ?? null;
                            const league = inputs?.league && inputs.league !== 'MLB' ? inputs.league : null;
                            const expansion = inputs?.expansion !== undefined ? inputs.expansion : 'BS';
                            const set_number = inputs?.set_number !== undefined ? inputs.set_number : null;

                            return (
                                <li key={index}>
                                    <div className="flex items-start gap-2 py-2 rounded-lg bg-(--background-primary) px-3">

                                        {/* Thumbnail */}
                                        {(() => {
                                            const thumbUrl = getImageUrl(group.record);
                                            const fullUrl = getFullImageUrl(group.record);
                                            return (
                                                <div
                                                    className={`relative z-0 shrink-0 w-20 rounded-lg overflow-hidden bg-(--background-secondary) group/thumb ${fullUrl ? 'cursor-zoom-in' : ''}`}
                                                    style={{ aspectRatio: '3.5 / 4.5' }}
                                                    onClick={() => fullUrl && setModalImageUrl(fullUrl)}
                                                >
                                                    {thumbUrl ? (
                                                        <>
                                                            <img
                                                                src={thumbUrl}
                                                                alt={`${group.record.name} card`}
                                                                loading="lazy"
                                                                className="w-full h-full object-contain transition-transform duration-200 group-hover/thumb:scale-105"
                                                                onError={(e) => { e.currentTarget.style.display = 'none'; }}
                                                            />
                                                            {fullUrl && (
                                                                <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover/thumb:bg-black/30 transition-colors duration-200">
                                                                    <FaExpand className="text-white opacity-0 group-hover/thumb:opacity-100 transition-opacity duration-200 text-sm drop-shadow" />
                                                                </div>
                                                            )}
                                                        </>
                                                    ) : (
                                                        <div className="w-full h-full flex items-center justify-center text-xs text-tertiary">
                                                            <FaImage />
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })()}

                                        {/* Text content */}
                                        <div className="flex-1 min-w-0 flex flex-col justify-between">

                                            {/* Top section */}
                                            <div className="flex flex-col gap-1">
                                                {/* Name + year */}
                                                <div className="flex items-baseline gap-1.5 overflow-hidden">
                                                    <span className="text-sm font-semibold truncate leading-tight">
                                                        {inputs?.name_original ? titleCase(inputs.name_original) : group.record.name}
                                                    </span>
                                                    <span className="text-xs text-secondary shrink-0">{group.record.year}</span>
                                                </div>

                                                {/* Set image + set number + expansion + league */}
                                                <div className="text-xs text-secondary flex items-center gap-1.5">
                                                    <img src={imageForSet(group.record.set)} alt={group.record.set} className="h-4 object-contain" />
                                                    {inputs?.set_number && (
                                                        <span className="text-[11px]">#{set_number}</span>
                                                    )}
                                                    {expansion && expansion !== 'BS' && (
                                                        <>
                                                            <img
                                                                src={`/images/card/expansion-${expansion.toLowerCase()}.png`}
                                                                alt={expansion}
                                                                className="h-4 object-contain"
                                                            />
                                                        </>
                                                    )}
                                                    {league && (
                                                        <>
                                                            <span>{league}</span>
                                                        </>
                                                    )}
                                                </div>

                                                {/* Edition + split (conditional) */}
                                                {(edition || split) && (
                                                    <div className="text-[11px] text-secondary flex items-center gap-1.5">
                                                        {edition && <span>{edition}</span>}
                                                        {edition && split && <span>•</span>}
                                                        {split && <span>{split}</span>}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Timestamps */}
                                            <div className="flex flex-col gap-0.5 mt-1.5">
                                                {group.timestamps.slice(0, 3).map((timestamp, idx) => (
                                                    <button
                                                        key={idx}
                                                        onClick={() => timestamp.user_inputs && onSelectCard?.(timestamp.user_inputs)}
                                                        disabled={!timestamp.user_inputs}
                                                        className={`text-[10px] flex justify-between items-center gap-1.5 overflow-hidden w-full text-left rounded px-1.5 py-1 transition-colors ${
                                                            timestamp.user_inputs ? 'hover:bg-(--background-tertiary) cursor-pointer' : 'cursor-default'
                                                        } ${timestamp.error_for_user ? 'text-(--red)' : 'text-(--green)'}`}
                                                    >
                                                        <span className="text-nowrap flex items-center gap-1" title={timestamp.error_for_user ?? ''}>
                                                            {timestamp.error_for_user ? <FaCircleXmark className="shrink-0 text-xs" /> : <FaCircleCheck className="shrink-0 text-xs" />}
                                                            <span className="truncate">{formatTimeUTC(timestamp.created_on)}</span>
                                                        </span>

                                                        <div className="flex items-center gap-1 shrink-0">
                                                            {timestamp.user_inputs && timestamp.user_inputs?.chart_version !== '1' && (
                                                                <span className="text-[10px] text-secondary font-medium">
                                                                    v{timestamp.user_inputs?.chart_version}
                                                                </span>
                                                            )}
                                                            {timestamp.user_inputs && timestamp.user_inputs.randomize && (
                                                                <FaShuffle className="text-[10px] text-secondary" />
                                                            )}
                                                        </div>
                                                    </button>
                                                ))}
                                                {group.timestamps.length > 3 && (
                                                    <span className="text-[10px] text-tertiary px-1.5">
                                                        +{group.timestamps.length - 3} more
                                                    </span>
                                                )}
                                            </div>

                                        </div>
                                    </div>
                                </li>
                            );
                        })}
                    </>
                )}
            </ul>

            {/* Lightbox */}
            {modalImageUrl && createPortal(
                <div
                    className="fixed inset-0 z-9999 flex items-center justify-center bg-black/80 backdrop-blur-sm"
                    onClick={() => setModalImageUrl(null)}
                >
                    <button
                        className="absolute top-4 right-4 text-white/70 hover:text-white transition-colors text-xl"
                        onClick={() => setModalImageUrl(null)}
                    >
                        <FaXmark />
                    </button>
                    <img
                        src={modalImageUrl}
                        alt="Card full view"
                        className="max-h-[90vh] max-w-[90vw] object-contain rounded-lg shadow-2xl"
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>,
                document.body
            )}
        </div>
    );
};