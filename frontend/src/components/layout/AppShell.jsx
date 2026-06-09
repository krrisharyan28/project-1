import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import Button from "../ui/Button";

const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/transactions", label: "Transactions" },
  { to: "/alerts", label: "Alerts" },
  { to: "/upload", label: "Upload CSV" },
];

function navClasses({ isActive }) {
  return `block rounded-md px-3 py-2 text-sm font-medium ${
    isActive
      ? "bg-brand-600 text-white"
      : "text-slate-300 hover:bg-slate-700 hover:text-white"
  }`;
}

export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 w-60 bg-slate-900 px-4 py-6">
        <div className="mb-8 px-2">
          <h1 className="text-lg font-semibold text-white">🛡️ Fraud Alert</h1>
          <p className="text-xs text-slate-400">AI Dashboard</p>
        </div>
        <nav className="space-y-1">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navClasses}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="pl-60">
        <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
          <span className="text-sm text-slate-500">
            Welcome back,{" "}
            <span className="font-medium text-slate-800">
              {user?.username}
            </span>
          </span>
          <Button variant="secondary" onClick={handleLogout}>
            Log out
          </Button>
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
