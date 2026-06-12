import { useState } from "react";
import { ConfidenceBadge } from "@/features/reports/ConfidenceBadge";
import type { RaidItemResponse } from "@/types/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type RaidItemsTableProps = {
  items: RaidItemResponse[];
};

export function RaidItemsTable({ items }: RaidItemsTableProps) {
  const [activeTraceId, setActiveTraceId] = useState<number | null>(null);
  const [expandedItemId, setExpandedItemId] = useState<number | null>(null);

  const getPriorityBadgeClass = (priority: string | null | undefined) => {
    const p = priority || "P4";
    if (p === "P1") return "bg-red-50 text-red-700 border-red-200";
    if (p === "P2") return "bg-amber-50 text-amber-700 border-amber-200";
    if (p === "P3") return "bg-blue-50 text-blue-700 border-blue-200";
    return "bg-slate-50 text-slate-700 border-slate-200";
  };

  const getOwnerBadgeClass = (owner: string | null | undefined) => {
    const o = owner || "Analyst";
    if (o === "Governance Lead") return "bg-indigo-50 text-indigo-700 border-indigo-200";
    if (o === "Manager") return "bg-purple-50 text-purple-700 border-purple-200";
    return "bg-cyan-50 text-cyan-700 border-cyan-200";
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return "bg-red-100 text-red-800 border-red-200";
    if (score >= 50) return "bg-amber-100 text-amber-800 border-amber-200";
    if (score >= 25) return "bg-blue-100 text-blue-800 border-blue-200";
    return "bg-slate-100 text-slate-800 border-slate-200";
  };

  return (
    <Card className="shadow-md border-slate-200 bg-white/80 backdrop-blur-md">
      <CardHeader className="pb-3">
        <CardTitle className="text-xl font-bold text-slate-900">Recommended Governance Actions</CardTitle>
        <CardDescription className="text-slate-500">
          Risks, issues, actions, and dependencies matched with deterministic playbooks, priority mapping, suggested owners, and mitigations.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyPanel message="No RAID items were extracted for this report." />
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-inner">
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead className="bg-slate-50/80 text-xs font-semibold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-5 py-4">Item Details</th>
                  <th className="px-5 py-4">Priority & Owner</th>
                  <th className="px-5 py-4">Risk Score</th>
                  <th className="px-5 py-4">Finding & Evidence</th>
                  <th className="px-5 py-4">Recommended Mitigations</th>
                  <th className="px-5 py-4 text-center">Explainability</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white/50">
                {items.map((item) => {
                  const trace = item.explainability_trace;
                  const mitigations: string[] = Array.isArray(item.recommended_mitigations)
                     ? item.recommended_mitigations
                     : [];
                  const hasInsights = !!(item.explain_why || item.suggested_actions || item.estimated_impact);

                  return (
                    <>
                      <tr key={item.id} className="hover:bg-slate-50/50 transition-colors">
                        {/* Item Details */}
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-800 border border-slate-200">
                            {item.type}
                          </span>
                          <div className="mt-1.5">
                            <ConfidenceBadge score={item.confidence_score} />
                          </div>
                        </td>

                        {/* Priority & Owner */}
                        <td className="px-5 py-4 whitespace-nowrap">
                          <div className="flex flex-col gap-1.5">
                            <span className={`inline-flex w-max items-center rounded-md px-2.5 py-0.5 text-xs font-semibold border ${getPriorityBadgeClass(item.priority || item.recommended_priority)}`}>
                              {item.priority || item.recommended_priority || "P4"}
                            </span>
                            <span className={`inline-flex w-max items-center rounded-md px-2.5 py-0.5 text-xs font-medium border ${getOwnerBadgeClass(item.suggested_owner_role)}`}>
                              {item.suggested_owner_role || "Analyst"}
                            </span>
                          </div>
                        </td>

                        {/* Risk Score */}
                        <td className="px-5 py-4 whitespace-nowrap">
                          <div className={`inline-flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold border-2 ${getScoreColor(item.risk_score || 0)}`}>
                            {item.risk_score || 0}
                          </div>
                        </td>

                        {/* Finding & Evidence */}
                        <td className="px-5 py-4 max-w-[300px]">
                          <p className="font-medium text-slate-800 leading-relaxed">{item.description}</p>
                          {item.source_excerpt && (
                            <div className="mt-2 rounded-lg bg-slate-50 p-2 text-xs border border-slate-100 text-slate-500 italic">
                              &ldquo;{item.source_excerpt}&rdquo;
                            </div>
                          )}
                        </td>

                        {/* Recommended Mitigations */}
                        <td className="px-5 py-4 max-w-[280px]">
                          {mitigations.length > 0 ? (
                            <div className="space-y-2">
                              <ul className="list-disc list-inside space-y-1 text-xs text-slate-700">
                                {mitigations.map((mit, idx) => (
                                  <li key={idx} className="leading-relaxed">{mit}</li>
                                ))}
                              </ul>
                              <div className="flex flex-wrap gap-2 pt-1">
                                {item.implementation_effort && (
                                  <span className="inline-flex items-center rounded bg-slate-50 px-2 py-0.5 text-[10px] font-medium text-slate-600 border border-slate-200">
                                    Effort: {item.implementation_effort}
                                  </span>
                                )}
                                {item.expected_risk_reduction && (
                                  <span className="inline-flex items-center rounded bg-green-50 px-2 py-0.5 text-[10px] font-medium text-green-700 border border-green-200">
                                    Reduction: {item.expected_risk_reduction}
                                  </span>
                                )}
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400 italic">No mitigations defined.</span>
                          )}
                        </td>

                        {/* Explainability Trace & AI Insights */}
                        <td className="px-5 py-4 text-center relative whitespace-nowrap">
                          <div className="flex flex-col gap-1.5 items-center justify-center">
                            {hasInsights && (
                              <button
                                onClick={() => setExpandedItemId(expandedItemId === item.id ? null : item.id)}
                                className="inline-flex items-center rounded bg-indigo-50 border border-indigo-200 px-2.5 py-1 text-xs font-semibold text-indigo-700 hover:bg-indigo-100/70 transition-colors"
                              >
                                {expandedItemId === item.id ? "Hide Insights" : "AI Insights"}
                              </button>
                            )}
                            <button
                              onClick={() => setActiveTraceId(activeTraceId === item.id ? null : item.id)}
                              className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-700 hover:underline"
                            >
                              Trace details
                            </button>
                          </div>
                          {activeTraceId === item.id && trace && (
                            <div className="absolute right-4 top-12 z-50 w-72 rounded-xl border border-slate-200 bg-white p-4 shadow-xl text-left whitespace-normal">
                              <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                                <h4 className="font-bold text-slate-800 text-xs">Explainability Lineage</h4>
                                <button
                                  onClick={() => setActiveTraceId(null)}
                                  className="text-slate-400 hover:text-slate-600 text-base font-bold"
                                >
                                  &times;
                                </button>
                              </div>
                              <div className="space-y-2 text-xs">
                                <div>
                                  <span className="font-semibold text-slate-500">Source:</span>{" "}
                                  <span className="capitalize font-medium text-slate-700">
                                    {trace.recommendation_source === "playbook" ? "Deterministic Playbook" : "AI Heuristic Model"}
                                  </span>
                                </div>
                                {trace.playbook && (
                                  <div>
                                    <span className="font-semibold text-slate-500">Playbook Used:</span>{" "}
                                    <span className="font-medium text-slate-700">{trace.playbook}</span>
                                  </div>
                                )}
                                {trace.matched_keywords && trace.matched_keywords.length > 0 && (
                                  <div>
                                    <span className="font-semibold text-slate-500">Matched Keywords:</span>{" "}
                                    <span className="font-mono bg-slate-100 px-1 py-0.5 rounded text-[10px] text-slate-600">
                                      {trace.matched_keywords.join(", ")}
                                    </span>
                                  </div>
                                )}
                                {trace.evidence && trace.evidence.length > 0 && (
                                  <div>
                                    <span className="font-semibold text-slate-500 block mb-1">Evidence Context:</span>
                                    <p className="bg-slate-50 p-2 rounded text-[11px] text-slate-600 italic border border-slate-100">
                                      &ldquo;{trace.evidence[0]}&rdquo;
                                    </p>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </td>
                      </tr>
                      {expandedItemId === item.id && (
                        <tr key={`${item.id}-insights`} className="bg-indigo-50/10">
                          <td colSpan={6} className="px-5 py-4 border-t border-slate-200">
                            <div className="grid gap-4 md:grid-cols-3">
                              <div className="bg-white p-3.5 rounded-xl border border-indigo-50 shadow-sm whitespace-normal">
                                <h5 className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-500"></span>
                                  Why it matters
                                </h5>
                                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                                  {item.explain_why || "No contextual explanation provided by AI."}
                                </p>
                              </div>
                              <div className="bg-white p-3.5 rounded-xl border border-indigo-50 shadow-sm whitespace-normal">
                                <h5 className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                                  <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
                                  Suggested actions
                                </h5>
                                <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line font-medium">
                                  {item.suggested_actions || "No actions suggested."}
                                </p>
                              </div>
                              <div className="bg-white p-3.5 rounded-xl border border-indigo-50 shadow-sm flex flex-col justify-between whitespace-normal">
                                <div>
                                  <h5 className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                                    <span className="h-1.5 w-1.5 rounded-full bg-green-500"></span>
                                    Estimated impact
                                  </h5>
                                  <p className="text-xs text-slate-500 mb-2">Quantified risk reduction metric:</p>
                                </div>
                                <div className="inline-flex w-max items-center gap-1 rounded bg-green-50 border border-green-200 px-2.5 py-1 text-xs font-semibold text-green-700">
                                  {item.estimated_impact || "No impact estimate."}
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}
