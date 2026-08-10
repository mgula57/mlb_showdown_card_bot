
const ORDINAL_SUFFIXES: Record<number, string> = { 1: "st", 2: "nd", 3: "rd" };

/** 1 -> "1st", 3 -> "3rd", 11 -> "11th". Used for innings and bases. */
export function ordinal(n: number): string {
    const suffix = n % 100 >= 11 && n % 100 <= 13 ? "th" : ORDINAL_SUFFIXES[n % 10] ?? "th";
    return `${n}${suffix}`;
}

/** Format a value for display in a slashline (ex: .950) */
export function formatSlashlineValue(value: unknown, digits = 3): string {
    if (value == null) return "";
    const n = Number(value);
    if (!Number.isFinite(n)) return String(value);
    // 0.950 -> .950, -0.950 -> -.950, 1.005 stays 1.005
    return n.toFixed(digits).replace(/^(-?)0\./, "$1.");
}

export function formatAsPct(value: unknown, digits = 1): string {
    const valueAsNumber = Number(value);
    return `${(valueAsNumber * 100).toFixed(digits)}%`
}

/** Format a value given a stat category */
export function formatStatValue(value: unknown, stat: string, digits = 3): string {
    if (value == null) return "";
    switch ((stat ?? "").toUpperCase().replace("*", "").split("-")[0]) {
        case "BA":
        case "AVG":
        case "AVERAGE":
        case "OBP":
        case "ONBASE":
        case "SLG":
        case "SLUGGING":
        case "WHIP":
        case "OPS":
            return formatSlashlineValue(value, digits);
        case "HOME_RUNS":
            return String(Math.round(Number(value) || 0));
        case "OUT_DISTRIBUTION":
            return formatAsPct(value, 1);
        case "BWAR":
            return Number(value).toFixed(1);
        case "DWAR":
            return Number(value).toFixed(2);
        case "FWAR":
            return Number(value).toFixed(2);
        case "ERA":
            return Number(value).toFixed(2);
        case "DRS":
        case "TZR":
        case "OAA":
            return Number(value).toFixed(0);
        default:
            return String(value);
    }
}

export function formatYear(year: string | number): string {
    const displayYear = year && year.toString().includes('-')
        ? year.toString().split('-').map(y => y.slice(-2)).join('-')
        : year.toString();
    return displayYear;
}