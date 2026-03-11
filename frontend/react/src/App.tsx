// import { Button } from "@/components/ui/button"
import { BrowserRouter, Routes, Route } from "react-router-dom";
// import { UsersList } from "./userList"
// import { AddTestForm } from "./components/AddTestForm";

import LoginPage from "./pages/LoginPage"
import DashboardPage from "./pages/DashboardPage";

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>        
    </BrowserRouter>
  )
}

export default App
