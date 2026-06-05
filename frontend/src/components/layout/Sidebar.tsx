import {
  BarChart3,
  ClipboardCheck,
  FileText,
  GitBranch,
  ShieldCheck,
  Siren,
  UploadCloud,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
  { name: "Upload", href: "/upload", icon: UploadCloud },
  { name: "Workflow", href: "/workflow", icon: GitBranch },
  { name: "Reports", href: "/reports", icon: FileText },
  { name: "Review", href: "/review", icon: ClipboardCheck },
  { name: "Escalations", href: "/escalations", icon: Siren },
];

export function Sidebar() {
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
        {navigation.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-900 hover:text-white",
              )
            }
          >
            <item.icon className="h-4 w-4" aria-hidden="true" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-800 px-6 py-4 text-xs text-slate-400">
        Live governance intelligence powered by the FastAPI backend.
      </div>
    </aside>
  );
}
