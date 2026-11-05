import type { CSSProperties, ReactNode } from 'react';
import { FaCircle, FaStar } from 'react-icons/fa6';
import type { LeagueListItem, LeagueListTeam } from '../../api/leagues';
import { getContrastTextColor, NEUTRAL_TEAM_COLOR, NEUTRAL_TEAM_COLOR_SECONDARY } from '../../functions/colors';
import { FramedTile } from '../shared/FramedTile';
import { Heading } from '../shared/Heading';
import { Plate } from '../shared/Plate';
import { SetBadgeRow } from '../shared/SetBadge';
import { SEASON_STATUS_LABEL } from './leagueUi';

/** Tile frame shared by LeagueItem and its skeleton. It fills its grid cell, since the pennant
 *  row needs the width of a full league. */
const TILE_FRAME = 'w-full h-60 rounded-trading-card';

/** A pennant's drop as a percentage of the row's height. The worst record in the league hangs at
 *  `min` and the best at `max`, so a close race still shows; `rest` is before any games are played. */
const PENNANT_DROP = { min: 56, rest: 68, max: 100 };

/** Long banner with a point at the bottom. */
const PENNANT_SHAPE = 'polygon(0 0, 100% 0, 100% calc(100% - 12px), 50% 100%, 0 calc(100% - 12px))';

/** Hovering a tile stirs the pennants: each swings the opposite way to its neighbor, in a ripple. */
const PENNANT_SWAY = { degrees: 3, staggerMs: 25 };

function pennantDrop(team: LeagueListTeam, teams: LeagueListTeam[]): number {
    if (team.is_champion || team.is_on_the_clock) return PENNANT_DROP.max;
    const played = teams.filter(t => t.wins + t.losses > 0);
    if (played.length === 0) return PENNANT_DROP.rest;
    const pcts = played.map(t => t.win_pct);
    const low = Math.min(...pcts);
    const high = Math.max(...pcts);
    if (high === low) return PENNANT_DROP.rest;
    return PENNANT_DROP.min + (PENNANT_DROP.max - PENNANT_DROP.min) * (team.win_pct - low) / (high - low);
}

const ordinal = (n: number) => `${n}${n === 1 ? 'st' : n === 2 ? 'nd' : n === 3 ? 'rd' : 'th'}`;

const recordLabel = (team: LeagueListTeam) => `${team.wins}-${team.losses}`;

type LeagueItemProps = {
    league: LeagueListItem;
    /** The viewer, to pick out their team and their turn on the clock. */
    userId: string | undefined;
    onClick: () => void;
};

/** League tile for the Leagues list: the pennant race. Every seat hangs a pennant from the rail in
 *  its team's colors, longest for the best record, over the league's name and where its season is.
 *  Open seats hang empty until someone takes them. */
export function LeagueItem({ league, userId, onClick }: LeagueItemProps) {
    const { teams, settings } = league;
    const isCommissioner = league.commissioner_user_id === userId;
    const myTeam = teams.find(team => team.user_id === userId) ?? null;
    const myRank = myTeam ? teams.indexOf(myTeam) + 1 : 0;
    const hasRecords = league.games_played > 0;

    return (
        <FramedTile onClick={onClick} className={TILE_FRAME}>
            {/* Pennants on the silver card-back field */}
            <div className="relative flex-1 min-h-0 bg-(--release-tile-field) bg-pinstripe">
                <div className="absolute top-1 inset-x-1 z-1 flex items-start justify-between gap-1">
                    <div className="flex flex-wrap gap-1">
                        {league.current_season_number !== null && <Plate variant="ink" size="sm">Season {league.current_season_number}</Plate>}
                        {isCommissioner && <Plate variant="outline" size="sm" className="bg-(--background-secondary)">Commissioner</Plate>}
                    </div>
                    <SetBadgeRow sets={[league.showdown_set]} />
                </div>
                <PennantRow league={league} myTeamId={myTeam?.team_id ?? null} />
            </div>

            {/* Details */}
            <div className="relative flex flex-col gap-1.5 px-2 py-2 border-t border-(--divider) bg-(--background-secondary)">
                <Heading level="section" as="div" fit>{league.name}</Heading>
                <div className="flex items-center justify-between gap-2 min-w-0">
                    <div className="flex items-center gap-1 min-w-0">
                        <SeasonPlate league={league} isMyPick={!!myTeam?.is_on_the_clock} />
                    </div>
                    <SeasonProgress league={league} />
                </div>
                <div className="flex items-center justify-between gap-2 text-[11px] font-medium tabular-nums text-(--text-tertiary)">
                    <span className="min-w-0 truncate">
                        {myTeam && `${myTeam.name}${hasRecords ? ` · ${recordLabel(myTeam)} · ${ordinal(myRank)} of ${teams.length}` : ''}`}
                    </span>
                    <span className="shrink-0">
                        {settings.roster_size} cards{settings.pts_cap ? ` · ${settings.pts_cap.toLocaleString()} PT. cap` : ''}
                    </span>
                </div>
            </div>
        </FramedTile>
    );
}

/** The rail and a pennant per seat. Before the first draft there are no teams yet, so taken seats
 *  hang plain navy pennants. */
