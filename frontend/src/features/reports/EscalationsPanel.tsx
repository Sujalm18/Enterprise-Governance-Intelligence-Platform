import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceBadge } from "@/features/reports/ConfidenceBadge";
import { StatusBadge } from "@/features/reports/StatusBadge";
import type { EscalationItemResponse } from "@/types/api";

type EscalationsPanelProps = {
  items: EscalationItemResponse[];
};

export function EscalationsPanel({ items }: EscalationsPanelProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

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
            {items.map((item) => {
              const hasInsights = !!(item.explain_why || item.suggested_actions || item.estimated_impact);
              const isExpanded = expandedId === item.id;

              return (
                <article key={item.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4 hover:shadow-sm transition-shadow">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2 mb-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={item.status} />
                      <span className="rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-semibold capitalize text-slate-700">
                        {item.severity}
                      </span>
                      <ConfidenceBadge score={item.confidence_score} />
                    </div>
                    {hasInsights && (
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : item.id)}
                        className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:underline bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded"
                      >
                        {isExpanded ? "Hide Insights" : "AI Insights"}
                      </button>
                    )}
                  </div>
                  <p className="text-sm leading-6 text-slate-800 font-medium">{item.description}</p>
                  {item.routing_target ? (
                    <p className="mt-2 text-xs font-semibold text-slate-500">
                      Routed to: <span className="text-slate-700">{item.routing_target}</span>
                    </p>
                  ) : null}
                  {item.source_excerpt ? (
                    <blockquote className="mt-2 border-l-2 border-slate-300 pl-2 text-xs text-slate-500 italic">
                      &ldquo;{item.source_excerpt}&rdquo;
                    </blockquote>
                  ) : null}

                  {isExpanded && hasInsights && (
                    <div className="mt-4 border-t border-slate-200 pt-3 space-y-3">
                      {item.explain_why && (
                        <div>
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Why it matters</span>
                          <p className="text-xs text-slate-700 leading-relaxed font-medium bg-white p-2 rounded-lg border border-slate-100">{item.explain_why}</p>
                        </div>
                      )}
                      {item.suggested_actions && (
                        <div>
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Suggested actions</span>
                          <p className="text-xs text-slate-700 leading-relaxed font-medium bg-white p-2 rounded-lg border border-slate-100 whitespace-pre-line">{item.suggested_actions}</p>
                        </div>
                      )}
                      {item.estimated_impact && (
                        <div>
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Estimated impact</span>
                          <div className="inline-flex items-center gap-1 rounded bg-green-50 px-2 py-0.5 text-xs font-semibold text-green-700 border border-green-200">
                            {item.estimated_impact}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
