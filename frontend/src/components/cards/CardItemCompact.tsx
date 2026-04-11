import type { ShowdownBotCard, ShowdownBotCardCompact } from "../../api/showdownBotCard";
import type { CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { useEffect, useRef, useState } from "react";
import CardCommand from "./card_elements/CardCommand";
import { getContrastColor } from "../shared/Color";
import { useTheme } from "../shared/SiteSettingsContext";

type CardItemCompactProps = {
    card?: ShowdownBotCardCompact | null;
    className?: string;
    isSelected?: boolean;
    onClick?: () => void;
};

export const CardItemCompact = ({
    card,
    className,
    isSelected,
    onClick,
}: CardItemCompactProps) => {

    const { isDark } = useTheme();
    const containerRef = useRef<HTMLButtonElement | null>(null);
    const [hidePoints, setHidePoints] = useState(false);
    const [showExtraDetails, setShowExtraDetails] = useState(false);

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

    const borderSettings = isSelected 
        ? (isDark ? 'border-2' : 'border-2') 
        : (isDark ? 'border-2 border-white/10' : 'border-2 border-gray-200');

    const getLastName = (name?: string): string => {
        if (!name) {
            return 'Unknown Player';
        }

        const trimmed = name.trim();
        if (!trimmed) {
            return 'Unknown Player';
        }

        const parts = trimmed.split(/\s+/);
        if (parts.length === 1) {
            return parts[0];
        }

        const last = parts[parts.length - 1].replace('.', '').toUpperCase();
        if (['JR', 'SR', 'II', 'III', 'IV', 'V'].includes(last) && parts.length > 1) {
            return `${parts[parts.length - 2]} ${parts[parts.length - 1]}`;
        }

        return parts[parts.length - 1];
    };

    const getFirstInitial = (name?: string): string => {
        if (!name) {
            return '';
        }

        const trimmed = name.trim();
        if (!trimmed) {
            return '';
        }

        const parts = trimmed.split(/\s+/);
        if (parts.length === 1) {
            return parts[0][0].toUpperCase();
        }

        return parts[0][0].toUpperCase();
    };

    const displayName = `${getFirstInitial(card?.name)}. ${getLastName(card?.name)}`;

    useEffect(() => {
        const element = containerRef.current;
        if (!element) {
            return;
        }
        const updateHidePoints = () => {
            const width = element.getBoundingClientRect().width || element.clientWidth;
            setHidePoints(width < 100);
            setShowExtraDetails(width >= 180);
        };

        updateHidePoints();

        const observers: ResizeObserver[] = [];

        if (typeof ResizeObserver !== 'undefined') {
            const elementObserver = new ResizeObserver(() => updateHidePoints());
            elementObserver.observe(element);
            observers.push(elementObserver);

            const parentElement = element.parentElement;
            if (parentElement) {
                const parentObserver = new ResizeObserver(() => updateHidePoints());
                parentObserver.observe(parentElement);
                observers.push(parentObserver);
            }
        }

        const rafId = requestAnimationFrame(updateHidePoints);
        window.addEventListener('resize', updateHidePoints);

        return () => {
            cancelAnimationFrame(rafId);
            window.removeEventListener('resize', updateHidePoints);
            observers.forEach((observer) => observer.disconnect());
        };
    }, []);


    return (
        <button
            ref={containerRef}
            type="button"
            onClick={onClick}
            className={`
                ${className || ''}
                w-full min-w-0
                flex items-center gap-2
                rounded-lg px-2 py-1.5 
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
                className="w-6 h-6 shrink-0"
            />

            <div className="min-w-0 flex-1 text-left">
                <div className="text-[12px] font-black text-(--text-primary) truncate">
                    {displayName}
                </div>
                <div className="flex items-center gap-1 min-w-0">
                    <div className="text-[10px] font-semibold text-(--text-secondary) truncate">
                        {card?.team || 'N/A'}
                    </div>
                    {!hidePoints && (
                        <div
                            className="shrink-0 text-[9px] leading-none font-black rounded px-0.5 py-0.5"
                            style={pointsBadgeStyle}
                        >
                            {card?.points != null ? `${card.points} PTS` : '-- PTS'}
                        </div>
                    )}
                </div>
            </div>

            {showExtraDetails && (
                <div className="shrink-0 max-w-30 text-right text-[12px] font-bold text-(--text-tertiary) truncate">
                    {card?.positions_and_defense_string || (card?.is_pitcher ? `IP ${card?.ip ?? 0}` : 'N/A')}
                </div>
            )}
        </button>
    );
};

type CardItemCompactFromCardProps = {
    card?: ShowdownBotCard | null;
    className?: string;
    isSelected?: boolean;
    onClick?: () => void;
};

export const CardItemCompactFromCard = ({ card, className, isSelected, onClick }: CardItemCompactFromCardProps) => {
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
                is_pitcher: card?.chart.is_pitcher || false,
                color_primary: primaryColor,
                color_secondary: secondaryColor,
                positions_and_defense_string: card?.positions_and_defense_string || '',
                ip: card?.ip || 0,
            }}
            className={className}
            isSelected={isSelected}
            onClick={onClick}
        />
    );
};

type CardItemCompactFromCardDatabaseRecordProps = {
    card?: CardDatabaseRecord;
    className?: string;
    isSelected?: boolean;
    onClick?: () => void;
};

export const CardItemCompactFromCardDatabaseRecord = ({ card, className, isSelected, onClick }: CardItemCompactFromCardDatabaseRecordProps) => {
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
                is_pitcher: card?.is_pitcher || false,
                color_primary: primaryColor,
                color_secondary: secondaryColor,
                positions_and_defense_string: card?.positions_and_defense_string || '',
                ip: card?.ip || 0,
            }}
            className={className}
            isSelected={isSelected}
            onClick={onClick}
        />
    );
};
