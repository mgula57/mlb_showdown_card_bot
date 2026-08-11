import type { GameBoxscoreDetail, BoxscoreDecisionPerson } from "../../../api/mlbAPI";
import type { ShowdownBotCardAPIResponse } from "../../../api/showdownBotCard";
import { cardKey } from "../../../domain/players";
import { CardItemFromCard, CardItemSkeleton } from "../../cards/CardItem";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

export default function Decisions({ boxscore, cardMap, onCardSelect, isLoadingCards }: { boxscore: GameBoxscoreDetail; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isLoadingCards?: boolean }) {
    const { winner, loser, save: saveDecision } = boxscore.decisions;

    // Find the pitcher note (e.g. "(W, 1-0)") for each decision pitcher
    const findPitcherNote = (pitcherId?: number): string => {
        if (!pitcherId) return "";
        for (const side of ["away", "home"] as const) {
            const pitcher = boxscore.teams[side].pitching.find((p) => p.id === pitcherId);
            if (pitcher?.stats.note) return pitcher.stats.note;
        }
        return "";
    };

    // Standarize the rendering of each decision item (W/L/S) since they all follow the same pattern
    const decisionItem = (color: string, label: string, pitcher: BoxscoreDecisionPerson, card?: ShowdownBotCardAPIResponse) => (

        <div className="space-y-1">
            <div className="flex items-center gap-1.5">
                <span className={`font-bold ${color}`}>{label}:</span>
                <span className="font-semibold text-(--primary)">{pitcher?.full_name}</span>
                <span className="text-(--secondary) text-xs">{findPitcherNote(pitcher?.id)}</span>

                {card && card.in_season_trends?.pts_change.day != null && card.in_season_trends.pts_change.day !== 0 && (
                    <span className={`text-[9px] font-bold leading-none ${card.in_season_trends.pts_change.day > 0 ? 'text-(--green)' : 'text-(--red)'}`}>
                        {card.in_season_trends.pts_change.day > 0 ? '▲' : '▼'}{Math.abs(card.in_season_trends.pts_change.day)} PTS
                    </span>
                )}
            </div>
            {isLoadingCards && !card ? (
                <CardItemSkeleton className="w-full" />
            ) : (
                <CardItemFromCard card={card?.card} className="w-full" onClick={card ? () => onCardSelect?.(card) : undefined} />
            )}
        </div>
    );

    if (!winner && !loser) return null;

    const winnerCardData = winner?.id ? cardMap[cardKey(winner.id, 'P')] : undefined;
    const loserCardData = loser?.id ? cardMap[cardKey(loser.id, 'P')] : undefined;
    const saveCardData = saveDecision?.id ? cardMap[cardKey(saveDecision.id, 'P')] : undefined;

    return (
        <div
            className="
                flex flex-col
                md:grid md:grid-cols-2
                p-3 gap-x-6 gap-y-2
                rounded-xl border border-(--divider) bg-(--background-secondary)
                text-sm
            ">
                {winner && decisionItem('text-(--green)', 'W', winner, winnerCardData)}
                {loser && decisionItem('text-(--red)', 'L', loser, loserCardData)}
                {saveDecision && decisionItem('text-blue-400', 'SV', saveDecision, saveCardData)}
        </div>
    );
}
