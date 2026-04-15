import { useState, useEffect, useCallback, useRef } from "react";
import ReactCountryFlag from "react-country-flag";
import { FaChevronLeft } from "react-icons/fa6";

import { countryCodeForTeam } from "../../functions/flags";
import { getReadableTextColor } from "../../functions/colors";
import { Modal } from "../shared/Modal";
import {
    fetchGameBoxscore,
    type GameBoxscoreDetail,
    type BoxscoreTeamData,
    type BoxscoreBatter,
    type BoxscorePitcher,
    type BoxscoreLinescoreInning,
    type MostRecentPlay,
    type BoxscoreDecisionPerson,
} from "../../api/mlbAPI";
import { buildCardsFromIds, type ShowdownBotCard, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import CardCommand from "../cards/card_elements/CardCommand";
import { CardItemFromCard } from "../cards/CardItem";
import { CardDetail } from "../cards/CardDetail";
import { getContrastColor } from "../shared/Color";
import {
    useFloating, useHover, useInteractions, offset, flip, shift, autoUpdate, FloatingPortal
} from "@floating-ui/react";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

// TODO: replace hard-coded IDs with a general two-way player detection strategy
const TWO_WAY_PLAYER_IDS = new Set([660271]); // Ohtani

/** Returns the CardMap key for a player in a given table context. */
const cardKey = (id: number, table: 'batting' | 'pitching'): string => {
    if (TWO_WAY_PLAYER_IDS.has(id)) return `${id}-${table === 'batting' ? 'H' : 'P'}`;
    return String(id);
};

type GameDetailProps = {
    gamePk: number;
    sportId?: number;
    season?: number;
    showdownSet?: string;
    /** When false, stops auto-refresh polling (e.g. user switched to another tab) */
    isActive?: boolean;
    onBack: () => void;
};

export default function GameDetail({ gamePk, sportId, season, showdownSet, isActive = true, onBack }: GameDetailProps) {
    const [boxscore, setBoxscore] = useState<GameBoxscoreDetail | null>(null);
    const [cardMap, setCardMap] = useState<CardMap>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isLoadingCards, setIsLoadingCards] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [selectedCard, setSelectedCard] = useState<ShowdownBotCardAPIResponse | null>(null);
    const handleModalCardClose = () => {
        setSelectedCard(null);
    };

    const refreshBoxscore = useCallback((silent = false) => {
        if (!silent) setIsRefreshing(true);
        return fetchGameBoxscore(gamePk).then((data) => {
            setBoxscore(data);
            return data;
        }).finally(() => {
            if (!silent) setIsRefreshing(false);
        });
    }, [gamePk]);

    // Initial fetch
    useEffect(() => {
        let cancelled = false;
        setIsLoading(true);
        setError(null);

        refreshBoxscore(true /* silent – initial load uses isLoading */)
            .catch((err) => {
                if (!cancelled) setError(err.message ?? "Failed to load boxscore");
            })
            .finally(() => {
                if (!cancelled) setIsLoading(false);
            });

        return () => { cancelled = true; };
    }, [refreshBoxscore]);

    // Auto-refresh every 30s while the game is in progress and tab is visible
    const isInProgressRef = useRef(false);
    useEffect(() => {
        const codedState = boxscore?.status?.coded_game_state;
        const isFinal = codedState === "F";
        const isNotStarted = codedState === "P" || codedState === "S";
        isInProgressRef.current = !!boxscore && !isFinal && !isNotStarted;
    }, [boxscore]);

    useEffect(() => {
        if (!boxscore) return;
        if (!isInProgressRef.current) return;
        if (!isActive) return;

        let timer: ReturnType<typeof setInterval> | null = null;

        const startPolling = () => {
            if (timer) return;
            timer = setInterval(() => {
                if (isInProgressRef.current) {
                    refreshBoxscore().catch(() => {});
                }
            }, 30_000);
        };

        const stopPolling = () => {
            if (timer) { clearInterval(timer); timer = null; }
        };

        const onVisibility = () => {
            if (document.hidden) {
                stopPolling();
            } else if (isInProgressRef.current) {
                // Refresh immediately when tab becomes visible again, then resume polling
                refreshBoxscore().catch(() => {});
                startPolling();
            }
        };

        document.addEventListener("visibilitychange", onVisibility);
        if (!document.hidden) startPolling();

        return () => {
            document.removeEventListener("visibilitychange", onVisibility);
            stopPolling();
        };
    }, [boxscore, refreshBoxscore, isActive]);

    // Fetch Showdown cards for all players in the boxscore
    useEffect(() => {
        if (!boxscore || !season || !showdownSet) return;
        let cancelled = false;

        const allIds = new Set<string>();
        for (const side of ["away", "home"] as const) {
            for (const b of boxscore.teams[side].batting) allIds.add(String(b.id));
            for (const p of boxscore.teams[side].pitching) allIds.add(String(p.id));
        }

        // Override the team for each ID based on the boxscore data, to ensure we get the correct card even if the player is now on a new team
        const overrides: Record<number, Record<string, unknown>> = {};
        for (const side of ["away", "home"] as const) {
            const teamAbbreviation = boxscore.teams[side].team.abbreviation;
            for (const b of boxscore.teams[side].batting) {
                overrides[b.id] = { team: teamAbbreviation };
            }
            for (const p of boxscore.teams[side].pitching) {
                overrides[p.id] = { team: teamAbbreviation };
            }
        }

        // Check if sport is not WBC and date is before May 1st of that season, if so subtract 1 from the season to use last year's cards
        const isCurrentSeason = new Date().getFullYear() === season;
        const useLastYear = new Date().getMonth() < 3; // Months are 0-indexed
        const adjustedSeason = (sportId === 1 && isCurrentSeason && useLastYear) ? season - 1 : season;
        const gameDate = new Date(boxscore.datetime.official_date ?? "") || new Date();
        const yesterday = new Date(gameDate);
        yesterday.setDate(yesterday.getDate() - 1);

        const cardSettings = {
            year: adjustedSeason,
            set: showdownSet,
            stat_highlights_type: "ALL",
            stats_period_type: "DATES",
            start_date: `${gameDate.getFullYear()}-03-01`, // Pull stats from the start of the season to ensure we have data for early-season games
            end_date: boxscore.datetime.official_date,
            in_season_trends_range_start_date: yesterday.toISOString().split("T")[0], // Notes the end date to start with to speed up processing
            in_season_trends_end_date: boxscore.datetime.official_date,
        }
        // No need to reload if all IDs are already in the map
        if ([...allIds].every(id => cardMap[id])) {
            return;
        }
        setIsLoadingCards(true);
        buildCardsFromIds([...allIds], adjustedSeason, cardSettings)
            .then((response) => {
                if (cancelled) return;
                const map: CardMap = {};
                for (const entry of response.cards ?? []) {
                    if (entry.card?.mlb_id != null) {
                        const id = entry.card.mlb_id;
                        if (TWO_WAY_PLAYER_IDS.has(id)) {
                            const suffix = entry.card.player_type === "Pitcher" ? "P" : "H";
                            map[`${id}-${suffix}`] = entry;
                        } else {
                            map[String(id)] = entry;
                        }
                    }
                }
                setCardMap(map);
            })
            .catch(() => { /* cards are supplementary – fail silently */ })
            .finally(() => { if (!cancelled) setIsLoadingCards(false); });

        return () => { cancelled = true; };
    }, [boxscore, season, showdownSet, sportId]);

    if (isLoading) {
        return (
            <div className="space-y-4">
                <BackButton onBack={onBack} />
                <div className="flex items-center justify-center py-20 text-(--secondary) text-sm">
                    Loading boxscore…
                </div>
            </div>
        );
    }

    if (error || !boxscore) {
        return (
            <div className="space-y-4">
                <BackButton onBack={onBack} />
                <div className="flex items-center justify-center py-20 text-red-400 text-sm">
                    {error ?? "Boxscore data unavailable."}
                </div>
            </div>
        );
    }

    const away = boxscore.teams.away;
    const home = boxscore.teams.home;
    const ls = boxscore.linescore;
    const isFinal = boxscore.status?.coded_game_state === "F";
    const isNotStarted = boxscore.status?.coded_game_state === "P" || boxscore.status?.coded_game_state === "S";
    const isInProgress = !isFinal && !isNotStarted;
    const detailedState = boxscore.status?.detailed_state ?? (isFinal ? "Final" : "In Progress");

    return (
        <div className="space-y-4 pb-24">
            <BackButton onBack={onBack} />

            {/* Header: Teams + Score */}
            <ScoreHeader
                away={away}
                home={home}
                linescore={ls}
                sportId={sportId}
                detailedState={detailedState}
                isInProgress={isInProgress}
            />

            {/* Matchup Strip */}
            {isInProgress && <MatchupStrip linescore={ls} mostRecentPlay={boxscore.most_recent_play} teams={boxscore.teams} isRefreshing={isRefreshing} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} />}

            {/* Linescore Table */}
            <LinescoreTable away={away} home={home} innings={ls.innings} teams={ls.teams} currentInning={ls.current_inning} isInProgress={isInProgress} />

            {/* Decisions */}
            {isFinal && <Decisions boxscore={boxscore} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} />}

            {/* Probable Starting Pitchers */}
            {isNotStarted && boxscore.probable_pitchers && <ProbableStartingPitchers away={away} home={home} probablePitchers={boxscore.probable_pitchers} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} />}

            <div className="grid sm:grid-cols-2 gap-4">
                {/* Away Batting */}
                <BattingTable team={away} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} />
                {/* Home Batting */}
                <BattingTable team={home} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} />

                {/* Away Pitching */}
                <PitchingTable team={away} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} />

                {/* Home Pitching */}
                <PitchingTable team={home} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} />

            </div>

            {/* Game Info */}
            <GameInfo away={away} home={home} />


            <div className={selectedCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={handleModalCardClose} isVisible={!!selectedCard}>
                    <CardDetail
                        showdownBotCardData={selectedCard}
                        hideTrendGraphs={true}
                        context="game_detail"
                        parent='game_detail'
                    />
                </Modal>
            </div>
        </div>
    );
}


