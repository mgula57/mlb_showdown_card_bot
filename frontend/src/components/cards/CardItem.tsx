import type { ShowdownBotCard } from "../../api/showdownBotCard";
import CardChart from "./card_elements/CardChart";
import CardCommand from "./card_elements/CardCommand";
import { getContrastColor } from "../shared/Color";
import { useTheme } from "../shared/SiteSettingsContext";


type CardItemProps = {
    card?: ShowdownBotCard | null;
    onClick: () => void;
    className?: string;
    isSelected?: boolean;
};

export const CardItem = ({ card, onClick, className, isSelected }: CardItemProps) => {

    // Color
    const { isDark } = useTheme();
    const primaryColor = (['NYM', 'SDP'].includes(card?.team || 'N/A') ? card?.image.color_secondary : card?.image.color_primary) || 'rgb(0, 0, 0)';
    const colorStylingPrimary = { backgroundColor: primaryColor, color: getContrastColor(primaryColor) }
    const secondaryColor = (['NYM', 'SDP'].includes(card?.team || 'N/A') ? card?.image.color_primary : card?.image.color_secondary) || 'rgb(0, 0, 0)';
    const colorStylingSecondary = { backgroundColor: secondaryColor, color: getContrastColor(secondaryColor) }
    const borderSettings = isSelected 
                              ? (isDark ? 'border-3' : 'border-3 shadow-xl hover:shadow-2xl') 
                              : (isDark ? 'border-white/10 hover:border-white/50' : 'shadow-xl hover:shadow-2xl border-transparent hover:border-black/10');

    // Metadata Array
    const metadataArray: (string | undefined)[] = card?.player_type === 'Hitter' ? [
        `SPD ${card?.speed.speed}`,
        `BATS ${card?.hand}`,
        card?.positions_and_defense_string,
    ] : [
        card?.positions_and_defense_string,
        `${card?.hand}HP`,
        `IP ${card?.ip}`
    ]

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
            {/* Command, Name, and Metadata */}
            <div className="flex flex-row gap-2 items-center text-nowrap">
                {/* Command */}
                <CardCommand card={card} className="w-9 h-9 shrink-0" />

                <div className="flex flex-col overflow-x-scroll scrollbar-hide">
                    {/* Name, Icons, Team */}
                    <div className="flex flex-row gap-1 items-center">
                        <div className="font-black">{card?.name.toUpperCase()}</div>
                        <div className="text-[9px] rounded-md px-1" style={colorStylingPrimary}>
                            {card?.year} {card?.team.toUpperCase()}
                        </div>
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
                    {/* Metadata */}
                    <div className="flex flex-row gap-1.5 text-[11px] text-secondary tracking-tight">
                        <div className="px-1 rounded-md font-semibold" style={colorStylingSecondary}>{`${card?.points} PTS`}</div>
                        {metadataArray.map((meta, index) => (
                            <div key={index}>{meta}</div>
                        ))}
                    </div>
                </div>
                

            </div>

            {/* Chart */}
            {card && <CardChart card={card} cellClassName="min-w-8" />}

            {/* Stat Highlights */}
            <div className="flex flex-row text-[9px] gap-1.5 px-1 text-nowrap overflow-x-scroll scrollbar-hide text-secondary">
                {card?.image.stat_highlights_list.map((stat, index) => (
                    <div key={index} className="">
                        {stat}
                    </div>
                ))}
            </div>

        </div>
    );
}