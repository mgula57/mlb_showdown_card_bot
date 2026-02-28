import ReactCountryFlag from "react-country-flag";

import { type Standings } from '../../api/mlbAPI';
import { countryCodeForTeam } from "../../functions/flags";
import { getContrastColor } from "../shared/Color";
import { useTheme } from "../shared/SiteSettingsContext";

type StandingsProps = {
	standingsEntries: [string, Standings[]][];
	selectedSportId?: number;
};

export default function Standings({ standingsEntries, selectedSportId }: StandingsProps) {
	const { isDark } = useTheme();

	return (
			<div className="sm:mt-0">
				<div className={`
					grid grid-cols-1 ${standingsEntries.length > 1 ? "xl:grid-cols-2" : ""} 
					gap-5`
				}>
					{standingsEntries.map(([leagueAbbreviation, leagueStandings]) => (
						<div key={leagueAbbreviation} className="bg-(--background-secondary) rounded-xl overflow-hidden border border-(--divider)">
							<h2 className="text-lg sm:text-xl font-semibold text-(--text-primary) bg-(--background-quaternary) px-4 py-2">
								{leagueAbbreviation}
							</h2>

							<div className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))]">
								{leagueStandings.map((leagueStanding, index) => (
									<div key={index} className="border-t border-(--divider) last:pb-1">
										{leagueStanding.division && (
											<h3 className="px-4 py-2.5 text-xs sm:text-sm font-semibold uppercase tracking-wide text-(--text-secondary)">
												{leagueStanding?.division?.name_short || leagueStanding?.division?.name}
											</h3>
										)}
										<table className="w-full text-left">
											<thead>
												<tr className="text-(--text-secondary) text-xs sm:text-sm uppercase">
													<th className="px-4 py-2.5">Team</th>
													<th className="px-4 py-2.5">Wins</th>
													<th className="px-4 py-2.5">Losses</th>
													<th className="px-4 py-2.5">Win %</th>
												</tr>
											</thead>
											<tbody>
												{leagueStanding.team_records?.map((record) => {
													const isoCountryCode = countryCodeForTeam(selectedSportId || 0, record.team.abbreviation || record.team.name);
													const darkeningMultiplier = isDark ? '70%' : '90%';
													return (
														<tr key={record.team.id} className="border-t border-(--divider) ">
															<td
																className="px-4 py-2.5"
																style={{
																	backgroundColor: `color-mix(in srgb, ${record.team.primary_color || "var(--background-quaternary)"} ${darkeningMultiplier}, black)`,
																	color: getContrastColor(record.team.primary_color || "var(--background-quaternary)"),
																}}
															>
																{isoCountryCode && (
																	<span className="mr-2">
																		<ReactCountryFlag
																			countryCode={isoCountryCode}
																			svg
																			style={{
																				width: '1em',
																				height: '1em',
																				marginRight: '0.25em',
																			}}
																		/>
																	</span>
																)}
																{record.team.abbreviation}
															</td>
															<td className="px-4 py-2.5">{record.league_record.wins}</td>
															<td className="px-4 py-2.5">{record.league_record.losses}</td>
															<td className="px-4 py-2.5">{record.league_record.percentage || '-'}</td>
														</tr>
													);
												})}
											</tbody>
										</table>
									</div>
								))}
							</div>
						</div>
					))}
				</div>
			</div>
	);
}
