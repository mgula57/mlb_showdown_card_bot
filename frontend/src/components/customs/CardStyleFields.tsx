/**
 * @fileoverview CardStyleFields - Set and Image style form fields shared by the Custom Card
 * Builder and the Release Builder's per-edition style defaults.
 *
 * Only covers the "style" settings that apply equally to any card. Per-card inputs (set number,
 * image link/upload) stay with the Custom Card Builder and are slotted in where needed.
 */

import type { ReactNode } from 'react';
import { FaImage, FaLayerGroup } from 'react-icons/fa';
import FormDropdown from './FormDropdown';
import FormEnabler from './FormEnabler';
import FormInput from './FormInput';
import FormSection from './FormSection';
import { formSectionSummary } from './FormSectionSummary';
import { InfoTooltip } from '../shared/InfoTooltip';
import { ParallelPreview } from './ParallelPreview';
import {
    canHideDisplayText, expansionOptions, editionOptions, imageParallelOptions, imageColoringOptions,
    outerGlowOptions, statHighlightsTypeOptions, nicknameIndexOptions, setStyleSummary, imageStyleSummary,
    type CardStyleSettings,
} from './cardStyle';

import { Eyebrow } from '../shared/Eyebrow';
import { NewBadge } from '../shared/NewBadge';

/** Parallels added recently enough to flag in the dropdown menu */
const NEW_PARALLELS = new Set(['BREAKOUT', 'BOOSTER']);

const parallelOptionsWithBadges = imageParallelOptions.map(option =>
    NEW_PARALLELS.has(option.value) ? { ...option, trailing: <NewBadge /> } : option
);

// ----------------------------------
// MARK: - Fields
// ----------------------------------

type StyleFieldsProps = {
    values: CardStyleSettings;
    onChange: (patch: Partial<CardStyleSettings>) => void;
};

type SetStyleFieldsProps = StyleFieldsProps & {
    /** Slots per-card inputs (e.g. Set Number) between Edition and the toggles */
    afterEdition?: ReactNode;
    /** Offers Set Year, for cards printed as part of a release */
    showSetYear?: boolean;
};

/** Set section fields. */
export function SetStyleFields({ values, onChange, afterEdition, showSetYear = false }: SetStyleFieldsProps) {
    return (
        <>
            <FormDropdown
                label="Expansion"
                options={expansionOptions}
                selectedOption={values.expansion}
                onChange={(value) => onChange({
                    expansion: value,
                    // Don't carry a TRUE hide-date-text value forward if it's no longer applicable.
                    ...(!canHideDisplayText(value, values.edition) && { disable_display_text_on_card: false }),
                })}
            />

            <FormDropdown
                label="Edition"
                options={editionOptions}
                selectedOption={values.edition}
                onChange={(value) => onChange({
                    edition: value,
                    ...(!canHideDisplayText(values.expansion, value) && { disable_display_text_on_card: false }),
                })}
            />

            {afterEdition}

            {showSetYear && (
                <FormInput
                    label="Set Year"
                    className='col-span-full'
                    value={values.set_year ?? ''}
                    placeholder="Card's year"
                    inputMode="numeric"
                    maxLength={4}
                    isClearable={true}
                    onChange={(value) => {
                        const setYear = value?.replace(/\D/g, '') || null;
                        onChange({ set_year: setYear, ...(setYear && { add_one_to_set_year: false }) });
                    }}
                />
            )}

            <FormEnabler label='Show Year as Text' isEnabled={values.show_year_text} onChange={(isEnabled) => onChange({ show_year_text: !isEnabled })} />
            <FormEnabler
                label='Add 1 to Set Year'
                isEnabled={values.add_one_to_set_year}
                onChange={(isEnabled) => onChange({ add_one_to_set_year: !isEnabled })}
                isDisabled={showSetYear && !!values.set_year}
                disabledReason='Not used when a Set Year is entered'
            />

            <FormEnabler
                label={
                    <span className="inline-flex items-center gap-1.5">
                        Hide Date Text <NewBadge />
                        <InfoTooltip text="Removes the banner that normally shows the split or date range used for this card's stats (e.g. 'First Half' or '2023-05-01 to 2023-10-01'). Only available with a Trading Deadline/Pennant Run expansion or an All-Star Game/Postseason edition, since those already communicate the card's context without it." />
                    </span>
                }
                className='col-span-full'
                isEnabled={values.disable_display_text_on_card || false}
                onChange={(isEnabled) => onChange({ disable_display_text_on_card: !isEnabled })}
                isDisabled={!canHideDisplayText(values.expansion, values.edition)}
                disabledReason='Only available with a Trading Deadline/Pennant Run expansion or an All-Star Game/Postseason edition'
            />
        </>
    );
}

