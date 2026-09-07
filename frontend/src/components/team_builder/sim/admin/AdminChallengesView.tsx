import { useCallback, useEffect, useState } from 'react';
import { FaPlus, FaArrowsRotate, FaBolt, FaPen, FaTrash, FaSpinner } from 'react-icons/fa6';
import BackButton from '../../../shared/BackButton';
import { Modal } from '../../../shared/Modal';
import { challengeCategoryMeta } from '../challengeCategory';
import type { ChallengeInstance } from '../../../../api/sim';
import {
    type ChallengeTemplate,
    type ChallengeTemplateInput,
    createChallengeTemplate,
    deleteChallengeTemplate,
    fetchAdminChallenges,
    generateChallengeInstance,
    runChallengeRotation,
    updateChallengeTemplate,
} from '../../../../api/adminChallenges';
import { ChallengeTemplateForm } from './ChallengeTemplateForm';

type Props = {
    token: string;
    onBack: () => void;
};

const GOAL_LABEL: Record<string, string> = {
    made_playoffs: 'Playoffs',
    win_division: 'Division',
    win_pennant: 'Pennant',
    win_world_series: 'World Series',
    min_wins: 'Win total',
    beat_team_record: 'Beat record',
};

function goalSummary(t: ChallengeTemplate): string {
    if (t.goal_type === 'min_wins') return `${t.goal_value?.min_wins ?? '?'} wins`;
    if (t.goal_type === 'beat_team_record') return `Beat ${t.goal_value?.target_abbr ?? '?'}`;
    return GOAL_LABEL[t.goal_type] ?? t.goal_type;
}

function expiresIn(iso: string): string {
    const ms = new Date(iso).getTime() - Date.now();
    if (ms <= 0) return 'expired';
    const days = Math.floor(ms / 86_400_000);
    if (days >= 1) return `${days}d left`;
    return `${Math.max(1, Math.floor(ms / 3_600_000))}h left`;
}

/** Admin-only Team Challenge template manager. Its own routed view (`/teams/admin/challenges`)
 *  so it isn't buried under the Challenges sub-tab state. Template CRUD, on-demand instance
 *  generation, and "run rotation now". */