// ─── Sub-components ──────────────────────────────────────────────

function BackButton({ onBack }: { onBack: () => void }) {
    return (
        <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm font-semibold text-(--secondary) hover:text-(--primary) bg-(--background-secondary) p-2 rounded-lg cursor-pointer transition-colors"
        >
            <FaChevronLeft className="h-3 w-3" />
            Back to Games
        </button>
    );
}


function ScoreHeader({
    away,
    home,
    linescore,
    sportId,
    detailedState,
    isInProgress,
}: {
    away: BoxscoreTeamData;
    home: BoxscoreTeamData;
    linescore: GameBoxscoreDetail["linescore"];
    sportId?: number;
    detailedState: string;
    isInProgress?: boolean;
}) {
    const awayCode = countryCodeForTeam(sportId ?? 0, away.team.abbreviation);
    const homeCode = countryCodeForTeam(sportId ?? 0, home.team.abbreviation);
    const awayRecord = away.team.record;
    const homeRecord = home.team.record;

    const awayBadgeBg = away.team.primary_color ?? '#374151';
    const awayBadgeText = getReadableTextColor(awayBadgeBg, '#ffffff');
    const homeBadgeBg = home.team.primary_color ?? '#374151';
    const homeBadgeText = getReadableTextColor(homeBadgeBg, '#ffffff');

    const awayRuns = linescore.teams.away.runs ?? 0;
    const homeRuns = linescore.teams.home.runs ?? 0;

    const rawHalf = (linescore.inning_half || linescore.inning_state || '');
    const inningHalf = rawHalf.charAt(0).toUpperCase() + rawHalf.slice(1).toLowerCase();
    const inningOrdinal = linescore.current_inning_ordinal || linescore.current_inning || '';
    const inningStr = inningHalf && inningOrdinal ? `${inningHalf} ${inningOrdinal}` : String(inningOrdinal);

    return (
        <>
        <style>{`@keyframes live-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }`}</style>
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-4">
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
                {/* Away team - left aligned */}
                <div className="flex flex-col gap-1">
                    {sportId === 51 && awayCode && (
                        <ReactCountryFlag countryCode={awayCode} svg style={{ width: '1.5em', height: '1.5em' }} />
                    )}
                    <div
                        className="flex items-center justify-center w-10 h-10 rounded-lg font-bold text-sm leading-none"
                        style={{ backgroundColor: awayBadgeBg, color: awayBadgeText }}
                    >{away.team.abbreviation}</div>
                    <div className="text-[14px] hidden sm:block font-semibold text-(--primary) leading-snug">{away.team.name}</div>
                    {awayRecord && (
                        <div className="text-[12px] text-(--secondary)">{awayRecord.wins ?? 0}-{awayRecord.losses ?? 0}</div>
                    )}
                </div>

                {/* Center: Score + status */}
                <div className="flex flex-col items-center gap-2">
                    <div className="flex items-center gap-3">
                        <span className={`text-[40px] font-bold leading-none text-(--primary)`}>
                            {awayRuns}
                        </span>
                        <span className="text-2xl font-bold text-(--secondary)">–</span>
                        <span className={`text-[40px] font-bold leading-none text-(--primary)`}>
                            {homeRuns}
                        </span>
                    </div>
                    {isInProgress && inningStr ? (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-(--background-primary) border border-(--divider) text-[11px]">
                            <span className="w-1.75 h-1.75 rounded-full bg-red-500 shrink-0" style={{ animation: 'live-pulse 1.4s ease-in-out infinite' }} />
                            <span className="font-semibold tracking-[0.5px] text-red-500">LIVE</span>
                            <span className="text-(--secondary) mx-0.5">·</span>
                            <span className="text-(--secondary)">{inningStr}</span>
                        </div>
                    ) : (
                        <div className="text-xs font-semibold text-(--secondary) uppercase tracking-wide">{detailedState}</div>
                    )}
                </div>

                {/* Home team - right aligned */}
                <div className="flex flex-col items-end gap-1">
                    {sportId === 51 && homeCode && (
                        <div className="self-end">
                            <ReactCountryFlag countryCode={homeCode} svg style={{ width: '1.5em', height: '1.5em' }} />
                        </div>
                    )}
                    <div
                        className="flex items-center justify-center w-10 h-10 rounded-lg font-bold text-sm leading-none"
                        style={{ backgroundColor: homeBadgeBg, color: homeBadgeText }}
                    >{home.team.abbreviation}</div>
                    <div className="text-[14px] hidden sm:block  font-semibold text-(--primary) leading-snug text-right">{home.team.name}</div>
                    {homeRecord && (
                        <div className="text-[12px] text-(--secondary)">{homeRecord.wins ?? 0}-{homeRecord.losses ?? 0}</div>
                    )}
                </div>
            </div>
        </div>
        </>
    );
}


