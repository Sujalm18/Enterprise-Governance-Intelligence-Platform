import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, RotateCcw, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { reviewGovernanceReport } from "@/lib/api/review";
import { queryKeys } from "@/lib/api/queryKeys";
import { useRole } from "@/lib/context/RoleContext";
import type { ReportReviewRequest } from "@/types/api";

type ReviewFormProps = {
  reportId: number;
};

export function ReviewForm({ reportId }: ReviewFormProps) {
  const { role, isManager } = useRole();
  const queryClient = useQueryClient();
  const [reviewer, setReviewer] = useState("manager_user");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewStatus, setReviewStatus] =
    useState<ReportReviewRequest["review_status"]>("approved");

  const reviewMutation = useMutation({
    mutationFn: () =>
      reviewGovernanceReport(reportId, {
        reviewer: reviewer.trim(),
        review_status: reviewStatus,
        review_notes: reviewNotes.trim() || null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.reports.pendingReview });
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
    },
  });

  const canSubmit = isManager && reviewer.trim().length > 0 && !reviewMutation.isPending;

  return (
    <div className="w-full max-w-xl rounded-md border border-slate-200 bg-slate-50 p-4">
      {!isManager ? (
        <div className="mb-4 flex items-start gap-2.5 rounded-md bg-amber-50 p-3 text-xs text-amber-800 border border-amber-200">
          <ShieldAlert className="h-4 w-4 mt-0.5 text-amber-600 flex-shrink-0" />
          <div>
            <span className="font-semibold">Review Disabled:</span> You are viewing as <span className="font-bold">{role}</span>. Only Managers can review reports.
          </div>
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
        <label className="block">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Reviewer
          </span>
          <input
            value={reviewer}
            onChange={(event) => setReviewer(event.target.value)}
            disabled={!isManager}
            className="mt-1 h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-100 disabled:text-slate-500"
          />
        </label>

        <label className="block">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Decision
          </span>
          <select
            value={reviewStatus}
            onChange={(event) =>
              setReviewStatus(event.target.value as ReportReviewRequest["review_status"])
            }
            disabled={!isManager}
            className="mt-1 h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm disabled:bg-slate-100 disabled:text-slate-500"
          >
            <option value="approved">Approve</option>
            <option value="changes_requested">Request changes</option>
          </select>
        </label>
      </div>

      <label className="mt-3 block">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Review Notes
        </span>
        <textarea
          value={reviewNotes}
          onChange={(event) => setReviewNotes(event.target.value)}
          rows={3}
          disabled={!isManager}
          className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-100 disabled:text-slate-500"
          placeholder="Add reviewer notes for audit traceability..."
        />
      </label>

      {reviewMutation.error ? (
        <p className="mt-3 text-sm text-red-700">
          {reviewMutation.error instanceof Error
            ? reviewMutation.error.message
            : "Review submission failed."}
        </p>
      ) : null}

      {reviewMutation.isSuccess ? (
        <p className="mt-3 text-sm text-emerald-700">Review submitted successfully.</p>
      ) : null}

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-end">
        <Button
          variant="outline"
          disabled={!isManager || reviewMutation.isPending}
          onClick={() => {
            setReviewNotes("");
            setReviewStatus("approved");
          }}
        >
          <RotateCcw className="mr-2 h-4 w-4" aria-hidden="true" />
          Reset
        </Button>
        <Button disabled={!canSubmit} onClick={() => reviewMutation.mutate()}>
          <CheckCircle2 className="mr-2 h-4 w-4" aria-hidden="true" />
          {reviewMutation.isPending ? "Submitting..." : "Submit review"}
        </Button>
      </div>
    </div>
  );
}
