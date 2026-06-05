import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Activity, CheckCircle2, Clock, FileText, Loader2, XCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/features/reports/StatusBadge";
import { getDashboardStats } from "@/lib/api/dashboard";
import { queryKeys } from "@/lib/api/queryKeys";
import { listGovernanceReports } from "@/lib/api/reports";
import type { AuditLogResponse, GovernanceReportResponse } from "@/types/api";

const pipelineStages = [
  "Uploaded",
  "Parsed",
  "Indexed",
  "AI Extraction",
  "Report Generated",
  "Review",
];

export function WorkflowPage() {
  const reportsQuery = useQuery({
    queryKey: queryKeys.reports.list({ is_latest: true }),
    queryFn: () => listGovernanceReports({ is_latest: true }),
    refetchInterval: 10_000,
  });

  const statsQuery = useQuery({
    queryKey: queryKeys.dashboard.stats,
    queryFn: getDashboardStats,
    refetchInterval: 10_000,
  });

  const reports = reportsQuery.data ?? [];
  const logs = statsQuery.data?.recent_logs ?? [];
  const workflowSummary = useMemo(() => summarizeWorkflow(reports, statsQuery.data?.failed_jobs ?? 0), [reports, statsQuery.data?.failed_jobs]);

  return (
    <>
      <PageHeader
        eyebrow="Pipeline visibility"
        title="Workflow Tracker"
        description="Monitor document processing progress from upload through generated governance reports and review outcomes."
      />

      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <WorkflowMetricCard label="Generated Reports" value={workflowSummary.generated} icon="report" />
        <WorkflowMetricCard label="Pending Review" value={workflowSummary.pendingReview} icon="pending" />
        <WorkflowMetricCard label="Approved" value={workflowSummary.approved} icon="approved" />
        <WorkflowMetricCard label="Failed Jobs" value={workflowSummary.failed} icon="failed" />
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Processing Stages</CardTitle>
          <CardDescription>
            Current workflow coverage based on backend upload, processing, report generation, and review APIs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {pipelineStages.map((stage, index) => (
              <div key={stage} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">
                  {index + 1}
                </div>
                <p className="text-sm font-semibold text-slate-950">{stage}</p>
                <p className="mt-1 text-xs text-slate-500">{stageDescription(stage)}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <WorkflowReportsCard
          reports={reports}
          isLoading={reportsQuery.isLoading}
          error={reportsQuery.error}
          onRetry={() => void reportsQuery.refetch()}
        />
        <WorkflowActivityCard
          logs={logs}
          isLoading={statsQuery.isLoading}
          error={statsQuery.error}
          onRetry={() => void statsQuery.refetch()}
        />
      </div>
    </>
  );
}

function summarizeWorkflow(reports: GovernanceReportResponse[], failedJobs: number) {
  return {
    generated: reports.length,
    pendingReview: reports.filter((report) => report.review_status === "pending_review").length,
    approved: reports.filter((report) => report.review_status === "approved").length,
    failed: failedJobs,
  };
}

function WorkflowMetricCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: "report" | "pending" | "approved" | "failed";
}) {
  const Icon =
    icon === "approved" ? CheckCircle2 : icon === "failed" ? XCircle : icon === "pending" ? Clock : FileText;
  const color =
    icon === "approved"
      ? "text-emerald-600"
      : icon === "failed"
        ? "text-red-600"
        : icon === "pending"
          ? "text-amber-600"
          : "text-blue-600";

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

function WorkflowReportsCard({
  reports,
  isLoading,
  error,
  onRetry,
}: {
  reports: GovernanceReportResponse[];
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Generated Report Workflow</CardTitle>
        <CardDescription>Latest generated reports and review states from the backend.</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <LoadingRows />
        ) : error ? (
          <ErrorState message={error instanceof Error ? error.message : "Workflow reports could not be loaded."} onRetry={onRetry} />
        ) : reports.length === 0 ? (
          <EmptyState message="No generated reports yet. Upload a document to start the workflow." />
        ) : (
          <div className="overflow-hidden rounded-md border border-slate-200">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">Document</th>
                  <th className="px-4 py-3 font-semibold">Type</th>
                  <th className="px-4 py-3 font-semibold">Review</th>
                  <th className="px-4 py-3 font-semibold">Created</th>
                  <th className="px-4 py-3 font-semibold">Report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {reports.slice(0, 12).map((report) => (
                  <tr key={report.id}>
                    <td className="px-4 py-3 font-medium text-slate-950">{report.filename}</td>
                    <td className="px-4 py-3 text-slate-600">{formatLabel(report.document_type ?? "unknown")}</td>
                    <td className="px-4 py-3"><StatusBadge status={report.review_status} /></td>
                    <td className="whitespace-nowrap px-4 py-3 text-slate-500">{formatDate(report.created_at)}</td>
                    <td className="px-4 py-3">
                      <Button asChild variant="outline" size="sm">
                        <Link to={`/reports/${report.id}`}>Open</Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function WorkflowActivityCard({
  logs,
  isLoading,
  error,
  onRetry,
}: {
  logs: AuditLogResponse[];
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Workflow Activity</CardTitle>
        <CardDescription>Audit trail events emitted by upload, processing, review, and routing actions.</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <LoadingRows />
        ) : error ? (
          <ErrorState message={error instanceof Error ? error.message : "Workflow activity could not be loaded."} onRetry={onRetry} />
        ) : logs.length === 0 ? (
          <EmptyState message="No workflow activity has been recorded yet." />
        ) : (
          <div className="space-y-3">
            {logs.slice(0, 10).map((log) => (
              <div key={log.id} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-950">{log.event}</p>
                  <span className="whitespace-nowrap text-xs text-slate-500">{formatDate(log.timestamp)}</span>
                </div>
                <p className="mt-1 text-xs font-medium text-slate-500">{log.user}</p>
                <p className="mt-2 text-sm text-slate-600">{log.details ?? "No details"}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function LoadingRows() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="h-16 animate-pulse rounded-md bg-slate-200" />
      ))}
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-red-700">
        <Activity className="h-4 w-4" aria-hidden="true" />
        Workflow data unavailable
      </div>
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

function stageDescription(stage: string) {
  const descriptions: Record<string, string> = {
    Uploaded: "Document saved and workflow job queued.",
    Parsed: "Text extracted through the ingestion parser.",
    Indexed: "Chunks prepared for retrieval context.",
    "AI Extraction": "Governance intelligence generated by backend services.",
    "Report Generated": "RAID, escalations, and actions persisted.",
    Review: "Report awaits approval or change request.",
  };
  return descriptions[stage] ?? "Workflow stage";
}

function formatLabel(value: string) {
  return value.replace(/_/g, " ");
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

