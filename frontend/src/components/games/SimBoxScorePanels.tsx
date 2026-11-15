/**
 * @fileoverview The box score rail tab for a sim between two clubs (a Faceoff or a live game): one
 * tab per side, each that side's box score as of the playback frame.
 */
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import type { GameView } from "../../domain/game";
import GameBoxScoreTabs from "./GameBoxScoreTabs";
import SimBoxScoreTable from "./SimBoxScoreTable";

export default function SimBoxScorePanels({ game, cardMap, onCardSelect }: {
    game: GameView;
    cardMap: Record<string, ShowdownBotCardAPIResponse>;
    onCardSelect: (card: ShowdownBotCardAPIResponse) => void;
}) {
    return (
        <div className="@container">
            <GameBoxScoreTabs
                awayLabel={game.away.team.abbreviation}
                homeLabel={game.home.team.abbreviation}
                renderSide={(side) => {
                    const boxscore = game[side].boxscore;
                    return boxscore ? <SimBoxScoreTable boxscore={boxscore} cardMap={cardMap} onCardSelect={onCardSelect} /> : null;
                }}
            />
        </div>
    );
}
