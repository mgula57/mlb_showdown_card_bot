
import { BrowserRouter, useLocation } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import CustomCardBuilder from "./components/customs/CustomCardBuilder";
import { SiteSettingsProvider } from "./components/shared/SiteSettingsContext";
import HomePage from "./components/home/HomePage";
import ShowdownCardTable from "./components/explore/ShowdownCardTable";

/** Handles defining content within each route */
const AppContent = () => {
    const location = useLocation();

    return (
        <AppLayout>
            {/* All components are always mounted */}
            <div className={location.pathname === '/' ? 'block' : 'hidden'}>
                <HomePage />
            </div>
            <div className={location.pathname === '/customs' ? 'block' : 'hidden'}>
                <CustomCardBuilder />
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
