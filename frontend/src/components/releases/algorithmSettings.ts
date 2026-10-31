/**
 * @fileoverview The Algorithm tab's settings: defaults and parsing the last-used config back out of an
 * edition's `attributes`. Shared by AlgorithmBuilder and EditionBuilder (whose Manual search starts
 * from the same seasons).
 */

import type { AlgorithmConfig, AlgorithmPlayerTypeDistribution, AlgorithmSelectionWeights, AlgorithmTeamMinimums } from '../../api/releases';

export const DEFAULT_PLAYER_TYPE_DISTRIBUTION: AlgorithmPlayerTypeDistribution = {
    hitters_percentage: 0.65,
    starters_percentage: 0.20,
    relievers_percentage: 0.15,
};

/** Mirrors `SelectionWeights` defaults on the backend. */
export const DEFAULT_SELECTION_WEIGHTS: AlgorithmSelectionWeights = {
    quality: 1,
    volume: 0.5,
    team_balance: 0.75,
    points_fit: 1,
    career: 0,
};

/** Career WAR minimum when Legends is first turned on — roughly a borderline Hall of Fame career. */
export const DEFAULT_LEGEND_MIN_CAREER_WAR = 60;

export const DEFAULT_TEAM_MINIMUMS: AlgorithmTeamMinimums = { hitters: 0, starters: 0, relievers: 0 };

export const CUSTOM_TEMPLATE_ID = 'custom';
export const ALL_STARS_TEMPLATE_ID = 'all-stars';
export const EXPANSION_TEMPLATE_ID = 'expansion';

/** Everything a template resets: who's eligible, what the set is made of and how players are
 * picked. Years, sets, size (unless the template sets them) and card options stay the user's own. */
export const SELECTION_DEFAULTS = {
    min_games_hitters: 60,
    min_ip_starters: 75,
    min_ip_relievers: 30,
    player_type_distribution: DEFAULT_PLAYER_TYPE_DISTRIBUTION,
    include_all_stars: true,
    include_award_winners: true,
    all_stars_only: false,
    legend_min_career_war: null,
    point_buckets: [],
    selection_weights: DEFAULT_SELECTION_WEIGHTS,
    position_targets: [],
    unique_players: true,
    team_weighting: 'EVEN',
    team_minimums: DEFAULT_TEAM_MINIMUMS,
    other_editions_rule: 'ALLOW',
} satisfies Partial<AlgorithmConfig>;

export function defaultAlgorithmConfig(defaultShowdownSet?: string | null): AlgorithmConfig {
    return {
        set_size: 100,
        years: String(new Date().getFullYear()),
        showdown_sets: defaultShowdownSet ? [defaultShowdownSet] : [],
        pitcher_showdown_sets: null,
        ...SELECTION_DEFAULTS,
        variable_speed: false,
        template_id: CUSTOM_TEMPLATE_ID,
    };
}

/** Every set the config's cards can come from, hitters and pitchers combined. */
export function allShowdownSets(config: AlgorithmConfig): string[] {
    return [...new Set([...config.showdown_sets, ...(config.pitcher_showdown_sets ?? [])])];
}

/** Seasons covered by a years string ("2023", "2000-2004", "2006+2014+2008"). */
function countSeasons(years: string): number {
    const range = years.match(/^\s*(\d{4})\s*-\s*(\d{4})\s*$/);
    if (range) return Math.max(1, Number(range[2]) - Number(range[1]) + 1);
    return Math.max(1, (years.match(/\d{4}/g) ?? []).length);
}

/** Rough run time in seconds: a fixed setup cost plus time per season per showdown set.
 *  A heuristic, not a measurement - tune the constants against real runs. */
export function estimateAlgorithmSeconds(config: AlgorithmConfig): number {
    const SETUP_SECONDS = 5;
    const SECONDS_PER_SEASON_SET = 1.5;
    const seconds = SETUP_SECONDS + countSeasons(config.years) * Math.max(1, allShowdownSets(config).length) * SECONDS_PER_SEASON_SET;
    return Math.round(seconds / 5) * 5 || 5;
}

/** Single low-point bucket fields that older editions saved before `point_buckets` existed. */
type LegacyLowPointSettings = {
    ideal_low_point_percentage?: number | null;
    low_point_max_points?: number;
};

/** Mirrors `parseNumberingSettings` in EditionBuilder.tsx — reads the last-used algorithm config
 * back out of the edition's free-form `attributes` blob. */
export function parseAlgorithmSettings(attributes: Record<string, unknown>, defaultShowdownSet?: string | null): AlgorithmConfig {
    const defaults = defaultAlgorithmConfig(defaultShowdownSet);
    const raw = attributes.algorithm as (Partial<AlgorithmConfig> & LegacyLowPointSettings) | undefined;
    if (!raw || typeof raw !== 'object') return defaults;
    const { ideal_low_point_percentage, low_point_max_points, ...rest } = raw;
    return {
        ...defaults,
        ...rest,
        // Editions saved before templates were persisted: all-star mode can only come from the All-Stars template
        template_id: raw.template_id ?? (raw.all_stars_only ? ALL_STARS_TEMPLATE_ID : CUSTOM_TEMPLATE_ID),
        player_type_distribution: {
            ...defaults.player_type_distribution!,
            ...(raw.player_type_distribution || {}),
        },
        selection_weights: {
            ...defaults.selection_weights!,
            ...(raw.selection_weights || {}),
        },
        team_minimums: {
            ...DEFAULT_TEAM_MINIMUMS,
            ...(raw.team_minimums || {}),
        },
        // Editions saved before multi-bucket support stored a single 10-max bucket
        point_buckets: raw.point_buckets
            ?? (ideal_low_point_percentage != null
                ? [{ min_points: 10, max_points: low_point_max_points ?? 50, percentage: ideal_low_point_percentage }]
                : []),
    };
}