export function AdminChallengesView({ token, onBack }: Props) {
    const [templates, setTemplates] = useState<ChallengeTemplate[] | null>(null);
    const [liveInstances, setLiveInstances] = useState<ChallengeInstance[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);
    const [busyId, setBusyId] = useState<string | null>(null);
    const [rotating, setRotating] = useState(false);
    const [editing, setEditing] = useState<ChallengeTemplate | 'new' | null>(null);
    const [formError, setFormError] = useState<string | null>(null);
    const [formBusy, setFormBusy] = useState(false);

    const load = useCallback(async () => {
        try {
            const data = await fetchAdminChallenges(token);
            setTemplates(data.templates);
            setLiveInstances(data.live_instances);
            setError(null);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to load templates.');
        }
    }, [token]);

    useEffect(() => { void load(); }, [load]);

    const submitForm = async (input: ChallengeTemplateInput) => {
        setFormBusy(true);
        setFormError(null);
        try {
            if (editing === 'new') {
                await createChallengeTemplate(token, input);
                setNotice(`Created "${input.title}".`);
            } else if (editing) {
                await updateChallengeTemplate(token, editing.template_id, input);
                setNotice(`Saved "${input.title}".`);
            }
            setEditing(null);
            await load();
        } catch (e) {
            setFormError(e instanceof Error ? e.message : 'Save failed.');
        } finally {
            setFormBusy(false);
        }
    };

    const withRowBusy = async (id: string, fn: () => Promise<void>) => {
        setBusyId(id);
        try {
            await fn();
            await load();
        } catch (e) {
            setNotice(e instanceof Error ? e.message : 'Action failed.');
        } finally {
            setBusyId(null);
        }
    };

    const toggleActive = (t: ChallengeTemplate) =>
        withRowBusy(t.template_id, () => updateChallengeTemplate(token, t.template_id, { active: !t.active }).then(() => {}));

    const generate = (t: ChallengeTemplate) => withRowBusy(t.template_id, async () => {
        let res;
        try {
            res = await generateChallengeInstance(token, t.template_id, false);
        } catch (e) {
            if (e instanceof Error && /already has a live instance/i.test(e.message)
                && window.confirm(`"${t.title}" already has a live instance. Create a second one?`)) {
                res = await generateChallengeInstance(token, t.template_id, true);
            } else {
                throw e;
            }
        }
        setNotice(`Generated ${res.year} ${res.replaces_abbr} for "${t.title}".`);
    });

    const remove = (t: ChallengeTemplate) => {
        if (!window.confirm(`Delete "${t.title}"? Expired instances go too. This can't be undone.`)) return;
        return withRowBusy(t.template_id, async () => {
            await deleteChallengeTemplate(token, t.template_id);
            setNotice(`Deleted "${t.title}".`);
        });
    };

    const rotate = async () => {
        setRotating(true);
        try {
            const res = await runChallengeRotation(token);
            const parts = [`pruned ${res.pruned}`, `created ${res.created.length}`];
            if (res.skipped.length) parts.push(`skipped ${res.skipped.length}`);
            setNotice(`Rotation: ${parts.join(', ')}.`);
            await load();
        } catch (e) {
            setNotice(e instanceof Error ? e.message : 'Rotation failed.');
        } finally {
            setRotating(false);
        }
    };

    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between gap-2">
                <BackButton onBack={onBack} label="Challenges" />
                <div className="flex flex-wrap gap-2">
                    <button
                        type="button"
                        onClick={() => { setFormError(null); setEditing('new'); }}
                        className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[12px] font-bold bg-(--secondary) text-(--background-primary) hover:opacity-90 cursor-pointer"
                    >
                        <FaPlus className="text-[10px]" /> New template
                    </button>
                    <button
                        type="button"
                        onClick={rotate}
                        disabled={rotating}
                        className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[12px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) hover:border-(--text-tertiary) disabled:opacity-40 cursor-pointer"
                    >
                        {rotating ? <FaSpinner className="animate-spin text-[10px]" /> : <FaArrowsRotate className="text-[10px]" />} Run rotation now
                    </button>
                </div>
            </div>

            <div>
                <h3 className="text-[16px] font-black text-(--text-primary)">Challenge Templates</h3>
                <p className="text-[12px] text-(--text-tertiary)">
                    Templates feed the weekly rotation — one live challenge per category. Generate forces one live now.
                </p>
            </div>

            {notice && <div className="text-[12px] text-(--text-secondary) px-3 py-2 rounded-lg bg-(--background-tertiary)">{notice}</div>}
            {error && <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">{error}</div>}

            {liveInstances.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                    {liveInstances.map(inst => {
                        const meta = challengeCategoryMeta(inst.category);
                        return (
                            <span
                                key={inst.instance_id}
                                className="flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-full bg-(--background-tertiary)"
                                style={{ color: `var(${meta.cssVar})` }}
                            >
                                {meta.label}: {inst.year} {inst.replaces_abbr}
                                <span className="text-(--text-tertiary)">· {expiresIn(inst.expires_at)}</span>
                            </span>
                        );
                    })}
                </div>
            )}

            {templates === null ? (
                <div className="flex justify-center py-10"><FaSpinner className="animate-spin text-(--text-tertiary) text-xl" /></div>
            ) : templates.length === 0 ? (
                <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No templates yet — create one to get started.</p>
            ) : (
                <div className="flex flex-col divide-y divide-(--divider) rounded-lg border border-(--divider)">
                    {templates.map(t => {
                        const meta = challengeCategoryMeta(t.category);
                        const rowBusy = busyId === t.template_id;
                        return (
                            <div key={t.template_id} className="flex items-center gap-2 px-3 py-2.5">
                                <span className="w-1.5 h-9 rounded-full shrink-0" style={{ backgroundColor: `var(${meta.cssVar})` }} />
                                <div className="min-w-0 flex-1">
                                    <div className="flex items-center gap-2">
                                        <span className={`text-[13px] font-bold truncate ${t.active ? 'text-(--text-primary)' : 'text-(--text-tertiary)'}`}>{t.title}</span>
                                        {!t.active && <span className="text-[10px] uppercase font-bold text-(--text-tertiary)">inactive</span>}
                                        {t.live_instance_count > 0 && <span className="text-[10px] uppercase font-bold" style={{ color: `var(${meta.cssVar})` }}>live</span>}
                                    </div>
                                    <div className="text-[11px] text-(--text-tertiary) truncate">
                                        {t.slug} · {goalSummary(t)} · {t.pts_limit ? `${t.pts_limit} pts` : 'no cap'} · {t.year_pool} / {t.replaces_pool}
                                    </div>
                                </div>
                                {rowBusy ? (
                                    <FaSpinner className="animate-spin text-(--text-tertiary) text-[12px]" />
                                ) : (
                                    <div className="flex items-center gap-1 shrink-0">
                                        <button type="button" title="Generate instance now" onClick={() => generate(t)} className="p-1.5 rounded-md hover:bg-(--background-tertiary) text-(--text-secondary) cursor-pointer"><FaBolt className="text-[11px]" /></button>
                                        <button type="button" title={t.active ? 'Deactivate' : 'Activate'} onClick={() => toggleActive(t)} className="px-1.5 py-1 rounded-md text-[10px] font-bold hover:bg-(--background-tertiary) text-(--text-secondary) cursor-pointer">{t.active ? 'ON' : 'OFF'}</button>
                                        <button type="button" title="Edit" onClick={() => { setFormError(null); setEditing(t); }} className="p-1.5 rounded-md hover:bg-(--background-tertiary) text-(--text-secondary) cursor-pointer"><FaPen className="text-[11px]" /></button>
                                        <button type="button" title="Delete" onClick={() => remove(t)} className="p-1.5 rounded-md hover:bg-red-400/10 text-red-400 cursor-pointer"><FaTrash className="text-[11px]" /></button>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {editing && (
                <Modal
                    title={editing === 'new' ? 'New challenge Template' : `Edit "${editing.title}"`}
                    subtitle="Templates feed the weekly rotation — one live challenge per category."
                    size="lg"
                    onClose={() => setEditing(null)}
                >
                    <ChallengeTemplateForm
                        initial={editing === 'new' ? undefined : editing}
                        submitLabel={editing === 'new' ? 'Create template' : 'Save changes'}
                        busy={formBusy}
                        error={formError}
                        onSubmit={submitForm}
                        onCancel={() => setEditing(null)}
                    />
                </Modal>
            )}
        </div>
    );
}
