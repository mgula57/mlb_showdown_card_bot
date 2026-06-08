/**
 * @fileoverview TeamPitchersView - Rotation (SP1-SP5) and Bullpen (RP1-RPn)
 */

import TeamSlot from './TeamSlot';
import FormSection from '../customs/FormSection';
import type { TeamBuilderSlot } from '../../api/teamBuilder';

interface TeamPitchersViewProps {
    slotMap: Record<string, TeamBuilderSlot>;
    bullpenSize: number;
    onSlotClick: (slotKey: string) => void;
    onSlotRemove: (slotKey: string) => void;
}

export default function TeamPitchersView({ slotMap, bullpenSize, onSlotClick, onSlotRemove }: TeamPitchersViewProps) {
    const rotationKeys = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5'];
    const bullpenKeys = Array.from({ length: Math.max(1, bullpenSize) }, (_, i) => `RP${i + 1}`);

    return (
        <div className="space-y-4">
            <FormSection title="Rotation" isOpenByDefault>
                <div className="flex flex-wrap gap-3 py-2">
                    {rotationKeys.map(key => (
                        <TeamSlot
                            key={key}
                            slotKey={key}
                            slot={slotMap[key]}
                            onClick={() => onSlotClick(key)}
                            onRemove={slotMap[key] ? () => onSlotRemove(key) : undefined}
                        />
                    ))}
                </div>
            </FormSection>

            <FormSection title="Bullpen" isOpenByDefault>
                <div className="flex flex-wrap gap-3 py-2">
                    {bullpenKeys.map(key => (
                        <TeamSlot
                            key={key}
                            slotKey={key}
                            slot={slotMap[key]}
                            onClick={() => onSlotClick(key)}
                            onRemove={slotMap[key] ? () => onSlotRemove(key) : undefined}
                        />
                    ))}
                </div>
            </FormSection>
        </div>
    );
}
