import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Shield, User, AlertOctagon, Check, X, UserCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRole } from "@/lib/context/RoleContext";
import { assignGovernanceReport, escalateGovernanceReport } from "@/lib/api/reports";
import { reviewGovernanceReport } from "@/lib/api/review";
import { queryKeys } from "@/lib/api/queryKeys";
import type { GovernanceReportResponse } from "@/types/api";

type GovernanceWorkflowPanelProps = {
  report: GovernanceReportResponse;
};

export function GovernanceWorkflowPanel({ report }: GovernanceWorkflowPanelProps) {
  const queryClient = useQueryClient();
  const { role, isManager } = useRole();
  const [assignee, setAssignee] = useState(report.assigned_to || "");
  const [reviewNotes, setReviewNotes] = useState("");

  const assignMutation = useMutation({
    mutationFn: () => assignGovernanceReport(report.id, assignee.trim()),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.reports.detail(String(report.id)) });
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
    },
  });

  const escalateMutation = useMutation({
    mutationFn: () => escalateGovernanceReport(report.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.reports.detail(String(report.id)) });
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
      void queryClient.invalidateQueries({ queryKey: ["escalations"] });
    },
  });

  const reviewMutation = useMutation({
    mutationFn: (status: "approved" | "changes_requested") =>
      reviewGovernanceReport(report.id, {
        reviewer: `manager_user (${role})`,
        review_status: status,
        review_notes: reviewNotes.trim() || null,
      }),
    onSuccess: () => {
      setReviewNotes("");
      void queryClient.invalidateQueries({ queryKey: queryKeys.reports.detail(String(report.id)) });
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["audit-events"] });
    },
  });

  const isPendingReview = report.status === "PENDING_MANAGER_REVIEW";

  return (
    <Card className="border-l-4 border-l-blue-600 bg-slate-900 text-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg text-white">
          <Shield className="h-5 w-5 text-blue-400" />
          Governance & Workflow
        </CardTitle>
        <CardDescription className="text-slate-400">
          Track workflow ownership, status lifecycle, and execute role-based approvals.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Ownership & Status Grid */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-lg bg-slate-800 p-3">
            <span className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Workflow Status
            </span>
            <span className="mt-1 block font-bold text-blue-300">{report.status}</span>
          </div>
          <div className="rounded-lg bg-slate-800 p-3">
            <span className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Assigned To
            </span>
            <span className="mt-1 block font-bold text-slate-100">{report.assigned_to || "None"}</span>
          </div>
          <div className="rounded-lg bg-slate-800 p-3">
            <span className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Created By
            </span>
            <span className="mt-1 block text-slate-300">{report.created_by || "Analyst"}</span>
          </div>
          <div className="rounded-lg bg-slate-800 p-3">
            <span className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Approved By
            </span>
            <span className="mt-1 block text-slate-300">{report.approved_by || "Unapproved"}</span>
          </div>
        </div>

        {/* Manager Actions Section */}
        {isManager ? (
          <div className="mt-4 border-t border-slate-800 pt-4 space-y-4">
            <h4 className="text-sm font-semibold text-slate-200">Manager Decisions & Actions</h4>
            
            {/* Assignee modification */}
            <div className="space-y-2">
              <label className="text-xs text-slate-400 block" htmlFor="workflow-assignee">
                Modify Assignee
              </label>
              <div className="flex gap-2">
                <input
                  id="workflow-assignee"
                  type="text"
                  value={assignee}
                  onChange={(e) => setAssignee(e.target.value)}
                  placeholder="Enter assignee role or name"
                  className="h-9 flex-1 rounded-md border border-slate-700 bg-slate-800 px-3 text-sm text-white outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
                <Button
                  size="sm"
                  onClick={() => assignMutation.mutate()}
                  disabled={assignMutation.isPending || !assignee.trim()}
                  className="bg-blue-600 hover:bg-blue-700 text-white h-9"
                >
                  <UserCheck className="mr-1 h-4 w-4" />
                  Assign
                </Button>
              </div>
              {assignMutation.error && (
                <p className="text-xs text-red-400">
                  {assignMutation.error instanceof Error ? assignMutation.error.message : "Assignment failed"}
                </p>
              )}
            </div>

            {/* Approval & Changes notes */}
            {isPendingReview && (
              <div className="space-y-3 pt-2">
                <div className="space-y-1">
                  <label className="text-xs text-slate-400 block" htmlFor="workflow-review-notes">
                    Decision / Review Notes
                  </label>
                  <textarea
                    id="workflow-review-notes"
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    placeholder="Provide justification or change requirements..."
                    rows={2}
                    className="w-full rounded-md border border-slate-700 bg-slate-800 p-2 text-sm text-white outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <Button
                    onClick={() => reviewMutation.mutate("approved")}
                    disabled={reviewMutation.isPending}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium"
                  >
                    <Check className="mr-1.5 h-4 w-4" />
                    Approve Report
                  </Button>
                  <Button
                    variant="default"
                    onClick={() => reviewMutation.mutate("changes_requested")}
                    disabled={reviewMutation.isPending}
                    className="bg-red-600 hover:bg-red-700 text-white font-medium"
                  >
                    <X className="mr-1.5 h-4 w-4" />
                    Request Changes
                  </Button>
                </div>
                {reviewMutation.error && (
                  <p className="text-xs text-red-400">
                    {reviewMutation.error instanceof Error ? reviewMutation.error.message : "Review submission failed"}
                  </p>
                )}
              </div>
            )}

            {/* Escalate Report */}
            {isPendingReview && (
              <div className="pt-2 border-t border-slate-800/50">
                <Button
                  onClick={() => escalateMutation.mutate()}
                  disabled={escalateMutation.isPending}
                  className="w-full bg-amber-600 hover:bg-amber-700 text-white font-medium"
                >
                  <AlertOctagon className="mr-1.5 h-4 w-4" />
                  Escalate Report
                </Button>
                {escalateMutation.error && (
                  <p className="text-xs text-red-400">
                    {escalateMutation.error instanceof Error ? escalateMutation.error.message : "Escalation failed"}
                  </p>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="mt-4 border-t border-slate-800 pt-4 text-center">
            <p className="text-xs text-slate-400 bg-slate-800 rounded-md p-3">
              <User className="h-4 w-4 inline mr-1 text-slate-400" />
              Viewing as <span className="font-semibold text-slate-200">{role}</span>.
              <br />
              Only <span className="text-blue-300">Managers</span> can perform workflow reviews, approvals, assignments, or escalations.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
