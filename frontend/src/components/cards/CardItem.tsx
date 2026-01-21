import type { ShowdownBotCard } from "../../api/showdownBotCard";
import type { CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import CardChart from "./card_elements/CardChart";
import CardCommand from "./card_elements/CardCommand";
import { getContrastColor } from "../shared/Color";
import { useTheme } from "../shared/SiteSettingsContext";
import { FaStar, FaBook, FaScrewdriverWrench } from 'react-icons/fa6';

/**
 * Props for the CardItem component
 */
type CardItemProps = {
    /** Card Id */
    cardId?: string;

    // Name and Year
    cardName?: string;
    cardYear?: string;
    cardTeam?: string;

    // Set
    cardSet?: string;
    cardExpansion?: string;
    cardSetNumber?: number;

    // Points
    cardPoints?: number;
    cardPointsEstimated?: number;
    cardPointsDiffEstimatedVsActual?: number;

    // Command and Outs
    cardCommand?: number;
    cardOuts?: number;

    // Card Metadata
    cardIsPitcher?: boolean;
    cardSpeed?: number;
    cardHand?: string;
    cardIp?: number;
    cardPositionsAndDefenseString?: string;

    // Awards and Stats
    cardIcons?: string[];
    cardAwardList?: string[];
    cardStatHighlightsList?: string[];

    // Image
    cardEdition?: string;
    cardPrimaryColor?: string;
    cardSecondaryColor?: string;

    // Chart
    cardChartRanges?: Record<string, string>;

    // Misc
    cardIsErrata?: boolean;
    cardNotes?: string;

    /** Click handler for card selection */
    onClick?: () => void | undefined;
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
export const CardItem = ({ 
    cardId, cardTeam, cardName, cardYear, 
    cardCommand, cardIsPitcher,
    cardPoints, cardPointsEstimated, cardPointsDiffEstimatedVsActual,
    cardSpeed, cardHand, cardIp, cardPositionsAndDefenseString,
    cardIsErrata, cardNotes,
    cardPrimaryColor, cardSecondaryColor, cardEdition,
    cardSet, cardExpansion, cardSetNumber,
    cardIcons, cardAwardList, cardStatHighlightsList,
    cardChartRanges,
    onClick, className, isSelected 
}: CardItemProps) => {

    const { isDark } = useTheme();
    const isRedacted = cardId === null || cardId === undefined;
    
    // Team-specific color handling for better contrast (NYM, SDP use secondary first)
    const primaryColor = (['NYM', 'SDP'].includes(cardTeam || 'N/A') 
        ? cardSecondaryColor
        : cardPrimaryColor) || 'rgb(0, 0, 0)';
    const colorStylingPrimary = { 
        backgroundColor: primaryColor, 
        color: getContrastColor(primaryColor) 
    };
    
    const secondaryColor = (['NYM', 'SDP'].includes(cardTeam || 'N/A') 
        ? cardPrimaryColor
        : cardSecondaryColor) || 'rgb(0, 0, 0)';
    const colorStylingSecondary = { 
        backgroundColor: secondaryColor, 
        color: getContrastColor(secondaryColor) 
    };
    
    // Dynamic border styling based on selection state and theme
    const borderSettings = isSelected 
        ? (isDark ? 'border-3' : 'border-3 shadow-xl hover:shadow-2xl') 
        : (isDark ? 'border-white/10 hover:border-white/50' : 'shadow-xl hover:shadow-2xl border-gray-200 hover:border-black/40');

    /**
     * Player-type specific metadata display
     * 
     * Hitters show: Speed, Batting handedness, Defensive positions
     * Pitchers show: Positions, Pitching handedness, Innings pitched
     */
    const metadataArray: (string | undefined)[] = cardIsPitcher ? [
        cardPositionsAndDefenseString,
        `${cardHand}HP`, // HP = Handed Pitcher
        `IP ${cardIp}`,
    ] : [
        `SPD ${cardSpeed}`,
        `BATS ${cardHand}`,
        cardPositionsAndDefenseString,
    ];

    const renderPointsComparison = (estPoints:number, diffPoints:number) => {
        const absoluteDifference = Math.abs(diffPoints);
        const differenceSign = diffPoints > 0 ? '▲' : '▼';
        return (
            <div className="flex items-center">
                EST: {estPoints}
                {diffPoints !== 0 && (
                    <span className={`ml-0.5 text-[8px] ${diffPoints > 0 ? 'text-[var(--green)]' : 'text-[var(--red)]'}`}>
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
                border-3
                ${onClick ? 'cursor-pointer' : ''}
                ${borderSettings}
            `}
            onClick={onClick}
        >
            {/* Header: Command Rating + Player Info */}
            <div className="flex flex-row gap-2 items-center text-nowrap">
                {/* Command rating with themed background */}
                <CardCommand
                    isPitcher={cardIsPitcher || false}
                    primaryColor={primaryColor}
                    secondaryColor={secondaryColor}
                    command={cardCommand}
                    team={cardTeam}
                    className="w-9 h-9 shrink-0" 
                />

                <div className="flex flex-col gap-0.5 overflow-x-scroll scrollbar-hide">
                    {/* Player name, year/team badge, and special ability icons */}
                    <div className="flex flex-row gap-1 items-center">
                        <div className={`font-black ${isRedacted ? 'redacted text-sm' : ''}`}>{cardName?.toUpperCase() || 'REDACTED NAME'}</div>

                        {cardIsErrata && (
                            <div 
                                className="
                                    text-[9px] flex
                                    items-center font-bold justify-center
                                    rounded-lg tracking-tight shrink-0
                                    border-1 border-white/30 px-1
                                    bg-[var(--red)] text-white
                                    " 
                                title="Errata Card"
                            >
                                <FaScrewdriverWrench className="inline-block w-2 h-2 mr-0.5" />
                                ER
                            </div>
                        )}

                        {cardNotes && (
                            <FaBook className="inline-block w-3 h-3 text-secondary shrink-0" title={cardNotes} />
                        )}
                        
                        {/* Year and team badge with team colors */}
                        <div className="text-[9px] rounded-md px-1" style={colorStylingPrimary}>
                            {cardYear} {cardTeam?.toUpperCase()}
                        </div>

                        {/* Edition */}
                        {(cardEdition && cardEdition !== 'NONE') && (
                            <>
                                {cardEdition === 'ASG' ? (
                                    <FaStar className="inline-block w-4 h-4 text-yellow-400 shrink-0" />
                                ) : (
                                    <img src={`/images/card/edition-${cardEdition.toLowerCase()}.png`} className="w-6 h-6 object-contain object-center" alt="Edition" />
                                )}
                                
                            </>
                        )}
                        
                        {/* Special ability icons (e.g., "R" for Rookie, "S" for Silver Slugger) */}
                        {cardIcons?.map((icon, index) => (
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
                            {isRedacted ? (
                                <span className="text-transparent">REDACTED</span>
                            ) : ( 
                                <>
                                    {`${cardPoints} PTS`}
                                </>
                            )}
                        </div>
                        {cardPointsEstimated && cardPoints && (
                            renderPointsComparison(cardPointsEstimated, cardPointsDiffEstimatedVsActual || 0)
                        )}
                        {metadataArray.map((meta, index) => (
                            <div key={index} className={`${isRedacted ? 'redacted' : ''}`}>{meta}</div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Interactive chart showing dice roll outcomes */}
            <CardChart
                chartRanges={cardChartRanges || {}} 
                showdownSet={cardSet || '2001'}
                primaryColor={colorStylingPrimary.backgroundColor}
                secondaryColor={colorStylingSecondary.backgroundColor}
                team={cardTeam}
                cellClassName="min-w-6 md:min-w-8" 
            />

            {/* Bottom bar */}
            <div className="flex flex-row justify-between items-center gap-x-1">

                {/* Statistical highlights ribbon */}
                <div className="flex flex-row text-[9px] gap-1.5 px-1 text-nowrap overflow-x-scroll scrollbar-hide text-secondary">
                    
                    {/* AWARDS: NEW WAY */}
                    {cardAwardList && cardAwardList.length > 0 && (
                        <div className="font-semibold underline">
                            {cardAwardList.map((stat, index) => (
                                <span key={index} className="font-semibold underline">
                                    {stat}{index < (cardAwardList.length || 0) - 1 ? ',' : ''}
                                </span>
                            ))}
                        </div>
                    )}

                    {isRedacted && (
                        <div className="space-x-2">
                            {['-----', '----', '----------', '-----'].map((stat, index) => (
                                <span key={index} className="font-semibold redacted">
                                    {stat}
                                </span>
                            ))}
                        </div>
                    )}
                    {cardStatHighlightsList?.map((stat, index) => (
                        <div key={index} className="">
                            {stat}
                        </div>
                    ))}
                </div>

                {/* Set and Expansion */}
                <div 
                    className="
                        flex flex-row justify-end items-center gap-x-1
                        text-[9px] text-nowrap tracking-tight text-primary
                        bg-[var(--background-tertiary)]
                        px-1 rounded-md font-bold shadow-md
                    "
                    style={{
                        minWidth: cardExpansion && ['TD', 'PR', 'ASG'].includes(cardExpansion) ? '75px' : undefined
                    }}
                >
                    {cardSetNumber && (
                        <span className="font-medium text-secondary">{String(cardSetNumber).padStart(3, '0')}</span>
                    )}
                    {cardExpansion && ['TD', 'PR'].includes(cardExpansion) && (
                        <img 
                            src={`/images/card/expansion-${cardExpansion.toLowerCase()}.png`} 
                            className="inline-block w-5 h-4 object-contain object-center flex-shrink-0"
                            alt="Expansion"
                        />
                    )}
                    {cardExpansion && cardExpansion === 'ASG' && (
                        <FaStar className="inline-block w-4 h-3 text-yellow-400" />
                    )}
                    {['PM'].includes(cardExpansion || '') && (
                        <span>PROMO</span>
                    )}
                    <span className={`${cardSet ? '' : 'redacted'}`}>{cardSet || '2005'}</span>
                </div>

            </div>
        </div>
    );
}

/**
 * Props for the CardItem component
 */
type CardItemFromCardProps = {
    /** Card **/
    card?: ShowdownBotCard | null;

    /** Click handler for card selection */
    onClick?: () => void | undefined;
    /** Optional CSS classes for styling */
    className?: string;
    /** Whether this card is currently selected */
    isSelected?: boolean;
};

export const CardItemFromCard = ({ card, onClick, className, isSelected }: CardItemFromCardProps) => {

    const primaryColor = (['NYM', 'SDP'].includes(card?.team || '') 
                            ? card?.image.color_secondary 
                            : card?.image.color_primary) || 'rgb(0, 0, 0)';
    const secondaryColor = (['NYM', 'SDP'].includes(card?.team || '') 
                            ? card?.image.color_primary 
                            : card?.image.color_secondary) || 'rgb(0, 0, 0)';
    return (
        <CardItem
            cardId={card === undefined || card === null ? undefined : `${card.bref_id}-${card.stats_period.year}-${card.set}`}
            cardTeam={card?.team}
            cardName={card?.name}
            cardYear={card?.stats_period.year}
            cardCommand={card?.chart.command}
            cardOuts={card?.chart.outs}
            cardIsPitcher={card?.chart.is_pitcher}
            cardPoints={card?.points}
            cardPointsEstimated={card?.points_estimated || undefined}
            cardPointsDiffEstimatedVsActual={card?.points_diff_estimated_vs_actual || undefined}
            cardSpeed={card?.speed.speed || undefined}
            cardHand={card?.hand || undefined}
            cardIp={card?.ip || undefined}
            cardPositionsAndDefenseString={card?.positions_and_defense_string || undefined}
            cardIsErrata={card?.is_errata || false}
            cardNotes={card?.notes || undefined}
            cardPrimaryColor={primaryColor}
            cardSecondaryColor={secondaryColor}
            cardEdition={card?.image.edition || undefined}
            cardSet={card?.set}
            cardExpansion={card?.image.expansion || undefined}
            cardSetNumber={card?.image.set_number || undefined}
            cardIcons={card?.icons || []}
            cardAwardList={card?.image.award_summary_list || []}
            cardStatHighlightsList={card?.image.stat_highlights_list || []}
            cardChartRanges={card?.chart.ranges || {}}
            onClick={onClick}
            className={className}
            isSelected={isSelected}
        />
    );
}

/**
 * Props for the CardItem component
 */
type CardItemFromCardDatabaseRecordProps = {
    /** Card **/
    card?: CardDatabaseRecord;

    /** Click handler for card selection */
    onClick?: () => void | undefined;
    /** Optional CSS classes for styling */
    className?: string;
    /** Whether this card is currently selected */
    isSelected?: boolean;
};

export const CardItemFromCardDatabaseRecord = ({ card, onClick, className, isSelected }: CardItemFromCardDatabaseRecordProps) => {
    const primaryColor = (['NYM', 'SDP'].includes(card?.team || '') 
                            ? card?.color_secondary
                            : card?.color_primary) || 'rgb(0, 0, 0)';
    const secondaryColor = (['NYM', 'SDP'].includes(card?.team || '') 
                            ? card?.color_primary 
                            : card?.color_secondary) || 'rgb(0, 0, 0)';
    
    return (
        <CardItem
            cardId={card?.card_id}
            cardTeam={card?.team}
            cardName={card?.name}
            cardYear={card?.card_year}
            cardCommand={card?.command}
            cardOuts={card?.outs}
            cardIsPitcher={card?.is_pitcher}
            cardPoints={card?.points}
            cardPointsEstimated={card?.points_estimated || undefined}
            cardPointsDiffEstimatedVsActual={card?.points_diff_estimated_vs_actual || undefined}
            cardSpeed={card?.speed || undefined}
            cardHand={card?.hand || undefined}
            cardIp={card?.ip || undefined}
            cardPositionsAndDefenseString={card?.positions_and_defense_string || undefined}
            cardIsErrata={card?.is_errata || false}
            cardNotes={card?.notes || undefined}
            cardPrimaryColor={primaryColor}
            cardSecondaryColor={secondaryColor}
            cardEdition={card?.edition || undefined}
            cardSet={card?.showdown_set}
            cardExpansion={card?.expansion || undefined}
            cardSetNumber={card?.set_number ? parseInt(card?.set_number) : undefined}
            cardIcons={card?.icons_list || []}
            cardAwardList={card?.awards_list || []}
            cardStatHighlightsList={card?.stat_highlights_list || []}
            cardChartRanges={card?.chart_ranges || {}}
            onClick={onClick}
            className={className}
            isSelected={isSelected}
        />
    );
}