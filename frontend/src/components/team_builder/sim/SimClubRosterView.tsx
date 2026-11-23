import { useMemo } from 'react';
import type { SimClubRoster, SimStatLine, SimTeamIdentity } from '../../../api/sim';
import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import type { CardItemStatBadge } from '../../cards/CardItemCompact';
import { useCardMap } from '../../../hooks/useCardMap';
import { useAuth } from '../../auth/AuthContext';
import { realCardId } from '../../../domain/adapters/simBoxscore';
import { FieldView } from '../FieldView';
import { formatStat, simVsReal, SIM_STATS_TOOLTIP } from './simStatColumns';
import { withSimTeamColors } from './simCardColors';

type Props = {
    snapshot: SimClubRoster;
    /** The club's own statlines this season (`useClubSeason`'s `players`). */
    players: SimStatLine[];
    /** The club's branding - its players' cards are recolored to it. */
    identity?: SimTeamIdentity | null;
};

/** The headline stat for a player's season, in the card's bottom-left corner: OPS for a hitter,
 *  ERA for a pitcher, with a green/red caret against the card's real-life season when it's known. */
function seasonBadge(line: SimStatLine, card: CardDatabaseRecord | null | undefined): CardItemStatBadge {
    const { key, simValue, diff, title } = simVsReal(line, card);
    return { label: key.toUpperCase(), value: formatStat(key, simValue), placement: 'corner', trend: diff, title };
}

/**
 * A club's season depth chart - a takeover club's drafted roster as it ran, or a real club's
 * most-used players - in the team page's field / rotation / bullpen / bench layout, read-only,
 * with each player's season OPS or ERA on the card and the full sim line in the card-detail modal.
 */
export function SimClubRosterView({ snapshot, players, identity }: Props) {
    const { session } = useAuth();
    const { cardMap, loading: isLoadingCards } = useCardMap(snapshot.roster, session?.access_token);

    // STATLINES ARE KEYED BY THE ENGINE'S BUILDER-PREFIXED ID; THE ROSTER BY THE BARE card_id.
    const lineByCardId = useMemo(
        () => Object.fromEntries(players.map(p => [realCardId(p.id), p])),
        [players],
    );

    const coloredCardMap = useMemo(() => {
        const colored: Record<string, CardDatabaseRecord | null> = {};
        for (const [cardId, record] of Object.entries(cardMap)) {
            colored[cardId] = withSimTeamColors(record, identity) ?? null;
        }
        return colored;
    }, [cardMap, identity]);

    const { statBadgeMap, simStatsMap } = useMemo(() => {
        const badges: Record<string, CardItemStatBadge> = {};
        const stats: Record<string, Record<string, number>> = {};
        for (const [cardId, line] of Object.entries(lineByCardId)) {
            badges[cardId] = seasonBadge(line, cardMap[cardId]);
            stats[cardId] = line.stats;
        }
        return { statBadgeMap: badges, simStatsMap: stats };
    }, [lineByCardId, cardMap]);

    return (
        <FieldView
            lineup={snapshot.lineup ?? { name: 'Default', index: 0, slots: [] }}
            cardMap={coloredCardMap}
            onSlotClick={() => {}}
            readOnly
            isLoadingCards={isLoadingCards}
            rosterData={{
                roster: snapshot.roster,
                rotation: snapshot.rotation,
                benchPtsMultiplier: snapshot.bench_pts_multiplier,
                bullpenOrderCustom: snapshot.bullpen_order_custom,
                minBench: snapshot.min_bench,
                minBullpen: snapshot.min_bullpen,
                maxRotation: snapshot.num_starters,
            }}
            headerLabel={snapshot.source === 'most_used' ? 'Most-Used Lineup' : undefined}
            statBadgeMap={statBadgeMap}
            simStatsMap={simStatsMap}
            simStatsTooltip={SIM_STATS_TOOLTIP}
        />
    );
}
