import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Route, Search, Send, Siren } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceBadge } from "@/features/reports/ConfidenceBadge";
import { StatusBadge } from "@/features/reports/StatusBadge";
import { listEscalations, routeEscalation } from "@/lib/api/escalations";
import { queryKeys } from "@/lib/api/queryKeys";
import type { EscalationItemResponse, EscalationStatus } from "@/types/api";

type StatusFilter = "all" | EscalationStatus;

export function EscalationsPage() {
  const [status, setStatus] = useState<StatusFilter>("all");
  const [search, setSearch] = useState("");
  const [routingTargets, setRoutingTargets] = useState<Record<number, string>>({});
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
  routingTarget,
  onRoutingTargetChange,
  onRoute,
  isRouting,
  routeError,
}: {
  item: EscalationItemResponse;
  routingTarget: string;
  onRoutingTargetChange: (value: string) => void;
  onRoute: () => void;
  isRouting: boolean;
  routeError: unknown;
}) {
  const canRoute = routingTarget.trim().length > 0 && !isRouting;

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <StatusBadge status={item.status} />
            <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold capitalize text-slate-700 ring-1 ring-slate-200">
              {item.severity}
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
          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-slate-500">
            <span>Created {formatDate(item.created_at)}</span>
            {item.routing_target ? <span>Routed to {item.routing_target}</span> : null}
            <Link className="font-semibold text-blue-700 hover:text-blue-800" to={`/reports/${item.report_id}`}>
              Open report
            </Link>
          </div>
        </div>

        <div className="w-full rounded-md border border-slate-200 bg-slate-50 p-4 lg:w-80">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500" htmlFor={`route-${item.id}`}>
            Routing target
          </label>
          <input
            id={`route-${item.id}`}
            value={routingTarget}
            onChange={(event) => onRoutingTargetChange(event.target.value)}
            placeholder="e.g. CIO, PMO, Steering Committee"
            className="mt-2 h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
          <Button className="mt-3 w-full" disabled={!canRoute} onClick={onRoute}>
            <Send className="mr-2 h-4 w-4" aria-hidden="true" />
            {isRouting ? "Routing..." : "Route escalation"}
          </Button>
          {routeError ? (
            <p className="mt-2 text-xs text-red-600">
              {routeError instanceof Error ? routeError.message : "Escalation routing failed."}
            </p>
          ) : null}
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

