
import { BrowserRouter, useLocation } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import CustomCardBuilder from "./components/customs/CustomCardBuilder";
import { SiteSettingsProvider } from "./components/shared/SiteSettingsContext";
import ShowdownCardExplore from "./components/cards/ShowdownCardExplore";

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
                <ShowdownCardExplore />
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
