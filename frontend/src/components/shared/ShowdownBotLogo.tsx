import React from "react";
import { useTheme } from "./SiteSettingsContext";

/** Props for the logo component */
type ShowdownBotLogoProps = {
    className?: string;
};

/** Showdown logo component */
const ShowdownBotLogo: React.FC<ShowdownBotLogoProps> = ({ className = "" }) => {

    const { isDark } = useTheme();

    return (
        <div className={`relative ${className}`}>
            <img 
                src={"/images/logos/logo-light.png"} 
                alt="Showdown logo" 
                className={`object-contain  ${isDark ? 'hidden' : 'block'}`}
            />
            <img 
                src={"/images/logos/logo-dark.png"} 
                alt="Showdown logo" 
                className={`object-contain  ${isDark ? 'block' : 'hidden'}`}
            />
        </div>
    );
};

export default ShowdownBotLogo;
