import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { GovernanceReportResponse } from "@/types/api";

type ExplainabilityPanelProps = {
  report: GovernanceReportResponse;
};

export function ExplainabilityPanel({ report }: ExplainabilityPanelProps) {
  const sections = [
    {
      title: "Classification",
      rows: [
        ["Document Type", report.document_type?.replace(/_/g, " ") ?? "Not exposed by API"],
        [
          "Classification Confidence",
          typeof report.classification_confidence === "number"
            ? `${Math.round(report.classification_confidence * 100)}%`
            : "Not exposed by API",
        ],
        ["Governance Relevance", report.governance_relevance ?? "Not exposed by API"],
      ],
    },
    {
      title: "Extraction Basis",
      rows: [
        ["RAID Items", `${report.raid_items.length} returned`],
        ["Escalations", `${report.escalation_items.length} returned`],
        [
          "Source Evidence",
          sourceEvidenceCount(report).toLocaleString() + " item(s) include source excerpts",
        ],
      ],
    },
    {
      title: "Review Context",
      rows: [
        ["Review Status", report.review_status.replace(/_/g, " ")],
        ["Reviewer", report.reviewer ?? "Pending"],
        ["Review Notes", report.review_notes ?? "No review notes"],
      ],
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Explainability</CardTitle>
        <CardDescription>Trace fields and extraction context currently available from the API.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {sections.map((section) => (
          <section key={section.title}>
            <h3 className="mb-2 text-sm font-semibold text-slate-950">{section.title}</h3>
            <div className="space-y-2">
              {section.rows.map(([label, value]) => (
                <div key={label} className="rounded-md bg-slate-50 px-3 py-2 text-sm">
                  <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    {label}
                  </div>
                  <div className="mt-1 text-slate-800">{value}</div>
                </div>
              ))}
            </div>
          </section>
        ))}
      </CardContent>
    </Card>
  );
}

function sourceEvidenceCount(report: GovernanceReportResponse) {
  return [
    ...report.raid_items.map((item) => item.source_excerpt),
    ...report.escalation_items.map((item) => item.source_excerpt),
  ].filter(Boolean).length;
}
