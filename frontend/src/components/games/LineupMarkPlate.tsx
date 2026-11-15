/**
 * @fileoverview The plate beside a marked batting line's name: AB for the batter at the plate, Next
 * for the hitter who leads off when the club in the field comes up.
 */
import { Plate } from "../shared/Plate";
import type { LineupMark } from "./lineupUpContext";

export default function LineupMarkPlate({ mark }: { mark: LineupMark }) {
    if (!mark) return null;
    return mark === "batter"
        ? <Plate variant="red" size="xs" title="At bat">AB</Plate>
        : <Plate variant="outline" size="xs" title="Leads off when this club bats next">Next</Plate>;
}
