import { FaRegBell } from 'react-icons/fa6';
import { NOTIFICATION_GROUPS } from '../../api/notifications';
import { useAuth } from '../auth/AuthContext';
import FormEnabler from '../customs/FormEnabler';
import AccountSection from './AccountSection';

/** Which kinds of notifications show up under the header bell. Everything is on until turned off. */
export default function NotificationSettings() {
    const { userSettings, syncSetting } = useAuth();
    const prefs = userSettings?.notification_prefs ?? {};
    return (
        <AccountSection title="Notifications" icon={<FaRegBell />} description="What shows up under the bell.">
            <div className="grid gap-2 sm:grid-cols-2">
                {NOTIFICATION_GROUPS.map(({ group, label, description }) => {
                    const isEnabled = prefs[group] !== false;
                    return (
                        <FormEnabler
                            key={group}
                            label={label}
                            description={description}
                            isEnabled={isEnabled}
                            isChanged={!isEnabled}
                            onChange={enabled => syncSetting({ notification_prefs: { ...prefs, [group]: !enabled } })}
                        />
                    );
                })}
            </div>
        </AccountSection>
    );
}
