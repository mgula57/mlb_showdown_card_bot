/** The spot a card stands on over field art (`.field-ground` in index.css): a patch of shade under
 *  the card's bottom edge, so it reads as standing on the field rather than pasted over it. Render
 *  it first inside an `isolate` wrapper that also holds the card, so it sits behind the card and
 *  only the half below the card's edge shows. */
export function FieldGround() {
    return <span aria-hidden className="field-ground" />;
}
