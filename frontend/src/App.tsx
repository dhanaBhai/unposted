import { NavLink, Outlet, Route, Routes, useLocation } from "react-router-dom";
import Home from "@/pages/Home";
import Journals from "@/pages/Journals";
import JournalDetailPage from "@/pages/JournalDetail";
import Settings from "@/pages/Settings";
import Streaks from "@/pages/Streaks";
import { Shield } from "lucide-react";

const navItems = [
  { label: "Journals", to: "/journals" },
  { label: "Streaks", to: "/streaks" },
  { label: "Settings", to: "/settings" }
];

const Sidebar = () => {
  const location = useLocation();

  return (
    <aside className="flex w-56 flex-col justify-between border-r border-gray-200 bg-white px-6 py-10">
      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block rounded-full px-4 py-2 text-sm font-semibold transition ${
                isActive
                  ? "bg-brand text-white shadow-md"
                  : "text-gray-600 hover:bg-gray-100"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="rounded-2xl bg-orange-50 p-4 text-sm text-brand">
        <div className="mb-2 inline-flex items-center gap-2 font-semibold">
          <Shield className="h-4 w-4" />
          Private by default
        </div>
        Stored locally in your browser.
      </div>
      <span className="text-xs text-gray-300">
        {location.pathname.replace("/", "") || "journals"}
      </span>
    </aside>
  );
};

const AppLayout = () => (
  <div className="flex min-h-screen bg-surface text-gray-900">
    <Sidebar />
    <main className="flex-1 overflow-y-auto px-12 py-12">
      <Outlet />
    </main>
  </div>
);

const App = () => (
  <Routes>
    <Route element={<AppLayout />}>
      <Route path="/" element={<Home />} />
      <Route path="/journals" element={<Journals />} />
      <Route path="/journals/:id" element={<JournalDetailPage />} />
      <Route path="/streaks" element={<Streaks />} />
      <Route path="/settings" element={<Settings />} />
    </Route>
  </Routes>
);

export default App;
