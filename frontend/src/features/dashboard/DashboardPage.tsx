import { useQuery } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getDashboardCharts, getDashboardStats } from "@/lib/api/dashboard";
import { queryKeys } from "@/lib/api/queryKeys";
import { DashboardStatsCards } from "@/features/dashboard/DashboardStatsCards";
import { GovernanceOverview } from "@/features/dashboard/GovernanceOverview";
import { ProcessingMetrics } from "@/features/dashboard/ProcessingMetrics";
import { RecentReports } from "@/features/dashboard/RecentReports";

export function DashboardPage() {
  const statsQuery = useQuery({
    queryKey: queryKeys.dashboard.stats,
    queryFn: getDashboardStats,
  });

  const chartsQuery = useQuery({
    queryKey: queryKeys.dashboard.charts,
    queryFn: getDashboardCharts,
  });

  const isLoading = statsQuery.isLoading || chartsQuery.isLoading;
  const error = statsQuery.error ?? chartsQuery.error;

  return (
    <>
      <PageHeader
        eyebrow="Executive workspace"
        title="Governance Dashboard"
        description="Portfolio-level view of report volume, pending reviews, escalations, RAID distribution, confidence, and processing performance."
      />

      {isLoading ? (
        <DashboardSkeleton />
      ) : error ? (
        <DashboardError
          message={error instanceof Error ? error.message : "Dashboard data could not be loaded."}
          onRetry={() => {
            void statsQuery.refetch();
            void chartsQuery.refetch();
          }}
        />
      ) : statsQuery.data && chartsQuery.data ? (
        <div className="space-y-6">
          <DashboardStatsCards stats={statsQuery.data} charts={chartsQuery.data} />
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
            <GovernanceOverview charts={chartsQuery.data} />
            <ProcessingMetrics stats={statsQuery.data} />
          </div>
          <RecentReports logs={statsQuery.data.recent_logs} />
        </div>
      ) : (
        <DashboardEmpty />
      )}
    </>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-32 animate-pulse rounded-lg bg-slate-200" />
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
        <div className="h-80 animate-pulse rounded-lg bg-slate-200" />
        <div className="h-80 animate-pulse rounded-lg bg-slate-200" />
      </div>
      <div className="h-72 animate-pulse rounded-lg bg-slate-200" />
    </div>
  );
}

type DashboardErrorProps = {
  message: string;
  onRetry: () => void;
};

function DashboardError({ message, onRetry }: DashboardErrorProps) {
  return (
    <Card className="border-red-200 bg-red-50">
      <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-none text-red-600" aria-hidden="true" />
          <div>
            <h3 className="font-semibold text-red-950">Dashboard unavailable</h3>
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

function DashboardEmpty() {
  return (
    <Card>
      <CardContent className="p-10 text-center">
        <h3 className="text-lg font-semibold text-slate-950">No dashboard data available</h3>
        <p className="mt-2 text-sm text-slate-600">
          Upload and process governance documents to populate executive metrics.
        </p>
      </CardContent>
    </Card>
  );
}
