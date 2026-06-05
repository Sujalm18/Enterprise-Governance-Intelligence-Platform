import { Link } from "react-router-dom";
import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ConfidenceBadge } from "@/features/reports/ConfidenceBadge";
import { StatusBadge } from "@/features/reports/StatusBadge";
import { ReviewForm } from "@/features/review/ReviewForm";
import type { GovernanceReportResponse } from "@/types/api";

type ReviewReportCardProps = {
  report: GovernanceReportResponse;
};

export function ReviewReportCard({ report }: ReviewReportCardProps) {
  return (
    <Card>
      <CardHeader className="border-b border-slate-200">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle>{report.filename}</CardTitle>
            <CardDescription className="mt-2">
              Report #{report.id} · Document #{report.document_id} · Created {formatDate(report.created_at)}
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge status={report.review_status} />
            <ConfidenceBadge score={report.confidence_score} />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5 p-5">
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
          <div className="space-y-4">
            <section>
              <h3 className="mb-2 text-sm font-semibold text-slate-950">Executive Summary</h3>
              <div className="rounded-md border-l-4 border-blue-600 bg-blue-50 px-4 py-3 text-sm leading-6 text-slate-800">
                {report.executive_summary}
              </div>
            </section>

            <section>
              <h3 className="mb-2 text-sm font-semibold text-slate-950">Detailed Summary</h3>
              <p className="line-clamp-5 text-sm leading-6 text-slate-700">{report.summary}</p>
            </section>
          </div>

          <div className="space-y-4">
            <ReviewMetrics report={report} />
            <ReviewExtractionPreview report={report} />
          </div>
        </div>

        <div className="flex flex-col gap-3 border-t border-slate-200 pt-5 lg:flex-row lg:items-start lg:justify-between">
          <Button asChild variant="outline">
            <Link to={`/reports/${report.id}`}>
              <ExternalLink className="mr-2 h-4 w-4" aria-hidden="true" />
              Open full report
            </Link>
          </Button>
          <ReviewForm reportId={report.id} />
        </div>
      </CardContent>
    </Card>
  );
}

function ReviewMetrics({ report }: { report: GovernanceReportResponse }) {
  const metrics = [
    ["RAID Items", report.raid_items.length.toLocaleString()],
    ["Escalations", report.escalation_items.length.toLocaleString()],
    ["Processing", `${report.processing_time_seconds.toFixed(2)}s`],
    ["Tokens", report.tokens_used.toLocaleString()],
  ];

  return (
    <div className="grid grid-cols-2 gap-3">
      {metrics.map(([label, value]) => (
        <div key={label} className="rounded-md bg-slate-50 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
        </div>
      ))}
    </div>
  );
}

function ReviewExtractionPreview({ report }: { report: GovernanceReportResponse }) {
  const raidPreview = report.raid_items.slice(0, 3);
  const escalationPreview = report.escalation_items.slice(0, 2);

  return (
    <div className="rounded-md border border-slate-200 p-4">
      <h3 className="text-sm font-semibold text-slate-950">Extraction Preview</h3>
      <div className="mt-3 space-y-3">
        {raidPreview.length === 0 && escalationPreview.length === 0 ? (
          <p className="text-sm text-slate-500">No RAID items or escalations were returned.</p>
        ) : null}
        {raidPreview.map((item) => (
          <p key={item.id} className="text-sm text-slate-700">
            <span className="font-medium capitalize text-slate-950">{item.type}:</span>{" "}
            {item.description}
          </p>
        ))}
        {escalationPreview.map((item) => (
          <p key={item.id} className="text-sm text-red-700">
            <span className="font-medium">Escalation:</span> {item.description}
          </p>
        ))}
      </div>
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
    year: "numeric",
  }).format(date);
}
