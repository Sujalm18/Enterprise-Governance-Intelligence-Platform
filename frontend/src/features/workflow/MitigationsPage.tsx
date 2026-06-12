import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle,
  AlertCircle,
  Calendar,
  User,
  Shield,
  Search,
  Filter,
  CheckSquare,
  ArrowRight,
  TrendingDown,
  RotateCcw,
  Sparkles,
  Settings,
  X,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useRole } from "@/lib/context/RoleContext";
import {
  listMitigations,
  updateMitigation,
  verifyMitigation,
  reopenMitigation,
} from "@/lib/api/mitigations";
import type { MitigationTaskResponse } from "@/types/api";

type StatusFilter = "all" | "PLANNED" | "IN_PROGRESS" | "BLOCKED" | "COMPLETED" | "VERIFIED";
type PriorityFilter = "all" | "P1" | "P2" | "P3" | "P4";
type SLAFilter = "all" | "ON_TRACK" | "AT_RISK" | "OVERDUE";

export function MitigationsPage() {
  const { role, isGovLead, isManager } = useRole();
  const queryClient = useQueryClient();

  // Filters state
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("all");
  const [slaFilter, setSlaFilter] = useState<SLAFilter>("all");
  const [search, setSearch] = useState("");

  // Slide-over state
  const [selectedTask, setSelectedTask] = useState<MitigationTaskResponse | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // Form states
  const [formTitle, setFormTitle] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formOwnerRole, setFormOwnerRole] = useState("Analyst");
  const [formOwnerName, setFormOwnerName] = useState("");
  const [formTargetDate, setFormTargetDate] = useState("");
  const [formPriority, setFormPriority] = useState("P3");
  const [formEffectiveness, setFormEffectiveness] = useState(20);
  const [formProgress, setFormProgress] = useState(0);
  const [formStatus, setFormStatus] = useState("PLANNED");

  // Query mitigations list
  const mitigationsQuery = useQuery({
    queryKey: ["mitigations", statusFilter, priorityFilter, slaFilter],
    queryFn: () => {
      const params: Record<string, any> = {};
      if (statusFilter !== "all") params.status = statusFilter;
      if (priorityFilter !== "all") params.priority = priorityFilter;
      return listMitigations(params);
    },
    refetchInterval: 15_000,
  });

  const mitigations = mitigationsQuery.data ?? [];

  // Filter client-side by SLA & search
  const filteredTasks = useMemo(() => {
    return mitigations.filter((task) => {
      // SLA Filter
      if (slaFilter !== "all" && task.sla_status !== slaFilter) {
        return false;
      }
      // Search term
      const normalizedSearch = search.trim().toLowerCase();
      if (normalizedSearch) {
        const matchesSearch =
          task.title.toLowerCase().includes(normalizedSearch) ||
          (task.description && task.description.toLowerCase().includes(normalizedSearch)) ||
          task.owner_role.toLowerCase().includes(normalizedSearch) ||
          (task.owner_name && task.owner_name.toLowerCase().includes(normalizedSearch));
        if (!matchesSearch) return false;
      }
      return true;
    });
  }, [mitigations, slaFilter, search]);

  // Mutations
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: any }) =>
      updateMitigation(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["mitigations"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
      setIsPanelOpen(false);
      setSelectedTask(null);
    },
  });

  const verifyMutation = useMutation({
    mutationFn: (id: number) => verifyMitigation(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["mitigations"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
    },
  });

  const reopenMutation = useMutation({
    mutationFn: (id: number) => reopenMitigation(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["mitigations"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
    },
  });

  // Open task for editing
  const handleEditClick = (task: MitigationTaskResponse) => {
    setSelectedTask(task);
    setFormTitle(task.title);
    setFormDescription(task.description ?? "");
    setFormOwnerRole(task.owner_role);
    setFormOwnerName(task.owner_name ?? "");
    setFormTargetDate(task.target_date ?? "");
    setFormPriority(task.priority);
    setFormEffectiveness(task.effectiveness);
    setFormProgress(task.completion_percentage);
    setFormStatus(task.status);
    setIsPanelOpen(true);
  };

  // Submit edits
  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask) return;

    const payload: any = {
      title: formTitle,
      description: formDescription || null,
      owner_role: formOwnerRole,
      owner_name: formOwnerName || null,
      priority: formPriority,
      target_date: formTargetDate || null,
      effectiveness: formEffectiveness,
      completion_percentage: formProgress,
      status: formStatus,
    };

    updateMutation.mutate({ id: selectedTask.id, payload });
  };

  // Summary statistics
  const stats = useMemo(() => {
    const total = mitigations.length;
    const planned = mitigations.filter((t) => t.status === "PLANNED").length;
    const inProgress = mitigations.filter((t) => t.status === "IN_PROGRESS").length;
    const blocked = mitigations.filter((t) => t.status === "BLOCKED").length;
    const completed = mitigations.filter((t) => t.status === "COMPLETED").length;
    const verified = mitigations.filter((t) => t.status === "VERIFIED").length;
    
    // SLA status
    const overdue = mitigations.filter((t) => t.status !== "COMPLETED" && t.status !== "VERIFIED" && t.sla_status === "OVERDUE").length;
    const atRisk = mitigations.filter((t) => t.status !== "COMPLETED" && t.status !== "VERIFIED" && t.sla_status === "AT_RISK").length;

    return { total, planned, inProgress, blocked, completed, verified, overdue, atRisk };
  }, [mitigations]);

  // Determine permissions based on role
  const isAnalyst = role === "Analyst";
  const canEditTask = (task: MitigationTaskResponse) => {
    if (task.status === "VERIFIED" && !isGovLead) return false;
    if (task.status === "COMPLETED" && isAnalyst) return false;
    return true;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Governance Remediation"
        title="Mitigation Task Lifecycle"
        description="Track and execute automated recommendations, monitor SLAs, update progress, and dynamically reduce RAID risk scores."
      />

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-slate-400">Total Tasks</p>
            <p className="mt-2 text-2xl font-bold text-slate-100">{stats.total}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-slate-400">In Progress</p>
            <p className="mt-2 text-2xl font-bold text-blue-400">{stats.inProgress}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-slate-400">Blocked</p>
            <p className="mt-2 text-2xl font-bold text-amber-500">{stats.blocked}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-slate-400">Completed</p>
            <p className="mt-2 text-2xl font-bold text-green-400">{stats.completed}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-slate-400">Verified</p>
            <p className="mt-2 text-2xl font-bold text-emerald-400">{stats.verified}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-red-950/20">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-red-400">Overdue SLA</p>
            <p className="mt-2 text-2xl font-bold text-red-500">{stats.overdue}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Search Section */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader className="p-4 pb-0">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Filter className="h-4 w-4 text-blue-500" /> Filters & Controls
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search by title, description, owner..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-md border border-slate-800 bg-slate-900/50 pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Dropdown Filters */}
            <div className="flex flex-wrap gap-3">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              >
                <option value="all">All Statuses</option>
                <option value="PLANNED">Planned</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="BLOCKED">Blocked</option>
                <option value="COMPLETED">Completed</option>
                <option value="VERIFIED">Verified</option>
              </select>

              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value as PriorityFilter)}
                className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              >
                <option value="all">All Priorities</option>
                <option value="P1">P1 (Critical)</option>
                <option value="P2">P2 (High)</option>
                <option value="P3">P3 (Medium)</option>
                <option value="P4">P4 (Low)</option>
              </select>

              <select
                value={slaFilter}
                onChange={(e) => setSlaFilter(e.target.value as SLAFilter)}
                className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
              >
                <option value="all">All SLAs</option>
                <option value="ON_TRACK">On Track</option>
                <option value="AT_RISK">At Risk</option>
                <option value="OVERDUE">Overdue</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading & Empty States */}
      {mitigationsQuery.isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
        </div>
      ) : filteredTasks.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900/20 text-center py-12">
          <CardContent className="space-y-3">
            <CheckSquare className="h-10 w-10 text-slate-600 mx-auto" />
            <p className="text-slate-400 font-medium">No mitigation tasks found matching the criteria.</p>
          </CardContent>
        </Card>
      ) : (
        /* Task Cards Grid */
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredTasks.map((task) => {
            const overdue = task.sla_status === "OVERDUE";
            const atRisk = task.sla_status === "AT_RISK";
            
            // Priority colors
            const pColors: Record<string, string> = {
              P1: "bg-red-500/10 text-red-400 border-red-500/20",
              P2: "bg-orange-500/10 text-orange-400 border-orange-500/20",
              P3: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
              P4: "bg-slate-500/10 text-slate-400 border-slate-500/20",
            };

            // Status colors
            const sColors: Record<string, string> = {
              PLANNED: "bg-slate-500/10 text-slate-400 border-slate-500/20",
              IN_PROGRESS: "bg-blue-500/10 text-blue-400 border-blue-500/20",
              BLOCKED: "bg-amber-500/10 text-amber-400 border-amber-500/20",
              COMPLETED: "bg-green-500/10 text-green-400 border-green-500/20",
              VERIFIED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
            };

            return (
              <Card
                key={task.id}
                className={`flex flex-col border-slate-800 bg-slate-900/30 transition-all hover:bg-slate-900/60 ${
                  overdue ? "border-red-900/40 ring-1 ring-red-900/20" : ""
                }`}
              >
                <CardHeader className="p-4 pb-2">
                  <div className="flex items-center justify-between gap-2">
                    {/* Priority Badge */}
                    <span className={`rounded-md border px-2 py-0.5 text-xs font-semibold uppercase tracking-wider ${pColors[task.priority] || pColors.P4}`}>
                      {task.priority}
                    </span>

                    {/* SLA Badge */}
                    <span
                      className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${
                        overdue
                          ? "bg-red-950/20 text-red-400 border-red-900/30"
                          : atRisk
                          ? "bg-orange-950/20 text-orange-400 border-orange-900/30"
                          : "bg-emerald-950/20 text-emerald-400 border-emerald-900/30"
                      }`}
                    >
                      {overdue ? (
                        <>
                          <AlertCircle className="h-3.5 w-3.5" /> OVERDUE
                        </>
                      ) : atRisk ? (
                        <>
                          <AlertCircle className="h-3.5 w-3.5" /> AT RISK
                        </>
                      ) : (
                        "ON TRACK"
                      )}
                    </span>
                  </div>

                  <CardTitle className="text-base font-bold text-slate-100 mt-3 line-clamp-1">
                    {task.title}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-400 mt-1 line-clamp-2 min-h-[2rem]">
                    {task.description || "No description provided."}
                  </CardDescription>
                </CardHeader>

                <CardContent className="flex-1 p-4 pt-2 space-y-4">
                  {/* Progress bar */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-medium">
                      <span className="text-slate-400">Progress</span>
                      <span className="text-slate-200">{task.completion_percentage}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${task.completion_percentage}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Impact / Owner details */}
                  <div className="grid grid-cols-2 gap-2 border-t border-slate-800/60 pt-3 text-xs">
                    <div className="space-y-1">
                      <p className="text-slate-500 font-medium uppercase tracking-wide text-[9px]">Effectiveness</p>
                      <p className="text-emerald-400 font-semibold flex items-center gap-1">
                        <TrendingDown className="h-3.5 w-3.5" /> -{task.effectiveness}% Risk
                      </p>
                    </div>

                    <div className="space-y-1">
                      <p className="text-slate-500 font-medium uppercase tracking-wide text-[9px]">Status</p>
                      <span className={`inline-block border px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-wider ${sColors[task.status] || sColors.PLANNED}`}>
                        {task.status}
                      </span>
                    </div>

                    <div className="space-y-1 col-span-2 pt-1">
                      <p className="text-slate-500 font-medium uppercase tracking-wide text-[9px]">Owner</p>
                      <p className="text-slate-300 font-medium flex items-center gap-1.5">
                        <User className="h-3.5 w-3.5 text-slate-500" />
                        {task.owner_name ? (
                          <span>
                            {task.owner_name} <span className="text-slate-500">({task.owner_role})</span>
                          </span>
                        ) : (
                          <span className="text-slate-500">{task.owner_role} (Unassigned)</span>
                        )}
                      </p>
                    </div>

                    {task.target_date && (
                      <div className="space-y-1 col-span-2 pt-1">
                        <p className="text-slate-500 font-medium uppercase tracking-wide text-[9px]">Target Date</p>
                        <p className="text-slate-300 font-medium flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5 text-slate-500" />
                          {task.target_date}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Actions Area */}
                  <div className="flex flex-wrap gap-2 border-t border-slate-800/60 pt-3 justify-end">
                    {/* Reopen button */}
                    {isGovLead && (task.status === "VERIFIED" || task.status === "COMPLETED") && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => reopenMutation.mutate(task.id)}
                        disabled={reopenMutation.isPending}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                      >
                        <RotateCcw className="h-3.5 w-3.5 mr-1" /> Reopen
                      </Button>
                    )}

                    {/* Verify button */}
                    {isGovLead && task.status === "COMPLETED" && (
                      <Button
                        size="sm"
                        onClick={() => verifyMutation.mutate(task.id)}
                        disabled={verifyMutation.isPending}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        <CheckCircle className="h-3.5 w-3.5 mr-1" /> Verify
                      </Button>
                    )}

                    {/* Manager Complete button */}
                    {isManager && task.status !== "COMPLETED" && task.status !== "VERIFIED" && (
                      <Button
                        size="sm"
                        onClick={() =>
                          updateMutation.mutate({
                            id: task.id,
                            payload: { status: "COMPLETED", completion_percentage: 100 },
                          })
                        }
                        disabled={updateMutation.isPending}
                        className="bg-green-600 hover:bg-green-700 text-white"
                      >
                        <CheckSquare className="h-3.5 w-3.5 mr-1" /> Complete
                      </Button>
                    )}

                    {/* Edit button */}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEditClick(task)}
                      className="border-slate-800 hover:bg-slate-800 hover:text-white"
                    >
                      <Settings className="h-3.5 w-3.5 mr-1" />
                      {canEditTask(task) ? "Edit Details" : "View Details"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Slide-over Edit Panel */}
      {isPanelOpen && selectedTask && (
        <div className="fixed inset-0 z-50 overflow-hidden" aria-labelledby="slide-over-title" role="dialog" aria-modal="true">
          <div className="absolute inset-0 overflow-hidden">
            {/* Background backdrop overlay */}
            <div
              className="absolute inset-0 bg-slate-950/80 transition-opacity"
              onClick={() => setIsPanelOpen(false)}
            ></div>

            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
              <div className="pointer-events-auto w-screen max-w-md">
                <form
                  onSubmit={handleFormSubmit}
                  className="flex h-full flex-col border-l border-slate-800 bg-slate-950 text-slate-100 shadow-2xl"
                >
                  {/* Panel Header */}
                  <div className="bg-slate-900 border-b border-slate-800 px-6 py-5">
                    <div className="flex items-start justify-between">
                      <div>
                        <h2 className="text-lg font-semibold leading-6 text-slate-100 flex items-center gap-2">
                          <Shield className="h-5 w-5 text-blue-500" />
                          {canEditTask(selectedTask) ? "Update Mitigation Task" : "Mitigation Task Info"}
                        </h2>
                        <p className="mt-1.5 text-xs text-slate-400">
                          Ref: RAID Risk Score: {selectedTask.risk_score} | ID: {selectedTask.id}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsPanelOpen(false)}
                        className="rounded-md bg-transparent text-slate-500 hover:text-slate-400 focus:outline-none"
                      >
                        <span className="sr-only">Close panel</span>
                        <X className="h-5 w-5" aria-hidden="true" />
                      </button>
                    </div>
                  </div>

                  {/* Panel Body */}
                  <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
                    {/* Read-only Alert Warning for permissions */}
                    {!canEditTask(selectedTask) && (
                      <div className="rounded-md border border-yellow-900/50 bg-yellow-950/20 p-3 text-xs text-yellow-400">
                        <AlertCircle className="h-4.5 w-4.5 text-yellow-500 inline mr-2 align-text-bottom" />
                        This task is currently in state <strong>{selectedTask.status}</strong>. Your active role (<strong>{role}</strong>) does not have permissions to modify this task.
                      </div>
                    )}

                    {/* Title */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Title</label>
                      <input
                        type="text"
                        required
                        disabled={!canEditTask(selectedTask)}
                        value={formTitle}
                        onChange={(e) => setFormTitle(e.target.value)}
                        className="w-full rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none disabled:opacity-60"
                      />
                    </div>

                    {/* Description */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Description</label>
                      <textarea
                        rows={3}
                        disabled={!canEditTask(selectedTask)}
                        value={formDescription}
                        onChange={(e) => setFormDescription(e.target.value)}
                        className="w-full rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none disabled:opacity-60"
                      />
                    </div>

                    {/* Owner Role & Owner Name */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Owner Role</label>
                        <select
                          disabled={!canEditTask(selectedTask)}
                          value={formOwnerRole}
                          onChange={(e) => setFormOwnerRole(e.target.value)}
                          className="w-full rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none disabled:opacity-60"
                        >
                          <option value="Analyst">Analyst</option>
                          <option value="Manager">Manager</option>
                          <option value="Governance Lead">Governance Lead</option>
                        </select>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Owner Name</label>
                        <input
                          type="text"
                          disabled={!canEditTask(selectedTask)}
                          value={formOwnerName}
                          onChange={(e) => setFormOwnerName(e.target.value)}
                          placeholder="e.g. John Doe"
                          className="w-full rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none disabled:opacity-60"
                        />
                      </div>
                    </div>

                    {/* Target Date & Priority */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Target Date</label>
                        <input
                          type="date"
                          disabled={!canEditTask(selectedTask)}
                          value={formTargetDate}
                          onChange={(e) => setFormTargetDate(e.target.value)}
                          className="w-full rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none disabled:opacity-60"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Priority</label>
                        <select
                          disabled={!canEditTask(selectedTask)}
                          value={formPriority}
                          onChange={(e) => setFormPriority(e.target.value)}
                          className="w-full rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none disabled:opacity-60"
                        >
                          <option value="P1">P1 (Critical)</option>
                          <option value="P2">P2 (High)</option>
                          <option value="P3">P3 (Medium)</option>
                          <option value="P4">P4 (Low)</option>
                        </select>
                      </div>
                    </div>

                    {/* Effectiveness */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Mitigation Effectiveness (% Risk Reduction Capacity)
                      </label>
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          step="5"
                          disabled={!canEditTask(selectedTask)}
                          value={formEffectiveness}
                          onChange={(e) => setFormEffectiveness(Number(e.target.value))}
                          className="flex-1 accent-blue-600 disabled:opacity-60"
                        />
                        <span className="text-sm font-semibold text-emerald-400 bg-emerald-950/40 border border-emerald-900/30 px-2 py-1 rounded min-w-[3.5rem] text-center">
                          -{formEffectiveness}%
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-500 leading-normal">
                        Percentage reduction applied to the related RAID item risk score upon task verification.
                      </p>
                    </div>

                    {/* Progress Slider */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Completion Progress</label>
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          step="5"
                          disabled={!canEditTask(selectedTask)}
                          value={formProgress}
                          onChange={(e) => {
                            const val = Number(e.target.value);
                            setFormProgress(val);
                            if (val === 100 && formStatus !== "VERIFIED") {
                              setFormStatus("COMPLETED");
                            }
                          }}
                          className="flex-1 accent-blue-600 disabled:opacity-60"
                        />
                        <span className="text-sm font-semibold text-blue-400 bg-blue-950/40 border border-blue-900/30 px-2 py-1 rounded min-w-[3.5rem] text-center">
                          {formProgress}%
                        </span>
                      </div>
                    </div>

                    {/* Status */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Status</label>
                      <select
                        disabled={!canEditTask(selectedTask)}
                        value={formStatus}
                        onChange={(e) => {
                          const val = e.target.value;
                          setFormStatus(val);
                          if (val === "COMPLETED" || val === "VERIFIED") {
                            setFormProgress(100);
                          }
                        }}
                        className="w-full rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none disabled:opacity-60"
                      >
                        <option value="PLANNED">Planned</option>
                        <option value="IN_PROGRESS">In Progress</option>
                        <option value="BLOCKED">Blocked</option>
                        <option value="COMPLETED">Completed (Awaiting Verification)</option>
                        {isGovLead && <option value="VERIFIED">Verified (Risk Reduced)</option>}
                      </select>
                    </div>
                  </div>

                  {/* Panel Footer */}
                  {canEditTask(selectedTask) && (
                    <div className="bg-slate-900 border-t border-slate-800 px-6 py-4 flex items-center justify-end gap-3">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => setIsPanelOpen(false)}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        disabled={updateMutation.isPending}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        {updateMutation.isPending ? "Saving..." : "Save Changes"}
                      </Button>
                    </div>
                  )}
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function summarizeMitigations(tasks: MitigationTaskResponse[]) {
  // Helpers
  return {};
}
