// Mirrors PostseasonRound in models.py (oldest to newest); WS is pulled out and rendered
// separately since it's the one round with no league.
export function roundLabel(round: string, league: string | null): string {
    switch (round) {
        case 'WC': return league ? `${league} Wild Card` : 'Wild Card';
        case 'DIV': return league ? `${league}DS` : 'Division Series';
        case 'CS': return league ? `${league}CS` : 'Championship Series';
        case 'WS': return 'World Series';
        default: return round;
    }
}
