import { Activity, Clock, Database, Gauge } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardStatsResponse } from "@/types/api";

type ProcessingMetricsProps = {
  stats: DashboardStatsResponse;
};

export function ProcessingMetrics({ stats }: ProcessingMetricsProps) {
  const metrics = [
    {
      label: "Average Confidence",
      value: `${Math.round(stats.average_confidence * 100)}%`,
      icon: Gauge,
    },
    {
      label: "Average Processing",
      value: `${stats.average_processing_time.toFixed(1)}s`,
      icon: Clock,
    },
    {
      label: "Tokens Consumed",
      value: stats.total_tokens_consumed.toLocaleString(),
      icon: Database,
    },
    {
      label: "Failed Jobs",
      value: stats.failed_jobs.toLocaleString(),
      icon: Activity,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Processing Metrics</CardTitle>
        <CardDescription>Operational performance and extraction confidence.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <metric.icon className="h-4 w-4 text-blue-600" aria-hidden="true" />
              <span className="text-sm font-medium text-slate-600">{metric.label}</span>
            </div>
            <span className="text-sm font-semibold text-slate-950">{metric.value}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
