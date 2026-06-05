import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceBadge } from "@/features/reports/ConfidenceBadge";
import { StatusBadge } from "@/features/reports/StatusBadge";
import type { EscalationItemResponse } from "@/types/api";

type EscalationsPanelProps = {
  items: EscalationItemResponse[];
};

export function EscalationsPanel({ items }: EscalationsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Escalations</CardTitle>
        <CardDescription>Active escalation records detected in the report.</CardDescription>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
            No escalations were detected for this report.
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <article key={item.id} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={item.status} />
                  <span className="rounded-full bg-slate-200 px-2.5 py-1 text-xs font-semibold capitalize text-slate-700">
                    {item.severity}
                  </span>
                  <ConfidenceBadge score={item.confidence_score} />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-800">{item.description}</p>
                {item.routing_target ? (
                  <p className="mt-2 text-xs font-medium text-slate-500">
                    Routed to {item.routing_target}
                  </p>
                ) : null}
                {item.source_excerpt ? (
                  <p className="mt-2 text-xs text-slate-500">Source: {item.source_excerpt}</p>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
