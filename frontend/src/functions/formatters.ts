
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
    switch ((stat ?? "").toUpperCase().replace("*", "")) {
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
        default:
            return String(value);
    }
}