import React from 'react';
import { useTheme } from '../shared/SiteSettingsContext';

type AccountSectionProps = {
    /** DOM id, for deep links (ex: /account#image-libraries). */
    id?: string;
    /** Section heading. Omit for headerless cards (ex: profile). */
    title?: string;
    icon?: React.ReactNode;
    /** Short line under the heading. */
    description?: React.ReactNode;
    /** Content aligned right of the heading (ex: an action button). */
    action?: React.ReactNode;
    children: React.ReactNode;
};

/** Bordered card used for each block on the Account page. */
export const AccountSection: React.FC<AccountSectionProps> = ({ id, title, icon, description, action, children }) => {
    const { isDark } = useTheme();
    return (
        <div id={id} className={`scroll-mt-4 rounded-lg border border-form-element p-6 ${isDark ? 'bg-background-secondary' : 'bg-white'}`}>
            {title && (
                <div className="flex items-start justify-between gap-4 mb-4">
                    <div>
                        <div className="flex items-center space-x-2">
                            {icon && <span className="text-secondary">{icon}</span>}
                            <h2 className="text-2xl font-semibold text-secondary">{title}</h2>
                        </div>
                        {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
                    </div>
                    {action}
                </div>
            )}
            {children}
        </div>
    );
};

export default AccountSection;
