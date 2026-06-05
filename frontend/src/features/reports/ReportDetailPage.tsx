import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, AlertCircle } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getGovernanceReport } from "@/lib/api/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { ConfidenceBadge } from "@/features/reports/ConfidenceBadge";
import { EscalationsPanel } from "@/features/reports/EscalationsPanel";
import { ExecutiveSummaryCard } from "@/features/reports/ExecutiveSummaryCard";
import { ExplainabilityPanel } from "@/features/reports/ExplainabilityPanel";
import { MeetingActionsPanel } from "@/features/reports/MeetingActionsPanel";
import { ProcessingMetricsPanel } from "@/features/reports/ProcessingMetricsPanel";
import { RaidItemsTable } from "@/features/reports/RaidItemsTable";
import { StatusBadge } from "@/features/reports/StatusBadge";

export function ReportDetailPage() {
  const { reportId } = useParams();
  const id = reportId ?? "";

  const reportQuery = useQuery({
    queryKey: queryKeys.reports.detail(id),
    queryFn: () => getGovernanceReport(id),
    enabled: Boolean(id),
  });

  if (!id) {
    return <ReportDetailError message="No report ID was provided." />;
  }

  if (reportQuery.isLoading) {
    return <ReportDetailSkeleton />;
  }

  if (reportQuery.error) {
    return (
      <ReportDetailError
        message={
          reportQuery.error instanceof Error
            ? reportQuery.error.message
            : "Report could not be loaded."
        }
        onRetry={() => void reportQuery.refetch()}
      />
    );
  }

  const report = reportQuery.data;

  if (!report) {
    return <ReportDetailError message="Report not found." />;
  }

  return (
    <>
      <div className="mb-4">
        <Button asChild variant="outline">
          <Link to="/reports">
            <ArrowLeft className="mr-2 h-4 w-4" aria-hidden="true" />
            Back to reports
          </Link>
        </Button>
      </div>

      <PageHeader
        eyebrow="Report detail"
        title={report.filename}
        description={`Governance report #${report.id} for document #${report.document_id}.`}
      />

      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <MetricTile label="Review Status" value={<StatusBadge status={report.review_status} />} />
        <MetricTile label="Confidence" value={<ConfidenceBadge score={report.confidence_score} />} />
        <MetricTile label="RAID Items" value={report.raid_items.length.toLocaleString()} />
        <MetricTile label="Escalations" value={report.escalation_items.length.toLocaleString()} />
      </div>

      <div className="space-y-6">
        <ExecutiveSummaryCard report={report} />
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(360px,0.7fr)]">
          <div className="space-y-6">
            <RaidItemsTable items={report.raid_items} />
            <EscalationsPanel items={report.escalation_items} />
            <MeetingActionsPanel actions={report.meeting_actions} />
          </div>
          <div className="space-y-6">
            <ProcessingMetricsPanel report={report} />
            <ExplainabilityPanel report={report} />
          </div>
        </div>
      </div>
    </>
  );
}

type MetricTileProps = {
  label: string;
  value: React.ReactNode;
};

function MetricTile({ label, value }: MetricTileProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <div className="mt-3 text-2xl font-semibold text-slate-950">{value}</div>
      </CardContent>
    </Card>
  );
}

function ReportDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-10 w-40 animate-pulse rounded-md bg-slate-200" />
      <div className="h-32 animate-pulse rounded-lg bg-slate-200" />
      <div className="grid gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-28 animate-pulse rounded-lg bg-slate-200" />
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(360px,0.7fr)]">
        <div className="h-96 animate-pulse rounded-lg bg-slate-200" />
        <div className="h-96 animate-pulse rounded-lg bg-slate-200" />
      </div>
    </div>
  );
}

type ReportDetailErrorProps = {
  message: string;
  onRetry?: () => void;
};

function ReportDetailError({ message, onRetry }: ReportDetailErrorProps) {
  return (
    <>
      <div className="mb-4">
        <Button asChild variant="outline">
          <Link to="/reports">
            <ArrowLeft className="mr-2 h-4 w-4" aria-hidden="true" />
            Back to reports
          </Link>
        </Button>
      </div>
      <Card className="border-red-200 bg-red-50">
        <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 flex-none text-red-600" aria-hidden="true" />
            <div>
              <h3 className="font-semibold text-red-950">Report unavailable</h3>
              <p className="mt-1 text-sm text-red-700">{message}</p>
            </div>
          </div>
          {onRetry ? (
            <Button variant="outline" onClick={onRetry}>
              Retry
            </Button>
          ) : null}
        </CardContent>
      </Card>
    </>
  );
}
