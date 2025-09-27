import showdownLogoLight from "../../assets/logo-light.png";
import showdownLogoDark from "../../assets/logo-dark.png";
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
                src={showdownLogoLight} 
                alt="Showdown logo" 
                className={`object-contain  ${isDark ? 'hidden' : 'block'}`}
            />
            <img 
                src={showdownLogoDark} 
                alt="Showdown logo" 
                className={`object-contain  ${isDark ? 'block' : 'hidden'}`}
            />
        </div>
    );
};

export default ShowdownBotLogo;
