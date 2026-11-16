/**
 * @fileoverview A fielder on an expanded field: a small single-row tag showing only what matters
 * when the club is in the field. That's the name, the defensive icons, and the rating at the
 * position the player is standing at. It's lighter than `FieldMarker`'s compact card, so the
 * pitcher, the batter and the runners stay the cards that stand out.
 */
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import type { PlayerRef } from "../../domain/game";
import { resolveCardKey } from "../../domain/players";
import { getLastName } from "../../functions/names";
import CardIcon from "../cards/card_elements/CardIcon";
import { defenseAtPosition } from "../shared/DefenseUtils";
import { FieldGround } from "../shared/FieldGround";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

/** Card icons that bear on defense: Gold Glove and Rookie. */
const DEFENSE_ICONS = new Set(["G", "R"]);

export default function FielderMarker({ player, position, cardMap, onCardSelect, isLoadingCards }: {
    player: PlayerRef;
    /** The position played here, e.g. "SS", which picks the rating to show. */
    position: string;
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
}) {
    if (!player.name) {
        return <span className="block h-2.5 w-2.5 rotate-45 rounded-plate bg-(--text-primary)/50" />;
    }

    const response = cardMap[resolveCardKey(player.id, "H") ?? ""];
    const card = response?.card;
    const rating = defenseAtPosition(card?.positions_and_defense, position);
    const icons = (card?.icons ?? []).filter((icon) => DEFENSE_ICONS.has(icon));
    const isLoading = !card && isLoadingCards;

    return (
        <div className="relative isolate">
            <FieldGround />
            <button
                type="button"
                onClick={response ? () => onCardSelect?.(response) : undefined}
                disabled={!response}
                aria-label={`${player.name}, ${position}${rating == null ? "" : ` ${rating >= 0 ? "+" : ""}${rating}`}`}
                className={`
                    flex items-center gap-1 whitespace-nowrap rounded-control border border-(--divider)
                    bg-(--background-primary)/70 px-1.5 py-0.5
                    font-display-upright uppercase leading-none text-(--text-primary)
                    text-[10px] @[520px]:text-[11px] @[650px]:text-xs
                    ${response ? "cursor-pointer hover:border-(--rule-strong)" : "cursor-default"}
                    ${isLoading ? "animate-pulse" : ""}
                `}
            >
                <span className="max-w-24 truncate">{getLastName(player.name)}</span>
                {icons.map((icon) => (
                    <CardIcon key={icon} value={icon} circleSize="3" textSize={8} color="var(--text-primary)" textColor="var(--background-primary)" />
                ))}
                <span className="tabular-nums opacity-70">
                    {position}{rating == null ? "" : `${rating >= 0 ? "+" : ""}${rating}`}
                </span>
            </button>
        </div>
    );
}