function LinescoreTable({
    away,
    home,
    innings,
    teams,
    currentInning,
    isInProgress,
}: {
    away: BoxscoreTeamData;
    home: BoxscoreTeamData;
    innings: BoxscoreLinescoreInning[];
    teams: GameBoxscoreDetail["linescore"]["teams"];
    currentInning?: number;
    isInProgress?: boolean;
}) {
    const filledInnings = [...innings];
    for (let i = innings.length + 1; i <= 9; i++) {
        filledInnings.push({ num: i, away: { runs: undefined }, home: { runs: undefined } });
    }

    const awayBadgeBg = away.team.primary_color ?? '#374151';
    const awayBadgeText = getReadableTextColor(awayBadgeBg, '#ffffff');
    const homeBadgeBg = home.team.primary_color ?? '#374151';
    const homeBadgeText = getReadableTextColor(homeBadgeBg, '#ffffff');

    const isCurrent = (n: number) => isInProgress && currentInning != null && n === currentInning;
    const isFuture = (n: number) => isInProgress && currentInning != null && n > currentInning;

    const rows = [
        { key: 'away', data: away, side: 'away' as const, badgeBg: awayBadgeBg, badgeText: awayBadgeText },
        { key: 'home', data: home, side: 'home' as const, badgeBg: homeBadgeBg, badgeText: homeBadgeText },
    ];

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-x-auto">
            <table className="w-full text-xs text-center">
                <thead>
                    <tr className="border-b border-(--divider) text-(--secondary)">
                        <th className="pl-3 pr-2 py-2 text-left w-16" />
                        {filledInnings.map((inn) => (
                            <th key={inn.num} className={`px-1.5 py-2 min-w-7 text-[10px] tracking-[0.5px] font-semibold ${isCurrent(inn.num) ? 'text-(--primary)' : ''}`}>
                                {inn.num}
                            </th>
                        ))}
                        <th className="px-2 py-2 text-[10px] tracking-[0.5px] font-semibold text-(--primary) border-l border-(--divider)">R</th>
                        <th className="px-2 py-2 text-[10px] tracking-[0.5px] font-semibold text-(--primary)">H</th>
                        <th className="px-2 py-2 text-[10px] tracking-[0.5px] font-semibold text-(--primary)">E</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map(({ key, data, side, badgeBg, badgeText }, rowIdx) => (
                        <tr key={key} className={rowIdx < rows.length - 1 ? 'border-b border-(--divider)' : ''}>
                            <td className="pl-3 pr-2 py-2 text-left">
                                <span
                                    className="inline-flex items-center justify-center rounded font-bold text-[10px] px-1 py-0.5 leading-none"
                                    style={{ backgroundColor: badgeBg, color: badgeText, minWidth: '22px' }}
                                >{data.team.abbreviation}</span>
                            </td>
                            {filledInnings.map((inn) => {
                                const val = inn[side].runs;
                                return (
                                    <td
                                        key={inn.num}
                                        className={`px-1.5 py-2 text-[13px] ${
                                            isCurrent(inn.num) ? 'bg-(--background-quaternary) text-(--primary)' :
                                            isFuture(inn.num) ? 'text-(--secondary) opacity-30' :
                                            'text-(--secondary)'
                                        }`}
                                    >
                                        {isFuture(inn.num) ? '' : (val ?? '-')}
                                    </td>
                                );
                            })}
                            <td className="px-2 py-2 font-semibold text-(--primary) border-l border-(--divider)">{teams[side].runs}</td>
                            <td className="px-2 py-2 font-semibold text-(--primary)">{teams[side].hits}</td>
                            <td className={`px-2 py-2 font-semibold text-(--primary)'}`}>{teams[side].errors}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}


function LastResultBanner({ play }: { play?: MostRecentPlay }) {
    if (!play?.result?.description) return null;

    const isScoringPlay = play.about?.isScoringPlay;
    const event = play.result.event;
    const description = play.result.description;
    const rbi = play.result.rbi;
    const awayScore = play.result.awayScore;
    const homeScore = play.result.homeScore;

    return (
        <div className={`rounded-lg px-3 py-2 text-xs border ${isScoringPlay ? 'bg-green-950/40 border-green-700/40' : 'bg-(--background-primary)/60 border-(--divider)'}`}>
            <div className="flex items-center justify-between gap-2 mb-0.5">
                <span className={`font-bold text-[11px] uppercase tracking-wide ${isScoringPlay ? 'text-green-400' : 'text-(--secondary)'}`}>
                    {event ?? 'Last Play'}
                </span>
                {isScoringPlay && rbi != null && rbi > 0 && (
                    <span className="text-[10px] font-semibold text-(--green)">{rbi} RBI · {awayScore}–{homeScore}</span>
                )}
            </div>
            <p className="text-(--secondary) leading-snug line-clamp-2">{description}</p>
        </div>
    );
}

function MatchupStrip({ linescore, mostRecentPlay, teams, isRefreshing, cardMap, onCardSelect, isLoadingCards }: { linescore: GameBoxscoreDetail["linescore"]; mostRecentPlay?: MostRecentPlay; teams?: GameBoxscoreDetail["teams"]; isRefreshing?: boolean; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isLoadingCards?: boolean }) {
    const inningHalf = (linescore.inning_half || linescore.inning_state || "").toUpperCase();
    const inningLabel = linescore.current_inning_ordinal || linescore.current_inning || "";
    const outs = linescore.outs ?? 0;
    const hasFirst = !!linescore.offense?.first;
    const hasSecond = !!linescore.offense?.second;
    const hasThird = !!linescore.offense?.third;
    const batterName = linescore.offense?.batter;
    const batterId = linescore.offense?.batter_id;
    const pitcherName = linescore.defense?.pitcher;
    const pitcherId = linescore.defense?.pitcher_id;

    const batterCard = batterId ? cardMap[cardKey(batterId, 'batting')] : undefined;
    console.log("Batter Card", batterCard);
    const pitcherCard = pitcherId ? cardMap[cardKey(pitcherId, 'pitching')] : undefined;

    const allBatters = [...(teams?.away.batting ?? []), ...(teams?.home.batting ?? [])];
    const allPitchers = [...(teams?.away.pitching ?? []), ...(teams?.home.pitching ?? [])];
    const batterSummary = batterId ? allBatters.find(b => b.id === batterId)?.stats.summary : undefined;
    const pitcherSummary = pitcherId ? allPitchers.find(p => p.id === pitcherId)?.stats.summary : undefined;

    return (
        <>
        <style>{`
            @keyframes live-border-glow {
                0%, 100% { box-shadow: 0 0 6px rgba(234,179,8,0.12); border-color: rgba(234,179,8,0.25); }
                50%       { box-shadow: 0 0 18px rgba(234,179,8,0.35); border-color: rgba(234,179,8,0.6); }
            }
        `}</style>
        <div
            className="rounded-xl border bg-(--background-secondary) p-4 space-y-3"
            style={{ animation: 'live-border-glow 2s ease-in-out infinite' }}
        >
            

            <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wide text-yellow-600">
                    {inningHalf} {inningLabel}
                </span>

                <div className="flex items-center gap-2">
                    {isRefreshing && (
                        <svg className="animate-spin h-3 w-3 text-yellow-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                    )}
                    {!isRefreshing && (
                        <span className="text-xs text-yellow-600/60 italic">Updates every 30s</span>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] items-center sm:items-start gap-x-8 max-w-280">
                {/* Pitcher side */}
                <div className="space-y-1.5 min-w-0">
                    <div className="flex items-baseline gap-1.5 justify-between w-full">
                        
                        <div className="flex items-center gap-1.5">
                            <div className="text-[10px] font-semibold uppercase tracking-[1px] text-(--secondary)">Pitching</div>
                            {pitcherSummary && <div className="text-[10px] text-(--secondary) truncate">{pitcherSummary}</div>}
                        </div>
                        {pitcherCard?.in_season_trends?.pts_change.day != null && pitcherCard?.in_season_trends?.pts_change.day !== 0 && (
                            <div className={`text-[10px] font-semibold ${pitcherCard.in_season_trends.pts_change.day >= 0 ? 'text-(--green)' : 'text-(--red)'}`}>
                                {pitcherCard.in_season_trends.pts_change.day >= 0 ? '+' : ''}{pitcherCard.in_season_trends.pts_change.day} PTS today
                            </div>
                        )}
                    </div>
                    {pitcherCard ? (
                        <CardItemFromCard card={pitcherCard.card} onClick={() => onCardSelect?.(cardMap[cardKey(pitcherId!, 'pitching')])} />
                    ) : isLoadingCards ? (
                        <CardItemSkeleton/>
                    ) : pitcherName ? (
                        <div className="text-sm font-semibold text-(--primary) truncate">{pitcherName}</div>
                    ) : <CardItemFromCard card={undefined} className="opacity-50" />}
                </div>

                {/* Center: Count + Diamond + Outs */}
                <div className="flex flex-row md:flex-col items-center justify-center gap-1.5 px-2 shrink-0 py-2 space-x-4 md:space-x-0">
                    {linescore.balls != null && linescore.strikes != null ? (
                        <div className="space-y-1 items-center">
                            <div className="text-[10px] uppercase text-(--secondary) tracking-wide">Count</div>
                            <div className="text-[22px] font-bold text-(--primary) leading-none">{linescore.balls}–{linescore.strikes}</div>
                        </div>
                    ) : null}
                    <div className="relative w-12 h-12 mt-1">
                        <div className={`absolute top-0 left-1/2 -translate-x-1/2 translate-y-1/4 w-4 h-4 rotate-45 border ${hasSecond ? 'bg-amber-400 border-amber-500' : 'border-(--secondary)/40'}`} />
                        <div className={`absolute bottom-1/4 left-0.5 w-4 h-4 rotate-45 border ${hasThird ? 'bg-amber-400 border-amber-500' : 'border-(--secondary)/40'}`} />
                        <div className={`absolute bottom-1/4 right-0.5 w-4 h-4 rotate-45 border ${hasFirst ? 'bg-amber-400 border-amber-500' : 'border-(--secondary)/40'}`} />
                    </div>
                    <div className="text-[14px] md:text-[12px] text-(--secondary)">{outs} out{outs !== 1 ? 's' : ''}</div>
                </div>

                {/* Batter side - right aligned */}
                <div className="space-y-1.5 min-w-0 flex flex-col items-start">
                    <div className="flex items-baseline w-full justify-between gap-1.5">
                        <div className="flex items-center gap-1.5">
                            <div className="text-[10px] font-semibold uppercase tracking-[1px] text-(--secondary) shrink-0">At Bat</div>
                            {batterSummary && <div className="text-[10px] text-(--secondary) truncate">{batterSummary}</div>}
                        </div>
                        
                        {batterCard?.in_season_trends?.pts_change.day != null && (
                            <div className={`text-[10px] font-semibold ${batterCard.in_season_trends.pts_change.day >= 0 ? 'text-(--green)' : 'text-(--red)'}`}>
                                {batterCard.in_season_trends.pts_change.day >= 0 ? '+' : ''}{batterCard.in_season_trends.pts_change.day} PTS today
                            </div>
                        )}
                    </div>
                    {batterCard ? (
                        <CardItemFromCard card={batterCard.card} className="w-full" onClick={() => onCardSelect?.(cardMap[cardKey(batterId!, 'batting')])} />
                    ) : isLoadingCards ? (
                        <CardItemSkeleton className="w-full" />
                    ) : batterName ? (
                        <div className="text-sm font-semibold text-(--primary) truncate">{batterName}</div>
                    ) : <CardItemFromCard card={undefined} className="opacity-50" />}
                </div>
            </div>

            <LastResultBanner play={mostRecentPlay} />

        </div>
        </>
    );
}


function Decisions({ boxscore, cardMap, onCardSelect, isLoadingCards }: { boxscore: GameBoxscoreDetail; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isLoadingCards?: boolean }) {
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

    const winnerCardData = winner?.id ? cardMap[cardKey(winner.id, 'pitching')] : undefined;
    const loserCardData = loser?.id ? cardMap[cardKey(loser.id, 'pitching')] : undefined;
    const saveCardData = saveDecision?.id ? cardMap[cardKey(saveDecision.id, 'pitching')] : undefined;

    return (
        <div 
            className="
                flex flex-col
                md:grid md:grid-cols-2 xl:grid-cols-3
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

function ProbableStartingPitchers({
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
        const card = pitcher?.id ? cardMap[cardKey(pitcher.id, 'pitching')] : undefined;
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

function PlayerNameCell({ name, position, card, ptsChange, isLoadingCard }: { name: string; position?: string; card?: ShowdownBotCard; ptsChange?: number | null; isLoadingCard?: boolean; onClick?: () => void }) {

    const defenseForPosition = () => {
        if (!card) return null;
        if (!position) return null;
        if (position === "DH") return null; // DH has no defensive value
        
        // Check for exact position match first
        const exactMatch = card.positions_and_defense[position];
        if (exactMatch != null) return exactMatch;

        // If no exact match, check for these common position groupings
        const positionGroups: Record<string, string[]> = {
            'IF': ['1B', '2B', '3B', 'SS'],
            'OF': ['LF', 'CF', 'RF'],
            'LF/RF': ['LF', 'RF'],
        };
        for (const group in positionGroups) {
            if (positionGroups[group].includes(position)) {
                const groupMatch = card.positions_and_defense[group];
                if (groupMatch != null) return groupMatch;
            }
        }

        return null;
    }
        
    return (
        <div className="flex items-center space-x-1.5">
            {isLoadingCard ? (
                <div className="w-6 h-6 rounded-full bg-(--background-quaternary) animate-pulse shrink-0" />
            ) : (
                <CardCommand
                    isPitcher={card?.chart.is_pitcher ?? true}
                    primaryColor={card?.image.color_primary ?? '#333'}
                    secondaryColor={card?.image.color_secondary ?? '#666'}
                    command={card?.chart.command}
                    team={card?.team ?? undefined}
                    className={`w-6 h-6 ${card === undefined && 'opacity-40'}`}
                />
            )}
            <div className="space-y-0.5">
                
                <div className="font-semibold text-(--primary) text-[11px] text-nowrap">{name}</div>
                <div className="flex items-center gap-1">
                    {isLoadingCard && <div className="h-4 w-10 rounded-full bg-(--background-quaternary) animate-pulse" />}
                    {card && <PointsBadge points={card.points} bg_color={card.image.color_secondary} />}
                    {card && ptsChange != null && ptsChange !== 0 && (
                        <span className={`text-[9px] font-bold leading-none ${ptsChange > 0 ? 'text-(--green)' : 'text-(--red)'}`}>
                            {ptsChange > 0 ? '▲' : '▼'}{Math.abs(ptsChange)}
                        </span>
                    )}
                    {position && <div className="text-[10px] text-(--text-tertiary)">
                        {position}{defenseForPosition() != null && (defenseForPosition() || 0) >= 0 ? "+" : ""}{defenseForPosition()}
                    </div>}
                </div>
                
            </div>
        </div>
    );

}

function TablePointsSummary({ totalPoints, pointsChange, backgroundColor }: { totalPoints: number; pointsChange: number; backgroundColor?: string }) {
    if (totalPoints === 0) return null;
    
    return (
        <>
            <div className="ml-auto text-[10px] font-bold text-(--quaternary) flex gap-x-2">
                <span className={`${pointsChange < 0 ? 'text-(--red)' : pointsChange > 0 ? 'text-(--green)' : ''}`}>{pointsChange > 0 ? '▲' : pointsChange < 0 ? '▼' : ''}{pointsChange !== 0 ? Math.abs(pointsChange) : ''}</span>
                <PointsBadge points={totalPoints} bg_color={backgroundColor} className="text-[10px]"/>
            </div>
        </>
    );
}

function BattingTable({ team, sportId, cardMap, onCardSelect, isLoadingCards, hasGameStarted }: { team: BoxscoreTeamData; sportId?: number; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isLoadingCards?: boolean; hasGameStarted?: boolean }) {
    const countryCode = countryCodeForTeam(sportId ?? 0, team.team.abbreviation);
    const badgeBg = team.team.primary_color ?? '#374151';
    const badgeBgSecondary = team.team.secondary_color ?? '#4b5563';
    const badgeText = getReadableTextColor(badgeBg, '#ffffff');
    const hasCards = Object.keys(cardMap).length > 0;

    const sortedBatters = [...team.batting]
        .filter((b) => b.batting_order != null && b.batting_order !== "")
        .sort((a, b) => {
            const orderA = a.batting_order ? parseInt(a.batting_order, 10) : 9999;
            const orderB = b.batting_order ? parseInt(b.batting_order, 10) : 9999;
            return orderA - orderB;
        });

    const totalPoints = hasCards
        ? sortedBatters.reduce((sum, b) => sum + (cardMap[cardKey(b.id, 'batting')]?.card?.points ?? 0), 0)
        : 0;
    const totalPointsChange = hasCards && hasGameStarted
        ? sortedBatters.reduce((sum, b) => sum + (cardMap[cardKey(b.id, 'batting')]?.in_season_trends?.pts_change.day ?? 0), 0)
        : 0;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-hidden">
            <div className="px-3 py-2 border-b border-(--divider) flex items-center gap-2">
                {sportId === 51 && countryCode && (
                    <ReactCountryFlag countryCode={countryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                )}
                <span
                    className="inline-flex items-center justify-center rounded font-bold text-[11px] px-1.5 py-0.5"
                    style={{ backgroundColor: badgeBg, color: badgeText }}
                >{team.team.abbreviation}</span>
                <span className="text-xs text-(--secondary) font-semibold">Batting</span>
                {hasCards && totalPoints > 0 && (
                    <TablePointsSummary totalPoints={totalPoints} pointsChange={totalPointsChange} backgroundColor={badgeBgSecondary} />
                )}
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-(--divider) text-(--secondary) font-semibold text-[10px] tracking-[0.5px] uppercase">
                            <th className="pl-3 pr-2 py-2 text-left min-w-36">Batters</th>
                            <th className="px-2 py-2 text-right">AB</th>
                            <th className="px-2 py-2 text-right">R</th>
                            <th className="px-2 py-2 text-right">H</th>
                            <th className="px-2 py-2 text-right">RBI</th>
                            <th className="px-2 py-2 text-right">BB</th>
                            <th className="px-2 py-2 text-right">K</th>
                            <th className="px-2 py-2 text-right">AVG</th>
                            <th className="px-2 py-2 text-right pr-3">OPS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedBatters.map((batter) => (
                            <BatterRow key={batter.id} batter={batter} cardResponse={cardMap[cardKey(batter.id, 'batting')]} onCardSelect={onCardSelect} isLoadingCards={isLoadingCards} />
                        ))}
                        {sortedBatters.length === 0 && (
                            <tr>
                                <td colSpan={9} className="px-3 py-4 text-center text-(--secondary)">
                                    No batting data available.
                                </td>
                            </tr>
                        )}
                        <tr className="border-t border-(--divider) font-bold">
                            <td className="pl-3 pr-2 py-2 text-left text-(--primary)">Totals</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.at_bats}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.runs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.hits}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.rbi}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.base_on_balls}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.strike_outs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)" />
                            <td className="px-2 py-2 text-right pr-3 text-(--primary)" />
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function BatterRow({ batter, cardResponse, onCardSelect, isLoadingCards }: { batter: BoxscoreBatter; cardResponse?: ShowdownBotCardAPIResponse; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isLoadingCards?: boolean }) {
    const [isOpen, setIsOpen] = useState(false);
    const { refs, floatingStyles, context } = useFloating({
        open: isOpen,
        onOpenChange: setIsOpen,
        placement: "right",           // start right, auto-flips if near edge
        middleware: [offset(8), flip(), shift({ padding: 8 })],
        whileElementsMounted: autoUpdate,
    });
    const hover = useHover(context, { delay: { open: 300, close: 100 } }); // 300ms open delay prevents flicker
    const { getReferenceProps, getFloatingProps } = useInteractions([hover]);

    const card = cardResponse?.card ?? undefined;
    const indent = batter.is_substitute;
    const hasHit = (batter.stats.hits ?? 0) > 0;

    if (batter.name == 'Brett Baty') {
        console.log("Baty Card Response", indent);
    }

    return (
        <tr
            className={`
                border-b border-(--divider)/50 hover:bg-(--background-primary)/50 
                ${cardResponse ? 'cursor-pointer' : ''}
            `}
            onClick={cardResponse ? () => onCardSelect?.(cardResponse) : undefined}
        >
            <td 
                ref={refs.setReference} {...getReferenceProps()} 
                className={`
                    pl-3 pr-2 py-1.5 text-left
                    ${indent ? 'pl-8' : ''}
                    ${!batter.is_in_lineup ? 'opacity-60' : ''}
                `} >
                    <PlayerNameCell name={batter.name} position={batter.position} card={card} ptsChange={cardResponse?.in_season_trends?.pts_change.day} isLoadingCard={isLoadingCards && !cardResponse} />
            </td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.at_bats}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.runs}</td>
            <td className={`px-2 py-1.5 text-right font-semibold ${hasHit ? 'text-(--primary)' : 'text-(--secondary)'}`}>{batter.stats.hits}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.rbi}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.base_on_balls}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.strike_outs}</td>
            <td className="px-2 py-1.5 text-right text-(--secondary)">{batter.season_stats.avg}</td>
            <td className="px-2 py-1.5 text-right pr-3 text-(--secondary)">{batter.season_stats.ops}</td>
            {isOpen && card && (
                <FloatingPortal>
                    <div
                        ref={refs.setFloating}
                        style={floatingStyles}
                        className="z-50 w-48"
                        {...getFloatingProps()}
                    >
                        <CardItemFromCard card={card} className="min-w-xs max-w-md" />
                    </div>
                </FloatingPortal>
            )}
        </tr>
    );
}


