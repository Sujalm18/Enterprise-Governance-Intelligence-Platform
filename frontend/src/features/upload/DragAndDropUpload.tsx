import { useRef, useState } from "react";
import { FileText, UploadCloud, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type DragAndDropUploadProps = {
  file: File | null;
  disabled?: boolean;
  onFileSelected: (file: File | null) => void;
};

const ACCEPTED_EXTENSIONS = ".pdf,.doc,.docx,.txt";

export function DragAndDropUpload({
  file,
  disabled = false,
  onFileSelected,
}: DragAndDropUploadProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (files: FileList | null) => {
    const nextFile = files?.[0] ?? null;
    if (nextFile) {
      onFileSelected(nextFile);
    }
  };

  return (
    <div
      className={cn(
        "rounded-lg border border-dashed p-8 text-center transition",
        isDragging ? "border-blue-500 bg-blue-50" : "border-slate-300 bg-slate-50",
        disabled && "cursor-not-allowed opacity-60",
      )}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) {
          setIsDragging(true);
        }
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        if (!disabled) {
          handleFiles(event.dataTransfer.files);
        }
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        className="hidden"
        disabled={disabled}
        onChange={(event) => handleFiles(event.target.files)}
      />

      {file ? (
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100">
            <FileText className="h-6 w-6 text-blue-700" aria-hidden="true" />
          </div>
          <div>
            <p className="font-medium text-slate-950">{file.name}</p>
            <p className="mt-1 text-sm text-slate-500">{formatFileSize(file.size)}</p>
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={disabled}
              onClick={() => inputRef.current?.click()}
            >
              Replace
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={disabled}
              onClick={() => onFileSelected(null)}
            >
              <X className="mr-2 h-4 w-4" aria-hidden="true" />
              Clear
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100">
            <UploadCloud className="h-6 w-6 text-blue-700" aria-hidden="true" />
          </div>
          <div>
            <p className="font-medium text-slate-950">Drag and drop a governance document</p>
            <p className="mt-1 text-sm text-slate-500">PDF, DOC, DOCX, or TXT</p>
          </div>
          <Button type="button" variant="outline" disabled={disabled} onClick={() => inputRef.current?.click()}>
            Browse files
          </Button>
        </div>
      )}
    </div>
  );
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} bytes`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
