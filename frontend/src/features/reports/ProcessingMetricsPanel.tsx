import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { GovernanceReportResponse } from "@/types/api";

type ProcessingMetricsPanelProps = {
  report: GovernanceReportResponse;
};

export function ProcessingMetricsPanel({ report }: ProcessingMetricsPanelProps) {
  const metrics = [
    ["Processing Time", `${report.processing_time_seconds.toFixed(2)}s`],
    ["Tokens Used", report.tokens_used.toLocaleString()],
    ["Provider", report.provider_name],
    ["Model Version", report.model_version],
    ["Prompt Version", report.prompt_version],
    ["Report Version", `V${report.version}`],
    ["Latest Version", report.is_latest ? "Yes" : "No"],
    ["Created", formatDate(report.created_at)],
    ["Updated", formatDate(report.updated_at)],
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Processing Metrics</CardTitle>
        <CardDescription>Execution metadata produced by the backend workflow.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {metrics.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 rounded-md bg-slate-50 px-3 py-2 text-sm">
            <span className="text-slate-500">{label}</span>
            <span className="text-right font-medium text-slate-900">{value}</span>
          </div>
        ))}
      </CardContent>
    </Card>
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
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
