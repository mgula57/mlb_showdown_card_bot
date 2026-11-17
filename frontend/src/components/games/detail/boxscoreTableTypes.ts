/**
 * @fileoverview The team shape `BattingTable` and `PitchingTable` draw: the MLB feed's
 * `BoxscoreTeamData`, with player ids widened so a sim's card ids (strings) fit too
 * (see `SimBoxScorePanels`).
 */
import type { BoxscoreBatter, BoxscorePitcher, BoxscoreTeamData } from "../../../api/mlbAPI";

type WithAnyId<T> = Omit<T, "id"> & { id: number | string };

export type BoxscoreTableBatter = WithAnyId<BoxscoreBatter>;
export type BoxscoreTablePitcher = WithAnyId<BoxscorePitcher>;
export type BoxscoreTableTeam = Omit<BoxscoreTeamData, "batting" | "pitching"> & {
    batting: BoxscoreTableBatter[];
    pitching: BoxscoreTablePitcher[];
};
