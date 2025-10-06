import { type ShowdownBotCard } from "../../../api/showdownBotCard";
import { useTheme } from "../../shared/SiteSettingsContext";

/** Type for the card command element props */
type CardCommandProps = {
    card?: ShowdownBotCard | null;
    className?: string;
};

export default function CardCommand({ card, className = "w-10 h-10" }: CardCommandProps) {

    const { isDark } = useTheme();
    const color = (['NYM', 'SDP'].includes(card?.team || 'N/A') ? card?.image.color_secondary : card?.image.color_primary) || 'rgb(0, 0, 0)';

    const getSrcImage = () => {
        const appearance = isDark ? 'dark' : 'light';
        const commandName = card?.chart.is_pitcher ? 'control' : 'onbase';
        return `/images/card/${commandName}-${appearance}.png`;
    }

    return (
        <div className={`relative ${className} text-xl`}>
            {/* Command background */}
            <img
                src={getSrcImage()}
                alt={card?.chart.is_pitcher ? 'Control Background' : 'Command Background'}
                className="absolute top-0 left-0 w-full h-full object-cover"
            />
            {/* Command text */}
            <div 
                className={`
                    absolute top-1/2 left-1/2 
                    transform -translate-x-1/2 ${card?.chart.is_pitcher ? '-translate-y-1/2' : '-translate-y-3/5'}
                    text-white font-black tracking-tighter
                    drop-shadow-lg
                `}
                style={{ 
                    color: color,
                 }}
            >
                {card?.chart.command}
            </div>
        </div>
    );
}