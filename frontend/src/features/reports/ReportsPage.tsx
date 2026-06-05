import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { listGovernanceReports } from "@/lib/api/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { ReportsTable } from "@/features/reports/ReportsTable";
import type { GovernanceReportResponse, ReviewStatus } from "@/types/api";

type SortDirection = "desc" | "asc";

export function ReportsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<"all" | ReviewStatus>("all");
  const [documentType, setDocumentType] = useState("all");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const queryParams = {
    is_latest: true,
    ...(status !== "all" ? { review_status: status } : {}),
  };

  const reportsQuery = useQuery({
    queryKey: queryKeys.reports.list(queryParams),
    queryFn: () => listGovernanceReports(queryParams),
  });

  const documentTypes = useMemo(
    () =>
      Array.from(
        new Set(
          (reportsQuery.data ?? [])
            .map((report) => report.document_type)
            .filter((value): value is string => Boolean(value)),
        ),
      ).sort(),
    [reportsQuery.data],
  );

  const filteredReports = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return (reportsQuery.data ?? [])
      .filter((report) => matchesSearch(report, normalizedSearch))
      .filter((report) => documentType === "all" || report.document_type === documentType)
      .sort((left, right) => {
        const leftTime = new Date(left.created_at).getTime();
        const rightTime = new Date(right.created_at).getTime();
        return sortDirection === "desc" ? rightTime - leftTime : leftTime - rightTime;
      });
  }, [documentType, reportsQuery.data, search, sortDirection]);

  return (
    <>
      <PageHeader
        eyebrow="Governance intelligence"
        title="Governance Reports"
        description="Browse extracted governance reports, inspect extraction quality, and open detailed intelligence views."
      />

      <Card className="mb-6">
        <CardContent className="p-5">
          <div className="grid gap-4 lg:grid-cols-[minmax(260px,1fr)_180px_220px_180px_auto]">
            <label className="relative block">
              <span className="sr-only">Search reports</span>
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search filename, summary, RAID, escalations..."
                className="h-10 w-full rounded-md border border-slate-300 bg-white pl-9 pr-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </label>

            <select
              value={status}
              onChange={(event) => setStatus(event.target.value as "all" | ReviewStatus)}
              className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
              aria-label="Filter by status"
            >
              <option value="all">All statuses</option>
              <option value="pending_review">Pending review</option>
              <option value="approved">Approved</option>
              <option value="changes_requested">Changes requested</option>
            </select>

            <select
              value={documentType}
              onChange={(event) => setDocumentType(event.target.value)}
              disabled={documentTypes.length === 0}
              className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm disabled:bg-slate-100 disabled:text-slate-400"
              aria-label="Filter by document type"
            >
              <option value="all">
                {documentTypes.length === 0 ? "Document type unavailable" : "All document types"}
              </option>
              {documentTypes.map((type) => (
                <option key={type} value={type}>
                  {type.replace(/_/g, " ")}
                </option>
              ))}
            </select>

            <select
              value={sortDirection}
              onChange={(event) => setSortDirection(event.target.value as SortDirection)}
              className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
              aria-label="Sort by created date"
            >
              <option value="desc">Newest first</option>
              <option value="asc">Oldest first</option>
            </select>

            <Button
              variant="outline"
              onClick={() => {
                setSearch("");
                setStatus("all");
                setDocumentType("all");
                setSortDirection("desc");
              }}
            >
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {reportsQuery.isLoading ? (
        <ReportsTableSkeleton />
      ) : reportsQuery.error ? (
        <ReportsError
          message={
            reportsQuery.error instanceof Error
              ? reportsQuery.error.message
              : "Reports could not be loaded."
          }
          onRetry={() => void reportsQuery.refetch()}
        />
      ) : (
        <ReportsTable reports={filteredReports} totalReports={(reportsQuery.data ?? []).length} />
      )}
    </>
  );
}

function matchesSearch(report: GovernanceReportResponse, search: string) {
  if (!search) {
    return true;
  }
  const haystack = [
    report.filename,
    report.summary,
    report.executive_summary,
    report.review_status,
    report.document_type,
    ...(report.raid_items ?? []).map((item) => item.description),
    ...(report.escalation_items ?? []).map((item) => item.description),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(search);
}

function ReportsTableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="h-20 animate-pulse rounded-lg bg-slate-200" />
      ))}
    </div>
  );
}

type ReportsErrorProps = {
  message: string;
  onRetry: () => void;
};

function ReportsError({ message, onRetry }: ReportsErrorProps) {
  return (
    <Card className="border-red-200 bg-red-50">
      <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="font-semibold text-red-950">Reports unavailable</h3>
          <p className="mt-1 text-sm text-red-700">{message}</p>
        </div>
        <Button variant="outline" onClick={onRetry}>
          Retry
        </Button>
      </CardContent>
    </Card>
  );
}
