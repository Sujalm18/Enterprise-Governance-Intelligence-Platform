import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { GovernanceReportResponse } from "@/types/api";

type ExecutiveSummaryCardProps = {
  report: GovernanceReportResponse;
};

export function ExecutiveSummaryCard({ report }: ExecutiveSummaryCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Executive Summary</CardTitle>
        <CardDescription>
          Executive-facing narrative and detailed governance interpretation.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <blockquote className="rounded-md border-l-4 border-blue-600 bg-blue-50 px-4 py-3 text-sm leading-6 text-slate-800">
          {report.executive_summary}
        </blockquote>
        <div>
          <h3 className="mb-2 text-sm font-semibold text-slate-950">Detailed Summary</h3>
          <p className="whitespace-pre-line text-sm leading-6 text-slate-700">{report.summary}</p>
        </div>
      </CardContent>
    </Card>
  );
}
