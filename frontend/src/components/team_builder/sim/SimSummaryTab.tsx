import { useMemo, type ReactNode } from 'react';
import { FaTrophy } from 'react-icons/fa6';
import type { AwardWinner, SeasonSimSummary } from '../../../api/sim';
import Standings from '../../seasons/Standings';
import { TeamChip } from '../../shared/TeamChip';
import { fromSimTeamIdentity, fallbackIdentity } from '../../../domain/adapters/fromSim';
import { useStandingsEntries, useIdentity, hashId } from './simStandings';
import { SimWinPctChart } from './SimWinPctChart';
import { SimStatsTable } from './SimStatsTable';
import { HITTER_COLUMNS, PITCHER_COLUMNS } from './simStatColumns';
import { roundLabel } from './roundLabel';

const TOP_PERFORMERS_COUNT = 5;

const AWARD_LABELS: Record<AwardWinner['category'], string> = {
    MVP: 'MVP',
    CY_YOUNG: 'Cy Young',
    ROY: 'Rookie of the Year',
    SILVER_SLUGGER: 'Silver Slugger',
};

function SectionCard({ title, children }: { title: string; children: ReactNode }) {
    return (
        <div className="rounded-xl bg-(--background-tertiary) p-3 flex flex-col gap-2 min-w-0">
            <p className="text-[12px] font-bold text-(--text-primary)">{title}</p>
            {children}
        </div>
    );
}

type Props = {
    summary: SeasonSimSummary;
    /** Schedule key the takeover team runs under (the club it replaced). */
    teamKey: string;
};

export function SimSummaryTab({ summary, teamKey }: Props) {
    const team = summary.team;
    const identityFor = useIdentity(summary);
    const standingsEntries = useStandingsEntries(summary);

    const divisionEntries = useMemo(
        () => standingsEntries.filter(([, groups]) => groups[0]?.division?.name === team.division),
        [standingsEntries, team.division],
    );

    const playoffCutlinePct = useMemo(() => {
        const playoffTeams = Object.values(summary.standings.divisions)
            .flat()
            .filter(record => record.playoff_seeding != null);
        return playoffTeams.length > 0 ? Math.min(...playoffTeams.map(record => record.win_pct)) : null;
    }, [summary.standings]);

    const mySeries = useMemo(
        () => summary.postseason.filter(s => s.home_team === teamKey || s.away_team === teamKey),
        [summary.postseason, teamKey],
    );

    const myPlayerIds = useMemo(() => new Set(summary.players.map(p => p.id)), [summary.players]);
    const myAwards = useMemo(() => {
        const awards = summary.awards;
        if (!awards) return [];
        return [...awards.mvp, ...awards.cy_young, ...awards.rookie_of_year, ...awards.silver_sluggers]
            .filter(a => myPlayerIds.has(a.player.id));
    }, [summary.awards, myPlayerIds]);

    const topHitters = useMemo(
        () => summary.players.filter(p => p.player_type === 'Hitter').slice(0, TOP_PERFORMERS_COUNT),
        [summary.players],
    );
    const topPitchers = useMemo(
        () => summary.players.filter(p => p.player_type === 'Pitcher').slice(0, TOP_PERFORMERS_COUNT),
        [summary.players],
    );

    return (
        <div className="flex flex-col gap-4">
            <div className="grid gap-4 md:grid-cols-2">
                <SectionCard title={team.division ? `${team.division} Standings` : 'Standings'}>
                    {divisionEntries.length > 0 ? (
                        <Standings standingsEntries={divisionEntries} selectedTeamId={teamKey ? hashId(teamKey) : null} />
                    ) : (
                        <p className="text-[13px] text-(--text-tertiary) py-2">No division data available.</p>
                    )}
                </SectionCard>

                <SectionCard title="Win % Over Time">
                    <SimWinPctChart games={summary.games} playoffCutlinePct={playoffCutlinePct} />
                </SectionCard>
            </div>

            {mySeries.length > 0 && (
                <SectionCard title="Postseason">
                    <div className="flex flex-col gap-1.5">
                        {mySeries.map((series, i) => {
                            const opponentKey = series.home_team === teamKey ? series.away_team : series.home_team;
                            const opponentIdentity = identityFor(opponentKey);
                            const myWins = series.home_team === teamKey ? series.home_team_wins : series.away_team_wins;
                            const oppWins = series.home_team === teamKey ? series.away_team_wins : series.home_team_wins;
                            const won = series.winner === teamKey;
                            return (
                                <div key={i} className="flex items-center gap-2 text-[12px] rounded-lg bg-(--background-secondary) px-3 py-2">
                                    <span className="text-(--text-tertiary) w-20 shrink-0 font-semibold">{roundLabel(series.round, series.league)}</span>
                                    <span className={`font-bold ${won ? 'text-(--showdown-blue)' : 'text-(--text-tertiary)'}`}>{won ? 'W' : 'L'}</span>
                                    <span className="text-(--text-primary)">{myWins}–{oppWins} vs</span>
                                    <TeamChip team={opponentIdentity ? fromSimTeamIdentity(opponentIdentity) : fallbackIdentity(opponentKey)} size="sm" />
                                </div>
                            );
                        })}
                    </div>
                </SectionCard>
            )}

            {myAwards.length > 0 && (
                <SectionCard title="Awards">
                    <div className="flex flex-col gap-1.5">
                        {myAwards.map((award, i) => (
                            <div key={i} className="flex items-center gap-2 text-[12px] rounded-lg bg-(--background-secondary) px-3 py-2">
                                <FaTrophy className="text-(--secondary) shrink-0" />
                                <span className="font-bold text-(--text-primary)">{award.player.name}</span>
                                <span className="text-(--text-tertiary)">
                                    won {award.league} {AWARD_LABELS[award.category]}{award.position ? ` (${award.position})` : ''} · {award.value_label}
                                </span>
                            </div>
                        ))}
                    </div>
                </SectionCard>
            )}

            <SectionCard title="Top Performers">
                <div className="flex flex-col gap-3">
                    <SimStatsTable rows={topHitters} columns={HITTER_COLUMNS} emptyLabel="No hitters on this roster." cardsEnabled identities={summary.identities} />
                    <SimStatsTable rows={topPitchers} columns={PITCHER_COLUMNS} emptyLabel="No pitchers on this roster." cardsEnabled identities={summary.identities} />
                </div>
            </SectionCard>
        </div>
    );
}
