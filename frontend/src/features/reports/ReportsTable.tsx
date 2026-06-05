import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ConfidenceBadge } from "@/features/reports/ConfidenceBadge";
import { StatusBadge } from "@/features/reports/StatusBadge";
import type { GovernanceReportResponse } from "@/types/api";

type ReportsTableProps = {
  reports: GovernanceReportResponse[];
  totalReports: number;
};

export function ReportsTable({ reports, totalReports }: ReportsTableProps) {
  if (totalReports === 0) {
    return (
      <Card>
        <CardContent className="p-10 text-center">
          <h3 className="text-lg font-semibold text-slate-950">No reports generated yet</h3>
          <p className="mt-2 text-sm text-slate-600">
            Upload and process governance documents to populate this workspace.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (reports.length === 0) {
    return (
      <Card>
        <CardContent className="p-10 text-center">
          <h3 className="text-lg font-semibold text-slate-950">No matching reports</h3>
          <p className="mt-2 text-sm text-slate-600">
            Adjust the search, status, or document type filters.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[880px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3 font-semibold">Report</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Confidence</th>
                <th className="px-5 py-3 font-semibold">RAID</th>
                <th className="px-5 py-3 font-semibold">Escalations</th>
                <th className="px-5 py-3 font-semibold">Created</th>
                <th className="px-5 py-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-slate-50">
                  <td className="px-5 py-4">
                    <div className="font-medium text-slate-950">{report.filename}</div>
                    <div className="mt-1 max-w-md truncate text-xs text-slate-500">
                      {report.document_type?.replace(/_/g, " ") ?? `Document #${report.document_id}`}
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge status={report.review_status} />
                  </td>
                  <td className="px-5 py-4">
                    <ConfidenceBadge score={report.confidence_score} />
                  </td>
                  <td className="px-5 py-4 font-medium text-slate-700">
                    {report.raid_items.length}
                  </td>
                  <td className="px-5 py-4 font-medium text-slate-700">
                    {report.escalation_items.length}
                  </td>
                  <td className="whitespace-nowrap px-5 py-4 text-slate-500">
                    {formatDate(report.created_at)}
                  </td>
                  <td className="px-5 py-4">
                    <Button asChild size="sm" variant="outline">
                      <Link to={`/reports/${report.id}`}>Open</Link>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
