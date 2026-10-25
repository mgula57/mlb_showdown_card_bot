/**
 * @fileoverview Post-game recap laid over the faded field once a game (real or simulated) is
 * final: the Player of the Game up top, then the pitchers of record. Reads only `GameView`, so the
 * caller decides when it's safe to show — a replay cursor short of the final out must not get it.
 */
import type { ReactNode } from "react";
import { FaStar } from "react-icons/fa6";

import type { GameView, PlayerRef } from "../../../domain/game";
import type { ShowdownBotCardAPIResponse } from "../../../api/showdownBotCard";
import { playerOfTheGame } from "../../../domain/gameSummary";
import { resolveCardKey } from "../../../domain/players";
import { CardItemFromCard, CardItemSkeleton } from "../../cards/CardItem";
import { Eyebrow } from "../../shared/Eyebrow";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

type GameFinalSummaryProps = {
    game: GameView;
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
    className?: string;
};

export default function GameFinalSummary({ game, cardMap, onCardSelect, isLoadingCards, className = "" }: GameFinalSummaryProps) {
    const potg = playerOfTheGame(game);
    const { winner, loser, save } = game.decisions ?? {};
    if (!potg && !winner && !loser) return null;

    const pitchingLine = (ref?: PlayerRef) =>
        ref ? [...(game.away.boxscore?.pitching ?? []), ...(game.home.boxscore?.pitching ?? [])].find((p) => String(p.id) === String(ref.id)) : undefined;

    const winningTeam = potg ? game[potg.side].team : undefined;
    const accent = winningTeam?.primaryColor ?? "var(--gold)";

    /* Every entry — Player of the Game and each decision — sits in the same tile, so they share
       one padding and read as a set; only the left accent and an optional heading differ. */
    const recapPlayer = (key: string, label: string, labelClass: string, accentColor: string, ref: PlayerRef, role: "H" | "P", detail?: string, heading?: ReactNode) => {
        const card = cardMap[resolveCardKey(ref.id, role) ?? ""];
        return (
            <div
                key={key}
                style={{ borderLeftColor: accentColor }}
                className="min-w-0 space-y-1 rounded-card border border-l-4 border-(--divider) bg-(--background-secondary) p-2.5"
            >
                {heading}
                <div className="flex items-baseline gap-1.5 text-sm min-w-0">
                    {label && <span className={`font-display-upright uppercase shrink-0 ${labelClass}`}>{label}</span>}
                    <span className="font-semibold text-(--primary) truncate">{ref.name}</span>
                    {detail && <span className="text-xs text-(--secondary) shrink-0">{detail}</span>}
                </div>
                {isLoadingCards && !card ? (
                    <CardItemSkeleton className="w-full" />
                ) : (
                    <CardItemFromCard card={card?.card} className="w-full" onClick={card ? () => onCardSelect?.(card) : undefined} />
                )}
            </div>
        );
    };

    const decisions = [
        winner && recapPlayer("W", "W", "text-(--green)", "var(--green)", winner, "P", pitchingLine(winner)?.note),
        loser && recapPlayer("L", "L", "text-(--red)", "var(--red)", loser, "P", pitchingLine(loser)?.note),
        save && recapPlayer("SV", "SV", "text-(--showdown-blue)", "var(--showdown-blue)", save, "P", pitchingLine(save)?.note),
    ].filter(Boolean);

    return (
        <div
            className={`@container mx-2 rounded-card border border-(--divider) bg-(--background-primary) shadow-overlay p-3 space-y-3 ${className}`}
        >
            <Eyebrow className="block">Game Recap</Eyebrow>

            {potg && recapPlayer(
                "POTG", "", "", accent, { id: potg.line.id, name: potg.line.name }, potg.role, potg.line.summary,
                <div className={`flex items-center gap-1.5 ${CAPS_LABEL_CLASS} text-(--text-primary)`}>
                    <FaStar className="text-(--gold)" />
                    Player of the Game
                    {winningTeam && <span className="text-(--secondary) font-bold">· {winningTeam.abbreviation}</span>}
                </div>,
            )}

            {decisions.length > 0 && (
                <div className="grid gap-3 @md:grid-cols-2">
                    {decisions}
                </div>
            )}
        </div>
    );
}
