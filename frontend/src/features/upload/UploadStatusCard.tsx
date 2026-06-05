import { Link } from "react-router-dom";
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DocumentResponse, GovernanceReportResponse } from "@/types/api";

type UploadStatusCardProps = {
  file: File | null;
  document: DocumentResponse | null;
  progress: number;
  isUploading: boolean;
  error: unknown;
  generatedReport?: GovernanceReportResponse;
};

export function UploadStatusCard({
  file,
  document,
  progress,
  isUploading,
  error,
  generatedReport,
}: UploadStatusCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Status</CardTitle>
        <CardDescription>Browser upload progress and backend acknowledgement.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!file ? (
          <div className="rounded-md border border-dashed border-slate-300 p-5 text-sm text-slate-500">
            Select a document to begin the upload workflow.
          </div>
        ) : null}

        {isUploading ? (
          <StatusRow icon={<Loader2 className="h-5 w-5 animate-spin text-blue-600" />} title="Uploading document" description={`${progress}% uploaded`} />
        ) : null}

        {error ? (
          <StatusRow
            icon={<AlertCircle className="h-5 w-5 text-red-600" />}
            title="Upload failed"
            description={error instanceof Error ? error.message : "The upload request failed."}
          />
        ) : null}

        {document ? (
          <StatusRow
            icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
            title="Upload accepted"
            description={`Document #${document.id} is queued with status ${document.status}.`}
          />
        ) : null}

        {file || isUploading || document ? (
          <div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-blue-600 transition-all"
                style={{ width: `${Math.max(0, Math.min(progress, 100))}%` }}
              />
            </div>
          </div>
        ) : null}

        {generatedReport ? (
          <Button asChild>
            <Link to={`/reports/${generatedReport.id}`}>Open generated report</Link>
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}

type StatusRowProps = {
  icon: React.ReactNode;
  title: string;
  description: string;
};

function StatusRow({ icon, title, description }: StatusRowProps) {
  return (
    <div className="flex gap-3 rounded-md bg-slate-50 p-4">
      <div className="mt-0.5">{icon}</div>
      <div>
        <p className="font-medium text-slate-950">{title}</p>
        <p className="mt-1 text-sm text-slate-600">{description}</p>
      </div>
    </div>
  );
}
