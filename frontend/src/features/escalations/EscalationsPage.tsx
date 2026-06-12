import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Route, Search, Send, Siren, ShieldAlert, UserCheck, Archive } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceBadge } from "@/features/reports/ConfidenceBadge";
import { StatusBadge } from "@/features/reports/StatusBadge";
import { listEscalations, routeEscalation, assignEscalation, resolveEscalation, closeEscalation } from "@/lib/api/escalations";
import { queryKeys } from "@/lib/api/queryKeys";
import { useRole } from "@/lib/context/RoleContext";
import type { EscalationItemResponse, EscalationStatus } from "@/types/api";

type StatusFilter = "all" | EscalationStatus;

export function EscalationsPage() {
  const { role, isGovLead, isManager } = useRole();
  const [status, setStatus] = useState<StatusFilter>("all");
  const [search, setSearch] = useState("");
  const [routingTargets, setRoutingTargets] = useState<Record<number, string>>({});
  const [assignees, setAssignees] = useState<Record<number, string>>({});
  const queryClient = useQueryClient();

  const params = status === "all" ? {} : { status };
  const escalationsQuery = useQuery({
    queryKey: queryKeys.escalations.list(params),
    queryFn: () => listEscalations(params),
    refetchInterval: 15_000,
  });

  const routeMutation = useMutation({
    mutationFn: ({ id, routing_target }: { id: number; routing_target: string }) =>
      routeEscalation(id, { routing_target }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escalations"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
    },
  });

  const assignMutation = useMutation({
    mutationFn: ({ id, assignedTo }: { id: number; assignedTo: string }) =>
      assignEscalation(id, assignedTo),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escalations"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (id: number) => resolveEscalation(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escalations"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
    },
  });

  const closeMutation = useMutation({
    mutationFn: (id: number) => closeEscalation(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escalations"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
    },
  });

  const escalations = escalationsQuery.data ?? [];
  const filteredEscalations = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    if (!normalized) {
      return escalations;
    }
    return escalations.filter((item) =>
      [
        item.filename,
        item.description,
        item.severity,
        item.status,
        item.routing_target,
        item.source_excerpt,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalized),
    );
  }, [escalations, search]);

  const summary = useMemo(() => summarizeEscalations(escalations), [escalations]);

  return (
    <>
      <PageHeader
        eyebrow="Executive action"
        title="Escalation Management"
        description="Track active escalation items, filter by status, and route executive actions to accountable stakeholders."
      />

      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <EscalationMetricCard label="Total" value={summary.total} icon="total" />
        <EscalationMetricCard label="Open" value={summary.open} icon="open" />
        <EscalationMetricCard label="Routed" value={summary.routed} icon="routed" />
        <EscalationMetricCard label="High/Critical" value={summary.highPriority} icon="priority" />
      </div>

      <Card className="mb-6">
        <CardContent className="p-5">
          <div className="grid gap-4 lg:grid-cols-[minmax(260px,1fr)_180px_auto]">
            <label className="relative block">
              <span className="sr-only">Search escalations</span>
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search escalation, source, severity, route..."
                className="h-10 w-full rounded-md border border-slate-300 bg-white pl-9 pr-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </label>

            <select
              value={status}
              onChange={(event) => setStatus(event.target.value as StatusFilter)}
              className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
              aria-label="Filter by escalation status"
            >
              <option value="all">All statuses</option>
              <option value="open">Open</option>
              <option value="routed">Routed</option>
              <option value="resolved">Resolved</option>
            </select>

            <Button
              variant="outline"
              onClick={() => {
                setSearch("");
                setStatus("all");
              }}
            >
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Escalation Queue</CardTitle>
          <CardDescription>Live escalation records returned by the FastAPI backend.</CardDescription>
        </CardHeader>
        <CardContent>
          {escalationsQuery.isLoading ? (
            <LoadingRows />
          ) : escalationsQuery.error ? (
            <ErrorState
              message={
                escalationsQuery.error instanceof Error
                  ? escalationsQuery.error.message
                  : "Escalations could not be loaded."
              }
              onRetry={() => void escalationsQuery.refetch()}
            />
          ) : filteredEscalations.length === 0 ? (
            <EmptyState message={escalations.length === 0 ? "No escalation items have been detected yet." : "No escalations match the current filters."} />
          ) : (
            <div className="space-y-4">
              {filteredEscalations.map((item) => (
                <EscalationCard
                  key={item.id}
                  item={item}
                  role={role}
                  isGovLead={isGovLead}
                  isManager={isManager}
                  routingTarget={routingTargets[item.id] ?? item.routing_target ?? ""}
                  onRoutingTargetChange={(value) =>
                    setRoutingTargets((current) => ({ ...current, [item.id]: value }))
                  }
                  onRoute={() =>
                    routeMutation.mutate({
                      id: item.id,
                      routing_target: (routingTargets[item.id] ?? item.routing_target ?? "").trim(),
                    })
                  }
                  isRouting={routeMutation.isPending}
                  routeError={routeMutation.error}
                  assigneeTarget={assignees[item.id] ?? item.assigned_to ?? ""}
                  onAssigneeTargetChange={(value) =>
                    setAssignees((current) => ({ ...current, [item.id]: value }))
                  }
                  onAssign={() =>
                    assignMutation.mutate({
                      id: item.id,
                      assignedTo: (assignees[item.id] ?? item.assigned_to ?? "").trim(),
                    })
                  }
                  isAssigning={assignMutation.isPending}
                  assignError={assignMutation.error}
                  onResolve={() => resolveMutation.mutate(item.id)}
                  isResolving={resolveMutation.isPending}
                  onClose={() => closeMutation.mutate(item.id)}
                  isClosing={closeMutation.isPending}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}

function EscalationCard({
  item,
  role,
  isGovLead,
  isManager,
  routingTarget,
  onRoutingTargetChange,
  onRoute,
  isRouting,
  routeError,
  assigneeTarget,
  onAssigneeTargetChange,
  onAssign,
  isAssigning,
  assignError,
  onResolve,
  isResolving,
  onClose,
  isClosing,
}: {
  item: EscalationItemResponse;
  role: string;
  isGovLead: boolean;
  isManager: boolean;
  routingTarget: string;
  onRoutingTargetChange: (value: string) => void;
  onRoute: () => void;
  isRouting: boolean;
  routeError: unknown;
  assigneeTarget: string;
  onAssigneeTargetChange: (value: string) => void;
  onAssign: () => void;
  isAssigning: boolean;
  assignError: unknown;
  onResolve: () => void;
  isResolving: boolean;
  onClose: () => void;
  isClosing: boolean;
}) {
  const canRoute = routingTarget.trim().length > 0 && !isRouting;

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <StatusBadge status={item.status} />
            <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold capitalize text-slate-700 ring-1 ring-slate-200">
              {item.severity}
            </span>
            <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-slate-200 ${
              item.priority === "P1" ? "bg-red-50 text-red-700 ring-red-200" :
              item.priority === "P2" ? "bg-amber-50 text-amber-700 ring-amber-200" :
              item.priority === "P3" ? "bg-blue-50 text-blue-700 ring-blue-200" : "bg-slate-50 text-slate-700 ring-slate-200"
            }`}>
              {item.priority || "P4"}
            </span>
            <span className="inline-flex items-center justify-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-800 ring-1 ring-slate-200">
              Score: {item.risk_score || 0}
            </span>
            <ConfidenceBadge score={item.confidence_score} />
          </div>
          <h3 className="text-base font-semibold text-slate-950">{item.description}</h3>
          <p className="mt-2 text-sm text-slate-500">
            Source document: <span className="font-medium text-slate-700">{item.filename}</span>
          </p>
          {item.source_excerpt ? (
            <blockquote className="mt-3 border-l-2 border-blue-200 pl-3 text-sm text-slate-600">
              {item.source_excerpt}
            </blockquote>
          ) : null}

          {/* Remediation Plan */}
          {item.remediation_plan ? (
            <div className="mt-4 bg-blue-50/50 border border-blue-100 rounded-lg p-3.5 text-sm text-blue-950">
              <span className="font-bold block text-[10px] uppercase text-blue-700 tracking-wider mb-1">Recommended Remediation Plan</span>
              <p className="leading-relaxed font-medium">{item.remediation_plan}</p>
              {item.expected_risk_reduction && (
                <div className="mt-2.5 flex items-center gap-1.5 text-xs font-semibold text-green-700">
                  <span className="inline-flex items-center rounded bg-green-50 px-2 py-0.5 border border-green-200">
                    Expected Reduction: {item.expected_risk_reduction}
                  </span>
                </div>
              )}
            </div>
          ) : null}

          {/* AI Contextual Insights */}
          {(item.explain_why || item.suggested_actions || item.estimated_impact) ? (
            <div className="mt-4 border border-indigo-100 rounded-xl p-4 bg-indigo-50/20 shadow-sm">
              <span className="font-bold block text-[10px] uppercase text-indigo-700 tracking-wider mb-3 flex items-center gap-1.5">
                <Siren className="h-3.5 w-3.5 text-indigo-500 animate-pulse" />
                AI Contextual Insights
              </span>
              <div className="grid gap-3 md:grid-cols-3">
                {item.explain_why && (
                  <div className="bg-white/85 p-3 rounded-lg border border-indigo-50/50">
                    <span className="font-bold block text-[10px] uppercase text-slate-500 tracking-wider mb-1">Why it matters</span>
                    <p className="text-xs text-slate-700 leading-relaxed font-medium">{item.explain_why}</p>
                  </div>
                )}
                {item.suggested_actions && (
                  <div className="bg-white/85 p-3 rounded-lg border border-indigo-50/50">
                    <span className="font-bold block text-[10px] uppercase text-slate-500 tracking-wider mb-1">Suggested actions</span>
                    <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line font-medium">{item.suggested_actions}</p>
                  </div>
                )}
                {item.estimated_impact && (
                  <div className="bg-white/85 p-3 rounded-lg border border-indigo-50/50 flex flex-col justify-between">
                    <div>
                      <span className="font-bold block text-[10px] uppercase text-slate-500 tracking-wider mb-1">Estimated impact</span>
                    </div>
                    <div className="inline-flex w-max items-center gap-1 rounded bg-green-50 px-2 py-0.5 text-xs font-semibold text-green-700 border border-green-200 mt-2">
                      {item.estimated_impact}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : null}

          {/* Ownership metadata block */}
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs bg-slate-50 p-2.5 rounded-md border border-slate-200/60 text-slate-600">
            <div>
              <span className="font-semibold text-slate-500 block">Raised By</span>
              <span className="font-medium text-slate-800">{item.raised_by || "System / AI"}</span>
            </div>
            <div>
              <span className="font-semibold text-slate-500 block">Assigned To</span>
              <span className="font-medium text-slate-800">{item.assigned_to || "Unassigned"}</span>
            </div>
            <div>
              <span className="font-semibold text-slate-500 block">Suggested Owner</span>
              <span className="font-medium text-indigo-700 font-semibold">{item.suggested_owner_role || "Governance Lead"}</span>
            </div>
            <div>
              <span className="font-semibold text-slate-500 block">Resolved By</span>
              <span className="font-medium text-slate-800">{item.resolved_by || "Unresolved"}</span>
            </div>
            <div>
              <span className="font-semibold text-slate-500 block">Target Routing</span>
              <span className="font-medium text-slate-800">{item.routing_target || "None"}</span>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-500">
            <span>Created {formatDate(item.created_at)}</span>
            <Link className="font-semibold text-blue-700 hover:text-blue-800" to={`/reports/${item.report_id}`}>
              Open report
            </Link>
            {item.explainability_trace && (
              <span className="border-l border-slate-200 pl-3">
                <span className="font-semibold text-slate-400">Trace:</span>{" "}
                <span className="text-slate-600">
                  {typeof item.explainability_trace === "object" && item.explainability_trace !== null
                    ? (item.explainability_trace.playbook
                      ? `Playbook: ${item.explainability_trace.playbook}`
                      : `Heuristics (${item.explainability_trace.recommendation_source})`)
                    : (typeof item.explainability_trace === "string" && (item.explainability_trace as string).includes("playbook")
                      ? "Playbook Engine matched" 
                      : "AI Heuristic matched")}
                </span>
              </span>
            )}
          </div>
        </div>

        <div className="w-full rounded-md border border-slate-200 bg-slate-50 p-4 lg:w-80 space-y-4">
          <div className="text-xs font-bold text-slate-500 border-b border-slate-200 pb-1.5 flex justify-between items-center">
            <span>WORKFLOW ACTIONS</span>
            <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded uppercase">{role}</span>
          </div>

          {/* 1. Routing action (Manager or Governance Lead) */}
          {(isManager || isGovLead) && (item.status === "OPEN" || item.status === "ASSIGNED" || item.status === "open" || item.status === "assigned") && (
            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold uppercase tracking-wide text-slate-500" htmlFor={`route-${item.id}`}>
                Routing target
              </label>
              <div className="flex gap-1">
                <input
                  id={`route-${item.id}`}
                  value={routingTarget}
                  onChange={(event) => onRoutingTargetChange(event.target.value)}
                  placeholder="e.g. CIO, PMO, Committee"
                  className="h-8 flex-1 rounded-md border border-slate-300 bg-white px-2.5 text-xs outline-none transition focus:border-blue-500 focus:ring-1 focus:ring-blue-100"
                />
                <Button size="sm" className="h-8 text-xs px-2.5" disabled={!canRoute} onClick={onRoute}>
                  <Send className="h-3 w-3" />
                </Button>
              </div>
              {!!routeError && (
                <p className="text-[10px] text-red-600">
                  {routeError instanceof Error ? routeError.message : "Routing failed"}
                </p>
              )}
            </div>
          )}

          {/* 2. Assign action (Governance Lead only) */}
          {isGovLead && (item.status !== "RESOLVED" && item.status !== "CLOSED" && item.status !== "resolved" && item.status !== "closed") && (
            <div className="space-y-1.5 pt-2 border-t border-slate-200/60">
              <label className="text-[11px] font-semibold uppercase tracking-wide text-slate-500" htmlFor={`assign-${item.id}`}>
                Assign Stakeholder
              </label>
              <div className="flex gap-1">
                <input
                  id={`assign-${item.id}`}
                  value={assigneeTarget}
                  onChange={(event) => onAssigneeTargetChange(event.target.value)}
                  placeholder="e.g. Governance Lead"
                  className="h-8 flex-1 rounded-md border border-slate-300 bg-white px-2.5 text-xs outline-none transition focus:border-blue-500 focus:ring-1 focus:ring-blue-100"
                />
                <Button size="sm" variant="secondary" className="h-8 text-xs px-2.5 border border-slate-300" disabled={assigneeTarget.trim().length === 0 || isAssigning} onClick={onAssign}>
                  <UserCheck className="h-3 w-3 text-slate-700" />
                </Button>
              </div>
              {!!assignError && (
                <p className="text-[10px] text-red-600">
                  {assignError instanceof Error ? assignError.message : "Assignment failed"}
                </p>
              )}
            </div>
          )}

          {/* 3. Resolve & Close actions (Governance Lead only) */}
          {isGovLead && (item.status !== "RESOLVED" && item.status !== "CLOSED" && item.status !== "resolved" && item.status !== "closed") && (
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200/60">
              <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold py-1.5 h-8" disabled={isResolving} onClick={onResolve}>
                <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                Resolve
              </Button>
              <Button size="sm" variant="default" className="bg-slate-700 hover:bg-slate-800 text-white text-xs font-semibold py-1.5 h-8" disabled={isClosing} onClick={onClose}>
                <Archive className="mr-1 h-3.5 w-3.5" />
                Close
              </Button>
            </div>
          )}

          {/* 4. Access warning (Analyst role) */}
          {!isManager && !isGovLead && (
            <div className="text-[11px] text-slate-500 bg-slate-100 rounded p-2 text-center">
              <ShieldAlert className="h-3.5 w-3.5 inline mr-1 text-slate-400" />
              Only Managers and Governance Leads can perform workflow actions.
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

function summarizeEscalations(items: EscalationItemResponse[]) {
  return {
    total: items.length,
    open: items.filter((item) => item.status === "open").length,
    routed: items.filter((item) => item.status === "routed").length,
    highPriority: items.filter((item) => ["high", "critical"].includes(item.severity.toLowerCase())).length,
  };
}

function EscalationMetricCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: "total" | "open" | "routed" | "priority";
}) {
  const Icon =
    icon === "routed" ? Route : icon === "open" ? Siren : icon === "priority" ? AlertTriangle : CheckCircle2;
  const color =
    icon === "priority"
      ? "text-red-600"
      : icon === "open"
        ? "text-amber-600"
        : icon === "routed"
          ? "text-blue-600"
          : "text-emerald-600";

  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{value.toLocaleString()}</p>
        </div>
        <Icon className={`h-6 w-6 ${color}`} aria-hidden="true" />
      </CardContent>
    </Card>
  );
}

function LoadingRows() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="h-28 animate-pulse rounded-md bg-slate-200" />
      ))}
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-4">
      <p className="text-sm font-semibold text-red-700">Escalation data unavailable</p>
      <p className="mt-2 text-sm text-red-600">{message}</p>
      <Button className="mt-4" variant="outline" size="sm" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