/** The Image Parallel dropdown with sample thumbnails. Also used by the Release Builder's style rules. */
export function ParallelDropdown({ value, onChange, className = '' }: { value: string; onChange: (value: string) => void; className?: string }) {
    return (
        <FormDropdown
            label={<span className="inline-flex items-center gap-1.5">Image Parallel <NewBadge /></span>}
            className={className}
            options={parallelOptionsWithBadges}
            selectedOption={value}
            onChange={onChange}
            imageClassName="mr-2 w-5 h-5 shrink-0 object-cover rounded-plate"
            menuImageClassName="mr-2 w-9 h-10 shrink-0 object-cover rounded-control"
        />
    );
}

/** Image section fields after the image source inputs. Parallel only applies to auto images, so
 * the Custom Card Builder hides it for linked/uploaded images. */
export function ImageStyleFields({ values, onChange, hideParallel = false }: StyleFieldsProps & { hideParallel?: boolean }) {
    // Base needs no preview; it's what the card looks like without a parallel
    const previewParallel = hideParallel || values.image_parallel === 'NONE'
        ? undefined
        : imageParallelOptions.find(option => option.value === values.image_parallel);
    return (
        <>
            <ParallelDropdown
                className={`col-span-full ${hideParallel ? 'hidden' : ''}`}
                value={values.image_parallel}
                onChange={(value) => onChange({ image_parallel: value })}
            />
            {previewParallel && <ParallelPreview parallel={previewParallel} />}

            <FormDropdown
                label="Image Coloring"
                options={imageColoringOptions}
                selectedOption={values.image_coloring}
                onChange={(value) => onChange({ image_coloring: value })}
                className='text-nowrap'
            />

            <FormDropdown
                label="Outer Glow"
                options={outerGlowOptions}
                selectedOption={values.image_glow_multiplier}
                onChange={(value) => onChange({ image_glow_multiplier: value })}
            />

            {/* Extras */}
            <Eyebrow className="col-span-full mt-2">Extras</Eyebrow>
            <FormDropdown
                label="Show Real Stats?"
                options={statHighlightsTypeOptions}
                selectedOption={values.stat_highlights_type || 'NONE'}
                onChange={(value) => onChange({ stat_highlights_type: value })}
            />
            <FormDropdown
                label="Show Nickname?"
                options={nicknameIndexOptions}
                selectedOption={values.nickname_index || 'NONE'}
                onChange={(value) => onChange({ nickname_index: value })}
            />
            <FormEnabler label='Add Border' isEnabled={values.is_bordered} onChange={(isEnabled) => onChange({ is_bordered: !isEnabled })} />
            <FormEnabler label='Dark Mode' isEnabled={values.is_dark_mode} onChange={(isEnabled) => onChange({ is_dark_mode: !isEnabled })} />
            <FormEnabler label='Remove Team' className='col-span-full' isEnabled={values.hide_team_logo} onChange={(isEnabled) => onChange({ hide_team_logo: !isEnabled })} />
        </>
    );
}

// ----------------------------------
// MARK: - Sections
// ----------------------------------

/** The Set and Image sections as standalone collapsible panels, for style editors outside the
 * Custom Card Builder (an edition's default style, a single card's style). Collapsed summaries
 * show what differs from `defaults`. */
export function CardStyleSections({ values, onChange, defaults, isOpenByDefault = true, showSetYear = false }: StyleFieldsProps & { defaults: CardStyleSettings; isOpenByDefault?: boolean; showSetYear?: boolean }) {
    return (
        <>
            <FormSection
                title='Set'
                icon={<FaLayerGroup />}
                isOpenByDefault={isOpenByDefault}
                childrenWhenClosed={formSectionSummary(setStyleSummary(values, defaults))}
            >
                <SetStyleFields values={values} onChange={onChange} showSetYear={showSetYear} />
            </FormSection>
            <FormSection
                title='Image'
                icon={<FaImage />}
                isOpenByDefault={isOpenByDefault}
                childrenWhenClosed={formSectionSummary(imageStyleSummary(values, defaults))}
            >
                <ImageStyleFields values={values} onChange={onChange} />
            </FormSection>
        </>
    );
}
