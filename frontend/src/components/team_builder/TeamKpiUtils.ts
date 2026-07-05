import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';

export type KpiTile = { label: string; value: string };

export function avgOf(nums: (number | string | null | undefined)[]): number | null {
    const valid = nums.map(n => (n != null ? Number(n) : null)).filter((n): n is number => n != null && !isNaN(n));
    return valid.length > 0 ? valid.reduce((a, b) => a + b, 0) / valid.length : null;
}

// Max defense value across non-DH, non-C positions (excludes catcher arm)
export function cardMaxFieldDefense(card: CardDatabaseRecord): number | null {
    const pad = card.positions_and_defense;
    if (!pad) return null;
    const values = Object.entries(pad)
        .filter(([pos]) => pos !== 'DH' && pos !== 'C')
        .map(([, val]) => (typeof val === 'number' ? val : null))
        .filter((v): v is number => v != null);
    return values.length > 0 ? Math.max(...values) : null;
}

export const fmtBat = (n: number) => n.toFixed(3).replace('0.', '.');
export const fmtDef = (n: number) => (n > 0 ? `+${n}` : `${n}`);
export const fmtAvg = (n: number) => Math.round(n).toString();

export function buildLineupKpis(
    cards: CardDatabaseRecord[],
    totalPts: number,
    totalDefIF: number | null,
    totalDefOF: number | null,
): KpiTile[] {
    const count = cards.length;
    const avgPts   = count > 0 ? totalPts / count : null;
    const avgOps   = avgOf(cards.map(c => c.real_onbase_plus_slugging));
    const avgSpeed = avgOf(cards.map(c => c.speed));
    const avgOb    = avgOf(cards.map(c => c.command));
    const totalDef = (totalDefIF ?? 0) + (totalDefOF ?? 0);
    return [
        avgPts   != null ? { label: 'Avg PTS', value: fmtAvg(avgPts) }   : null,
        avgOps   != null ? { label: 'Exp OPS', value: fmtBat(avgOps) }   : null,
        avgSpeed != null ? { label: 'Avg SPD', value: fmtAvg(avgSpeed) } : null,
        avgOb    != null ? { label: 'Avg OB',  value: avgOb.toFixed(1) } : null,
        totalDef !== 0   ? { label: 'DEF',     value: fmtDef(totalDef) } : null,
    ].filter(Boolean) as KpiTile[];
}

export function buildBenchKpis(
    cards: CardDatabaseRecord[],
    multiplier: number,
): KpiTile[] {
    const count   = cards.length;
    const rawPts  = cards.reduce((sum, c) => sum + (c.points ?? 0), 0);
    const avgPts  = count > 0 ? rawPts / count : null;
    const avgSpd  = avgOf(cards.map(c => c.speed));
    const totalDef = cards.reduce((sum, c) => sum + (cardMaxFieldDefense(c) ?? 0), 0);
    return [
        avgPts   != null  ? { label: 'Avg PTS',    value: fmtAvg(avgPts) }    : null,
        multiplier !== 1  ? { label: 'Multiplier',  value: `${multiplier}x` }  : null,
        avgSpd   != null  ? { label: 'Avg SPD',    value: fmtAvg(avgSpd) }    : null,
        totalDef !== 0    ? { label: 'DEF',         value: fmtDef(totalDef) }  : null,
    ].filter(Boolean) as KpiTile[];
}

export function buildPitcherKpis(
    cards: CardDatabaseRecord[],
    totalPts: number,
): KpiTile[] {
    const count   = cards.length;
    const avgPts  = count > 0 ? totalPts / count : null;
    const avgEra  = avgOf(cards.map(c => c.real_earned_run_avg));
    const avgWhip = avgOf(cards.map(c => c.real_whip));
    const avgCtl  = avgOf(cards.map(c => c.command));
    const avgOuts = avgOf(cards.map(c => c.outs));
    return [
        avgPts  != null ? { label: 'Avg PTS',  value: fmtAvg(avgPts) }        : null,
        avgEra  != null ? { label: 'Exp ERA',  value: avgEra.toFixed(2) }      : null,
        avgWhip != null ? { label: 'Exp WHIP', value: avgWhip.toFixed(2) }     : null,
        avgCtl  != null ? { label: 'Avg CTL',  value: avgCtl.toFixed(1) }      : null,
        avgOuts != null ? { label: 'Avg OUTS', value: avgOuts.toFixed(1) }     : null,
    ].filter(Boolean) as KpiTile[];
}
