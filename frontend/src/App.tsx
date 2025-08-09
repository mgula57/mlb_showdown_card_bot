
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import CustomCardBuilder from "./components/customs/CustomCardBuilder";

function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<div>Welcome to the MLB Showdown Card Bot!</div>} />
          <Route path="/customs" element={<CustomCardBuilder />} />
          <Route path="/explore" element={<div>Explore Page</div>} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}

export default App;
