import { TeamChip } from '../../shared/TeamChip';
import { ProgressRing } from '../../team_builder/ProgressRing';
import type { LeagueSettings, LeagueTeam } from '../../../api/leagues';
import { leagueTeamIdentity } from '../leagueUi';
import { luxuryTaxCost } from './draftView';

type Props = {
    team: LeagueTeam;
    points: number;
    picksMade: number;
    settings: LeagueSettings;
    /** `lg` heads a team's field view; `md` is a row in a list of teams. */
    size?: 'md' | 'lg';
    isOnTheClock?: boolean;
};

const SIZES = {
    md: { ring: 34, stroke: 3, ringLabel: 'text-[12px]', name: 'text-[13px]', meta: 'text-[11px]', cap: 'text-[11px]' },
    lg: { ring: 44, stroke: 4, ringLabel: 'text-[16px]', name: 'text-[18px]', meta: 'text-[13px]', cap: 'text-[13px]' },
};

/** A drafting team at a glance: a ring of picks made out of the roster size, its name and
 *  points, what's left under the cap (in total and per pick still to make), and what it owes
 *  under the luxury tax (which lets a team go over the cap). */
export function DraftTeamSummary({ team, points, picksMade, settings, size = 'md', isOnTheClock = false }: Props) {
    const sizing = SIZES[size];
    const cap = settings.pts_cap;
    const tax = settings.luxury_tax ?? null;
    const cost = cap && tax ? luxuryTaxCost(points, cap, tax) : null;
    const left = cap ? cap - points : null;
    const isOverCap = left !== null && left < 0;
    // Points left spread over the picks still to make
    const picksLeft = settings.roster_size - picksMade;
    const avgLeft = left !== null && picksLeft > 0 ? Math.round(left / picksLeft) : null;

    return (
        <div className="flex items-center gap-2.5 min-w-0">
            <span className="text-(--green)">
                <ProgressRing
                    filled={picksMade}
                    target={settings.roster_size}
                    size={sizing.ring}
                    stroke={sizing.stroke}
                    label={<span className={`${sizing.ringLabel} text-(--text-primary)`}>{picksMade}</span>}
                />
            </span>
            <div className="flex flex-col min-w-0 flex-1">
                <div className="flex items-center gap-1.5 min-w-0">
                    <TeamChip team={leagueTeamIdentity(team)} size="sm" />
                    <span className={`${sizing.name} font-black uppercase truncate`} title={team.name}>{team.name}</span>
                </div>
                <span className={`${sizing.meta} font-semibold tabular-nums text-(--text-secondary) truncate`}>
                    {isOnTheClock ? <span className="font-black text-(--secondary)">On the clock · </span> : null}
                    {points} pts · {picksMade}/{settings.roster_size} picks
                </span>
            </div>
            {cap && (
                <div className={`${sizing.cap} shrink-0 text-right font-bold tabular-nums leading-tight`}>
                    <div className="text-(--text-tertiary)">CAP <span className="text-(--text-primary)">{cap}</span></div>
                    <div className="text-(--text-tertiary)">LEFT <span className={isOverCap ? 'text-(--red)' : 'text-(--green)'}>{left}</span></div>
                    {avgLeft !== null && (
                        <div className="text-(--text-tertiary)">AVG <span className={isOverCap ? 'text-(--red)' : 'text-(--text-primary)'}>{avgLeft}</span></div>
                    )}
                    {cost && tax && (
                        <div className="text-(--text-tertiary)" title={`$${tax.buy_in} buy-in + $${cost.tax} luxury tax`}>
                            COST <span className={cost.tax > 0 ? 'text-(--red)' : 'text-(--text-primary)'}>${cost.total}</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
