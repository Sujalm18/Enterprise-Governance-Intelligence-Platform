import { Link } from "react-router-dom";
import { CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DocumentResponse, GovernanceReportResponse, WorkflowJobResponse } from "@/types/api";

type ProcessingTrackerProps = {
  document: DocumentResponse | null;
  workflowJob: WorkflowJobResponse | null | undefined;
  generatedReport?: GovernanceReportResponse;
  isPolling: boolean;
};

export function ProcessingTracker({
  document,
  workflowJob,
  generatedReport,
  isPolling,
}: ProcessingTrackerProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Processing Tracker</CardTitle>
        <CardDescription>Backend workflow polling and generated report detection.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!document ? (
          <div className="rounded-md border border-dashed border-slate-300 p-5 text-sm text-slate-500">
            Upload a document to start tracking backend processing.
          </div>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-3">
              <TrackerTile label="Document ID" value={`#${document.id}`} />
              <TrackerTile label="Document Status" value={document.status} />
              <TrackerTile
                label="Report"
                value={generatedReport ? `#${generatedReport.id}` : isPolling ? "Polling" : "Pending"}
              />
            </div>

            {workflowJob?.logs ? (
              <div className="rounded-md bg-slate-950 p-4 text-xs leading-5 text-slate-100">
                <pre className="max-h-64 overflow-auto whitespace-pre-wrap">{workflowJob.logs}</pre>
              </div>
            ) : (
              <div className="rounded-md bg-slate-50 p-4 text-sm text-slate-600">
                Workflow logs are not available yet. The UI is polling for the generated report.
              </div>
            )}

            {generatedReport ? (
              <div className="flex flex-col gap-3 rounded-md bg-emerald-50 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex gap-3">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-600" aria-hidden="true" />
                  <div>
                    <p className="font-medium text-emerald-950">Processing complete</p>
                    <p className="mt-1 text-sm text-emerald-700">
                      Governance report is ready for RAID and escalation review.
                    </p>
                  </div>
                </div>
                <Button asChild>
                  <Link to={`/reports/${generatedReport.id}`}>Open report</Link>
                </Button>
              </div>
            ) : isPolling ? (
              <div className="flex items-center gap-3 rounded-md bg-blue-50 p-4 text-sm text-blue-700">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Processing in background. Checking for generated report...
              </div>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function TrackerTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold capitalize text-slate-950">{value.replace(/_/g, " ")}</p>
    </div>
  );
}
