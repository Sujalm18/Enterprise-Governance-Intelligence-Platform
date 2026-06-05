import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { GovernanceReportResponse } from "@/types/api";

type UploadHistoryTableProps = {
  reports: GovernanceReportResponse[];
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
};

export function UploadHistoryTable({
  reports,
  isLoading,
  error,
  onRetry,
}: UploadHistoryTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload History</CardTitle>
        <CardDescription>Recent generated reports from uploaded governance documents.</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-14 animate-pulse rounded-md bg-slate-200" />
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col gap-3 rounded-md bg-red-50 p-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-red-700">
              {error instanceof Error ? error.message : "Upload history could not be loaded."}
            </p>
            <Button variant="outline" onClick={onRetry}>
              Retry
            </Button>
          </div>
        ) : reports.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
            No generated reports yet.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-md border border-slate-200">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">Document</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">RAID</th>
                  <th className="px-4 py-3 font-semibold">Escalations</th>
                  <th className="px-4 py-3 font-semibold">Created</th>
                  <th className="px-4 py-3 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {reports.slice(0, 8).map((report) => (
                  <tr key={report.id}>
                    <td className="px-4 py-3 font-medium text-slate-950">{report.filename}</td>
                    <td className="px-4 py-3 capitalize text-slate-600">
                      {report.review_status.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{report.raid_items.length}</td>
                    <td className="px-4 py-3 text-slate-600">{report.escalation_items.length}</td>
                    <td className="px-4 py-3 text-slate-500">{formatDate(report.created_at)}</td>
                    <td className="px-4 py-3">
                      <Button asChild size="sm" variant="outline">
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
