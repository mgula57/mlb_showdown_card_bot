/**
 * @fileoverview The full-width strip that marks a page as being in a special mode: the release
 * builder's PREVIEW/EDITING bar, the team builder's DRAFTING/EDITING bar, and the game page's
 * TAKEOVER SIM bar.
 *
 * A flat fill (see frontend/DESIGN.md: no decorative gradients). A team's own bar passes its team
 * `color` and the ink is picked for contrast by `bannerTokens`; app modes pass a brand `tone`.
 * `ModeBannerButton`s inside it pick up the same ink.
 */
import { createContext, useContext, type ReactNode } from "react";
import { bannerTokens, BANNER_TOKENS_ON_DARK, type BannerTokens } from "../../functions/colors";

type ModeBannerTone = 'navy' | 'red';

const TONE_CLASSES: Record<ModeBannerTone, string> = {
    navy: 'bg-(--showdown-blue)',
    red: 'bg-(--showdown-red)',
};

const BannerTokensContext = createContext<BannerTokens>(BANNER_TOKENS_ON_DARK);

type ModeBannerProps = {
    /** A team color for a team's own bar. Takes precedence over `tone`. */
    color?: string;
    /** Brand fill for app modes (navy: preview, red: live edits). */
    tone?: ModeBannerTone;
    label: ReactNode;
    /** Hidden below md, where the bar is too narrow for a full sentence. */
    detail?: ReactNode;
    /** Whether the leading status dot pulses. */
    pulse?: boolean;
    /** Trailing controls, e.g. `ModeBannerButton`s. */
    children?: ReactNode;
    className?: string;
};

export function ModeBanner({ color, tone = 'navy', label, detail, pulse = false, children, className = '' }: ModeBannerProps) {
    const tokens = color ? bannerTokens(color) : BANNER_TOKENS_ON_DARK;
    return (
        <BannerTokensContext.Provider value={tokens}>
            <div
                className={`flex items-center gap-3 px-4 py-2 shrink-0 ${color ? '' : TONE_CLASSES[tone]} ${className}`}
                style={color ? { backgroundColor: color } : undefined}
            >
                <span
                    className={`w-2 h-2 rounded-full shrink-0 ${pulse ? 'animate-pulse' : ''}`}
                    style={{ backgroundColor: tokens.dot }}
                />
                <span className="text-[11px] font-bold flex-1 flex items-center gap-4" style={{ color: tokens.fill }}>
                    {label}
                    {detail && <span className="hidden md:inline font-normal">{detail}</span>}
                </span>
                {children && <div className="flex items-center gap-2 shrink-0">{children}</div>}
            </div>
        </BannerTokensContext.Provider>
    );
}

type ModeBannerButtonProps = {
    onClick: () => void;
    disabled?: boolean;
    title?: string;
    /** Ink for a button on a hand-built bar outside `ModeBanner`; defaults to the enclosing banner's. */
    tokens?: BannerTokens;
    className?: string;
    children: ReactNode;
};

/** A compact translucent button on a mode bar, inked to read against the bar's fill. */
export function ModeBannerButton({ onClick, disabled, title, tokens, className = '', children }: ModeBannerButtonProps) {
    const contextTokens = useContext(BannerTokensContext);
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            title={title}
            className={`flex items-center gap-1 rounded-control px-2 py-1 h-7 text-[11px] font-bold whitespace-nowrap cursor-pointer transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${(tokens ?? contextTokens).btnClass} ${className}`}
        >
            {children}
        </button>
    );
}
