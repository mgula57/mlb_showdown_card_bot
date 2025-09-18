
import { BrowserRouter, useLocation } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import CustomCardBuilder from "./components/customs/CustomCardBuilder";
import { SiteSettingsProvider } from "./components/shared/SiteSettingsContext";
import ShowdownCardTable from "./components/cards/ShowdownCardTable";

/** Handles defining content within each route */
const AppContent = () => {
    const location = useLocation();

    return (
        <AppLayout>
            {/* All components are always mounted */}
            <div className={['/customs', '/'].includes(location.pathname) ? 'block' : 'hidden'}>
                <CustomCardBuilder isHidden={location.pathname !== '/customs'} />
            </div>
            <div className={location.pathname === '/explore' ? 'block' : 'hidden'}>
                <ShowdownCardTable />
            </div>
        </AppLayout>
    );
};

function App() {
    return (
        <BrowserRouter>
            <SiteSettingsProvider>
                <AppContent />
            </SiteSettingsProvider>
        </BrowserRouter>
    );
}

export default App;
