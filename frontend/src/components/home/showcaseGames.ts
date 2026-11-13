/**
 * @fileoverview The real games the Home page's game reel replays. Each entry must have full
 * play-by-play (with `postOnFirst/Second/Third` runner identity) in the MLB feed. `season` picks
 * which year's archived cards the players use.
 */
export type ShowcaseGame = {
    gamePk: number;
    season: number;
    label: string;
};

export const SHOWCASE_GAMES: ShowcaseGame[] = [
    { gamePk: 487637, season: 2016, label: "2016 World Series · Game 7" },
    { gamePk: 9101, season: 2001, label: "2001 World Series · Game 7" },
    { gamePk: 317072, season: 2011, label: "2011 World Series · Game 6" },
    { gamePk: 22605, season: 2004, label: "2004 ALCS · Game 4" },
    { gamePk: 526515, season: 2017, label: "2017 World Series · Game 5" },
    { gamePk: 599377, season: 2019, label: "2019 World Series · Game 7" },
    { gamePk: 775296, season: 2024, label: "2024 World Series · Game 5" },
    { gamePk: 813024, season: 2025, label: "2025 World Series · Game 7" },
];
