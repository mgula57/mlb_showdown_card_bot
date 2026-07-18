import type { ShowdownBotCard, ShowdownBotCardCompact } from "../../api/showdownBotCard";
import type { CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import CardCommand from "./card_elements/CardCommand";
import { getContrastColor } from "../shared/Color";
import { useTheme } from "../shared/SiteSettingsContext";
import { formatYear } from "../../functions/formatters";
import { FaHatWizard } from "react-icons/fa6";
import { imageForSet } from '../shared/SiteSettingsContext';
import { defenseAtPosition } from "../shared/DefenseUtils";
import CardIcon from "./card_elements/CardIcon";
import { getFirstName, getLastName, getFirstInitial } from "../../functions/names"

// =============================================================================
// TYPES
// =============================================================================

export type CardItemActionButton = {
    icon: React.ReactNode;
    onClick: () => void;
    /** aria-label for the action button */
    label?: string;
    bgColorClass?: string; // Optional additional background color class for the action button (e.g. "bg-red-500")
};

type CardItemCompactProps = {
    card?: ShowdownBotCardCompact | null;
    className?: string;
    isSelected?: boolean;
    isLoading?: boolean;
    onClick?: () => void;
    /** Optional action button shown in the top-right corner */
    actionButton?: CardItemActionButton;
    /** Show defense only for this position (e.g. 'SS', 'CF'). Falls back to full string. */
    fieldPosition?: string;
    /** Optional override for the player's defensive rating at the specified field position */
    detailStat1Category?: 'defense' | 'hr' | 'outs';
    /** Always hide the set icon and defense/handedness row, regardless of container width */
    hideDetails?: boolean;
};

// =============================================================================
// COMPONENT
// =============================================================================

function getDefenseDisplay(card: ShowdownBotCardCompact | null | undefined, fieldPosition?: string): string | number {
    if (!card) return 'N/A';
    if (card.is_pitcher) return `IP ${card.ip ?? 0}`;
    if (fieldPosition === 'DH') return 'DH';

    const defAtPos = defenseAtPosition(card.positions_and_defense, fieldPosition || '');
    if (defAtPos !== null) return `${fieldPosition}${defAtPos >= 0 ? '+' : ''}${defAtPos}`;
    return defenseAtPosition(card.positions_and_defense, fieldPosition || '') || card.positions_and_defense_string || 'N/A';
}

export const CardItemCompact = ({
    card,
    className,
    isSelected,
    isLoading,
    onClick,
    actionButton,
    fieldPosition,
    detailStat1Category,
    hideDetails,
}: CardItemCompactProps) => {

    const { isDark } = useTheme();

    const primaryColor = (['NYM', 'SDP', 'JPN'].includes(card?.team || 'N/A')
        ? card?.color_secondary
        : card?.color_primary) || 'rgb(0, 0, 0)';

    const secondaryColor = (['NYM', 'SDP', 'JPN'].includes(card?.team || 'N/A')
        ? card?.color_primary
        : card?.color_secondary) || 'rgb(0, 0, 0)';

    const pointsBadgeStyle = {
        backgroundColor: secondaryColor,
        color: getContrastColor(secondaryColor),
    };

    const teamStyle = {
        backgroundColor: primaryColor,
        color: getContrastColor(primaryColor),
    };

    const isClickable = onClick !== undefined;

    const borderSettings = isSelected
        ? `border-3 shadow-xl${isClickable ? ' hover:shadow-2xl' : ''}`
        : (isDark
            ? `border-3 border-white/10 shadow-xl${isClickable ? ' hover:border-white/50 hover:shadow-2xl' : ''}`
            : `border-3 border-gray-200 shadow-xl${isClickable ? ' hover:shadow-2xl hover:border-black/40' : ''}`);

    const isRedacted = card?.isEmpty || false;

    return (
        <div
            role={onClick ? 'button' : undefined}
            tabIndex={onClick ? 0 : undefined}
            onClick={onClick}
            onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); } : undefined}
            className={`
                ${className || ''}
                relative @container
                w-full min-w-0
                flex items-top gap-2
                rounded-lg px-1.5 py-1
                bg-secondary
                ${borderSettings}
                ${onClick ? 'cursor-pointer' : 'cursor-default'}
            `}
        >
            <CardCommand
                isPitcher={card?.is_pitcher || false}
                primaryColor={primaryColor}
                secondaryColor={secondaryColor}
                command={card?.command}
                team={card?.team || 'N/A'}
                className={`w-6.5 h-6.5 shrink-0 mt-1 ${hideDetails ? '' : '@[70px]:mt-1.5'}`}
            />

            <div className="min-w-0 flex-1 space-y-0.5 text-left">
                <div className={`flex gap-x-0.5 text-[12px] font-black text-(--text-primary) overflow-x-scroll scrollbar-hide truncate ${isRedacted ? 'redacted' : ''}`}>
                    {isRedacted 
                        ? 'REDACTED NAME' 
                        : 
                            <>
                                {/* First Initial */}
                                <span className="hidden @[70px]:flex @[150px]:hidden">{getFirstInitial(card?.name)}. </span>

                                {/* Full First Name */}
                                <span className="hidden @[150px]:flex">{getFirstName(card?.name)} </span>
                            
                                {/* Last Name */}
                                {getLastName(card?.name)}

                            </>
                    }
                    
                </div>
                <div className="flex items-center gap-1 min-w-0">
                    <div
                        className={`text-[9px] flex leading-none shrink-0 font-semibold tracking-tight rounded px-0.5 py-0.5 ${isRedacted ? 'redacted' : ''}`}
                        style={isRedacted ? undefined : teamStyle}
                    >
                        {card?.team || 'N/A'}
                        <span className="hidden @[150px]:block ml-0.5"> {formatYear(card?.year || '-')}</span>
                    </div>
                    <div
                        className={`hidden @[80px]:flex shrink-0 text-[9px] leading-none font-semibold tracking-tight rounded px-0.5 py-0.5 ${isRedacted ? 'redacted' : ''}`}
                        style={isRedacted ? undefined : pointsBadgeStyle}
                    >
                        {card?.points != null ? `${card.points} PT` : '-- PT'}
                        <span className="hidden @[90px]:block">S</span>
                    </div>
                </div>
                {!hideDetails && (
                    <div className={`hidden @[70px]:flex py-0.5 text-[9px] tracking-tight w-full font-bold text-(--text-tertiary) truncate text-nowrap overflow-x-scroll scrollbar-hide ${isRedacted ? 'redacted' : ''}`}>
                        {isRedacted ? '--- • ---' : (
                            <>
                                {/* STAT 1 */}
                                {(detailStat1Category === undefined || detailStat1Category === 'defense') && getDefenseDisplay(card, fieldPosition)}
                                {detailStat1Category === 'hr' && (`${card?.hr_range?.split('-')[0].split('+')[0]}+ HR`)}
                                {detailStat1Category === 'outs' && (`${card?.outs} OUT`)}

                                {/* OUTS/SPEED */}
                                <span className="hidden @[90px]:flex">
                                    <span className="px-0.5 opacity-50">•</span>
                                    {card?.is_pitcher ? `${card.outs} OUT` : `SPD ${card?.speed || '-'}`}
                                </span>

                                {/* HANDEDNESS */}
                                <span className="hidden @[110px]:flex">
                                    <span className="px-0.5 opacity-50">•</span>
                                    {card?.is_pitcher ? `${card?.hand}HP` : `${card?.hand}H`}
                                </span>
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Absolute positioned elements */}
            {!hideDetails && !isRedacted && (
                <div className="hidden @[70px]:block absolute bottom-1.5 left-1 bg-(--background-secondary)/70 backdrop-blur-[1px] rounded">
                    <img src={imageForSet(card?.set || '', true)} alt={card?.set ?? 'N/A'} className="h-3.5 object-contain object-center" />
                </div>
            )}

            {card?.source === 'WOTC' && (
                <FaHatWizard className="absolute bottom-0.5 right-0.5 w-3 h-3 text-(--secondary)" title="WOTC Card" />
            )}

            {/* Icons - top-right corner */}
            <div className="absolute -top-2 -right-0.5 flex gap-0.5">
                {card?.icons_list?.map((icon, index) => (
                    <CardIcon 
                        key={`${card?.id}-icon-${index}`} 
                        color={secondaryColor} 
                        value={icon} 
                        circleSize={((card?.icons_list?.length ?? 0) > 2 ? "3" : "4")}
                        textSize={(card?.icons_list?.length ?? 0) > 2 ? 8 : 9} 
                    />
                ))}
            </div>

            {/* Optional action button — top-right corner */}
            {actionButton && (
                <button
                    type="button"
                    aria-label={actionButton.label}
                    onClick={(e) => { e.stopPropagation(); actionButton.onClick(); }}
                    className="
                        absolute top-0.5 right-0.5
                        flex items-center justify-center
                        w-5 h-5 rounded
                        text-(--text-tertiary)
                        hover:bg-(--background-quaternary) hover:text-(--text-primary)
                        transition-colors
                    "
                >
                    {actionButton.icon}
                </button>
            )}

            {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center gap-1 rounded-lg bg-(--background-secondary)/70 backdrop-blur-[1px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-(--secondary) animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-(--secondary) animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-(--secondary) animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
            )}
        </div>
    );
};

// =============================================================================
// WRAPPER VARIANTS
// =============================================================================

type CardItemCompactFromCardProps = {
    card?: ShowdownBotCard | null;
    className?: string;
    fieldPosition?: string;
    hideDetails?: boolean;
    detailStat1Category?: 'defense' | 'hr' | 'outs';
    isSelected?: boolean;
    onClick?: () => void;
    actionButton?: CardItemActionButton;
};

export const CardItemCompactFromCard = ({ card, className, fieldPosition,  hideDetails, detailStat1Category, isSelected, onClick, actionButton }: CardItemCompactFromCardProps) => {
    const primaryColor = (['NYM', 'SDP', 'JPN'].includes(card?.wbc_team || card?.team || 'N/A')
        ? card?.image.color_secondary
        : card?.image.color_primary) || 'rgb(0, 0, 0)';

    const secondaryColor = (['NYM', 'SDP', 'JPN'].includes(card?.wbc_team || card?.team || 'N/A')
        ? card?.image.color_primary
        : card?.image.color_secondary) || 'rgb(0, 0, 0)';

    return (
        <CardItemCompact
            card={{
                id: `${card?.wbc_year || card?.year || '----'}-${card?.bref_id || card?.mlb_id || '---'}`,
                name: card?.name || 'Unknown Player',
                year: card?.wbc_year || card?.year || '----',
                team: card?.wbc_team || card?.team || 'N/A',
                set: card?.set || '---',
                points: card?.points ?? 0,
                command: card?.chart.command || 0,
                outs: card?.chart.outs_full || 0,
                is_pitcher: card?.chart.is_pitcher || false,
                color_primary: primaryColor,
                color_secondary: secondaryColor,
                positions_and_defense_string: card?.positions_and_defense_string || '',
                positions_and_defense: card?.positions_and_defense || {},
                ip: card?.ip || 0,
                speed: card?.speed.speed || null,
                icons_list: card?.icons || [],
                hand: card?.hand || null,
                hr_range: card?.chart.ranges.HR || null,
                source: card?.is_wotc ? 'WOTC' : 'BOT',
                isEmpty: card == null || card === undefined,
            }}
            className={className}
            isSelected={isSelected}
            fieldPosition={fieldPosition}
            hideDetails={hideDetails}
            detailStat1Category={detailStat1Category}
            onClick={onClick}
            actionButton={actionButton}
        />
    );
};

type CardItemCompactFromCardDatabaseRecordProps = {
    card?: CardDatabaseRecord;
    className?: string;
    isSelected?: boolean;
    isLoading?: boolean;
    onClick?: () => void;
    actionButton?: CardItemActionButton;
    fieldPosition?: string;
    detailStat1Category?: 'defense' | 'hr' | 'outs';
    hideDetails?: boolean;
};

export const CardItemCompactFromCardDatabaseRecord = ({ card, className, isSelected, isLoading, onClick, actionButton, fieldPosition, hideDetails, detailStat1Category, }: CardItemCompactFromCardDatabaseRecordProps) => {
    const primaryColor = (['NYM', 'SDP', 'JPN'].includes(card?.wbc_team || card?.team || 'N/A')
        ? card?.color_secondary
        : card?.color_primary) || 'rgb(0, 0, 0)';

    const secondaryColor = (['NYM', 'SDP', 'JPN'].includes(card?.wbc_team || card?.team || 'N/A')
        ? card?.color_primary
        : card?.color_secondary) || 'rgb(0, 0, 0)';

    return (
        <CardItemCompact
            card={{
                id: card?.id || '',
                name: card?.name || 'Unknown Player',
                year: card?.year || '----',
                set: card?.showdown_set || '---',
                team: card?.wbc_team || card?.team || 'N/A',
                points: card?.points ?? 0,
                command: card?.command || 0,
                outs: Math.round(card?.outs || 0),
                is_pitcher: card?.is_pitcher || false,
                color_primary: primaryColor,
                color_secondary: secondaryColor,
                positions_and_defense_string: card?.positions_and_defense_string || '',
                positions_and_defense: card?.positions_and_defense || {},
                ip: card?.ip || 0,
                speed: card?.speed || null,
                hand: card?.hand || null,
                hr_range: card?.chart_ranges?.HR || null,
                icons_list: card?.icons_list || [],
                source: card?.source || 'BOT',
                isEmpty: card == null || card === undefined,
            }}
            className={className}
            isSelected={isSelected}
            isLoading={isLoading}
            onClick={onClick}
            actionButton={actionButton}
            fieldPosition={fieldPosition}
            hideDetails={hideDetails}
            detailStat1Category={detailStat1Category}
        />
    );
};
