import { useState, useEffect, useCallback, useRef } from "react";
import ReactCountryFlag from "react-country-flag";
import { FaChevronLeft } from "react-icons/fa6";

import { countryCodeForTeam } from "../../functions/flags";
import { Modal } from "../shared/Modal";
import {
    fetchGameBoxscore,
    type GameBoxscoreDetail,
    type BoxscoreTeamData,
    type BoxscoreBatter,
    type BoxscorePitcher,
    type BoxscoreLinescoreInning,
} from "../../api/mlbAPI";
import { type CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { fetchCardsByMlbIds } from "../../api/card_db/cardDatabase";
import CardCommand from "../cards/card_elements/CardCommand";
import { CardItemFromCardDatabaseRecord } from "../cards/CardItem";
import { CardDetail } from "../cards/CardDetail";
import { type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { getContrastColor } from "../shared/Color";

type CardMap = Record<number, CardDatabaseRecord>;

type GameDetailProps = {
    gamePk: number;
    sportId?: number;
    season?: number;
    showdownSet?: string;
    onBack: () => void;
};

export default function GameDetail({ gamePk, sportId, season, showdownSet, onBack }: GameDetailProps) {
    const [boxscore, setBoxscore] = useState<GameBoxscoreDetail | null>(null);
    const [cardMap, setCardMap] = useState<CardMap>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [selectedCard, setSelectedCard] = useState<CardDatabaseRecord | null>(null);
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
    }, [boxscore, refreshBoxscore]);

    // Fetch Showdown cards for all players in the boxscore
    useEffect(() => {
        if (!boxscore || !season || !showdownSet) return;
        let cancelled = false;

        const allIds = new Set<number>();
        for (const side of ["away", "home"] as const) {
            for (const b of boxscore.teams[side].batting) allIds.add(b.id);
            for (const p of boxscore.teams[side].pitching) allIds.add(p.id);
        }

        // Check if sport is not WBC and date is before May 1st of that season, if so subtract 1 from the season to use last year's cards
        const isCurrentSeason = new Date().getFullYear() === season;
        const isBeforeMay = new Date().getMonth() < 4; // Months are 0-indexed
        const adjustedSeason = (sportId === 1 && isCurrentSeason && isBeforeMay) ? season - 1 : season;

        const isWbc = sportId === 51;
        fetchCardsByMlbIds([...allIds], adjustedSeason, showdownSet, isWbc)
            .then((map) => { if (!cancelled) setCardMap(map); })
            .catch(() => { /* cards are supplementary – fail silently */ });

        return () => { cancelled = true; };
    }, [boxscore, season, showdownSet, sportId]);

    if (isLoading) {
        return (
            <div className="space-y-4">
                <BackButton onBack={onBack} />
                <div className="flex items-center justify-center py-20 text-(--text-secondary) text-sm">
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
            />

            {/* Live Situation */}
            {isInProgress && <LiveSituation linescore={ls} isRefreshing={isRefreshing} cardMap={cardMap} onCardSelect={setSelectedCard} />}

            {/* Linescore Table */}
            <LinescoreTable away={away} home={home} innings={ls.innings} teams={ls.teams} />

            {/* Decisions */}
            {isFinal && <Decisions boxscore={boxscore} />}

            <div className="grid sm:grid-cols-2 gap-4">
                {/* Away Batting */}
                <BattingTable team={away} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} />
                {/* Home Batting */}
                <BattingTable team={home} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} />

                {/* Away Pitching */}
                <PitchingTable team={away} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} />

                {/* Home Pitching */}
                <PitchingTable team={home} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} />

            </div>

            {/* Game Info */}
            <GameInfo away={away} home={home} />


            <div className={selectedCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={handleModalCardClose} isVisible={!!selectedCard}>
                    <CardDetail
                        cardId={selectedCard?.card_id}
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
            className="flex items-center gap-1.5 text-sm font-semibold text-(--text-secondary) hover:text-(--text-primary) cursor-pointer transition-colors"
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
}: {
    away: BoxscoreTeamData;
    home: BoxscoreTeamData;
    linescore: GameBoxscoreDetail["linescore"];
    sportId?: number;
    detailedState: string;
}) {
    const awayCode = countryCodeForTeam(sportId ?? 0, away.team.abbreviation);
    const homeCode = countryCodeForTeam(sportId ?? 0, home.team.abbreviation);
    const awayRecord = away.team.record;
    const homeRecord = home.team.record;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-4 space-y-3">
            <div className="text-center text-xs font-bold uppercase tracking-wide text-(--text-secondary)">
                {detailedState}
            </div>

            <div className="flex items-center justify-center gap-6">
                {/* Away */}
                <div className="flex flex-col items-center gap-1 min-w-20">
                    {sportId === 51 && awayCode && (
                        <ReactCountryFlag countryCode={awayCode} svg style={{ width: '2em', height: '2em' }} />
                    )}
                    <span className="text-lg font-black text-(--text-primary)">{away.team.abbreviation}</span>
                    {awayRecord && (
                        <span className="text-[11px] text-(--text-secondary)">
                            {awayRecord.wins ?? 0}-{awayRecord.losses ?? 0}
                        </span>
                    )}
                </div>

                {/* Score */}
                <div className="flex items-center gap-3">
                    <span className="text-4xl font-black text-(--text-primary)">{linescore.teams.away.runs}</span>
                    <span className="text-xl font-bold text-(--text-secondary)">-</span>
                    <span className="text-4xl font-black text-(--text-primary)">{linescore.teams.home.runs}</span>
                </div>

                {/* Home */}
                <div className="flex flex-col items-center gap-1 min-w-20">
                    {sportId === 51 && homeCode && (
                        <ReactCountryFlag countryCode={homeCode} svg style={{ width: '2em', height: '2em' }} />
                    )}
                    <span className="text-lg font-black text-(--text-primary)">{home.team.abbreviation}</span>
                    {homeRecord && (
                        <span className="text-[11px] text-(--text-secondary)">
                            {homeRecord.wins ?? 0}-{homeRecord.losses ?? 0}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}


function LinescoreTable({
    away,
    home,
    innings,
    teams,
}: {
    away: BoxscoreTeamData;
    home: BoxscoreTeamData;
    innings: BoxscoreLinescoreInning[];
    teams: GameBoxscoreDetail["linescore"]["teams"];
}) {

    // Fill in innings if there are less than 9, to keep the table layout consistent
    const filledInnings = [...innings];
    for (let i = innings.length + 1; i <= 9; i++) {
        filledInnings.push({ num: i, away: { runs: undefined }, home: { runs: undefined } });
    }

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-x-auto">
            <table className="w-full text-xs text-center">
                <thead>
                    <tr className="border-b border-(--divider) text-(--text-secondary) font-bold">
                        <th className="pl-3 pr-2 py-2 text-left w-16" />
                        {filledInnings.map((inn) => (
                            <th key={inn.num} className="px-1.5 py-2 min-w-7">{inn.num}</th>
                        ))}
                        <th className="px-2 py-2 font-black text-(--text-primary) border-l border-(--divider)">R</th>
                        <th className="px-2 py-2 font-black text-(--text-primary)">H</th>
                        <th className="px-2 py-2 font-black text-(--text-primary)">E</th>
                    </tr>
                </thead>
                <tbody>
                    <tr className="border-b border-(--divider)">
                        <td className="pl-3 pr-2 py-2 text-left font-black text-(--text-primary)">{away.team.abbreviation}</td>
                        {filledInnings.map((inn) => (
                            <td key={inn.num} className="px-1.5 py-2 text-(--text-primary)">{inn.away.runs ?? "-"}</td>
                        ))}
                        <td className="px-2 py-2 font-black text-(--text-primary) border-l border-(--divider)">{teams.away.runs}</td>
                        <td className="px-2 py-2 font-bold text-(--text-primary)">{teams.away.hits}</td>
                        <td className="px-2 py-2 font-bold text-(--text-primary)">{teams.away.errors}</td>
                    </tr>
                    <tr>
                        <td className="pl-3 pr-2 py-2 text-left font-black text-(--text-primary)">{home.team.abbreviation}</td>
                        {filledInnings.map((inn) => (
                            <td key={inn.num} className="px-1.5 py-2 text-(--text-primary)">{inn.home.runs ?? "-"}</td>
                        ))}
                        {/* Add a divider */}
                        <td className="px-2 py-2 font-black text-(--text-primary) border-l border-(--divider)">{teams.home.runs}</td>
                        <td className="px-2 py-2 font-bold text-(--text-primary)">{teams.home.hits}</td>
                        <td className="px-2 py-2 font-bold text-(--text-primary)">{teams.home.errors}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    );
}


function LiveSituation({ linescore, isRefreshing, cardMap, onCardSelect }: { linescore: GameBoxscoreDetail["linescore"]; isRefreshing?: boolean; cardMap: CardMap; onCardSelect?: (card: CardDatabaseRecord) => void }) {
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

    const batterCard = batterId ? cardMap[batterId] : undefined;
    const pitcherCard = pitcherId ? cardMap[pitcherId] : undefined;

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
            {/* ── Top-left: LIVE badge + Inning + refresh spinner ── */}
            <div className="flex items-center gap-2 justify-between">
                <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-red-500/15 border border-red-500/30">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                        </span>
                        <span className="text-[10px] font-black uppercase tracking-wider text-red-400">Live</span>
                    </span>
                    <span className="text-xs font-bold uppercase tracking-wide text-yellow-600 whitespace-nowrap">
                        {inningHalf} {inningLabel}
                    </span>
                    {isRefreshing && (
                        <svg className="animate-spin h-3 w-3 text-yellow-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                    )}
                </div>

                <div className="text-xs text-yellow-600 italic">
                    Updates every 30s
                </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-4">

                {/* ── Left: situation indicators ── */}
                <div className="flex items-center justify-center gap-4 sm:pr-4 sm:border-r sm:border-yellow-500/15 shrink-0">

                    {/* Diamond + Outs + Count */}
                    <div className="flex items-center gap-6">
                        {/* Bases diamond */}
                        <div className="flex flex-col items-center gap-1">
                            <div className="relative w-12 h-12">
                                <div className={`absolute top-0 left-1/2 -translate-x-1/2 translate-y-1/4 w-4 h-4 rotate-45 border ${
                                    hasSecond ? 'bg-yellow-400 border-yellow-500' : 'bg-gray-600 border-gray-500'
                                }`} />
                                <div className={`absolute bottom-1/4 left-0.5 w-4 h-4 rotate-45 border ${
                                    hasThird ? 'bg-yellow-400 border-yellow-500' : 'bg-gray-600 border-gray-500'
                                }`} />
                                <div className={`absolute bottom-1/4 right-0.5 w-4 h-4 rotate-45 border ${
                                    hasFirst ? 'bg-yellow-400 border-yellow-500' : 'bg-gray-600 border-gray-500'
                                }`} />
                            </div>
                            {/* Outs */}
                            <div className="flex items-center gap-1.5">
                                {[0, 1, 2].map((i) => (
                                    <span
                                        key={i}
                                        className={`h-2.5 w-2.5 rounded-full border ${
                                            i < outs ? 'bg-yellow-400 border-yellow-500' : 'bg-transparent border-(--text-secondary)/50'
                                        }`}
                                    />
                                ))}
                            </div>
                        </div>

                        {/* Count */}
                        {(linescore.balls != null && linescore.strikes != null) && (
                            <div className="flex flex-col items-center gap-0.5">
                                <span className="text-[10px] font-bold uppercase tracking-wide text-(--text-secondary)">Count</span>
                                <span className="text-xl font-black text-(--text-primary)">{linescore.balls}-{linescore.strikes}</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* ── Right: Batter / Pitcher cards ── */}
                {(batterName || pitcherName) && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 min-w-0 flex-1">
                        <div className="space-y-1 min-w-0">
                            <div className="text-[10px] font-bold uppercase tracking-wide text-(--text-secondary) pl-1">Pitching</div>
                            {pitcherCard ? (
                                <CardItemFromCardDatabaseRecord card={pitcherCard} onClick={() => onCardSelect?.(pitcherCard)} />
                            ) : pitcherName ? (
                                <div className="px-2 py-1.5 text-sm font-semibold text-(--text-primary) truncate">{pitcherName}</div>
                            ) : null}
                        </div>
                        <div className="space-y-1 min-w-0">
                            <div className="text-[10px] font-bold uppercase tracking-wide text-(--text-secondary) pl-1">At Bat</div>
                            {batterCard ? (
                                <CardItemFromCardDatabaseRecord card={batterCard} onClick={() => onCardSelect?.(batterCard)} />
                            ) : batterName ? (
                                <div className="px-2 py-1.5 text-sm font-semibold text-(--text-primary) truncate">{batterName}</div>
                            ) : null}
                        </div>
                    </div>
                )}

            </div>
        </div>
        </>
    );
}


function Decisions({ boxscore }: { boxscore: GameBoxscoreDetail }) {
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

    if (!winner && !loser) return null;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3 flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {winner && (
                <div className="flex items-center gap-1.5">
                    <span className="font-bold text-green-400">W:</span>
                    <span className="font-semibold text-(--text-primary)">{winner.full_name}</span>
                    <span className="text-(--text-secondary) text-xs">{findPitcherNote(winner.id)}</span>
                </div>
            )}
            {loser && (
                <div className="flex items-center gap-1.5">
                    <span className="font-bold text-red-400">L:</span>
                    <span className="font-semibold text-(--text-primary)">{loser.full_name}</span>
                    <span className="text-(--text-secondary) text-xs">{findPitcherNote(loser.id)}</span>
                </div>
            )}
            {saveDecision && (
                <div className="flex items-center gap-1.5">
                    <span className="font-bold text-blue-400">SV:</span>
                    <span className="font-semibold text-(--text-primary)">{saveDecision.full_name}</span>
                    <span className="text-(--text-secondary) text-xs">{findPitcherNote(saveDecision.id)}</span>
                </div>
            )}
        </div>
    );
}


function BattingTable({ team, sportId, cardMap, onCardSelect }: { team: BoxscoreTeamData; sportId?: number; cardMap: CardMap; onCardSelect?: (card: CardDatabaseRecord) => void }) {
    const countryCode = countryCodeForTeam(sportId ?? 0, team.team.abbreviation);
    const hasCards = Object.keys(cardMap).length > 0;

    // Sort: lineup batters first in batting order, then substitutes
    const sortedBatters = [...team.batting]
        .filter((b) => b.is_in_lineup)
        .sort((a, b) => {
            const orderA = a.batting_order ? parseInt(a.batting_order, 10) : 9999;
            const orderB = b.batting_order ? parseInt(b.batting_order, 10) : 9999;
            return orderA - orderB;
        });

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-hidden">
            <div className="px-3 py-2 border-b border-(--divider) flex items-center gap-2">
                {sportId === 51 && countryCode && (
                    <ReactCountryFlag countryCode={countryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                )}
                <span className="font-black text-(--text-primary)">{team.team.abbreviation}</span>
                <span className="text-xs text-(--text-secondary) font-semibold">Batting</span>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-(--divider) text-(--text-secondary) font-bold">
                            <th className="pl-3 pr-2 py-2 text-left min-w-36">Batters</th>
                            {hasCards && <th className="px-1 py-2 text-center min-w-9">CMD</th>}
                            {hasCards && <th className="px-1 py-2 text-center min-w-8">PTS</th>}
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
                            <BatterRow key={batter.id} batter={batter} card={cardMap[batter.id]} hasCards={hasCards} onCardSelect={onCardSelect} />
                        ))}
                        {sortedBatters.length === 0 && (
                            <tr>
                                <td colSpan={hasCards ? 14 : 12} className="px-3 py-4 text-center text-(--text-secondary)">
                                    No batting data available.
                                </td>
                            </tr>
                        )}
                        <tr className="border-t border-(--divider) font-bold">
                            <td className="pl-3 pr-2 py-2 text-left text-(--text-primary)">Totals</td>
                            {hasCards && <td />}
                            {hasCards && <td />}
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.at_bats}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.runs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.hits}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.rbi}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.base_on_balls}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.batting_totals.strike_outs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)" />
                            <td className="px-2 py-2 text-right pr-3 text-(--text-primary)" />
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function BatterRow({ batter, card, hasCards, onCardSelect }: { batter: BoxscoreBatter; card?: CardDatabaseRecord; hasCards: boolean; onCardSelect?: (card: CardDatabaseRecord) => void }) {
    const indent = batter.is_substitute && !batter.is_in_lineup;

    return (
        <tr 
            className={`border-b border-(--divider)/50 hover:bg-(--background-primary)/50 ${card ? 'cursor-pointer' : ''}`}
            onClick={card ? () => onCardSelect?.(card) : undefined}
        >
            <td className={`${indent ? 'pl-6' : 'pl-3'} pr-2 py-1.5 text-left`}>
                <span className="font-semibold text-(--text-primary)">{batter.name}</span>
                <span className="ml-1.5 text-(--text-secondary)">{batter.position}</span>
            </td>
            {hasCards && (
                <td className="px-1 py-1 text-center">
                    {card && (
                        <div
                            className="flex justify-center"
                        >
                            <CardCommand
                                isPitcher={false}
                                primaryColor={card.color_primary ?? '#333'}
                                secondaryColor={card.color_secondary ?? '#666'}
                                command={card.command}
                                team={card.team ?? undefined}
                                className="w-7 h-7 text-[12px]"
                            />
                        </div>
                    )}
                </td>
            )}
            {hasCards && (
                <td className="px-1 py-1 text-center">
                    {card && <PointsBadge points={card.points} bg_color={card.color_secondary} />}
                </td>
            )}
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.at_bats}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.runs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.hits}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.rbi}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.base_on_balls}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{batter.stats.strike_outs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-secondary)">{batter.season_stats.avg}</td>
            <td className="px-2 py-1.5 text-right pr-3 text-(--text-secondary)">{batter.season_stats.ops}</td>
        </tr>
    );
}


