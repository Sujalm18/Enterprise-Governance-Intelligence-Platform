import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DocumentResponse, GovernanceReportResponse, WorkflowJobResponse } from "@/types/api";

type JobStatusTimelineProps = {
  document: DocumentResponse | null;
  workflowJob: WorkflowJobResponse | null | undefined;
  generatedReport?: GovernanceReportResponse;
};

export function JobStatusTimeline({
  document,
  workflowJob,
  generatedReport,
}: JobStatusTimelineProps) {
  const stages = [
    {
      label: "Upload Document",
      complete: Boolean(document),
      active: false,
      detail: document ? `Document #${document.id}` : "Waiting for file",
    },
    {
      label: "Track Processing",
      complete: Boolean(generatedReport),
      active: Boolean(document && !generatedReport),
      detail: workflowJob?.status ? workflowJob.status.replace(/_/g, " ") : "Background workflow",
    },
    {
      label: "Generate Report",
      complete: Boolean(generatedReport),
      active: false,
      detail: generatedReport ? `Report #${generatedReport.id}` : "Pending report",
    },
    {
      label: "Review RAID and Escalations",
      complete: false,
      active: Boolean(generatedReport),
      detail: generatedReport ? "Ready in Reports" : "Available after report generation",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Status Timeline</CardTitle>
        <CardDescription>Recruiter-demo flow from upload to generated governance report.</CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="space-y-4">
          {stages.map((stage, index) => (
            <li key={stage.label} className="flex gap-3">
              <div className="flex flex-col items-center">
                {stage.complete ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" aria-hidden="true" />
                ) : stage.active ? (
                  <Loader2 className="h-5 w-5 animate-spin text-blue-600" aria-hidden="true" />
                ) : (
                  <Circle className="h-5 w-5 text-slate-300" aria-hidden="true" />
                )}
                {index < stages.length - 1 ? <div className="mt-2 h-8 w-px bg-slate-200" /> : null}
              </div>
              <div>
                <p className="font-medium text-slate-950">{stage.label}</p>
                <p className="mt-1 text-sm capitalize text-slate-500">{stage.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
