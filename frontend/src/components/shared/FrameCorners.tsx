/** Corner positions: each base is centered on the outer border's corner. */
const CORNERS = [
    '-top-[3.5px] -left-[3.5px]',
    '-top-[3.5px] -right-[3.5px]',
    '-bottom-[3.5px] -left-[3.5px]',
    '-bottom-[3.5px] -right-[3.5px]',
];

/**
 * The four "bases" on the corners of the 2001 card-back frame: small diamonds cut into the double
 * rule (see frontend/DESIGN.md, "Frames"). Drop inside any `relative` element that already draws the
 * double rule; they reach about 5px past its edge, so neighbors need a gap of at least 12px.
 */
export function FrameCorners() {
    return (
        <>
            {CORNERS.map(position => (
                <span
                    key={position}
                    aria-hidden
                    className={`pointer-events-none absolute z-10 ${position} size-1.75 rotate-45 border-[1.5px] border-(--rule-strong) bg-(--background-secondary)`}
                />
            ))}
        </>
    );
}

export default FrameCorners;
