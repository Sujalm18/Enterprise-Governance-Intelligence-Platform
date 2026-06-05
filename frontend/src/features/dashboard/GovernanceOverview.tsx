import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardChartsResponse, StatusCount } from "@/types/api";

type GovernanceOverviewProps = {
  charts: DashboardChartsResponse;
};

export function GovernanceOverview({ charts }: GovernanceOverviewProps) {
  const totalRaid = total(charts.raid_distribution);
  const totalStatuses = total(charts.reports_by_status);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Governance Overview</CardTitle>
        <CardDescription>
          Distribution of governance outputs returned by the backend dashboard API.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-6 lg:grid-cols-2">
        <DistributionList
          title="RAID Distribution"
          items={charts.raid_distribution}
          total={totalRaid}
          emptyLabel="No RAID items detected yet."
        />
        <DistributionList
          title="Report Status"
          items={charts.reports_by_status}
          total={totalStatuses}
          emptyLabel="No report statuses available."
        />
      </CardContent>
    </Card>
  );
}

type DistributionListProps = {
  title: string;
  items: StatusCount[];
  total: number;
  emptyLabel: string;
};

function DistributionList({ title, items, total, emptyLabel }: DistributionListProps) {
  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        <span className="text-xs font-medium text-slate-500">{total.toLocaleString()} total</span>
      </div>
      {items.length === 0 ? (
        <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          {emptyLabel}
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const percent = total > 0 ? (item.count / total) * 100 : 0;
            return (
              <div key={item.label}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-medium capitalize text-slate-700">
                    {item.label.replace(/_/g, " ")}
                  </span>
                  <span className="text-slate-500">{item.count.toLocaleString()}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-blue-600"
                    style={{ width: `${Math.max(percent, item.count > 0 ? 6 : 0)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function total(items: StatusCount[]) {
  return items.reduce((sum, item) => sum + item.count, 0);
}
