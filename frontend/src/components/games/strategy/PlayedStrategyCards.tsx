/**
 * @fileoverview The strategy cards on the table for one side of the matchup, sitting on that
 * player's card: the batting club's on the hitter, the fielding club's on the pitcher. Each new one
 * drops in as it's played (`strategy-land`), so the matchup shows everything bearing on the at-bat.
 */
import type { PlayedStrategyCard } from "../../../domain/strategy";
import { Plate } from "../../shared/Plate";
import { StrategyCardFace } from "./StrategyCardFace";

export default function PlayedStrategyCards({ cards }: { cards: PlayedStrategyCard[] }) {
    if (cards.length === 0) return null;
    return (
        <div className="flex flex-wrap gap-1" aria-label="Strategy cards in play">
            {cards.map(({ card, isCarriedOver }) => (
                <StrategyCardFace
                    key={card.id}
                    card={card}
                    size="mini"
                    className="strategy-land max-w-full"
                    tag={isCarriedOver && <Plate variant="outline" size="xs" className="shrink-0">In play</Plate>}
                />
            ))}
        </div>
    );
}
