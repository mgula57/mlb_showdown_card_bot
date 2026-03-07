

/** Enhance the visibility of colors based on the theme */
export const countryCodeForTeam = (sportId: number, team: string) => {
    // Convert team to ISO country code
    if (sportId !== 51) {
        return null; // Only apply for International
    }
    const teamToCountryCode: Record<string, string> = {
        AUS: "AU",
        BRA: "BR",
        CAN: "CA",
        CHN: "CN",
        COL: "CO",
        CUB: "CU",
        CZE: "CZ",
        DOM: "DO",
        ESP: "ES",
        GBR: "GB",
        ISR: "IS",
        ITA: "IT",
        JPN: "JP",
        KOR: "KR",
        MEX: "MX",
        NCA: "NI",
        NED: "NL",
        PAN: "PA",
        PUR: "PR",
        RSA: "ZA",
        TPE: "TW",
        USA: "US",
        VEN: "VE",
    };
    return teamToCountryCode[team] || null;
};