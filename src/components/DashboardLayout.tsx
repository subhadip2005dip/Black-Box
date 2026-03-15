import { Link, useLocation, useNavigate } from "react-router-dom";
import { AlertTriangle, Monitor, Headphones, Video, LayoutDashboard, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const navItems = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Crash Data", url: "/crash-data", icon: AlertTriangle },
  { title: "System Info", url: "/system-info", icon: Monitor },
  { title: "Support", url: "/support", icon: Headphones },
  { title: "Recordings", url: "/recordings", icon: Video },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex w-full">
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card">
        <div className="p-6">
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            <span className="text-primary">●</span> Dashboard
          </h1>
        </div>
        <nav className="flex-1 px-3 space-y-1">
          {navItems.map((item) => {
            const active = location.pathname === item.url;
            return (
              <Link
                key={item.url}
                to={item.url}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.title}
              </Link>
            );
          })}
        </nav>
        <div className="px-3 mb-3">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
        <div className="p-4 mx-3 mb-4 rounded-lg bg-secondary">
          <p className="text-xs text-muted-foreground">Enterprise v2.4.1</p>
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="md:hidden flex items-center justify-between border-b border-border bg-card px-4 h-14">
          <h1 className="text-lg font-semibold text-foreground">
            <span className="text-primary">●</span> Dashboard
          </h1>
          <button onClick={handleLogout} className="text-destructive">
            <LogOut className="h-5 w-5" />
          </button>
        </header>
        <nav className="md:hidden fixed bottom-0 left-0 right-0 border-t border-border bg-card flex z-50">
          {navItems.slice(0, 5).map((item) => {
            const active = location.pathname === item.url;
            return (
              <Link
                key={item.url}
                to={item.url}
                className={`flex-1 flex flex-col items-center gap-1 py-2 text-[10px] font-medium transition-colors ${
                  active ? "text-primary" : "text-muted-foreground"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.title}
              </Link>
            );
          })}
        </nav>
        <main className="flex-1 p-6 md:p-8 pb-20 md:pb-8">{children}</main>
      </div>
    </div>
  );
}
