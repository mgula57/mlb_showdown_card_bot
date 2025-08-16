
/** Format a value for display in a slashline (ex: .950) */
export function formatSlashlineValue(value: unknown, digits = 3): string {
    if (value == null) return "";
    const n = Number(value);
    if (!Number.isFinite(n)) return String(value);
    // 0.950 -> .950, -0.950 -> -.950, 1.005 stays 1.005
    return n.toFixed(digits).replace(/^(-?)0\./, "$1.");
}

/** Format a value given a stat category */
export function formatStatValue(value: unknown, stat: string, digits = 3): string {
    if (value == null) return "";
    switch ((stat ?? "").toUpperCase()) {
        case "BA":
        case "AVG":
        case "OBP":
        case "SLG":
        case "OPS":
            return formatSlashlineValue(value, digits);
        default:
            return String(value);
    }
}