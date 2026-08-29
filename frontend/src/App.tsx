import { BrowserRouter, Route, Routes } from "react-router-dom";
import { CustomerDetailView } from "./views/CustomerDetailView";
import { DashboardView } from "./views/DashboardView";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardView />} />
        <Route path="/customers/:customerId" element={<CustomerDetailView />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
