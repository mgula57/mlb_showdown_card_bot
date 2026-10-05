/**
 * @fileoverview A player marker built from the shared compact card, so on-field players (and the
 * sim's runner readout) read consistently with the rest of the app.
 */
import { resolveCardKey } from "../../domain/players";
import type { PlayerRef } from "../../domain/game";
import type { ShowdownBotCardAPIResponse, ShowdownBotCardCompact } from "../../api/showdownBotCard";
import { CardItemCompact, CardItemCompactFromCard } from "../cards/CardItemCompact";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

/** Border accent distinguishing offense from defense — a translucent version of the same
 * live/divider colors the rest of the field UI already leans on. */
const TONE_ACCENT: Record<"offense" | "defense", string | undefined> = {
    offense: "color-mix(in srgb, var(--live) 60%, transparent)",
    defense: undefined,
};

/** A player marker on the field, built from the shared compact card so it reads consistently
 * with the rest of the app. Falls back to an unnamed dot for runners the source can only report
 * as "occupied" (the sim tracks base state, not who's standing there), and to a name-only
 * placeholder card while the real one is still being fetched. */
export default function FieldMarker({
    player, role, cardMap, onCardSelect, isLoadingCards, tone,
    hideCommand = false, hideTeamPoints = false, detailStat1Category, liveIp, fieldPosition, backgroundSettings, hasAdvantage,
}: {
    player: PlayerRef;
    role: "H" | "P";
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
    tone: "offense" | "defense";
    hideCommand?: boolean;
    /** Hide the team/points row, leaving just the name and detail stat. Defaults to whatever hideCommand is, since the two go together on these lean field chips. */
    hideTeamPoints?: boolean;
    detailStat1Category?: "defense" | "speed" | "hr";
    liveIp?: string | number | null;
    fieldPosition?: string;
    /** Optional background settings for the card container, e.g., "bg-secondary" */
    backgroundSettings?: string;
    hasAdvantage?: boolean;
}) {
    if (!player.name) {
        return <span className="block h-3 w-3 rotate-45 rounded-xs bg-(--live) shadow-sm" />;
    }

    const response = cardMap[resolveCardKey(player.id, role) ?? ""];
    const accentColor = TONE_ACCENT[tone];
    const showDetails = detailStat1Category != null;

    const placeholderCard: ShowdownBotCardCompact = {
        id: `${player.id}-${role}`,
        name: player.name,
        year: "----",
        set: "---",
        points: 0,
        command: 0,
        outs: 0,
        is_pitcher: role === "P",
        color_primary: null,
        color_secondary: null,
        team: null,
        positions_and_defense_string: null,
        positions_and_defense: null,
        ip: null,
        speed: null,
        hand: null,
        hr_range: null,
        source: "BOT",
    };

    return (
        <div className="w-18 @[380px]:w-24 @[520px]:w-30 @[650px]:w-40">
            {response?.card ? (
                <CardItemCompactFromCard
                    card={response.card}
                    onClick={() => onCardSelect?.(response)}
                    hideCommand={hideCommand}
                    hideTeamPoints={hideTeamPoints}
                    hideDetails={!showDetails}
                    detailStat1Category={detailStat1Category}
                    liveIp={liveIp}
                    fieldPosition={fieldPosition}
                    accentColor={accentColor}
                    backgroundSettings={backgroundSettings}
                    hasAdvantage={hasAdvantage}
                />
            ) : (
                <CardItemCompact
                    card={placeholderCard}
                    isLoading={isLoadingCards}
                    hideCommand={hideCommand}
                    hideTeamPoints={hideTeamPoints}
                    hideDetails
                    accentColor={accentColor}
                    backgroundSettings={backgroundSettings}
                    hasAdvantage={hasAdvantage}
                />
            )}
        </div>
    );
}
