
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import CustomCardBuilder from "./components/customs/CustomCardBuilder";
import { SiteSettingsProvider } from "./components/shared/SiteSettingsContext";
import HomePage from "./components/home/HomePage";

function App() {
    return (
        <BrowserRouter>
            <SiteSettingsProvider>
                <AppLayout>
                    <Routes>
                        <Route path="/" element={<HomePage/>} />
                        <Route path="/customs" element={<CustomCardBuilder />} />
                        <Route path="/explore" element={<div>Explore Page</div>} />
                    </Routes>
                </AppLayout>
            </SiteSettingsProvider>
        </BrowserRouter>
    );
}

export default App;
