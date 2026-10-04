/**
 * Small "ADV" pill pinned to a card's bottom edge, paired with the `card-advantage` glow class on
 * the card itself. Shared by `CardItem` and `CardItemCompact` so both flag the winner of a sim
 * plate appearance's advantage roll the same way. The parent must be `relative`.
 */
export default function AdvantageBadge() {
    return (
        <span
            aria-label="Won the advantage"
            className="pointer-events-none absolute -bottom-2 left-1/2 z-10 -translate-x-1/2 rounded-full bg-(--advantage) px-1.5 py-px text-[8px] font-black uppercase leading-none tracking-wider text-black shadow-sm"
        >
            ADV
        </span>
    );
}
