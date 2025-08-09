import showdownLogoLight from "../../assets/logo-light.png";
import showdownLogoDark from "../../assets/logo-dark.png";
import React from "react";

/** Props for the logo component */
type ShowdownBotLogoProps = {
    className?: string;
};

/** Showdown logo component */
const ShowdownBotLogo: React.FC<ShowdownBotLogoProps> = ({ className = "" }) => {
    return (
        <div className={`relative ${className}`}>
            <img 
                src={showdownLogoLight} 
                alt="Showdown logo" 
                className="object-contain block dark:hidden" 
            />
            <img 
                src={showdownLogoDark} 
                alt="Showdown logo" 
                className="object-contain hidden dark:block" 
            />
        </div>
    );
};

export default ShowdownBotLogo;
