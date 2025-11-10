/**
 * @fileoverview FormElementGrid - Grid layout component for form elements
 * 
 * Provides a standardized 2-column grid layout for organizing form inputs
 * side-by-side. Used throughout the custom card builder to create consistent
 * spacing and alignment of related form fields.
 */

import React from "react";

/**
 * Props for the FormElementGrid component
 */
type FormElementGridProps = {
    /** Child form elements to be arranged in grid layout */
    children: React.ReactNode;
};

/**
 * FormElementGrid - Two-column layout container for form elements
 * 
 * Creates a responsive 2-column grid layout with consistent spacing for
 * organizing form inputs. Provides standardized gap spacing and bottom
 * margin for proper form section separation.
 * 
 * @example
 * ```tsx
 * <FormElementGrid>
 *   <FormInput label="First Name" value={firstName} onChange={setFirstName} />
 *   <FormInput label="Last Name" value={lastName} onChange={setLastName} />
 * </FormElementGrid>
 * ```
 * 
 * @param children - Form elements to be arranged in grid
 * @returns Grid container with 2-column layout
 */
const FormElementGrid: React.FC<FormElementGridProps> = ({ children }) => {
    return (
        <div className="grid grid-cols-2 gap-4 mb-2">
            {children}
        </div>
    );
};

export default FormElementGrid;