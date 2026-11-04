import { useMemo, type ReactNode } from 'react';
import { FaArrowDown, FaArrowUp, FaPlus, FaTrash, FaXmark } from 'react-icons/fa6';
import type { ReleaseCard } from '../../api/releases';
import FormDropdown from '../customs/FormDropdown';
import FormEnabler from '../customs/FormEnabler';
import { ParallelDropdown } from '../customs/CardStyleFields';
import { editionOptions, imageColoringOptions, parallelColoringOptions, type CardStyleSettings } from '../customs/cardStyle';
import CustomSelect from '../shared/CustomSelect';
import MultiSelect from '../shared/MultiSelect';
import IconButton from '../shared/IconButton';
import { Eyebrow } from '../shared/Eyebrow';
import { Plate } from '../shared/Plate';
import { buttonClass } from '../shared/buttonStyles';
import { poolFilterValueOptions, type PoolFilterBy } from './poolGrouping';
import {
    RULE_STYLE_KEYS, STYLE_RULE_DIMENSIONS, newStyleRule, styleRuleMatches,
    type EditionStyleRule, type RuleStyleKey,
} from './editionStyle';

const RULE_STYLE_LABELS: Record<RuleStyleKey, string> = {
    image_parallel: 'Image Parallel',
    image_parallel_coloring: 'Parallel Coloring',
    edition: 'Edition',
    image_coloring: 'Image Coloring',
    show_year_text: 'Show Year as Text',
    is_dark_mode: 'Dark Mode',
    hide_team_logo: 'Remove Team',
};

const BOOLEAN_RULE_STYLE_KEYS = new Set<RuleStyleKey>(['show_year_text', 'is_dark_mode', 'hide_team_logo']);

const dimensionLabel = (key: PoolFilterBy): string => STYLE_RULE_DIMENSIONS.find(o => o.value === key)?.label ?? key;

type EditionStyleRulesProps = {
    rules: EditionStyleRule[];
    onChange: (rules: EditionStyleRule[]) => void;
    /** The edition's cards, for condition values and match counts */
    cards: ReleaseCard[];
    /** The edition style the rules layer over, so a newly added toggle starts flipped from it */
    editionStyle: CardStyleSettings;
};

/** "IF ... THEN ..." style rules for an edition, applied in order over the edition style. */
export function EditionStyleRules({ rules, onChange, cards, editionStyle }: EditionStyleRulesProps) {
    const updateRule = (index: number, rule: EditionStyleRule) => onChange(rules.map((r, i) => i === index ? rule : r));
    const moveRule = (index: number, offset: number) => {
        const next = [...rules];
        [next[index], next[index + offset]] = [next[index + offset], next[index]];
        onChange(next);
    };
    return (
        <div className="flex flex-col gap-3">
            <p className="text-[12px] text-(--text-secondary)">
                Restyle the cards that match, on top of the default style. Later rules win, and a card's own style edits win over rules.
            </p>
            {rules.map((rule, index) => (
                <StyleRuleEditor
                    key={rule.id}
                    rule={rule}
                    index={index}
                    cards={cards}
                    editionStyle={editionStyle}
                    onChange={next => updateRule(index, next)}
                    onMoveUp={index > 0 ? () => moveRule(index, -1) : undefined}
                    onMoveDown={index < rules.length - 1 ? () => moveRule(index, 1) : undefined}
                    onRemove={() => onChange(rules.filter((_, i) => i !== index))}
                />
            ))}
            <button type="button" onClick={() => onChange([...rules, newStyleRule()])} className={buttonClass('secondary', 'sm', 'self-start')}>
                <FaPlus className="text-[11px]" /> Add rule
            </button>
        </div>
    );
}

type StyleRuleEditorProps = {
    rule: EditionStyleRule;
    index: number;
    cards: ReleaseCard[];
    editionStyle: CardStyleSettings;
    onChange: (rule: EditionStyleRule) => void;
    onMoveUp?: () => void;
    onMoveDown?: () => void;
    onRemove: () => void;
};

