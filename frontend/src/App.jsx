/**
 * Application routes.
 *
 * Public: /login. Everything else is wrapped in <ProtectedRoute> and rendered
 * inside the <AppShell> (sidebar + topbar).
 */
import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute";
import AppShell from "./components/layout/AppShell";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import TransactionsPage from "./pages/TransactionsPage";
import AlertsPage from "./pages/AlertsPage";
import AlertDetailPage from "./pages/AlertDetailPage";
import UploadPage from "./pages/UploadPage";

function Protected({ children }) {
  return (
    <ProtectedRoute>
      <AppShell>{children}</AppShell>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Protected><DashboardPage /></Protected>} />
      <Route
        path="/transactions"
        element={<Protected><TransactionsPage /></Protected>}
      />
      <Route path="/alerts" element={<Protected><AlertsPage /></Protected>} />
      <Route
        path="/alerts/:id"
        element={<Protected><AlertDetailPage /></Protected>}
      />
      <Route path="/upload" element={<Protected><UploadPage /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
