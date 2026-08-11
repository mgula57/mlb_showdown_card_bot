/**
 * @fileoverview The score/inning/count/bases summary bug at the top of a game's detail view.
 * Reads only `GameView`, so it renders identically for a live feed, a stored sim, or (later) a
 * historical replay frame — the caller decides which `GameView` to hand it.
 */
import ReactCountryFlag from "react-country-flag";

import type { GameView } from "../../../domain/game";
import { getReadableTextColor } from "../../../functions/colors";
import { BasesDiamond } from "../BasesDiamond";

type ScoreHeaderProps = {
    game: GameView;
    className?: string;
};

export default function ScoreHeader({ game, className = "" }: ScoreHeaderProps) {
    const { away, home } = game;
    const situation = game.situation;
    const isInProgress = game.state === "LIVE";

    const awayCode = away.team.countryCode;
    const homeCode = home.team.countryCode;
    const awayRecord = away.record;
    const homeRecord = home.record;

    const awayBadgeBg = away.team.primaryColor ?? '#374151';
    const awayBadgeText = getReadableTextColor(awayBadgeBg, '#ffffff');
    const homeBadgeBg = home.team.primaryColor ?? '#374151';
    const homeBadgeText = getReadableTextColor(homeBadgeBg, '#ffffff');

    const awayRuns = away.score ?? 0;
    const homeRuns = home.score ?? 0;

    const inningHalf = situation?.isTop ? "Top" : "Bot";
    const inningStr = situation?.inningLabel ? `${inningHalf} ${situation.inningLabel}` : "";

    const hasCount = situation?.balls != null && situation?.strikes != null;
    const bases = { first: situation?.bases.first ?? null, second: situation?.bases.second ?? null, third: situation?.bases.third ?? null };

    return (
        <div className={`rounded-xl border border-(--divider) bg-(--background-secondary)/30 mx-2 p-4 ${className}`}>
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
                {/* Away team - left aligned, score next to the badge rather than in the center */}
                <div className="flex flex-col gap-1">
                    {awayCode && (
                        <ReactCountryFlag countryCode={awayCode} svg style={{ width: '1.5em', height: '1.5em' }} />
                    )}
                    <div className="flex items-center gap-2.5">
                        <div
                            className="flex items-center justify-center w-10 h-10 rounded-lg font-bold text-sm leading-none shrink-0"
                            style={{ backgroundColor: awayBadgeBg, color: awayBadgeText }}
                        >{away.team.abbreviation}</div>
                        <span className="text-[32px] font-bold leading-none text-(--primary)">{awayRuns}</span>
                    </div>
                    <div className="text-[14px] hidden sm:block font-semibold text-(--primary) leading-snug">{away.team.name}</div>
                    {awayRecord && (
                        <div className="text-[12px] text-(--secondary)">{awayRecord.wins ?? 0}-{awayRecord.losses ?? 0}</div>
                    )}
                </div>

                {/* Center: game state, count and bases — the situational info, not the score */}
                <div className="flex flex-col items-center gap-2">
                    {isInProgress && inningStr ? (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-(--background-primary) border border-(--divider) text-[11px]">
                            <span className="live-pulse w-1.75 h-1.75 rounded-full bg-(--live) shrink-0" />
                            <span className="font-semibold tracking-[0.5px] text-(--live)">LIVE</span>
                            <span className="text-(--secondary) mx-0.5">·</span>
                            <span className="text-(--secondary)">{inningStr}</span>
                        </div>
                    ) : (
                        <div className="text-xs font-semibold text-(--secondary) uppercase tracking-wide">{game.detailedState}</div>
                    )}

                    {isInProgress && (
                        <div className="flex items-center gap-3">
                            {hasCount && (
                                <div className="text-center">
                                    <div className="text-[9px] uppercase tracking-wide text-(--secondary)">Count</div>
                                    <div className="text-[16px] font-bold leading-none text-(--primary)">{situation?.balls}–{situation?.strikes}</div>
                                </div>
                            )}
                            <BasesDiamond bases={bases} outs={situation?.outs} size="sm" />
                        </div>
                    )}
                </div>

                {/* Home team - right aligned, mirrored: score then badge so the abbreviation
                    anchors the outer edge same as away's */}
                <div className="flex flex-col items-end gap-1">
                    {homeCode && (
                        <div className="self-end">
                            <ReactCountryFlag countryCode={homeCode} svg style={{ width: '1.5em', height: '1.5em' }} />
                        </div>
                    )}
                    <div className="flex items-center gap-2.5">
                        <span className="text-[32px] font-bold leading-none text-(--primary)">{homeRuns}</span>
                        <div
                            className="flex items-center justify-center w-10 h-10 rounded-lg font-bold text-sm leading-none shrink-0"
                            style={{ backgroundColor: homeBadgeBg, color: homeBadgeText }}
                        >{home.team.abbreviation}</div>
                    </div>
                    <div className="text-[14px] hidden sm:block  font-semibold text-(--primary) leading-snug text-right">{home.team.name}</div>
                    {homeRecord && (
                        <div className="text-[12px] text-(--secondary)">{homeRecord.wins ?? 0}-{homeRecord.losses ?? 0}</div>
                    )}
                </div>
            </div>
        </div>
    );
}
