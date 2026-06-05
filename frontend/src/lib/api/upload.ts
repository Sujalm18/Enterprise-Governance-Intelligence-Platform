import { endpoints } from "@/lib/api/endpoints";
import { request } from "@/lib/api/client";
import type { DocumentResponse, UploadDocumentParams } from "@/types/api";

export type UploadDocumentInput = {
  file: File;
  params?: UploadDocumentParams;
  onUploadProgress?: (progressPercent: number) => void;
};

export function uploadDocument({
  file,
  params,
  onUploadProgress,
}: UploadDocumentInput): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return request<DocumentResponse>({
    method: "POST",
    url: endpoints.upload,
    data: formData,
    params,
    timeout: 120_000,
    onUploadProgress: (event) => {
      if (!onUploadProgress || !event.total) {
        return;
      }
      onUploadProgress(Math.round((event.loaded * 100) / event.total));
    },
  });
}
