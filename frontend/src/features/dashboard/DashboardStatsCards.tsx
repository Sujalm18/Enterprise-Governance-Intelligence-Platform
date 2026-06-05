import { ClipboardCheck, FileText, Gauge, Siren } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { DashboardChartsResponse, DashboardStatsResponse } from "@/types/api";

type DashboardStatsCardsProps = {
  stats: DashboardStatsResponse;
  charts: DashboardChartsResponse;
};

export function DashboardStatsCards({ stats, charts }: DashboardStatsCardsProps) {
  const raidItems = charts.raid_distribution.reduce((total, item) => total + item.count, 0);
  const averageConfidence = `${Math.round(stats.average_confidence * 100)}%`;

  const cards = [
    {
      label: "Total Reports",
      value: stats.reports_generated.toLocaleString(),
      detail: `${stats.total_documents.toLocaleString()} documents ingested`,
      icon: FileText,
      tone: "text-blue-600",
    },
    {
      label: "Pending Reviews",
      value: stats.pending_reviews.toLocaleString(),
      detail: `${stats.approved_reports.toLocaleString()} approved reports`,
      icon: ClipboardCheck,
      tone: "text-amber-600",
    },
    {
      label: "Escalations",
      value: stats.total_escalations.toLocaleString(),
      detail: `${stats.open_escalations.toLocaleString()} open escalations`,
      icon: Siren,
      tone: "text-red-600",
    },
    {
      label: "RAID Items",
      value: raidItems.toLocaleString(),
      detail: `Average confidence ${averageConfidence}`,
      icon: Gauge,
      tone: "text-emerald-600",
    },
  ];

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" aria-label="Dashboard metrics">
      {cards.map((card) => (
        <Card key={card.label}>
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-500">{card.label}</p>
                <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
                  {card.value}
                </p>
              </div>
              <div className="rounded-md bg-slate-100 p-2">
                <card.icon className={`h-5 w-5 ${card.tone}`} aria-hidden="true" />
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-500">{card.detail}</p>
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
