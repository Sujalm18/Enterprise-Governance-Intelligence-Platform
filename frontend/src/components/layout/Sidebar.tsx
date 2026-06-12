import {
  BarChart3,
  ClipboardCheck,
  FileText,
  GitBranch,
  ShieldCheck,
  Siren,
  UploadCloud,
  CheckSquare,
  Brain,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { useRole } from "@/lib/context/RoleContext";
import { listNotifications } from "@/lib/api/notifications";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
  { name: "Executive Hub", href: "/intelligence", icon: Brain },
  { name: "Upload", href: "/upload", icon: UploadCloud },
  { name: "Workflow", href: "/workflow", icon: GitBranch },
  { name: "Reports", href: "/reports", icon: FileText },
  { name: "Review", href: "/review", icon: ClipboardCheck },
  { name: "Escalations", href: "/escalations", icon: Siren },
  { name: "Mitigations", href: "/mitigations", icon: CheckSquare },
  { name: "Architecture", href: "/architecture", icon: ShieldCheck },
];

export function Sidebar() {
  const { role, setRole } = useRole();

  const { data: notifications } = useQuery({
    queryKey: ["notifications", role],
    queryFn: listNotifications,
    refetchInterval: 10_000,
  });

  const unreadCount = notifications?.filter((n) => !n.read_status).length || 0;

  return (
    <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-800 bg-slate-950 text-slate-100 lg:flex lg:flex-col">
      <div className="border-b border-slate-800 px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
            <ShieldCheck className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-200">
              Enterprise
            </p>
            <h1 className="text-base font-semibold leading-tight">
              Governance Intelligence
            </h1>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-5" aria-label="Primary navigation">
        {navigation.map((item) => {
          const isDashboard = item.href === "/dashboard";
          return (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  "flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-slate-300 hover:bg-slate-900 hover:text-white",
                )
              }
            >
              <div className="flex items-center gap-3">
                <item.icon className="h-4 w-4" aria-hidden="true" />
                <span>{item.name}</span>
              </div>
              {isDashboard && unreadCount > 0 && (
                <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-red-600 px-1.5 text-[10px] font-bold text-white animate-pulse">
                  {unreadCount}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 px-6 py-4 space-y-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
            Active Role
          </label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as any)}
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm font-medium text-white shadow-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="Analyst">Analyst</option>
            <option value="Manager">Manager</option>
            <option value="Governance Lead">Governance Lead</option>
          </select>
          <p className="mt-1.5 text-[10px] text-slate-500 leading-normal">
            Toggles active backend permissions & UI state visibility.
          </p>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
            Demo Tenant
          </label>
          <select
            value={localStorage.getItem("tenant_id") || "1"}
            onChange={(e) => {
              localStorage.setItem("tenant_id", e.target.value);
              window.location.reload();
            }}
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm font-medium text-white shadow-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="1">Default Tenant (ID: 1)</option>
            <option value="2">Acme Corp (ID: 2)</option>
            <option value="3">Globex Corp (ID: 3)</option>
          </select>
          <p className="mt-1.5 text-[10px] text-slate-500 leading-normal">
            Isolates risk registers by X-Tenant-ID header context.
          </p>
        </div>
      </div>

      <div className="border-t border-slate-800 px-6 py-4 text-xs text-slate-400">
        Live governance intelligence powered by the FastAPI backend.
      </div>
    </aside>
  );
}
