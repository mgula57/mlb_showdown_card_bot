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
import FormSection from './FormSection';
import { formSectionSummary } from './FormSectionSummary';
import { InfoTooltip } from '../shared/InfoTooltip';
import {
    canHideDisplayText, expansionOptions, editionOptions, imageParallelOptions, imageColoringOptions,
    outerGlowOptions, statHighlightsTypeOptions, nicknameIndexOptions, setStyleSummary, imageStyleSummary,
    type CardStyleSettings,
} from './cardStyle';

/** Small pill badge used to flag newly added options/fields */
export const NewBadge = () => (
    <span className="text-[9px] font-bold leading-none px-1.5 py-0.5 rounded-full bg-(--red) text-white uppercase tracking-wide">
        New
    </span>
);

// ----------------------------------
// MARK: - Fields
// ----------------------------------

type StyleFieldsProps = {
    values: CardStyleSettings;
    onChange: (patch: Partial<CardStyleSettings>) => void;
};

/** Set section fields. `afterEdition` slots per-card inputs (e.g. Set Number) between Edition and the toggles. */
export function SetStyleFields({ values, onChange, afterEdition }: StyleFieldsProps & { afterEdition?: ReactNode }) {
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

            <FormEnabler label='Show Year as Text' isEnabled={values.show_year_text} onChange={(isEnabled) => onChange({ show_year_text: !isEnabled })} />
            <FormEnabler label='Add 1 to Set Year' isEnabled={values.add_one_to_set_year} onChange={(isEnabled) => onChange({ add_one_to_set_year: !isEnabled })} />

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

/** Image section fields after the image source inputs. Parallel only applies to auto images, so
 * the Custom Card Builder hides it for linked/uploaded images. */
export function ImageStyleFields({ values, onChange, hideParallel = false }: StyleFieldsProps & { hideParallel?: boolean }) {
    return (
        <>
            <FormDropdown
                label="Image Parallel"
                className={`col-span-full ${hideParallel ? 'hidden' : ''}`}
                options={imageParallelOptions}
                selectedOption={values.image_parallel}
                onChange={(value) => onChange({ image_parallel: value })}
            />

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
            <h1 className="col-span-full text-md font-semibold text-secondary mt-2">Extras</h1>
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
export function CardStyleSections({ values, onChange, defaults, isOpenByDefault = true }: StyleFieldsProps & { defaults: CardStyleSettings; isOpenByDefault?: boolean }) {
    return (
        <>
            <FormSection
                title='Set'
                icon={<FaLayerGroup />}
                isOpenByDefault={isOpenByDefault}
                childrenWhenClosed={formSectionSummary(setStyleSummary(values, defaults))}
            >
                <SetStyleFields values={values} onChange={onChange} />
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