function PennantRow({ league, myTeamId }: { league: LeagueListItem; myTeamId: string | null }) {
    const { teams, settings, member_count } = league;
    const takenSeats = teams.length > 0 ? 0 : member_count;
    const openSeats = Math.max(0, settings.team_count - teams.length - takenSeats);
    const swayStyle = (index: number) => ({
        '--sway': `${index % 2 === 0 ? PENNANT_SWAY.degrees : -PENNANT_SWAY.degrees}deg`,
        transitionDelay: `${index * PENNANT_SWAY.staggerMs}ms`,
    } as CSSProperties);

    return (
        <div aria-hidden className="absolute top-8 bottom-2 inset-x-0">
            <div className="absolute top-0 inset-x-0 h-0.5 bg-(--rule-strong)" />
            <div className="absolute inset-x-3 top-0.5 bottom-0 flex justify-center gap-1">
                {teams.map((team, i) => (
                    <PennantHanger key={team.team_id} style={swayStyle(i)} pulse={team.is_on_the_clock}>
                        <TeamPennant team={team} drop={pennantDrop(team, teams)} isMine={team.team_id === myTeamId} />
                    </PennantHanger>
                ))}
                {Array.from({ length: takenSeats }, (_, i) => (
                    <PennantHanger key={`taken-${i}`} style={swayStyle(i)}>
                        <div className="w-full bg-(--showdown-blue-fill)" style={{ height: `${PENNANT_DROP.rest}%`, clipPath: PENNANT_SHAPE }} />
                    </PennantHanger>
                ))}
                {Array.from({ length: openSeats }, (_, i) => (
                    <PennantHanger key={`open-${i}`} style={swayStyle(teams.length + takenSeats + i)}>
                        <div className="w-full bg-(--rule-strong)/20" style={{ height: `${PENNANT_DROP.min}%`, clipPath: PENNANT_SHAPE }} />
                    </PennantHanger>
                ))}
            </div>
        </div>
    );
}

/** One seat's slot on the rail, hinged at the top. The hard shadow sits out here because a
 *  pennant's own clip path would cut it off. */
function PennantHanger({ children, style, pulse = false }: { children: ReactNode; style: CSSProperties; pulse?: boolean }) {
    return (
        <div
            className={`
                flex-1 min-w-0 max-w-11 h-full origin-top drop-shadow-[0_2px_0_rgb(0_0_0/0.25)]
                transition-[rotate] duration-300 ease-out [@media(hover:hover)]:group-hover:rotate-(--sway)
                ${pulse ? 'animate-pulse' : ''}
            `}
            style={style}
        >
            {children}
        </div>
    );
}

/** A team's pennant, trimmed in the white card edge so dark team colors hold up on the dark field. */
function TeamPennant({ team, drop, isMine }: { team: LeagueListTeam; drop: number; isMine: boolean }) {
    const primary = team.primary_color || NEUTRAL_TEAM_COLOR;
    return (
        <div className="w-full bg-(--card-edge) p-px" style={{ height: `${drop}%`, clipPath: PENNANT_SHAPE }}>
            <div
                className="flex flex-col items-center gap-1 h-full"
                style={{ backgroundColor: primary, color: getContrastTextColor(primary), clipPath: PENNANT_SHAPE }}
            >
                <span className="h-1 w-full shrink-0" style={{ backgroundColor: team.secondary_color || NEUTRAL_TEAM_COLOR_SECONDARY }} />
                <span className="font-display-upright uppercase text-[12px] leading-none tracking-wide [writing-mode:vertical-rl]">
                    {team.abbreviation}
                </span>
                <span className="flex-1 min-h-0" />
                {team.is_champion ? (
                    <span className="flex items-center justify-center size-3.5 mb-3 rounded-plate bg-(--field-ink) text-(--gold)">
                        <FaStar className="size-2.5" />
                    </span>
                ) : isMine ? (
                    <span className="size-2 mb-3.5 rotate-45 bg-(--card-edge) ring-1 ring-(--field-ink)" />
                ) : null}
            </div>
        </div>
    );
}

function SeasonPlate({ league, isMyPick }: { league: LeagueListItem; isMyPick: boolean }) {
    const status = league.current_season_status;
    if (!status) return <Plate variant="outline" size="sm">Waiting for the draft</Plate>;
    if (isMyPick) return <Plate variant="navy" size="sm">Your pick</Plate>;
    if (status === 'drafting') {
        return (
            <Plate variant="red" size="sm">
                <FaCircle className="animate-pulse w-1.5 h-1.5" />
                {SEASON_STATUS_LABEL.drafting}
            </Plate>
        );
    }
    return <Plate variant={status === 'regular' || status === 'postseason' ? 'ink' : 'outline'} size="sm">{SEASON_STATUS_LABEL[status]}</Plate>;
}

/** How far along things are, opposite the status plate: picks, games, or who won it all. */
function SeasonProgress({ league }: { league: LeagueListItem }) {
    const { teams, draft_pick, draft_total_picks, games_played, games_per_team, current_season_status: status } = league;
    const champion = teams.find(team => team.is_champion);
    const text = !status ? `${league.member_count}/${league.settings.team_count} teams`
        : draft_pick !== null ? `Pick ${draft_pick} of ${draft_total_picks}`
        : champion ? `${champion.abbreviation} won it all`
        : status === 'regular' && games_per_team ? `${games_played} of ${games_per_team} games`
        : null;
    if (!text) return null;
    return <span className="shrink-0 text-[11px] font-semibold tabular-nums text-(--text-secondary)">{text}</span>;
}

/** Loading placeholder sized to match LeagueItem. */
export function LeagueItemSkeleton() {
    return <div aria-hidden className={`${TILE_FRAME} border-2 border-(--divider) bg-(--background-tertiary) animate-pulse`} />;
}

export default LeagueItem;
