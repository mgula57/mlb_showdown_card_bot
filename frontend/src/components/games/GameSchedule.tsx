import ReactCountryFlag from "react-country-flag";

import { countryCodeForTeam } from "../../functions/flags";
import { type GameScheduled } from "../../api/mlbAPI";
import { CardItemCompact } from "../cards/CardItemCompact";

type GameScheduleProps = {
    games: GameScheduled[];
    dateLabel: string;
    description?: string;
    sportId?: number;
};

const formatGameTime = (gameDate?: string): string => {
    if (!gameDate) {
        return "TBD";
    }

    const parsedDate = new Date(gameDate);
    if (Number.isNaN(parsedDate.getTime())) {
        return "TBD";
    }

    return new Intl.DateTimeFormat(undefined, {
        hour: 'numeric',
        minute: '2-digit',
    }).format(parsedDate);
};

export default function GameSchedule({ games, dateLabel, description, sportId }: GameScheduleProps) {
    if (!games.length) {
        return null;
    }

    return (
        <div className="space-y-3">
            <div>
                <div className="text-lg font-extrabold text-(--text-primary)">{dateLabel}</div>
                {description && (
                    <div className="text-sm font-semibold text-(--text-secondary)">{description}</div>
                )}
            </div>

            <div className="grid grid-cols-[repeat(auto-fit,minmax(270px,1fr))] gap-4">
                {games.map((game) => {
                    const awayTeam = game.teams?.away?.team;
                    const homeTeam = game.teams?.home?.team;
                    const awayAbbr = awayTeam?.abbreviation || awayTeam?.name || "AWAY";
                    const homeAbbr = homeTeam?.abbreviation || homeTeam?.name || "HOME";
                    const awayScore = game.teams?.away?.score;
                    const homeScore = game.teams?.home?.score;
                    const isFinal = game.status?.coded_game_state === 'F' || game.status?.status_code === 'F';
                    const hasStarted = game.status?.coded_game_state === 'F' || game.status?.coded_game_state === 'I' || game.status?.coded_game_state === 'P' || game.status?.coded_game_state === 'L' || game.status?.coded_game_state === 'M' || game.status?.coded_game_state === 'D';

                    const awayCountryCode = countryCodeForTeam(sportId || 0, awayAbbr);
                    const homeCountryCode = countryCodeForTeam(sportId || 0, homeAbbr);

                    const awayRecord = game.teams?.away?.league_record;
                    const homeRecord = game.teams?.home?.league_record;
                    const awayPitcherCard = game.teams?.away?.probable_pitcher?.card;
                    const homePitcherCard = game.teams?.home?.probable_pitcher?.card;

                    return (
                        <div
                            key={game.game_pk}
                            className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-hidden p-3"
                        >
                            <div className="bg-(--background-primary) text-(--text-primary) rounded-md px-3 py-1 text-center text-sm font-bold">
                                {(game.series_description || game.description || "Game")}
                                {game.series_game_number ? ` | Game ${game.series_game_number}` : ""}
                            </div>

                            <div className="py-2 text-md font-extrabold text-(--text-primary)">
                                {isFinal && (
                                    <><span>FINAL</span></>
                                )}
                                {!isFinal && hasStarted && (
                                    <span>{game.status?.detailed_state}</span>
                                )}
                                {!isFinal && !hasStarted && (
                                    <span>{formatGameTime(game.game_date)}</span>
                                )}
                            </div>

                            <div className="border-t border-(--divider)" />

                            <div className="space-y-2 py-2">
                                <div className="flex items-center justify-between gap-3">
                                    <div className="flex items-center gap-2 min-w-0">
                                        {sportId === 51 && awayCountryCode && (
                                            <ReactCountryFlag countryCode={awayCountryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                                        )}
                                        <span className="text-lg font-black text-(--text-primary)">{awayAbbr}</span>
                                        {awayRecord && (
                                            <span className="text-[11px] font-semibold text-(--text-secondary)">{awayRecord.wins ?? 0} - {awayRecord.losses ?? 0}</span>
                                        )}
                                    </div>
                                    {hasStarted && awayScore != null && (
                                        <span className="text-lg font-black text-(--text-primary)">{awayScore}</span>
                                    )}
                                </div>

                                <div className="flex items-center justify-between gap-3">
                                    <div className="flex items-center gap-2 min-w-0">
                                        {sportId === 51 && homeCountryCode && (
                                            <ReactCountryFlag countryCode={homeCountryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                                        )}
                                        <span className="text-lg font-black text-(--text-primary)">{homeAbbr}</span>
                                        {homeRecord && (
                                            <span className="text-[12px] font-semibold text-(--text-secondary)">{homeRecord.wins ?? 0} - {homeRecord.losses ?? 0}</span>
                                        )}
                                    </div>
                                    {hasStarted && homeScore != null && (
                                        <span className="text-lg font-black text-(--text-primary)">{homeScore}</span>
                                    )}
                                </div>
                            </div>

                            {(awayPitcherCard || homePitcherCard) && (
                                <>
                                    <div className="border-t border-(--divider) my-2" />
                                    <div className="flex justify-between items-center">
                                        <div className="flex gap-1 items-center">
                                            {sportId === 51 && awayCountryCode && (
                                                <ReactCountryFlag countryCode={awayCountryCode} svg style={{ width: '1.0em', height: '1.0em' }} />
                                            )}
                                            <span className="text-sm font-black text-(--text-primary)">{awayAbbr}</span>
                                        </div>
                                        <span className="text-[10px]">Probables</span>
                                        <div className="flex gap-1 items-center">
                                            {sportId === 51 && homeCountryCode && (
                                                <ReactCountryFlag countryCode={homeCountryCode} svg style={{ width: '1.0em', height: '1.0em' }} />
                                            )}
                                            <span className="text-sm font-black text-(--text-primary)">{homeAbbr}</span>
                                        </div>
                                    </div>
                                    <div className="pt-1 grid grid-cols-1 sm:grid-cols-2 gap-2">
                                        <CardItemCompact
                                            card={awayPitcherCard}
                                        />
                                        <CardItemCompact
                                            card={homePitcherCard}
                                        />
                                    </div>
                                </>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
