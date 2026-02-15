import { type CustomCardLogRecord } from "../../api/card_db/cardDatabase";
import { FaCircleCheck, FaCircleXmark } from "react-icons/fa6";
import { imageForSet } from "../shared/SiteSettingsContext";
import type { CustomCardFormState } from "../customs/CustomCardBuilder";

type CardHistoryProps = {
    history?: CustomCardLogRecord[];
};

export const CardHistory = ({ history }: CardHistoryProps) => {
    // Group only consecutive records with the same card (name + year + set)
    const groupConsecutiveRecords = () => {
        if (!history || history.length === 0) return [];
        
        const groups: Array<{ record: CustomCardLogRecord; timestamps: Array<{ created_on: string; error_for_user?: string | null, user_inputs?: CustomCardFormState | null }> }> = [];
        let currentGroup: { record: CustomCardLogRecord; timestamps: Array<{ created_on: string; error_for_user?: string | null, user_inputs?: CustomCardFormState | null }> } | null = null;
        
        history.forEach((record) => {
            const key = `${record.name}-${record.year}-${record.set}-${record.user_inputs?.expansion !== undefined ? record.user_inputs.expansion : 'BS'}-${record.user_inputs?.set_number !== undefined ? record.user_inputs.set_number : '0'}`;
            const currentKey = currentGroup ? `${currentGroup.record.name}-${currentGroup.record.year}-${currentGroup.record.set}-${currentGroup.record.user_inputs?.expansion !== undefined ? currentGroup.record.user_inputs.expansion : 'BS'}-${currentGroup.record.user_inputs?.set_number !== undefined ? currentGroup.record.user_inputs.set_number : '0'}` : null;
            
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
            second: '2-digit',
        });
    };

    return (
        <div className="h-full">
            <ul className="list-inside space-y-4 overflow-y-scroll h-full pb-20 px-4">
                {!history || history.length === 0 ? (
                    <li>No history available.</li>
                ) : (
                    <>
                        {groupedArray.map((group, index) => (
                            <li key={index}>
                                <div className="flex flex-col py-2 rounded-lg bg-(--background-primary) px-3">

                                    {/* Player name and year */}
                                    <div className="flex items-center gap-1.5 text-nowrap overflow-x-clip">
                                        <span className="text-md font-medium">{group.record.name}</span>
                                        <span className="text-xs text-tertiary">{group.record.year}</span>
                                    </div>

                                    {/* Showdown Set */}
                                    <div className="text-xs text-secondary flex items-center gap-1 mt-0.5">
                                        <img src={imageForSet(group.record.set)} alt={group.record.set} className="h-5 object-contain" />
                                        {group.record.user_inputs?.set_number && `${group.record.user_inputs.set_number}`}
                                    </div>

                                    {/* Timestamps and statuses */}
                                    <div className="flex flex-col gap-1 mt-1">
                                        {group.timestamps.map((timestamp, idx) => (
                                            <div
                                                key={idx}
                                                className={`text-[11px] flex justify-between items-center gap-1 overflow-x-clip ${timestamp.error_for_user ? 'text-(--red)' : 'text-(--green)'}`}
                                            >
                                                
                                                <span className="text-nowrap flex items-center gap-1">
                                                    {timestamp.error_for_user ? <FaCircleXmark /> : <FaCircleCheck />}
                                                    {formatTimeUTC(timestamp.created_on)}
                                                </span>

                                                {timestamp.user_inputs && timestamp.user_inputs?.chart_version !== '1' && (
                                                    <span className="text-xs text-secondary">
                                                        v{timestamp.user_inputs?.chart_version}
                                                    </span>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                    
                                </div>
                            </li>
                        ))}
                    </>
                )}
            </ul>
        </div>
    );
};