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
    /** Compact variant for the mobile field view: same translucent-over-grass framing as the
     *  desktop bug, but with the team records dropped and every text/symbol stepped down a size
     *  so it takes less vertical room above the field. */
    compact?: boolean;
};

export default function ScoreHeader({ game, className = "", compact = false }: ScoreHeaderProps) {
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

    const flagEm = compact ? '1.1em' : '1.5em';
    const badgeSize = compact ? "w-8 h-8 text-xs" : "w-10 h-10 text-sm";
    const scoreSize = compact ? "text-[24px]" : "text-[32px]";
    const nameSize = compact ? "text-[13px]" : "text-[14px]";

    return (
        <div
            className={`rounded-xl border border-(--divider) bg-(--background-secondary)/30 ${
                compact ? "mx-2 px-3 py-1.5" : "mx-2 px-4 py-2 lg:py-4"
            } ${className}`}
        >
            <div className={`grid grid-cols-[1fr_auto_1fr] items-center ${compact ? "gap-2" : "gap-4"}`}>
                {/* Away team - left aligned, score next to the badge rather than in the center */}
                <div className="flex flex-col gap-1">
                    {awayCode && (
                        <ReactCountryFlag countryCode={awayCode} svg style={{ width: flagEm, height: flagEm }} />
                    )}
                    <div className={`flex items-center ${compact ? "gap-2" : "gap-2.5"}`}>
                        <div
                            className={`flex items-center justify-center rounded-lg font-bold leading-none shrink-0 ${badgeSize}`}
                            style={{ backgroundColor: awayBadgeBg, color: awayBadgeText }}
                        >{away.team.abbreviation}</div>
                        <span className={`${scoreSize} font-bold leading-none text-(--primary)`}>{awayRuns}</span>
                    </div>
                    <div className={`${nameSize} hidden sm:block font-semibold text-(--primary) leading-snug`}>{away.team.name}</div>
                    {!compact && awayRecord && (
                        <div className="text-[12px] text-(--secondary)">{awayRecord.wins ?? 0}-{awayRecord.losses ?? 0}</div>
                    )}
                </div>

                {/* Center: game state, count and bases — the situational info, not the score */}
                <div className={`flex flex-col items-center ${compact ? "gap-1.5" : "gap-2"}`}>
                    {isInProgress && inningStr ? (
                        <div className={`inline-flex items-center gap-1.5 rounded-full bg-(--background-primary) border border-(--divider) ${
                            compact ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-[11px]"
                        }`}>
                            <span className="live-pulse w-1.75 h-1.75 rounded-full bg-(--live) shrink-0" />
                            <span className="font-semibold tracking-[0.5px] text-(--live)">LIVE</span>
                            <span className="text-(--secondary) mx-0.5">·</span>
                            <span className="text-(--secondary)">{inningStr}</span>
                        </div>
                    ) : (
                        <div className={`font-semibold text-(--secondary) uppercase tracking-wide ${compact ? "text-[10px]" : "text-xs"}`}>{game.detailedState}</div>
                    )}

                    {isInProgress && (
                        <div className={`flex items-center ${compact ? "gap-2.5" : "gap-3"}`}>
                            {hasCount && (
                                <div className="text-center">
                                    <div className="text-[9px] uppercase tracking-wide text-(--secondary)">Count</div>
                                    <div className={`font-bold leading-none text-(--primary) ${compact ? "text-[14px]" : "text-[16px]"}`}>{situation?.balls}–{situation?.strikes}</div>
                                </div>
                            )}
                            <BasesDiamond bases={bases} outs={situation?.outs} size={compact ? 30 : "sm"} />
                        </div>
                    )}
                </div>

                {/* Home team - right aligned, mirrored: score then badge so the abbreviation
                    anchors the outer edge same as away's */}
                <div className="flex flex-col items-end gap-1">
                    {homeCode && (
                        <div className="self-end">
                            <ReactCountryFlag countryCode={homeCode} svg style={{ width: flagEm, height: flagEm }} />
                        </div>
                    )}
                    <div className={`flex items-center ${compact ? "gap-2" : "gap-2.5"}`}>
                        <span className={`${scoreSize} font-bold leading-none text-(--primary)`}>{homeRuns}</span>
                        <div
                            className={`flex items-center justify-center rounded-lg font-bold leading-none shrink-0 ${badgeSize}`}
                            style={{ backgroundColor: homeBadgeBg, color: homeBadgeText }}
                        >{home.team.abbreviation}</div>
                    </div>
                    <div className={`${nameSize} hidden sm:block font-semibold text-(--primary) leading-snug text-right`}>{home.team.name}</div>
                    {!compact && homeRecord && (
                        <div className="text-[12px] text-(--secondary)">{homeRecord.wins ?? 0}-{homeRecord.losses ?? 0}</div>
                    )}
                </div>
            </div>
        </div>
    );
}
