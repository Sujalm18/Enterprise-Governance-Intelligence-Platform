import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ClipboardCheck } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { listGovernanceReports } from "@/lib/api/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { ReviewReportCard } from "@/features/review/ReviewReportCard";

const pendingReviewParams = {
  is_latest: true,
  review_status: "pending_review",
};

export function ReviewQueuePage() {
  const pendingReportsQuery = useQuery({
    queryKey: queryKeys.reports.pendingReview,
    queryFn: () => listGovernanceReports(pendingReviewParams),
  });

  return (
    <>
      <PageHeader
        eyebrow="Human oversight"
        title="Review Queue"
        description="Inspect pending governance reports, approve executive-ready outputs, or request changes with reviewer notes."
      />

      {pendingReportsQuery.isLoading ? (
        <ReviewQueueSkeleton />
      ) : pendingReportsQuery.error ? (
        <ReviewQueueError
          message={
            pendingReportsQuery.error instanceof Error
              ? pendingReportsQuery.error.message
              : "Review queue could not be loaded."
          }
          onRetry={() => void pendingReportsQuery.refetch()}
        />
      ) : pendingReportsQuery.data && pendingReportsQuery.data.length > 0 ? (
        <div className="space-y-5">
          <QueueSummary count={pendingReportsQuery.data.length} />
          {pendingReportsQuery.data.map((report) => (
            <ReviewReportCard key={report.id} report={report} />
          ))}
        </div>
      ) : (
        <ReviewQueueEmpty />
      )}
    </>
  );
}

function QueueSummary({ count }: { count: number }) {
  return (
    <Card className="border-blue-200 bg-blue-50">
      <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-3">
          <ClipboardCheck className="mt-0.5 h-5 w-5 text-blue-700" aria-hidden="true" />
          <div>
            <h3 className="font-semibold text-blue-950">Reviewer workload</h3>
            <p className="mt-1 text-sm text-blue-700">
              {count} governance report{count === 1 ? "" : "s"} awaiting review.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ReviewQueueSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, index) => (
        <div key={index} className="h-72 animate-pulse rounded-lg bg-slate-200" />
      ))}
    </div>
  );
}

type ReviewQueueErrorProps = {
  message: string;
  onRetry: () => void;
};

function ReviewQueueError({ message, onRetry }: ReviewQueueErrorProps) {
  return (
    <Card className="border-red-200 bg-red-50">
      <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-none text-red-600" aria-hidden="true" />
          <div>
            <h3 className="font-semibold text-red-950">Review queue unavailable</h3>
            <p className="mt-1 text-sm text-red-700">{message}</p>
          </div>
        </div>
        <Button variant="outline" onClick={onRetry}>
          Retry
        </Button>
      </CardContent>
    </Card>
  );
}

function ReviewQueueEmpty() {
  return (
    <Card>
      <CardContent className="p-10 text-center">
        <h3 className="text-lg font-semibold text-slate-950">Review queue is clear</h3>
        <p className="mt-2 text-sm text-slate-600">
          There are no pending governance reports. New processed uploads will appear here.
        </p>
      </CardContent>
    </Card>
  );
}
