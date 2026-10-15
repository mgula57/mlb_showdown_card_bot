import { useState } from 'react';
import { FaCheck, FaCopy, FaLink, FaPlay, FaRobot, FaSpinner, FaUserMinus } from 'react-icons/fa6';
import {
    addLeagueBots, removeLeagueMember, startDraft, type LeagueMember, type LeagueState,
} from '../../api/leagues';
import {
    ERROR_BOX_CLASS, PRIMARY_BUTTON_CLASS, SECONDARY_BUTTON_CLASS, SECTION_LABEL_CLASS, errorMessage,
} from './leagueUi';

type Props = {
    state: LeagueState;
    token: string;
    userId?: string;
    onStateChange: (state: LeagueState) => void;
    /** The draft started - the caller refetches and moves to the draft room. */
    onDraftStarted: () => void;
    /** The caller left the league. */
    onLeft: () => void;
};

/** Who's in the league, how to invite more, and (commissioner) filling seats and starting the draft. */
export function LeagueMembersTab({ state, token, userId, onStateChange, onDraftStarted, onLeft }: Props) {
    const { league, members, is_commissioner: isCommissioner } = state;
    const [busy, setBusy] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState<'code' | 'link' | null>(null);

    const isOpen = league.status === 'open';
    const openSeats = league.settings.team_count - members.length;
    const inviteLink = `${window.location.origin}/leagues/join/${league.join_code}`;

    async function run(key: string, action: () => Promise<void>) {
        setBusy(key);
        setError(null);
        try {
            await action();
        } catch (err) {
            setError(errorMessage(err));
        } finally {
            setBusy(null);
        }
    }

    function copy(text: string, which: 'code' | 'link') {
        navigator.clipboard?.writeText(text).then(() => {
            setCopied(which);
            window.setTimeout(() => setCopied(null), 1500);
        });
    }

    const handleRemove = (member: LeagueMember) => run(`remove-${member.member_id}`, async () => {
        const next = await removeLeagueMember(token, league.league_id, member.member_id);
        if (member.user_id === userId) onLeft();
        else onStateChange(next);
    });

    return (
        <div className="flex flex-col gap-5">
            {isOpen && (
                <section className="flex flex-col gap-2">
                    <div className={SECTION_LABEL_CLASS}>Invite</div>
                    <div className="flex flex-wrap items-center gap-2">
                        <div className="flex items-center gap-2 rounded-xl border border-(--divider) bg-(--background-secondary) pl-3 pr-1 py-1">
                            <span className="text-[18px] font-black tracking-[0.2em] text-(--text-primary) tabular-nums">{league.join_code}</span>
                            <button type="button" onClick={() => copy(league.join_code, 'code')} className={SECONDARY_BUTTON_CLASS} title="Copy code">
                                {copied === 'code' ? <FaCheck /> : <FaCopy />}
                            </button>
                        </div>
                        <button type="button" onClick={() => copy(inviteLink, 'link')} className={SECONDARY_BUTTON_CLASS}>
                            {copied === 'link' ? <FaCheck /> : <FaLink />}
                            {copied === 'link' ? 'Link copied' : 'Copy invite link'}
                        </button>
                    </div>
                </section>
            )}

            <section className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                    <div className={SECTION_LABEL_CLASS}>Members · {members.length}/{league.settings.team_count}</div>
                    {isCommissioner && isOpen && openSeats > 0 && (
                        <button type="button" onClick={() => run('bots', async () => onStateChange(await addLeagueBots(token, league.league_id)))} disabled={busy !== null} className={SECONDARY_BUTTON_CLASS}>
                            {busy === 'bots' ? <FaSpinner className="animate-spin" /> : <FaRobot />}
                            Fill {openSeats} seat{openSeats === 1 ? '' : 's'} with bots
                        </button>
                    )}
                </div>
                <div className="flex flex-col rounded-xl border border-(--divider) divide-y divide-(--divider) overflow-hidden">
                    {members.map(member => {
                        const isMe = member.user_id === userId;
                        const isMemberCommissioner = member.user_id === league.commissioner_user_id;
                        const canRemove = isOpen && !isMemberCommissioner && (isCommissioner || isMe);
                        return (
                            <div key={member.member_id} className="flex items-center gap-3 px-3 py-2 bg-(--background-secondary)">
                                <div className="size-8 shrink-0 rounded-full bg-(--background-tertiary) flex items-center justify-center text-[12px] font-black text-(--text-secondary) overflow-hidden">
                                    {member.avatar_url
                                        ? <img src={member.avatar_url} alt="" className="size-full object-cover" />
                                        : member.user_id ? member.display_name.slice(0, 1).toUpperCase() : <FaRobot />}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="text-[13px] font-bold text-(--text-primary) truncate">{member.display_name}</div>
                                    <div className="text-[11px] text-(--text-tertiary)">
                                        {[isMemberCommissioner && 'Commissioner', !member.user_id && 'Bot', isMe && 'You'].filter(Boolean).join(' · ') || 'Member'}
                                    </div>
                                </div>
                                {canRemove && (
                                    <button type="button" onClick={() => handleRemove(member)} disabled={busy !== null} className={SECONDARY_BUTTON_CLASS} title={isMe ? 'Leave league' : 'Remove'}>
                                        {busy === `remove-${member.member_id}` ? <FaSpinner className="animate-spin" /> : <FaUserMinus />}
                                        <span className="hidden sm:inline">{isMe ? 'Leave' : 'Remove'}</span>
                                    </button>
                                )}
                            </div>
                        );
                    })}
                    {isOpen && Array.from({ length: Math.max(0, openSeats) }, (_, i) => (
                        <div key={`open-${i}`} className="flex items-center gap-3 px-3 py-2 text-[12px] text-(--text-tertiary)">
                            <div className="size-8 shrink-0 rounded-full border border-dashed border-(--divider)" />
                            Open seat
                        </div>
                    ))}
                </div>
            </section>

            <section className="flex flex-col gap-2">
                <div className={SECTION_LABEL_CLASS}>Rules</div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[12px]">
                    {[
                        ['Roster', `${league.settings.roster_size} cards`],
                        ['Rotation', `${league.settings.num_starters} starters`],
                        ['Bench / bullpen', `${league.settings.min_bench}+ / ${league.settings.min_bullpen}+`],
                        ['Points cap', league.settings.pts_cap ? `${league.settings.pts_cap} pts` : 'None'],
                    ].map(([label, value]) => (
                        <div key={label} className="rounded-lg border border-(--divider) bg-(--background-secondary) px-3 py-2">
                            <div className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">{label}</div>
                            <div className="font-bold text-(--text-primary)">{value}</div>
                        </div>
                    ))}
                </div>
            </section>

            {error && <div className={ERROR_BOX_CLASS}>{error}</div>}

            {isCommissioner && isOpen && (
                <section className="flex flex-col items-start gap-1">
                    <button
                        type="button"
                        onClick={() => run('draft', async () => { await startDraft(token, league.league_id, 1); onDraftStarted(); })}
                        disabled={busy !== null || members.length < 2}
                        className={PRIMARY_BUTTON_CLASS}
                    >
                        {busy === 'draft' ? <FaSpinner className="animate-spin" /> : <FaPlay className="text-[10px]" />}
                        Start Draft
                    </button>
                    <span className="text-[11px] text-(--text-tertiary)">
                        {members.length < 2
                            ? 'You need at least 2 teams to draft.'
                            : openSeats > 0
                                ? `${openSeats} seat${openSeats === 1 ? ' is' : 's are'} still open - the draft runs with the ${members.length} teams here. Fill seats with bots first if you want ${league.settings.team_count}.`
                                : 'The draft order is random. Members are locked in once it starts.'}
                    </span>
                </section>
            )}
        </div>
    );
}
