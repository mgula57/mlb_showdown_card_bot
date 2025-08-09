import React from "react";

/** Props for the form element grid component */
type FormElementGridProps = {
    children: React.ReactNode;
};

/**
 * FormElementGrid handles the layout of form elements that are paired together.
 */
const FormElementGrid: React.FC<FormElementGridProps> = ({ children }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {children}
        </div>
    );
};

export default FormElementGrid;