/**
 * @fileoverview Shared team-identity badge: country flag (WBC only) + colored abbreviation pill,
 * with an optional record and star (display-only or an interactive toggle). Replaces the inline
 * flag+abbreviation+star markup that used to be duplicated in GameItem (x2) and the Home page
 * games ticker (x2).
 *
 * Standings renders a full-row colored bar, and the Seasons sidebar tints the whole row on
 * hover/select via CSS custom properties — both genuinely different layouts from this inline
 * badge, not more copies of the same pattern, so they're left as their own thing.
 */
import ReactCountryFlag from "react-country-flag";
import { FaStar, FaRegStar } from "react-icons/fa6";

import type { TeamIdentity, TeamRecordLine } from "../../domain/team";
import { getReadableTextColor } from "../../functions/colors";

type TeamChipSize = "sm" | "md";

type TeamChipProps = {
    team: TeamIdentity;
    record?: TeamRecordLine;
    size?: TeamChipSize;
    isStarred?: boolean;
    onToggleStar?: () => void;
    className?: string;
};

const SIZE_CLASSES: Record<TeamChipSize, { badge: string; flag: string; record: string }> = {
    sm: { badge: "font-black text-[11px]", flag: "1em", record: "text-[10px]" },
    md: { badge: "font-black", flag: "1.25em", record: "text-[11px]" },
};

export function TeamChip({ team, record, size = "md", isStarred, onToggleStar, className = "" }: TeamChipProps) {
    const sizing = SIZE_CLASSES[size];
    const badgeBg = team.primaryColor;
    const badgeText = badgeBg ? getReadableTextColor(badgeBg, "#ffffff") : undefined;

    return (
        <div className={`flex items-center gap-1.5 min-w-0 ${className}`}>
            {team.countryCode && (
                <ReactCountryFlag countryCode={team.countryCode} svg style={{ width: sizing.flag, height: sizing.flag }} />
            )}
            <span
                className={`${sizing.badge} ${badgeBg ? "px-1.5 py-0.5 rounded" : "text-(--text-primary)"}`}
                style={badgeBg ? { backgroundColor: badgeBg, color: badgeText } : undefined}
            >
                {team.abbreviation}
            </span>
            {record && (
                <span className={`${sizing.record} font-semibold text-(--text-secondary)`}>
                    {record.wins}-{record.losses}
                </span>
            )}
            {onToggleStar ? (
                <span
                    role="button"
                    tabIndex={0}
                    aria-label={isStarred ? `Unstar ${team.abbreviation}` : `Star ${team.abbreviation}`}
                    onClick={(event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        onToggleStar();
                    }}
                    onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            event.stopPropagation();
                            onToggleStar();
                        }
                    }}
                    className={`text-sm leading-none cursor-pointer ${isStarred ? "text-yellow-300" : "text-(--quaternary) hover:text-yellow-300"}`}
                >
                    {isStarred ? <FaStar className="h-3.5 w-3.5" /> : <FaRegStar className="h-3.5 w-3.5" />}
                </span>
            ) : isStarred ? (
                <FaStar className="h-3 w-3 shrink-0 text-yellow-400" aria-label={`${team.abbreviation} is starred`} />
            ) : null}
        </div>
    );
}

export default TeamChip;