function PitchingTable({ team, sportId, cardMap, onCardSelect, isLoadingCards, hasGameStarted }: { team: BoxscoreTeamData; sportId?: number; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isLoadingCards?: boolean; hasGameStarted?: boolean }) {
    const countryCode = countryCodeForTeam(sportId ?? 0, team.team.abbreviation);
    const badgeBg = team.team.primary_color ?? '#374151';
    const badgeBgSecondary = team.team.secondary_color ?? '#4b5563';
    const badgeText = getReadableTextColor(badgeBg, '#ffffff');

    const hasCards = Object.keys(cardMap).length > 0;

    const totalPoints = hasCards
        ? team.pitching.reduce((sum, p) => sum + (cardMap[cardKey(p.id, 'pitching')]?.card?.points ?? 0), 0)
        : 0;
    const totalPointsChange = hasCards && hasGameStarted
        ? team.pitching.reduce((sum, p) => sum + (cardMap[cardKey(p.id, 'pitching')]?.in_season_trends?.pts_change.day ?? 0), 0)
        : 0;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-hidden">
            <div className="px-3 py-2 border-b border-(--divider) flex items-center gap-2">
                {sportId === 51 && countryCode && (
                    <ReactCountryFlag countryCode={countryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                )}
                <span
                    className="inline-flex items-center justify-center rounded font-bold text-[11px] px-1.5 py-0.5"
                    style={{ backgroundColor: badgeBg, color: badgeText }}
                >{team.team.abbreviation}</span>
                <span className="text-xs text-(--secondary) font-semibold">Pitching</span>
                {hasCards && totalPoints > 0 && (
                    <TablePointsSummary totalPoints={totalPoints} pointsChange={totalPointsChange} backgroundColor={badgeBgSecondary} />
                )}
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-(--divider) text-(--secondary) font-semibold text-[10px] tracking-[0.5px] uppercase">
                            <th className="pl-3 pr-2 py-2 text-left min-w-36">Pitchers</th>
                            <th className="px-2 py-2 text-right">IP</th>
                            <th className="px-2 py-2 text-right">H</th>
                            <th className="px-2 py-2 text-right">R</th>
                            <th className="px-2 py-2 text-right">ER</th>
                            <th className="px-2 py-2 text-right">BB</th>
                            <th className="px-2 py-2 text-right">K</th>
                            <th className="px-2 py-2 text-right">HR</th>
                            <th className="px-2 py-2 text-right">P-S</th>
                            <th className="px-2 py-2 text-right pr-3">ERA</th>
                        </tr>
                    </thead>
                    <tbody>
                        {team.pitching.map((pitcher) => (
                            <PitcherRow key={pitcher.id} pitcher={pitcher} cardResponse={cardMap[cardKey(pitcher.id, 'pitching')]} onCardSelect={onCardSelect} isLoadingCards={isLoadingCards} />
                        ))}
                        {team.pitching.length === 0 && (
                            <tr>
                                <td colSpan={10} className="px-3 py-4 text-center text-(--secondary)">
                                    No pitching data available.
                                </td>
                            </tr>
                        )}
                        <tr className="border-t border-(--divider) font-bold">
                            <td className="pl-3 pr-2 py-2 text-left text-(--primary)">Totals</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.innings_pitched}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.hits}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.runs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.earned_runs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.base_on_balls}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.strike_outs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.home_runs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">
                                {team.pitching_totals.pitches_thrown}-{team.pitching_totals.strikes}
                            </td>
                            <td className="px-2 py-2 text-right pr-3 text-(--primary)" />
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function PitcherRow({ pitcher, cardResponse, onCardSelect, isLoadingCards }: { pitcher: BoxscorePitcher; cardResponse?: ShowdownBotCardAPIResponse; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isLoadingCards?: boolean }) {
    
    const [isOpen, setIsOpen] = useState(false);
    const { refs, floatingStyles, context } = useFloating({
        open: isOpen,
        onOpenChange: setIsOpen,
        placement: "right",           // start right, auto-flips if near edge
        middleware: [offset(8), flip(), shift({ padding: 8 })],
        whileElementsMounted: autoUpdate,
    });
    const hover = useHover(context, { delay: { open: 300, close: 100 } }); // 300ms open delay prevents flicker
    const { getReferenceProps, getFloatingProps } = useInteractions([hover]);

    const card = cardResponse?.card ?? undefined;
    return (
        <tr
            className={`border-b border-(--divider)/50 hover:bg-(--background-primary)/50 ${cardResponse ? 'cursor-pointer' : ''}`}
            onClick={cardResponse ? () => onCardSelect?.(cardResponse) : undefined}
        >
            <td ref={refs.setReference} {...getReferenceProps()} className="pl-3 pr-2 py-1.5 text-left" >
                <PlayerNameCell name={pitcher.name} position={'P'} card={card} ptsChange={cardResponse?.in_season_trends?.pts_change.day} isLoadingCard={isLoadingCards && !cardResponse} />
            </td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.innings_pitched}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.hits}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.runs}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.earned_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.base_on_balls}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.strike_outs}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.home_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">
                {pitcher.stats.pitches_thrown}-{pitcher.stats.strikes}
            </td>
            <td className="px-2 py-1.5 text-right pr-3 text-(--secondary)">{pitcher.season_stats.era}</td>
            {isOpen && card && (
                <FloatingPortal>
                    <div
                        ref={refs.setFloating}
                        style={floatingStyles}
                        className="z-50 w-48"
                        {...getFloatingProps()}
                    >
                        <CardItemFromCard card={card} className="min-w-xs max-w-md" />
                    </div>
                </FloatingPortal>
            )}
        </tr>
    );
}


