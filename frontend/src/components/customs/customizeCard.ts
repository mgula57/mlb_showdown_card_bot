/**
 * @fileoverview Bridges any card view (CardDetail) to the Custom Card Builder.
 *
 * The card is handed over via React Router location state so the builder can prefill its form
 * (and preview) without re-fetching. Kept separate from CustomCardBuilder.tsx so CardDetail can
 * import it without a circular dependency (the builder renders CardDetail).
 */

import { useNavigate } from 'react-router-dom';
import type { ShowdownBotCard } from '../../api/showdownBotCard';
import type { CustomCardFormState } from './CustomCardBuilder';

/** Location state passed to `/customs` to prefill the builder from an existing card */
export type CustomizeCardRouteState = {
    customizeCard: ShowdownBotCard;
};

/** Stats period types the builder form supports (excludes PROJECTED/REPLACEMENT) */
const FORM_STATS_PERIOD_TYPES = ['REGULAR', 'POST', 'DATES', 'SPLIT'];

/**
 * Maps a generated card back to the builder form inputs that would reproduce it.
 * Only returns fields that have a value, so the result can be spread over `FORM_DEFAULTS`.
 */
export const formInputsFromCard = (card: ShowdownBotCard): Partial<CustomCardFormState> => {
    const period = card.stats_period;
    const year = String(period?.year ?? card.year);
    const isMlbApiYear = parseInt(year, 10) >= 2026; // 2026+ splits are keyed by MLB API situation code
    const statsPeriodType = period && FORM_STATS_PERIOD_TYPES.includes(period.type) ? period.type : 'REGULAR';

    const inputs: Partial<CustomCardFormState> = {
        name: card.name,
        player_id: card.bref_id || null,
        player_type_override: card.player_type_override?.toUpperCase(),
        year,
        stats_period_type: statsPeriodType,
        start_date: statsPeriodType === 'DATES' ? period?.start_date : null,
        end_date: statsPeriodType === 'DATES' ? period?.end_date : null,
        split: statsPeriodType === 'SPLIT' ? ((isMlbApiYear ? period?.situation_code : null) ?? period?.split) : null,
        league: period?.league ?? undefined,
        team_selection: period?.team_selection ?? undefined,
        disable_display_text_on_card: period?.disable_display_text_on_card ?? undefined,
        expansion: card.image?.expansion ?? undefined,
        edition: card.image?.edition ?? undefined,
        image_parallel: card.image?.parallel ?? undefined,
        chart_version: card.chart_version ? String(card.chart_version) : undefined,
    };

    // Drop empty values so they don't clobber form defaults when spread
    return Object.fromEntries(
        Object.entries(inputs).filter(([, value]) => value !== undefined)
    ) as Partial<CustomCardFormState>;
};

/** Returns a callback that opens the Custom Card Builder prefilled with the given card */
export const useCustomizeCard = () => {
    const navigate = useNavigate();
    return (card: ShowdownBotCard) => {
        const state: CustomizeCardRouteState = { customizeCard: card };
        navigate('/customs', { state });
    };
};
