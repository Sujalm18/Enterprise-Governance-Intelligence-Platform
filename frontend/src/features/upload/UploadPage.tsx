import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listGovernanceReports, getWorkflowJob } from "@/lib/api/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { uploadDocument } from "@/lib/api/upload";
import { DragAndDropUpload } from "@/features/upload/DragAndDropUpload";
import { JobStatusTimeline } from "@/features/upload/JobStatusTimeline";
import { ProcessingTracker } from "@/features/upload/ProcessingTracker";
import { UploadHistoryTable } from "@/features/upload/UploadHistoryTable";
import { UploadStatusCard } from "@/features/upload/UploadStatusCard";
import type { DocumentResponse } from "@/types/api";

export function UploadPage() {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedDocument, setUploadedDocument] = useState<DocumentResponse | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      uploadDocument({
        file,
        params: {
          chunk_size: 1200,
          chunk_overlap: 200,
          use_rag: true,
        },
        onUploadProgress: setUploadProgress,
      }),
    onMutate: () => {
      setUploadProgress(0);
      setUploadedDocument(null);
    },
    onSuccess: (document) => {
      setUploadedDocument(document);
      setUploadProgress(100);
      void queryClient.invalidateQueries({ queryKey: queryKeys.reports.list({ is_latest: true }) });
    },
  });

  const reportsQuery = useQuery({
    queryKey: queryKeys.reports.list({ is_latest: true }),
    queryFn: () => listGovernanceReports({ is_latest: true }),
    refetchInterval: uploadedDocument ? 4_000 : false,
  });

  const workflowQuery = useQuery({
    queryKey: uploadedDocument
      ? queryKeys.workflow.job(uploadedDocument.id)
      : ["workflow", "job", "none"],
    queryFn: () => getWorkflowJob(uploadedDocument!.id).catch(() => null),
    enabled: Boolean(uploadedDocument),
    refetchInterval: uploadedDocument ? 3_000 : false,
  });

  const generatedReport = useMemo(() => {
    if (!uploadedDocument || !reportsQuery.data) {
      return undefined;
    }
    return reportsQuery.data.find((report) => report.document_id === uploadedDocument.id);
  }, [reportsQuery.data, uploadedDocument]);

  const handleUpload = () => {
    if (!selectedFile) {
      return;
    }
    uploadMutation.mutate(selectedFile);
  };

  return (
    <>
      <PageHeader
        eyebrow="Document ingestion"
        title="Upload Center"
        description="Upload governance documents, track backend processing, and open generated intelligence reports."
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Upload Document</CardTitle>
              <CardDescription>
                Supported by the current backend contract: PDF, DOC, DOCX, and TXT.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <DragAndDropUpload
                file={selectedFile}
                disabled={uploadMutation.isPending}
                onFileSelected={setSelectedFile}
              />
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-slate-500">
                  Processing uses the existing FastAPI upload endpoint and background workflow.
                </p>
                <Button disabled={!selectedFile || uploadMutation.isPending} onClick={handleUpload}>
                  {uploadMutation.isPending ? "Uploading..." : "Upload and process"}
                </Button>
              </div>
            </CardContent>
          </Card>

          <UploadStatusCard
            file={selectedFile}
            document={uploadedDocument}
            progress={uploadProgress}
            isUploading={uploadMutation.isPending}
            error={uploadMutation.error}
            generatedReport={generatedReport}
          />

          <ProcessingTracker
            document={uploadedDocument}
            workflowJob={workflowQuery.data}
            generatedReport={generatedReport}
            isPolling={Boolean(uploadedDocument && !generatedReport)}
          />
        </div>

        <div className="space-y-6">
          <JobStatusTimeline
            document={uploadedDocument}
            workflowJob={workflowQuery.data}
            generatedReport={generatedReport}
          />
          {generatedReport ? (
            <Card className="border-emerald-200 bg-emerald-50">
              <CardContent className="p-5">
                <h3 className="font-semibold text-emerald-950">Governance report ready</h3>
                <p className="mt-2 text-sm text-emerald-700">
                  Open the generated report to review RAID items and escalations.
                </p>
                <Button asChild className="mt-4">
                  <Link to={`/reports/${generatedReport.id}`}>Open generated report</Link>
                </Button>
              </CardContent>
            </Card>
          ) : null}
        </div>
      </div>

      <div className="mt-6">
        <UploadHistoryTable
          reports={reportsQuery.data ?? []}
          isLoading={reportsQuery.isLoading}
          error={reportsQuery.error}
          onRetry={() => void reportsQuery.refetch()}
        />
      </div>
    </>
  );
}
