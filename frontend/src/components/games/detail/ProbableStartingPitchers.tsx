import type { GameBoxscoreDetail, BoxscoreTeamData } from "../../../api/mlbAPI";
import type { ShowdownBotCardAPIResponse } from "../../../api/showdownBotCard";
import { cardKey } from "../../../domain/players";
import { getReadableTextColor } from "../../../functions/colors";
import { CardItemFromCard, CardItemSkeleton } from "../../cards/CardItem";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

export default function ProbableStartingPitchers({
    away, home, probablePitchers, cardMap, onCardSelect, isLoadingCards
}: {
    away: BoxscoreTeamData;
    home: BoxscoreTeamData;
    probablePitchers: NonNullable<GameBoxscoreDetail["probable_pitchers"]>;
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
}) {
    const pitcherItem = (team: BoxscoreTeamData, pitcher?: { id?: number; full_name?: string }) => {
        const card = pitcher?.id ? cardMap[cardKey(pitcher.id, 'P')] : undefined;
        const badgeBg = team.team.primary_color ?? '#374151';
        const badgeText = getReadableTextColor(badgeBg, '#ffffff');
        return (
            <div className="space-y-1.5">
                <div className="flex items-center gap-1.5">
                    <span
                        className="inline-flex items-center justify-center rounded font-bold text-[11px] px-1.5 py-0.5"
                        style={{ backgroundColor: badgeBg, color: badgeText }}
                    >{team.team.abbreviation}</span>
                    <span className="font-semibold text-(--primary) text-sm">{pitcher?.full_name ?? 'TBD'}</span>
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
    };

    return (
        <div className="flex flex-col md:grid md:grid-cols-2 p-3 gap-x-6 gap-y-2 rounded-xl border border-(--divider) bg-(--background-secondary) text-sm">
            <div className="col-span-full mb-1">
                <span className="text-xs font-bold uppercase tracking-wide text-(--secondary)">Probable Starting Pitchers</span>
            </div>
            {pitcherItem(away, probablePitchers.away)}
            {pitcherItem(home, probablePitchers.home)}
        </div>
    );
}
