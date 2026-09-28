/**
 * @fileoverview Client-side profanity check for user-submitted team names/abbreviations.
 * This is instant feedback only — the backend (mlb_showdown_bot/api/utils/profanity_filter.py)
 * is the real enforcement point and re-checks on every create/update, since this check is
 * trivially bypassed by calling the API directly.
 */
import * as leoProfanity from 'leo-profanity';

export const containsProfanity = (text: string | null | undefined): boolean =>
    !!text && leoProfanity.check(text);
