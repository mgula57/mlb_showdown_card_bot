/**
 * @fileoverview Two-way (TWP) card rules shared by the builder and every card view.
 *
 * A two-way card is the player's hitting card with his full pitching card nested in `two_way`, and
 * `total_points` holding the sum. Mirrors `TwoWayCardImage.SUPPORTED_SETS` /
 * `UNSUPPORTED_PARALLELS_00_01` in core/card/two_way_image.py: keep both in sync.
 */

import type { ShowdownBotCard } from '../api/showdownBotCard';
import { hasVariableSpeedSet } from '../functions/showdownSets';

/** Sets with a two-way card layout */
export const TWO_WAY_SETS: ReadonlySet<string> = new Set(['2000', '2001', 'CLASSIC', '2002', '2003', '2004', '2005', 'EXPANDED']);

/** Parallels the 2000/2001 split layout can't show */
const UNSUPPORTED_PARALLELS_00_01 = ['BREAKOUT', 'BOOSTER'];

/** Image sources a two-way card can use. One uploaded/linked photo can't fill both halves. */
export const TWO_WAY_IMAGE_SOURCES: ReadonlySet<string> = new Set(['AUTO']);

export const supportsTwoWay = (set: string): boolean => TWO_WAY_SETS.has(set);

/** Parallels a two-way card can't use in the given set */
export const twoWayExcludedParallels = (set: string): string[] =>
    hasVariableSpeedSet([set]) ? UNSUPPORTED_PARALLELS_00_01 : [];

/** Readable list of the supported sets, e.g. for a disabled control's tooltip */
export const TWO_WAY_SETS_LABEL = [...TWO_WAY_SETS].join(', ');

export type TwoWayCard = ShowdownBotCard & { two_way: ShowdownBotCard };

export const isTwoWayCard = (card: ShowdownBotCard | null | undefined): card is TwoWayCard =>
    !!card?.two_way;

export type TwoWaySide = 'hitting' | 'pitching';

/** The card for one side of a two-way card. Regular cards return themselves. */
export const twoWaySide = (card: ShowdownBotCard, side: TwoWaySide): ShowdownBotCard =>
    side === 'pitching' && card.two_way ? card.two_way : card;

/** Points shown for a card: the hitting + pitching total on two-way cards */
export const displayPoints = (card: ShowdownBotCard): number =>
    card.two_way ? (card.total_points ?? card.points + card.two_way.points) : card.points;

// ----------------------------------
// Builder versions
// ----------------------------------

/** Which card a two-way player's search pick builds */
export type PlayerVersion = 'TWO_WAY' | 'HITTER' | 'PITCHER';

export const PLAYER_VERSION_LABELS: Record<PlayerVersion, string> = {
    TWO_WAY: 'Two-Way',
    HITTER: 'Hitter',
    PITCHER: 'Pitcher',
};

/** The backend reads a hitter/pitcher choice from a "(HITTER)"/"(PITCHER)" suffix on the name */
const TYPE_SUFFIX_PATTERN = /\s*\((hitter|hitting|pitcher|pitching)\)/gi;

/** Form fields for a version. Two-way keeps the HITTER override (the hitting side is the main card)
 *  and a plain name, since the backend builds each side with its own suffix. */
export const versionFormFields = (name: string, version: PlayerVersion): { name: string; player_type_override: string; two_way: boolean } => {
    const baseName = name.replace(TYPE_SUFFIX_PATTERN, '').trim();
    return {
        name: version === 'TWO_WAY' ? baseName : `${baseName} (${version})`,
        player_type_override: version === 'PITCHER' ? 'PITCHER' : 'HITTER',
        two_way: version === 'TWO_WAY',
    };
};

/** The form's version. Null for a hand-typed name with no version picked yet (the backend picks the type). */
export const versionFromForm = (form: { player_type_override?: string | null; two_way?: boolean }): PlayerVersion | null => {
    if (form.two_way) return 'TWO_WAY';
    const override = form.player_type_override?.toUpperCase();
    return override === 'PITCHER' || override === 'HITTER' ? override : null;
};
