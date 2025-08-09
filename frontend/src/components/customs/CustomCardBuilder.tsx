import React, { useState, type JSX, type ReactElement } from 'react';
import FormInput from './FormInput';
import FormSection from './FormSection';
import FormDropdown from './FormDropdown';
import type { SelectOption } from '../shared/CustomSelect';

// Image Assets
import expansionBS from '../../assets/expansion-bs.png';
import expansionTD from '../../assets/expansion-td.png';
import expansionPR from '../../assets/expansion-pr.png';



/** State for the custom card form */
interface CustomCardFormState {
    // Basics
    name: string;
    year: string;
    period: string;
    expansion: string;
    set_number: string;

    // Period Extras (Shown in basics)
    start_date: string;
    end_date: string;
    split: string;


    // Image

    // Chart

    // Extras

}

/** 
 * Card Creation Page for users to create and customize their own cards. 
*/
const CustomCardBuilder: React.FC = () => {

    // Define the form state
    const [form, setForm] = useState<CustomCardFormState>({
        name: "", year: "", expansion: "BS", set_number: "",
        period: "REGULAR", start_date: "", end_date: "", split: "" 
    });

    // Expansion options
    const expansionOptions: SelectOption[] = [
        { label: "Base Set", value: "BS", image: expansionBS },
        { label: "Trading Deadline", value: "TD", image: expansionTD },
        { label: "Pennant Run", value: "PR", image: expansionPR },
    ]

    // Period Options
    const periodOptions: SelectOption[] = [
        { 'value': 'REGULAR', 'label': 'Regular Season', 'symbol': '⚾' },
        { 'value': 'POST', 'label': 'Postseason', 'symbol': '🏆' },
        { 'value': 'DATES', 'label': 'Date Range', 'symbol': '📅' },
        { 'value': 'SPLIT', 'label': 'Split', 'symbol': '🔀' },
    ]

    const renderPeriodInputs = () => {
        switch (form.period) {
            case 'DATES':
                return (
                    <>
                        <FormInput
                            label="Start Date"
                            value={form.start_date}
                            type="date"
                            onChange={(value) => setForm({ ...form, start_date: value })}
                        />
                        <FormInput
                            label="End Date"
                            value={form.end_date}
                            type="date"
                            onChange={(value) => setForm({ ...form, end_date: value })}
                        />
                    </>
                );
            case 'SPLIT':
                return (
                    <FormInput
                        label="Split"
                        value={form.split}
                        onChange={(value) => setForm({ ...form, split: value })}
                        isClearable={true}
                        className='col-span-full'
                    />
                );
            default:
                return null;
        }
    }


    return (
        <div className="h-full flex flex-col md:flex-row overflow-hidden">

            {/* Form Inputs */}
            <section className="
                w-full lg:w-2/3 md:max-w-128
                md:border-r border-r-gray-800
                bg-background-secondary
                overflow-y-auto
                p-4 space-y-2
            ">
                {/* Basics */}
                <FormSection title='Basics' isOpenByDefault={true}>

                    <FormInput
                        label="Name"
                        className='col-span-full'
                        value={form.name}
                        onChange={(value) => setForm({ ...form, name: value })}
                        isClearable={true}
                    />

                    <FormInput
                        label="Year"
                        value={form.year}
                        onChange={(value) => setForm({ ...form, year: value })}
                        isClearable={true}
                    />

                    <FormDropdown
                        label="Period"
                        options={periodOptions}
                        selectedOption={form.period}
                        onChange={(value) => setForm({ ...form, period: value })}
                    />

                    {renderPeriodInputs()}

                    <FormDropdown
                        label="Expansion"
                        options={expansionOptions}
                        selectedOption={form.expansion}
                        onChange={(value) => setForm({ ...form, expansion: value })}
                    />

                    <FormInput
                        label="Set Number"
                        value={form.set_number}
                        onChange={(value) => setForm({ ...form, set_number: value })}
                        isClearable={true}
                    />

                </FormSection>

                

            </section>

            {/* Preview Section */}
            <section className="
                w-full
                bg-background-secondary
                overflow-y-auto
                p-4 space-y-6
            ">
                <h1 className="text-2xl font-semibold text-secondary">Preview</h1>
                <p className="text-secondary">
                
                </p>
            </section>
        </div>
    );
}

export default CustomCardBuilder;