function PitchingTable({ team, sportId, cardMap, onCardSelect }: { team: BoxscoreTeamData; sportId?: number; cardMap: CardMap; onCardSelect?: (card: CardDatabaseRecord) => void }) {
    const countryCode = countryCodeForTeam(sportId ?? 0, team.team.abbreviation);
    const hasCards = Object.keys(cardMap).length > 0;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-hidden">
            <div className="px-3 py-2 border-b border-(--divider) flex items-center gap-2">
                {sportId === 51 && countryCode && (
                    <ReactCountryFlag countryCode={countryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                )}
                <span className="font-black text-(--text-primary)">{team.team.abbreviation}</span>
                <span className="text-xs text-(--text-secondary) font-semibold">Pitching</span>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-(--divider) text-(--text-secondary) font-bold">
                            <th className="pl-3 pr-2 py-2 text-left min-w-36">Pitchers</th>
                            {hasCards && <th className="px-1 py-2 text-center min-w-9">CMD</th>}
                            {hasCards && <th className="px-1 py-2 text-center min-w-8">PT</th>}
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
                            <PitcherRow key={pitcher.id} pitcher={pitcher} card={cardMap[pitcher.id]} hasCards={hasCards} onCardSelect={onCardSelect} />
                        ))}
                        {team.pitching.length === 0 && (
                            <tr>
                                <td colSpan={hasCards ? 15 : 13} className="px-3 py-4 text-center text-(--text-secondary)">
                                    No pitching data available.
                                </td>
                            </tr>
                        )}
                        <tr className="border-t border-(--divider) font-bold">
                            <td className="pl-3 pr-2 py-2 text-left text-(--text-primary)">Totals</td>
                            {hasCards && <td />}
                            {hasCards && <td />}
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.innings_pitched}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.hits}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.runs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.earned_runs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.base_on_balls}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.strike_outs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">{team.pitching_totals.home_runs}</td>
                            <td className="px-2 py-2 text-right text-(--text-primary)">
                                {team.pitching_totals.pitches_thrown}-{team.pitching_totals.strikes}
                            </td>
                            <td className="px-2 py-2 text-right pr-3 text-(--text-primary)" />
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function PitcherRow({ pitcher, card, hasCards, onCardSelect }: { pitcher: BoxscorePitcher; card?: CardDatabaseRecord; hasCards: boolean; onCardSelect?: (card: CardDatabaseRecord) => void }) {
    return (
        <tr 
            className={`border-b border-(--divider)/50 hover:bg-(--background-primary)/50 ${card ? 'cursor-pointer' : ''}`}
            onClick={card ? () => onCardSelect?.(card) : undefined}
        >
            <td className="pl-3 pr-2 py-1.5 text-left">
                <span className="font-semibold text-(--text-primary)">{pitcher.name}</span>
                {pitcher.stats.note && (
                    <span className="ml-1.5 text-[10px] font-bold text-(--text-secondary)">{pitcher.stats.note}</span>
                )}
            </td>
            {hasCards && (
                <td className="px-1 py-1 text-center">
                    {card && (
                        <div
                            className="flex justify-center"
                        >
                            <CardCommand
                                isPitcher={true}
                                primaryColor={card.color_primary ?? '#333'}
                                secondaryColor={card.color_secondary ?? '#666'}
                                command={card.command}
                                team={card.team ?? undefined}
                                className="w-7 h-7 text-[12px]"
                            />
                        </div>
                    )}
                </td>
            )}
            {hasCards && (
                <td className="px-1 py-1 text-center">
                    {card && <PointsBadge points={card.points} bg_color={card.color_secondary} />}
                </td>
            )}
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.innings_pitched}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.hits}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.runs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.earned_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.base_on_balls}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.strike_outs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">{pitcher.stats.home_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--text-primary)">
                {pitcher.stats.pitches_thrown}-{pitcher.stats.strikes}
            </td>
            <td className="px-2 py-1.5 text-right pr-3 text-(--text-secondary)">{pitcher.season_stats.era}</td>
        </tr>
    );
}


function PointsBadge({ points, bg_color }: { points: number, bg_color?: string | null }) {
    return (
        <span 
            className="inline-flex items-center justify-center min-w-5 px-1 py-0.5 rounded-full text-[10px] font-bold leading-none"
            style={
                { backgroundColor: bg_color ?? 'var(--text-secondary)/15', color: getContrastColor(bg_color ?? 'var(--text-secondary)/15') }}    
        >
            {points}
        </span>
    );
}


function GameInfo({ away, home }: { away: BoxscoreTeamData; home: BoxscoreTeamData }) {
    const allInfo = [...away.info, ...home.info];

    if (allInfo.length === 0) return null;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3 space-y-3">
            <div className="font-black text-sm text-(--text-primary)">Game Info</div>
            {allInfo.map((section, idx) => (
                <div key={idx} className="space-y-1">
                    <div className="text-xs font-bold text-(--text-secondary) uppercase tracking-wide">{section.title}</div>
                    {section.fieldList.map((field, fidx) => (
                        <div key={fidx} className="flex gap-2 text-xs">
                            <span className="font-bold text-(--text-primary) shrink-0">{field.label}:</span>
                            <span className="text-(--text-secondary)">{field.value}</span>
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
}