function CardItemSkeleton({ className }: { className?: string }) {
    return (
        <div className={`${className ?? ''} relative flex flex-col p-2 gap-1.5 rounded-xl border border-(--divider) animate-pulse`}>
            <div className="flex flex-row gap-2 items-center">
                <div className="w-9 h-9 rounded-full bg-(--background-quaternary) shrink-0" />
                <div className="flex flex-col gap-1.5 flex-1 min-w-0">
                    <div className="h-3 w-20 rounded bg-(--background-quaternary)" />
                    <div className="h-2.5 w-14 rounded bg-(--background-quaternary)" />
                </div>
            </div>
            <div className="h-5 w-full rounded bg-(--background-quaternary)" />
            <div className="h-2.5 w-full rounded bg-(--background-quaternary)" />
            <div className="absolute inset-0 flex items-center justify-center gap-1.5 rounded-xl bg-(--background-secondary)/60 backdrop-blur-[1px]">
                <span className="w-1.5 h-1.5 rounded-full bg-(--secondary) animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-(--secondary) animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-(--secondary) animate-bounce [animation-delay:300ms]" />
            </div>
        </div>
    );
}

function PointsBadge({ points, bg_color, className }: { points: number, bg_color?: string | null, className?: string }) {
    return (
        <span 
            className={`inline-flex items-center justify-center min-w-5 px-1 py-0.5 rounded-full text-[9px] font-bold leading-none text-nowrap ${className ?? ''}`}
            style={
                { backgroundColor: bg_color ?? 'var(--secondary)/15', color: getContrastColor(bg_color ?? 'var(--secondary)/15') }}    
        >
            {points} PT
        </span>
    );
}


function GameInfo({ away, home }: { away: BoxscoreTeamData; home: BoxscoreTeamData }) {
    const allInfo = [...away.info, ...home.info];

    if (allInfo.length === 0) return null;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3 space-y-3">
            <div className="font-black text-sm text-(--primary)">Game Info</div>
            {allInfo.map((section, idx) => (
                <div key={idx} className="space-y-1">
                    <div className="text-xs font-bold text-(--secondary) uppercase tracking-wide">{section.title}</div>
                    {section.fieldList.map((field, fidx) => (
                        <div key={fidx} className="flex gap-2 text-xs">
                            <span className="font-bold text-(--primary) shrink-0">{field.label}:</span>
                            <span className="text-(--secondary)">{field.value}</span>
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
}
