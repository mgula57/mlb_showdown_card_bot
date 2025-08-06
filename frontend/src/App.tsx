
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";

function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<div>Welcome to the MLB Showdown Card Bot!</div>} />
          <Route path="/customs" element={<div>Customs Page</div>} />
          <Route path="/explore" element={<div>Explore Page</div>} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}

export default App;
