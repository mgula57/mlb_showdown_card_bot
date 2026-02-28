import { useTheme } from "../../shared/SiteSettingsContext";
import { darkenIfLowContrastOnWhite } from "../../../functions/colors";
/**
 * Props for the CardCommand component
 */
type CardCommandProps = {
    /** Card data containing command rating and player type */
    isPitcher: boolean;
    primaryColor: string;
    secondaryColor: string;
    command?: number;
    team?: string;
    /** Optional CSS classes for sizing and positioning */
    className?: string;
};

/**
 * CardCommand - Displays the command rating with themed background
 * 
 * Shows either "OnBase" (hitters) or "Control" (pitchers) rating with the
 * appropriate background image that adapts to the current theme (light/dark).
 * The command rating is styled with team colors for visual consistency.
 * 
 * Command ratings represent:
 * - OnBase (Hitters): Higher values mean more favorable dice rolls for the batter
 * - Control (Pitchers): Higher values mean more favorable dice rolls for the pitcher
 * 
 * @param card - ShowdownBotCard data containing command info and styling
 * @param className - CSS classes for customizing size and positioning
 * 
 * @example
 * ```tsx
 * <CardCommand 
 *   card={cardData} 
 *   className="w-12 h-12" 
 * />
 * ```
 */
export default function CardCommand({ isPitcher, primaryColor, secondaryColor, command, team, className = "w-10 h-10" }: CardCommandProps) {
    const { isDark } = useTheme();
    
    // Use secondary color for certain teams for better contrast
    const color = (['NYM', 'SDP'].includes(team || 'N/A') 
        ? secondaryColor 
        : primaryColor) || 'rgb(0, 0, 0)';
    const colorAdjusted = darkenIfLowContrastOnWhite(color);

    /**
     * Gets the appropriate background image based on player type and theme
     * @returns Path to the command background image
     */
    const getSrcImage = () => {
        const appearance = isDark ? 'dark' : 'light';
        const commandName = isPitcher ? 'control' : 'onbase';
        return `/images/card/${commandName}-${appearance}.png`;
    };

    return (
        <div className={`relative ${className} text-xl`}>
            {/* Theme-aware command background image */}
            <img
                src={getSrcImage()}
                alt={isPitcher ? 'Control Background' : 'OnBase Background'}
                className="absolute top-0 left-0 w-full h-full object-cover"
            />
            
            {/* Command rating number with team color styling */}
            <div 
                className={`
                    absolute top-1/2 left-1/2 
                    transform -translate-x-1/2 
                    ${isPitcher ? '-translate-y-1/2' : '-translate-y-3/5'}
                    text-white font-black tracking-tighter
                    drop-shadow-lg
                `}
                style={{ 
                    color: colorAdjusted,
                }}
            >
                {command}
            </div>
        </div>
    );
}