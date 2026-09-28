/**
 * @fileoverview Manager preference — per-run, team-wide manager tendencies for the club a user
 * takes over. Mirrors `ManagerPreference` in `mlb_showdown_bot/core/simulation/models.py`: every
 * field is a 1–5 level with 3 = neutral, and a neutral profile is a no-op the engine skips.
 * Chosen in a sim setup form, never saved to the team.
 */

export type ManagerPreference = {
    /** 1 = rarely runs, 5 = runs constantly. */
    steal_aggression: number;
    /** 1 = station to station, 5 = always taking the extra base. */
    baserunning_aggression: number;
    /** 1 = quick hook, 5 = slow hook. */
    bullpen_hook: number;
    /** 1 = closer in save situations only, 5 = closer earlier / in non-save spots. */
    closer_usage: number;
};

export const NEUTRAL_MANAGER: ManagerPreference = {
    steal_aggression: 3,
    baserunning_aggression: 3,
    bullpen_hook: 3,
    closer_usage: 3,
};

export function isNeutralManager(m: ManagerPreference): boolean {
    return (
        m.steal_aggression === 3 &&
        m.baserunning_aggression === 3 &&
        m.bullpen_hook === 3 &&
        m.closer_usage === 3
    );
}

/** Sent only when non-neutral, so a plain run carries nothing extra. */
export function managerPayload(m: ManagerPreference): ManagerPreference | undefined {
    return isNeutralManager(m) ? undefined : m;
}

/** The 1–5 options for each tendency, worst→best direction, for a `FormDropdown`. */
export const MANAGER_FIELDS: {
    key: keyof ManagerPreference;
    label: string;
    options: { value: string; label: string }[];
}[] = [
    {
        key: 'steal_aggression',
        label: 'Steal aggression',
        options: [
            { value: '1', label: 'Rarely runs' },
            { value: '2', label: 'Conservative' },
            { value: '3', label: 'Balanced' },
            { value: '4', label: 'Aggressive' },
            { value: '5', label: 'Always running' },
        ],
    },
    {
        key: 'baserunning_aggression',
        label: 'Extra-base aggression',
        options: [
            { value: '1', label: 'Station to station' },
            { value: '2', label: 'Conservative' },
            { value: '3', label: 'Balanced' },
            { value: '4', label: 'Aggressive' },
            { value: '5', label: 'Takes every base' },
        ],
    },
    {
        key: 'bullpen_hook',
        label: 'Bullpen hook',
        options: [
            { value: '1', label: 'Very quick hook' },
            { value: '2', label: 'Quick hook' },
            { value: '3', label: 'Balanced' },
            { value: '4', label: 'Slow hook' },
            { value: '5', label: 'Very slow hook' },
        ],
    },
    {
        key: 'closer_usage',
        label: 'Closer usage',
        options: [
            { value: '1', label: 'Save situations only' },
            { value: '2', label: 'Mostly saves' },
            { value: '3', label: 'Balanced' },
            { value: '4', label: 'High-leverage spots' },
            { value: '5', label: "Whenever it's close" },
        ],
    },
];