function StyleRuleEditor({ rule, index, cards, editionStyle, onChange, onMoveUp, onMoveDown, onRemove }: StyleRuleEditorProps) {
    const conditionKeys = Object.keys(rule.when) as PoolFilterBy[];
    const styleKeys = RULE_STYLE_KEYS.filter(key => key in rule.style);
    const matchCount = useMemo(() => cards.filter(card => styleRuleMatches(rule, card)).length, [cards, rule]);
    const isComplete = conditionKeys.some(key => (rule.when[key]?.length ?? 0) > 0) && styleKeys.length > 0;

    const conditionOptions = STYLE_RULE_DIMENSIONS.filter(o => !conditionKeys.includes(o.value));
    const styleOptions = RULE_STYLE_KEYS.filter(key => !styleKeys.includes(key)).map(key => ({ label: RULE_STYLE_LABELS[key], value: key }));

    const setCondition = (key: PoolFilterBy, values: string[]) => onChange({ ...rule, when: { ...rule.when, [key]: values } });
    const removeCondition = (key: PoolFilterBy) => onChange({ ...rule, when: Object.fromEntries(Object.entries(rule.when).filter(([k]) => k !== key)) });
    const setStyle = (key: RuleStyleKey, value: string | boolean) => onChange({ ...rule, style: { ...rule.style, [key]: value } });
    const removeStyle = (key: RuleStyleKey) => onChange({ ...rule, style: Object.fromEntries(Object.entries(rule.style).filter(([k]) => k !== key)) });
    // Toggles start flipped from the edition style, since matching it would do nothing
    const addStyle = (key: RuleStyleKey) => setStyle(key, BOOLEAN_RULE_STYLE_KEYS.has(key) ? !editionStyle[key] : editionStyle[key] as string);

    return (
        <div className="flex flex-col gap-3 p-3 rounded-card border border-(--divider) bg-(--background-primary)">
            <div className="flex items-center gap-2">
                <Eyebrow>Rule {index + 1}</Eyebrow>
                {isComplete
                    ? <Plate size="sm" variant="outline">{matchCount} {matchCount === 1 ? 'card' : 'cards'}</Plate>
                    : <span className="text-[11px] text-(--text-tertiary)">Add a condition and a style</span>}
                <div className="ml-auto flex items-center gap-1">
                    <IconButton icon={<FaArrowUp className="text-[10px]" />} label="Move rule up" onClick={() => onMoveUp?.()} disabled={!onMoveUp} />
                    <IconButton icon={<FaArrowDown className="text-[10px]" />} label="Move rule down" onClick={() => onMoveDown?.()} disabled={!onMoveDown} />
                    <IconButton icon={<FaTrash className="text-[10px]" />} label="Delete rule" onClick={onRemove} />
                </div>
            </div>

            <RuleClause title="If" emptyHint="Every condition must match. Pick several values to match any of them.">
                {conditionKeys.map(key => (
                    <RemovableRow key={key} label={`Remove ${dimensionLabel(key)} condition`} onRemove={() => removeCondition(key)}>
                        <MultiSelect
                            label={dimensionLabel(key)}
                            options={poolFilterValueOptions(cards, key)}
                            selections={rule.when[key] ?? []}
                            onChange={values => setCondition(key, values)}
                            placeholder="Pick values"
                            className="text-[13px]"
                        />
                    </RemovableRow>
                ))}
                {conditionOptions.length > 0 && (
                    <CustomSelect value="" placeholder="Add condition…" size="sm" options={conditionOptions} onChange={value => setCondition(value as PoolFilterBy, [])} />
                )}
            </RuleClause>

            <RuleClause title="Then">
                {styleKeys.map(key => (
                    <RemovableRow key={key} label={`Remove ${RULE_STYLE_LABELS[key]}`} onRemove={() => removeStyle(key)}>
                        <RuleStyleField styleKey={key} value={rule.style[key]} onChange={value => setStyle(key, value)} />
                    </RemovableRow>
                ))}
                {styleOptions.length > 0 && (
                    <CustomSelect value="" placeholder="Add style…" size="sm" options={styleOptions} onChange={value => addStyle(value as RuleStyleKey)} />
                )}
            </RuleClause>
        </div>
    );
}

function RuleClause({ title, emptyHint, children }: { title: string; emptyHint?: string; children: ReactNode }) {
    return (
        <div className="flex flex-col gap-2">
            <div className="flex items-baseline gap-2">
                <Eyebrow>{title}</Eyebrow>
                {emptyHint && <span className="text-[11px] text-(--text-tertiary)">{emptyHint}</span>}
            </div>
            {children}
        </div>
    );
}

/** A rule field with a remove button level with its input. */
function RemovableRow({ label, onRemove, children }: { label: string; onRemove: () => void; children: ReactNode }) {
    return (
        <div className="flex items-end gap-2">
            <div className="flex-1 min-w-0">{children}</div>
            <IconButton icon={<FaXmark className="text-[12px]" />} label={label} onClick={onRemove} className="mb-1.5" />
        </div>
    );
}

/** The same control the edition style uses for this field. */
function RuleStyleField({ styleKey, value, onChange }: { styleKey: RuleStyleKey; value: string | boolean | undefined; onChange: (value: string | boolean) => void }) {
    switch (styleKey) {
        case 'image_parallel':
            return <ParallelDropdown value={String(value ?? 'NONE')} onChange={onChange} />;
        case 'image_parallel_coloring':
            return <FormDropdown label={RULE_STYLE_LABELS.image_parallel_coloring} options={parallelColoringOptions} selectedOption={String(value ?? 'DEFAULT')} onChange={onChange} />;
        case 'edition':
            return <FormDropdown label={RULE_STYLE_LABELS.edition} options={editionOptions} selectedOption={String(value ?? 'NONE')} onChange={onChange} />;
        case 'image_coloring':
            return <FormDropdown label={RULE_STYLE_LABELS.image_coloring} options={imageColoringOptions} selectedOption={String(value ?? 'PRIMARY')} onChange={onChange} />;
        default:
            return <FormEnabler label={RULE_STYLE_LABELS[styleKey]} isEnabled={!!value} onChange={isEnabled => onChange(!isEnabled)} />;
    }
}
