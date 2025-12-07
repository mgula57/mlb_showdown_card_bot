import type { ShowdownBotCard } from "../../api/showdownBotCard";
import CardChart from "./card_elements/CardChart";
import CardCommand from "./card_elements/CardCommand";
import { getContrastColor } from "../shared/Color";
import { useTheme } from "../shared/SiteSettingsContext";

/**
 * Props for the CardItem component
 */
type CardItemProps = {
    /** Card data to display */
    card?: ShowdownBotCard | null;
    /** Click handler for card selection */
    onClick: () => void;
    /** Optional CSS classes for styling */
    className?: string;
    /** Whether this card is currently selected */
    isSelected?: boolean;
};

/**
 * CardItem - Compact card display component for lists and grids
 * 
 * Displays essential card information in a condensed format including:
 * - Command rating with themed background
 * - Player name, year, team, and special icons
 * - Key metadata (points, speed, positions, etc.)
 * - Interactive chart showing dice roll outcomes
 * - Stat highlights ribbon
 * 
 * The component adapts its styling based on team colors and selection state,
 * providing visual feedback and maintaining design consistency.
 * 
 * @param card - ShowdownBotCard data to display
 * @param onClick - Handler for when the card is clicked
 * @param className - Additional CSS classes
 * @param isSelected - Whether this card is currently selected
 * 
 * @example
 * ```tsx
 * <CardItem 
 *   card={cardData}
 *   onClick={() => setSelectedCard(cardData)}
 *   isSelected={selectedCard?.id === cardData.id}
 *   className="w-full"
 * />
 * ```
 */
export const CardItem = ({ card, onClick, className, isSelected }: CardItemProps) => {
    const { isDark } = useTheme();
    
    // Team-specific color handling for better contrast (NYM, SDP use secondary first)
    const primaryColor = (['NYM', 'SDP'].includes(card?.team || 'N/A') 
        ? card?.image.color_secondary 
        : card?.image.color_primary) || 'rgb(0, 0, 0)';
    const colorStylingPrimary = { 
        backgroundColor: primaryColor, 
        color: getContrastColor(primaryColor) 
    };
    
    const secondaryColor = (['NYM', 'SDP'].includes(card?.team || 'N/A') 
        ? card?.image.color_primary 
        : card?.image.color_secondary) || 'rgb(0, 0, 0)';
    const colorStylingSecondary = { 
        backgroundColor: secondaryColor, 
        color: getContrastColor(secondaryColor) 
    };
    
    // Dynamic border styling based on selection state and theme
    const borderSettings = isSelected 
        ? (isDark ? 'border-3' : 'border-3 shadow-xl hover:shadow-2xl') 
        : (isDark ? 'border-white/10 hover:border-white/50' : 'shadow-xl hover:shadow-2xl border-transparent hover:border-black/10');

    /**
     * Player-type specific metadata display
     * 
     * Hitters show: Speed, Batting handedness, Defensive positions
     * Pitchers show: Positions, Pitching handedness, Innings pitched
     */
    const metadataArray: (string | undefined)[] = card?.player_type === 'Hitter' ? [
        `SPD ${card?.speed.speed}`,
        `BATS ${card?.hand}`,
        card?.positions_and_defense_string,
    ] : [
        card?.positions_and_defense_string,
        `${card?.hand}HP`, // HP = Handed Pitcher
        `IP ${card?.ip}`
    ];

    const renderPointsComparison = (originalPoints: number, newPoints:number) => {
        const difference = newPoints - originalPoints;
        const absoluteDifference = Math.abs(difference);
        const differenceSign = difference > 0 ? '▲' : '▼';
        return (
            <div className="flex items-center">
                EST: {newPoints}
                {difference !== 0 && (
                    <span className={`ml-0.5 text-[8px] ${difference > 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {differenceSign}
                        {absoluteDifference}
                    </span>
                )}
            </div>
        );
    }

    return (
        <div
            className={`
                ${className}
                flex flex-col p-2 gap-1
                bg-secondary
                rounded-xl
                border-3 cursor-pointer
                ${borderSettings}
            `}
            onClick={onClick}
        >
            {/* Header: Command Rating + Player Info */}
            <div className="flex flex-row gap-2 items-center text-nowrap">
                {/* Command rating with themed background */}
                <CardCommand card={card} className="w-9 h-9 shrink-0" />

                <div className="flex flex-col overflow-x-scroll scrollbar-hide">
                    {/* Player name, year/team badge, and special ability icons */}
                    <div className="flex flex-row gap-1 items-center">
                        <div className="font-black">{card?.name.toUpperCase()}</div>
                        
                        {/* Year and team badge with team colors */}
                        <div className="text-[9px] rounded-md px-1" style={colorStylingPrimary}>
                            {card?.year} {card?.team.toUpperCase()}
                        </div>

                        {/* Edition */}
                        {(card?.image.edition && card?.image.edition !== 'NONE') && (
                            <img src={`/images/card/edition-${card?.image.edition?.toLowerCase()}.png`} className="w-6 h-6 object-contain object-center" alt="Edition" />
                        )}
                        
                        {/* Special ability icons (e.g., "R" for Rookie, "S" for Silver Slugger) */}
                        {card?.icons.map((icon, index) => (
                            <div 
                                key={index} 
                                className="
                                    text-[9px] flex w-4 h-4 
                                    items-center font-bold justify-center 
                                    rounded-full tracking-tight shrink-0
                                " 
                                style={colorStylingSecondary} 
                            >
                                {icon}
                            </div>
                        ))}
                    </div>
                    
                    {/* Point value and player-specific metadata */}
                    <div className="flex flex-row gap-1.5 text-[11px] text-secondary tracking-tight items-center">
                        <div className="px-1 rounded-md font-semibold" style={colorStylingSecondary}>
                            {`${card?.points} PTS`}
                        </div>
                        {card?.points_estimated && card?.points && (
                            renderPointsComparison(card.points, card.points_estimated)
                        )}
                        {metadataArray.map((meta, index) => (
                            <div key={index}>{meta}</div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Interactive chart showing dice roll outcomes */}
            {card && <CardChart card={card} cellClassName="min-w-8" />}

            {/* Bottom bar */}
            <div className="flex flex-row justify-between items-center gap-x-1">

                {/* Statistical highlights ribbon */}
                <div className="flex flex-row text-[9px] gap-1.5 px-1 text-nowrap overflow-x-scroll scrollbar-hide text-secondary">
                    {card?.stats.award_summary?.length > 0 && (
                        <div className="font-semibold underline">
                            {card?.stats.award_summary}
                        </div>
                    )}
                    {card?.image.stat_highlights_list?.map((stat, index) => (
                        <div key={index} className="">
                            {stat}
                        </div>
                    ))}
                </div>

                {/* Set and Expansion */}
                <div className="
                    flex flex-row justify-end items-center
                    text-[9px] text-nowrap tracking-tight text-white 
                    bg-[var(--background-tertiary)]
                    px-1 rounded-md font-bold shadow-md
                ">
                    {card?.image.expansion && ['TD', 'PR'].includes(card?.image.expansion) && (
                        <img 
                            src={`/images/card/expansion-${card?.image.expansion.toLowerCase()}.png`} 
                            className="inline-block w-5 h-4 object-contain object-center mr-0.5"
                            alt="Expansion"
                        />
                    )}
                    {['PM'].includes(card?.image.expansion || '') && (
                        <span className="mr-1">PROMO</span>
                    )}
                    {card?.set}
                </div>

            </div>
        </div>
    );
}