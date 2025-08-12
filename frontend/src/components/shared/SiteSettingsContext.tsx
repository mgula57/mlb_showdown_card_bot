import React, { createContext, useContext, useState, useEffect } from "react";

export const showdownSets: Array<{ value: string; label: string }> = [
    { value: "2000", label: "2000" },
    { value: "2001", label: "2001" },
    { value: "2002", label: "2002" },
    { value: "2003", label: "2003" },
    { value: "2004", label: "2004" },
    { value: "2005", label: "2005" },
    { value: "CLASSIC", label: "Classic" },
    { value: "EXPANDED", label: "Expanded" },
];


/** Props for the SiteSettingsContext */
type SiteSettings = {
    userShowdownSet: string;
    setUserShowdownSet: (v: string) => void;
};

/** Context for site settings */
const SiteSettingsContext = createContext<SiteSettings | undefined>(undefined);

export const SiteSettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {

    // State to hold the user's MLB Showdown Set of choice
    const [userShowdownSet, setUserShowdownSetState] = useState("2000");

    // Load from localStorage on mount
    useEffect(() => {
        const stored = localStorage.getItem("userShowdownSet");
        if (stored) setUserShowdownSetState(stored);
    }, []);

    // Save to localStorage on change
    const setUserShowdownSet = (v: string) => {
        setUserShowdownSetState(v);
        localStorage.setItem("userShowdownSet", v);
    };

    return (
        <SiteSettingsContext.Provider value={{ userShowdownSet, setUserShowdownSet }}>
            {children}
        </SiteSettingsContext.Provider>
    );
};

export const useSiteSettings = () => {
    const ctx = useContext(SiteSettingsContext);
    if (!ctx) throw new Error("useSiteSettings must be used within SiteSettingsProvider");
    return ctx;
};