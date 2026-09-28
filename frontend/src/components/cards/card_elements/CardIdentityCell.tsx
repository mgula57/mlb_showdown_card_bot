import CardCommand from "./CardCommand";
import PointsBadge from "./PointsBadge";
import { defenseAtPosition } from "../../shared/DefenseUtils";

/**
 * A player-identity table cell: command badge + name + points/defense. Takes primitive props
 * rather than a whole card object so it works for both a full `ShowdownBotCard` (game boxscores)
 * and a flatter `CardDatabaseRecord` (roster/sim tables) without an adapter shape in between.
 */
type CardIdentityCellProps = {
    name: string;
    position?: string | null;
    isLoadingCard?: boolean;
    /** False (the default) shows a dimmed placeholder command badge and hides points/defense —
     * used when no card could be resolved for this player at all. */
    hasCard?: boolean;
    isPitcher?: boolean;
    primaryColor?: string | null;
    secondaryColor?: string | null;
    command?: number | null;
    team?: string | null;
    points?: number;
    ptsChange?: number | null;
    positionsAndDefense?: Record<string, number> | null;
};

export default function CardIdentityCell({
    name, position, isLoadingCard, hasCard = false,
    isPitcher, primaryColor, secondaryColor, command, team,
    points, ptsChange, positionsAndDefense,
}: CardIdentityCellProps) {
    const defense = defenseAtPosition(positionsAndDefense, position);

    return (
        <div className="flex items-center space-x-1.5">
            {isLoadingCard ? (
                <div className="w-6 h-6 rounded-full bg-(--background-quaternary) animate-pulse shrink-0" />
            ) : (
                <CardCommand
                    isPitcher={isPitcher ?? true}
                    primaryColor={primaryColor ?? '#333'}
                    secondaryColor={secondaryColor ?? '#666'}
                    command={command ?? undefined}
                    team={team ?? undefined}
                    className={`w-6 h-6 ${!hasCard ? 'opacity-40' : ''}`}
                />
            )}
            <div className="space-y-0.5">
                <div className="font-semibold text-(--primary) text-[11px] text-nowrap">{name}</div>
                <div className="flex items-center gap-1">
                    {isLoadingCard && <div className="h-4 w-10 rounded-full bg-(--background-quaternary) animate-pulse" />}
                    {hasCard && points != null && <PointsBadge points={points} bg_color={secondaryColor} />}
                    {hasCard && ptsChange != null && ptsChange !== 0 && (
                        <span className={`text-[9px] font-bold leading-none ${ptsChange > 0 ? 'text-(--green)' : 'text-(--red)'}`}>
                            {ptsChange > 0 ? '▲' : '▼'}{Math.abs(ptsChange)}
                        </span>
                    )}
                    {position && (
                        <div className="text-[10px] text-(--text-tertiary)">
                            {position}{defense != null && (defense >= 0 ? "+" : "")}{defense}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
