/**
 * @fileoverview Where an MLB season stands on its calendar: upcoming, in progress, or over.
 */
import type { Season } from '../api/mlbAPI';

/** A season calendar date (YYYY-MM-DD) as local time, at the start or end of that day. */
const localDate = (isoDate: string, endOfDay = false): Date => new Date(`${isoDate}T${endOfDay ? '23:59:59' : '00:00:00'}`);

const isValid = (date: Date): boolean => !Number.isNaN(date.getTime());

/** Over once its end date has passed. Schedule browsing only applies before then. */
export const isSeasonOver = (season: Season | null | undefined): boolean => {
    if (!season?.season_end_date) return false;
    const end = localDate(season.season_end_date, true);
    return isValid(end) && end < new Date();
};

/** Before Opening Day. An upcoming season plays on the prior year's cards and current 40-man rosters. */
export const isSeasonUpcoming = (season: Season | null | undefined): boolean => {
    if (!season?.regular_season_start_date) return false;
    const start = localDate(season.regular_season_start_date);
    return isValid(start) && new Date() < start;
};

/** Between Opening Day and the end of the World Series. */
export const isSeasonInProgress = (season: Season | null | undefined): boolean => {
    if (!season || season.postseason_complete) return false;
    return !isSeasonUpcoming(season) && !isSeasonOver(season) && !!season.regular_season_start_date;
};

/** The season a page opens on: the newest one that has started. An upcoming season is opt-in. */
export const defaultSeason = (seasons: Season[]): Season | undefined =>
    seasons.find((season) => !isSeasonUpcoming(season)) ?? seasons[0];
