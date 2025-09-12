import { type ShowdownBotCard } from "../../../api/showdownBotCard";
import { useTheme } from "../../shared/SiteSettingsContext";

// Import different command background images
import controlLight from '../../../assets/control-light.png';
import controlDark from '../../../assets/control-dark.png';
import commandLight from '../../../assets/onbase-light.png';
import commandDark from '../../../assets/onbase-dark.png';

/** Type for the card command element props */
type CardCommandProps = {
    card: ShowdownBotCard;
    className?: string;
};

export default function CardCommand({ card, className = "w-10 h-10" }: CardCommandProps) {

    const { isDark } = useTheme();

    const getSrcImage = () => {
        if (card.chart.is_pitcher) {
            return isDark ? controlDark : controlLight;
        } else {
            return isDark ? commandDark : commandLight;
        }
    }

    return (
        <div className={`relative ${className}`}>
            {/* Command background */}
            <img
                src={getSrcImage()}
                alt={card.chart.is_pitcher ? 'Control Background' : 'Command Background'}
                className="absolute top-0 left-0 w-full h-full object-cover"
            />
            {/* Command text */}
            <div 
                className={`
                    absolute top-1/2 left-1/2 
                    transform -translate-x-1/2 ${card.chart.is_pitcher ? '-translate-y-1/2' : '-translate-y-3/5'}
                    text-white font-bold text-2xl
                    drop-shadow-lg
                `}
                style={{ 
                    color: card.image.color_primary || 'rgb(0, 0, 0)',
                 }}
            >
                {card.chart.command}
            </div>
        </div>
    );
}