import ReactCountryFlag from "react-country-flag";

import { type Standings, type Team } from '../../api/mlbAPI';
import { countryCodeForTeam } from "../../functions/flags";
import { getContrastColor } from "../shared/Color";

type StandingsProps = {
	standingsEntries: [string, Standings[]][];
	selectedSportId?: number;
	selectedTeamId?: number | null;
	onTeamSelect?: (team: Team) => void;
};

const formatGamesBack = (gamesBack?: string): string => {
	if (!gamesBack || gamesBack === '-') {
		return '--';
	}
	return gamesBack;
};

export default function Standings({ standingsEntries, selectedSportId, selectedTeamId, onTeamSelect }: StandingsProps) {

	// Flatten leagues into a single list of divisions, each rendered as its own card
	const divisionStandings = standingsEntries.flatMap(([leagueAbbreviation, leagueStandings]) =>
		leagueStandings.map((standing) => ({ leagueAbbreviation, standing }))
	);

	return (
		<div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4 sm:mt-0">
			{divisionStandings.map(({ leagueAbbreviation, standing }, index) => {
				const showPoints = standing.team_records?.[0]?.showdown_points !== undefined;
				const title = standing.division?.name_short || standing.division?.name || leagueAbbreviation;
				const rowTemplate = showPoints
					? "grid-cols-[minmax(0,1fr)_4.5rem_3rem_3.5rem]"
					: "grid-cols-[minmax(0,1fr)_4.5rem_3rem]";
				return (
					<div key={`${leagueAbbreviation}-${index}`} className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3">
						<h3 className="px-1 pb-2 text-sm font-black uppercase tracking-wide text-(--text-primary)">
							{title}
						</h3>

						{/* Column headers */}
						<div className={`grid ${rowTemplate} gap-x-2 px-3 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-(--text-secondary)`}>
							<span>Team</span>
							<span className="text-center">Record</span>
							<span className="text-right">GB</span>
							{showPoints && <span className="text-right">Pts</span>}
						</div>

						{/* Team bars */}
						<div className="space-y-1.5">
							{standing.team_records?.map((record) => {
								const isoCountryCode = countryCodeForTeam(selectedSportId || 0, record.team.abbreviation || record.team.name);
								const backgroundColor = record.team.primary_color || "var(--background-quaternary)";
								const isSelected = selectedTeamId != null && record.team.id === selectedTeamId;
								return (
									<div
										key={record.team.id}
										onClick={() => onTeamSelect?.(record.team)}
										title="View team roster below"
										className={`
											grid ${rowTemplate} gap-x-2 items-center
											rounded-lg border border-black/70 px-3 py-2
											cursor-pointer transition-[filter] hover:brightness-60
											${isSelected ? 'ring-2 ring-(--text-primary)' : ''}
										`}
										style={{
											backgroundColor,
											color: getContrastColor(backgroundColor),
										}}
									>
										<span className="flex items-center gap-1.5 font-black tracking-wide truncate">
											{isoCountryCode && (
												<ReactCountryFlag
													countryCode={isoCountryCode}
													svg
													style={{
														width: '1.1em',
														height: '1.1em',
													}}
												/>
											)}
											{record.team.abbreviation || record.team.name}
										</span>
										<span className="text-center font-bold tabular-nums">
											{record.league_record.wins}-{record.league_record.losses}
										</span>
										<span className="text-right font-bold tabular-nums">
											{formatGamesBack(record.games_back)}
										</span>
										{showPoints && (
											<span className="text-right font-bold tabular-nums">
												{record.showdown_points != null ? record.showdown_points : '-'}
											</span>
										)}
									</div>
								);
							})}
						</div>
					</div>
				);
			})}
		</div>
	);
}
