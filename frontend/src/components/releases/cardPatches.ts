import { PATCHABLE_CARD_FIELDS, type ReleaseCard, type ReleaseCardPatch } from '../../api/releases';

/** Card patches by source card id: what's waiting to save. */
export type CardPatches = Map<string, ReleaseCardPatch>;

/** The patches that turn `previous` into `next`, or null when only a full save will do: a card
 *  added, removed or swapped, or a card's snapshot replaced (e.g. a chart rebuild). Fields compare
 *  by reference, which is how edits build them (`{ ...card, tags }`), so a false "changed" just
 *  sends a field again. */
export function cardPatchesBetween(previous: ReleaseCard[], next: ReleaseCard[]): CardPatches | null {
    const previousById = new Map(previous.map(card => [card.source_card_id, card]));
    if (previousById.size !== previous.length || next.length !== previous.length) return null;
    const patches: CardPatches = new Map();
    for (const card of next) {
        const before = card.source_card_id ? previousById.get(card.source_card_id) : undefined;
        if (!card.source_card_id || !before || before.card_snapshot !== card.card_snapshot || before.source_card_type !== card.source_card_type) {
            return null;
        }
        const changed = PATCHABLE_CARD_FIELDS.filter(field => before[field] !== card[field]);
        if (changed.length === 0) continue;
        patches.set(card.source_card_id, {
            source_card_id: card.source_card_id,
            ...Object.fromEntries(changed.map(field => [field, card[field]])),
        });
    }
    return patches;
}

/** `later`'s fields on top of `earlier`'s, card by card. */
export function mergeCardPatches(earlier: CardPatches, later: CardPatches): CardPatches {
    const merged: CardPatches = new Map(earlier);
    for (const [id, patch] of later) merged.set(id, { ...merged.get(id), ...patch });
    return merged;
}
