import { Navigate, Route, Routes } from "react-router-dom";
import LoginPage from "../pages/LoginPage";
import DashboardPage from "../pages/DashboardPage";
import InfoPage from "../pages/InfoPage";
import { useAuthStore } from "../features/auth/store";

const App = () => {
  const { token } = useAuthStore();
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={token ? <DashboardPage /> : <Navigate to="/login" replace />}
      />
      <Route path="/info" element={<InfoPage />} />
    </Routes>
  );
};

export default App;
