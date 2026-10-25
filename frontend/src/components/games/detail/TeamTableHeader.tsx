/**
 * @fileoverview Title row over a team's batting or pitching table: the team's flag (WBC only),
 * its abbreviation in a team-color plate and the table's name, with room on the right for totals.
 */
import type { ReactNode } from "react";
import ReactCountryFlag from "react-country-flag";

import type { BoxscoreTeamData } from "../../../api/mlbAPI";
import { countryCodeForTeam } from "../../../functions/flags";
import { getReadableTextColor, NEUTRAL_TEAM_COLOR } from '../../../functions/colors';
import { Heading } from "../../shared/Heading";
import { Plate } from "../../shared/Plate";

type TeamTableHeaderProps = {
    team: BoxscoreTeamData["team"];
    sportId?: number;
    title: string;
    children?: ReactNode;
};

export default function TeamTableHeader({ team, sportId, title, children }: TeamTableHeaderProps) {
    const countryCode = countryCodeForTeam(sportId ?? 0, team.abbreviation);
    const badgeBg = team.primary_color ?? NEUTRAL_TEAM_COLOR;
    return (
        <div className="px-3 py-2 border-b border-(--divider) flex items-center gap-2">
            {sportId === 51 && countryCode && (
                <ReactCountryFlag countryCode={countryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
            )}
            <Plate variant="custom" size="sm" style={{ backgroundColor: badgeBg, color: getReadableTextColor(badgeBg, '#ffffff') }}>
                {team.abbreviation}
            </Plate>
            <Heading level="panel" as="div">{title}</Heading>
            {children}
        </div>
    );
}
