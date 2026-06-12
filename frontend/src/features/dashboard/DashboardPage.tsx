import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Clock,
  ShieldAlert,
  CheckCircle,
  UserCheck,
  ArrowRight,
  TrendingDown,
  User,
  Check,
  RotateCcw,
  Activity,
  Bell,
  RefreshCw,
  Sliders,
  Shield,
  AlertTriangle,
  ChevronRight,
  CheckSquare,
  FileText,
  Sparkles,
  Info,
  Download,
  Settings,
  Siren
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getDashboardCharts, getDashboardStats } from "@/lib/api/dashboard";
import { getAuditEvents } from "@/lib/api/audit";
import { listGovernanceReports, assignGovernanceReport, escalateGovernanceReport } from "@/lib/api/reports";
import { listEscalations, assignEscalation, routeEscalation, resolveEscalation, closeEscalation } from "@/lib/api/escalations";
import { listMitigations, updateMitigation, verifyMitigation, reopenMitigation } from "@/lib/api/mitigations";
import { listNotifications, readNotification, readAllNotifications, getInbox, generateDemoData } from "@/lib/api/notifications";
import { reviewGovernanceReport } from "@/lib/api/review";
import { queryKeys } from "@/lib/api/queryKeys";
import { useRole } from "@/lib/context/RoleContext";
import { GovernanceOverview } from "@/features/dashboard/GovernanceOverview";
import { ProcessingMetrics } from "@/features/dashboard/ProcessingMetrics";
import { Timeline } from "@/components/ui/Timeline";
import { Link } from "react-router-dom";
import { apiClient } from "@/lib/api/client";

export function DashboardPage() {
  const { role } = useRole();
  const queryClient = useQueryClient();

  // Selected states for inline forms
  const [activeTab, setActiveTab] = useState<"reviews" | "escalations" | "mitigations" | "verifications">("reviews");
  const [reviewNotes, setReviewNotes] = useState<Record<number, string>>({});
  const [reportAssignee, setReportAssignee] = useState<Record<number, string>>({});
  const [escAssignee, setEscAssignee] = useState<Record<number, string>>({});
  const [escRoute, setEscRoute] = useState<Record<number, string>>({});
  const [mitProgress, setMitProgress] = useState<Record<number, number>>({});
  const [mitAssignee, setMitAssignee] = useState<Record<number, string>>({});
  
  // Demo Mode State
  const [demoSize, setDemoSize] = useState<"small" | "medium" | "enterprise">("medium");
  const [isSeeding, setIsSeeding] = useState(false);
  const [seedSuccess, setSeedSuccess] = useState(false);

  // Loading states for actions
  const [isActionLoading, setIsActionLoading] = useState<Record<string, boolean>>({});

  // Webhooks & Export State
  const [slackWebhook, setSlackWebhook] = useState("");
  const [teamsWebhook, setTeamsWebhook] = useState("");
  const [isSavingWebhooks, setIsSavingWebhooks] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isExportingExcel, setIsExportingExcel] = useState(false);
  const [isExportingCsv, setIsExportingCsv] = useState(false);


  // Queries
  const statsQuery = useQuery({
    queryKey: queryKeys.dashboard.stats,
    queryFn: getDashboardStats,
    refetchInterval: 12_000,
  });

  const chartsQuery = useQuery({
    queryKey: queryKeys.dashboard.charts,
    queryFn: getDashboardCharts,
    refetchInterval: 12_000,
  });

  const auditQuery = useQuery({
    queryKey: ["audit-events"],
    queryFn: getAuditEvents,
    refetchInterval: 12_000,
  });

  const reportsQuery = useQuery({
    queryKey: ["reports", "all-latest"],
    queryFn: () => listGovernanceReports({ is_latest: true }),
  });

  const escalationsQuery = useQuery({
    queryKey: ["escalations", "all"],
    queryFn: () => listEscalations(),
  });

  const mitigationsQuery = useQuery({
    queryKey: ["mitigations", "all"],
    queryFn: () => listMitigations({}),
  });

  const notificationsQuery = useQuery({
    queryKey: ["notifications", role],
    queryFn: listNotifications,
    refetchInterval: 10_000,
  });

  const inboxQuery = useQuery({
    queryKey: ["inbox", role],
    queryFn: getInbox,
    refetchInterval: 10_000,
  });

  const isLoading =
    statsQuery.isLoading ||
    chartsQuery.isLoading ||
    auditQuery.isLoading ||
    reportsQuery.isLoading ||
    escalationsQuery.isLoading ||
    mitigationsQuery.isLoading ||
    notificationsQuery.isLoading ||
    inboxQuery.isLoading;

  const error =
    statsQuery.error ??
    chartsQuery.error ??
    auditQuery.error ??
    reportsQuery.error ??
    escalationsQuery.error ??
    mitigationsQuery.error ??
    notificationsQuery.error ??
    inboxQuery.error;

  // Sync sliders with fetched progress values
  useEffect(() => {
    if (inboxQuery.data?.assigned_mitigations) {
      const initialProgress: Record<number, number> = {};
      inboxQuery.data.assigned_mitigations.forEach((task) => {
        initialProgress[task.id] = task.completion_percentage;
      });
      setMitProgress((prev) => ({ ...initialProgress, ...prev }));
    }
  }, [inboxQuery.data?.assigned_mitigations]);

  // Actions
  const handleApproveReport = async (reportId: number) => {
    const actionId = `report-approve-${reportId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await reviewGovernanceReport(reportId, {
        reviewer: role,
        review_status: "approved",
        review_notes: reviewNotes[reportId] || "Approved via inline Operations Cockpit",
      });
      setReviewNotes((prev) => ({ ...prev, [reportId]: "" }));
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to approve report", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleRequestChanges = async (reportId: number) => {
    const actionId = `report-changes-${reportId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await reviewGovernanceReport(reportId, {
        reviewer: role,
        review_status: "changes_requested",
        review_notes: reviewNotes[reportId] || "Changes requested via inline Operations Cockpit",
      });
      setReviewNotes((prev) => ({ ...prev, [reportId]: "" }));
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to request changes", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleEscalateReport = async (reportId: number) => {
    const actionId = `report-escalate-${reportId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await escalateGovernanceReport(reportId);
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to escalate report", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleAssignReport = async (reportId: number, targetRole: string) => {
    if (!targetRole) return;
    const actionId = `report-assign-${reportId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await assignGovernanceReport(reportId, targetRole);
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to assign report", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleAssignEscalation = async (escId: number, targetRole: string) => {
    if (!targetRole) return;
    const actionId = `esc-assign-${escId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await assignEscalation(escId, targetRole);
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to assign escalation", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleRouteEscalation = async (escId: number, routingTarget: string) => {
    if (!routingTarget) return;
    const actionId = `esc-route-${escId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await routeEscalation(escId, { routing_target: routingTarget });
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to route escalation", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleResolveEscalation = async (escId: number) => {
    const actionId = `esc-resolve-${escId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await resolveEscalation(escId);
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to resolve escalation", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleCloseEscalation = async (escId: number) => {
    const actionId = `esc-close-${escId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await closeEscalation(escId);
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to close escalation", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleUpdateMitigationProgress = async (taskId: number) => {
    const progress = mitProgress[taskId] !== undefined ? mitProgress[taskId] : 0;
    const actionId = `mit-progress-${taskId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await updateMitigation(taskId, {
        completion_percentage: progress,
        status: progress === 100 ? "COMPLETED" : "IN_PROGRESS",
      });
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to update progress", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleCompleteMitigation = async (taskId: number) => {
    const actionId = `mit-complete-${taskId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await updateMitigation(taskId, {
        completion_percentage: 100,
        status: "COMPLETED",
      });
      setMitProgress((prev) => ({ ...prev, [taskId]: 100 }));
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to complete task", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleReassignMitigation = async (taskId: number, targetRole: string) => {
    if (!targetRole) return;
    const actionId = `mit-assign-${taskId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await updateMitigation(taskId, { owner_role: targetRole });
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to reassign task", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleVerifyMitigation = async (taskId: number) => {
    const actionId = `mit-verify-${taskId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await verifyMitigation(taskId);
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to verify task", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleReopenMitigation = async (taskId: number) => {
    const actionId = `mit-reopen-${taskId}`;
    setIsActionLoading((prev) => ({ ...prev, [actionId]: true }));
    try {
      await reopenMitigation(taskId);
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to reopen task", err);
    } finally {
      setIsActionLoading((prev) => ({ ...prev, [actionId]: false }));
    }
  };

  const handleReadNotification = async (nId: number) => {
    try {
      await readNotification(nId);
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to dismiss notification", err);
    }
  };

  const handleReadAll = async () => {
    try {
      await readAllNotifications();
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error("Failed to mark all as read", err);
    }
  };

  const handleGenerateDemo = async () => {
    setIsSeeding(true);
    setSeedSuccess(false);
    try {
      await generateDemoData(demoSize);
      await queryClient.invalidateQueries();
      setSeedSuccess(true);
      setTimeout(() => setSeedSuccess(false), 4000);
    } catch (err) {
      console.error("Failed to seed demo data", err);
    } finally {
      setIsSeeding(false);
    }
  };

  useEffect(() => {
    async function fetchWebhooks() {
      try {
        const res = await apiClient.get("/api/governance/integrations");
        setSlackWebhook(res.data.slack_webhook_url || "");
        setTeamsWebhook(res.data.teams_webhook_url || "");
      } catch (err) {
        console.error("Failed to fetch integration settings", err);
      }
    }
    fetchWebhooks();
  }, []);

  const handleSaveIntegrations = async () => {
    setIsSavingWebhooks(true);
    setSaveSuccess(false);
    try {
      await apiClient.post("/api/governance/integrations", {
        slack_webhook_url: slackWebhook,
        teams_webhook_url: teamsWebhook,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save integration settings", err);
    } finally {
      setIsSavingWebhooks(false);
    }
  };

  const handleExportCsv = async () => {
    setIsExportingCsv(true);
    try {
      const response = await apiClient.get("/api/governance/export/csv", {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "governance_risk_register.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Failed to export CSV", err);
    } finally {
      setIsExportingCsv(false);
    }
  };

  const handleExportExcel = async () => {
    setIsExportingExcel(true);
    try {
      const response = await apiClient.get("/api/governance/export/xlsx", {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "governance_risk_register.xlsx");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Failed to export Excel", err);
    } finally {
      setIsExportingExcel(false);
    }
  };


  // Filter collections client-side for lists
  const allReports = reportsQuery.data ?? [];
  const allEscalations = escalationsQuery.data ?? [];
  const allMitigations = mitigationsQuery.data ?? [];
  const allNotifications = notificationsQuery.data ?? [];
  
  const unreadNotifications = allNotifications.filter((n) => !n.read_status);

  const pendingInboxReviews = inboxQuery.data?.pending_reviews ?? [];
  const assignedInboxEscalations = inboxQuery.data?.assigned_escalations ?? [];
  const assignedInboxMitigations = inboxQuery.data?.assigned_mitigations ?? [];
  const pendingInboxVerifications = inboxQuery.data?.pending_verifications ?? [];

  const allRaidItems = allReports.flatMap((r) => r.raid_items || []);
  const criticalRaidItems = allRaidItems.filter(
    (item) => (item.severity === "critical" || item.severity === "high") && (item.risk_score && item.risk_score > 60)
  ).slice(0, 5);

  const overdueMitigations = allMitigations.filter(
    (t) => t.status !== "COMPLETED" && t.status !== "VERIFIED" && t.sla_status === "OVERDUE"
  );

  const openEscalations = allEscalations.filter(
    (e) => e.status !== "RESOLVED" && e.status !== "CLOSED" && e.status !== "resolved" && e.status !== "closed"
  );

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <PageHeader
          eyebrow="Cockpit Workspace"
          title="Governance Operations Center"
          description={`Unified operations cockpit & real-time governance response queue.`}
        />
        
        {/* Enterprise Demo Mode Seeder Dropdown */}
        <div className="flex items-center gap-2.5 bg-white border border-slate-200/80 rounded-xl px-4 py-2.5 shadow-sm">
          <Sparkles className="h-4.5 w-4.5 text-blue-500 animate-pulse" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Demo Environment</span>
            <div className="flex items-center gap-2 mt-0.5">
              <select
                value={demoSize}
                onChange={(e) => setDemoSize(e.target.value as any)}
                className="bg-transparent text-xs font-semibold text-slate-700 focus:outline-none border-b border-slate-200 pb-0.5 cursor-pointer"
              >
                <option value="small">Small Dataset</option>
                <option value="medium">Medium Enterprise</option>
                <option value="enterprise">Global Enterprise</option>
              </select>
              <Button
                size="sm"
                variant="outline"
                onClick={handleGenerateDemo}
                disabled={isSeeding}
                className="h-7 px-2.5 text-xs text-blue-600 hover:text-blue-800 border-blue-200 bg-blue-50/50 hover:bg-blue-100/60 font-semibold gap-1.5 flex items-center transition-all"
              >
                <RefreshCw className={`h-3 w-3 ${isSeeding ? "animate-spin" : ""}`} />
                {isSeeding ? "Seeding..." : "Seed"}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {seedSuccess && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 px-4 py-3 rounded-xl flex items-center gap-2.5 text-xs font-semibold animate-fade-in">
          <CheckCircle className="h-4.5 w-4.5 text-emerald-600" />
          <span>Demo environment successfully wiped and seeded with {demoSize} dataset! Refreshing cockpit...</span>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-5">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-28 animate-pulse rounded-xl bg-slate-100 border border-slate-200" />
            ))}
          </div>
          <div className="h-96 animate-pulse rounded-xl bg-slate-100 border border-slate-200" />
        </div>
      ) : error ? (
        <Card className="border-red-200 bg-red-50/40">
          <CardContent className="p-6 text-center space-y-3">
            <AlertCircle className="mx-auto h-10 w-10 text-red-500" />
            <h3 className="text-base font-bold text-red-950">Operations Center Unavailable</h3>
            <p className="text-xs text-red-700 max-w-md mx-auto">
              {error instanceof Error ? error.message : "An error occurred while establishing connection to the governance engine."}
            </p>
            <Button
              variant="outline"
              className="mt-2 text-xs border-red-200 hover:bg-red-100/50 text-red-700"
              onClick={() => {
                void statsQuery.refetch();
                void chartsQuery.refetch();
                void auditQuery.refetch();
                void reportsQuery.refetch();
                void escalationsQuery.refetch();
                void mitigationsQuery.refetch();
                void notificationsQuery.refetch();
                void inboxQuery.refetch();
              }}
            >
              Retry Connection
            </Button>
          </CardContent>
        </Card>
      ) : statsQuery.data && chartsQuery.data ? (
        <div className="space-y-6">
          {/* Operations Cockpit Metrics Bar */}
          <section className="grid gap-4 grid-cols-2 md:grid-cols-5" aria-label="Operations metrics">
            {/* Health Score Gauge */}
            <Card className="bg-white border-slate-200/80 shadow-sm relative overflow-hidden flex flex-col justify-between p-4 col-span-2 md:col-span-1">
              <div className="flex justify-between items-start">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Governance Health</span>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                  statsQuery.data.governance_health_score >= 85
                    ? "bg-emerald-50 text-emerald-600 border border-emerald-100"
                    : statsQuery.data.governance_health_score >= 70
                    ? "bg-amber-50 text-amber-600 border border-amber-100"
                    : "bg-red-50 text-red-600 border border-red-100"
                }`}>
                  {statsQuery.data.governance_health_score >= 85 ? "Stable" : statsQuery.data.governance_health_score >= 70 ? "Warning" : "Critical"}
                </span>
              </div>
              <div className="flex items-center gap-3 my-2.5">
                <div className="relative flex items-center justify-center h-12 w-12">
                  <svg className="h-12 w-12 transform -rotate-90">
                    <circle cx="24" cy="24" r="20" className="stroke-slate-100" strokeWidth="4" fill="transparent" />
                    <circle
                      cx="24"
                      cy="24"
                      r="20"
                      className={`${
                        statsQuery.data.governance_health_score >= 85
                          ? "stroke-emerald-500"
                          : statsQuery.data.governance_health_score >= 70
                          ? "stroke-amber-500"
                          : "stroke-red-500"
                      } transition-all duration-500`}
                      strokeWidth="4"
                      fill="transparent"
                      strokeDasharray={2 * Math.PI * 20}
                      strokeDashoffset={2 * Math.PI * 20 - (statsQuery.data.governance_health_score / 100) * 2 * Math.PI * 20}
                      strokeLinecap="round"
                    />
                  </svg>
                  <span className="absolute text-sm font-black text-slate-800">{statsQuery.data.governance_health_score}</span>
                </div>
                <div>
                  <span className="block text-xl font-extrabold text-slate-800 leading-tight">Index</span>
                  <span className="text-[9px] text-slate-500 font-semibold uppercase">Compliance Score</span>
                </div>
              </div>
              <span className="text-[10px] text-slate-400">Deductions based on active risks</span>
            </Card>

            {/* Risk Mitigation Original vs Residual */}
            <Card className="bg-white border-slate-200/80 shadow-sm relative overflow-hidden flex flex-col justify-between p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Risk Mitigation</span>
              <div className="my-2.5 space-y-1">
                <div className="flex justify-between items-baseline">
                  <span className="text-[10px] text-slate-500">Original vs Current</span>
                  <span className="text-xs font-bold text-slate-700">
                    {statsQuery.data.total_original_risk} → <span className="text-emerald-600 font-extrabold">{statsQuery.data.total_current_risk}</span>
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100 flex">
                  <div
                    className="h-full bg-emerald-500 rounded-full"
                    style={{ width: `${statsQuery.data.risk_reduction_percentage}%` }}
                  />
                </div>
              </div>
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-slate-400">Total reduction</span>
                <span className="text-emerald-600 font-bold flex items-center gap-0.5">
                  <TrendingDown className="h-3 w-3" /> -{statsQuery.data.risk_reduction_percentage}%
                </span>
              </div>
            </Card>

            {/* Overdue Mitigations SLA Alert */}
            <Card className="bg-white border-slate-200/80 shadow-sm relative overflow-hidden flex flex-col justify-between p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Overdue Mitigations</span>
              <div className="flex items-baseline gap-1 my-2">
                <span className={`text-3xl font-black ${statsQuery.data.overdue_mitigations_count > 0 ? "text-red-600 animate-pulse" : "text-slate-800"}`}>
                  {statsQuery.data.overdue_mitigations_count}
                </span>
                <span className="text-xs text-slate-500 font-semibold">items overdue</span>
              </div>
              <div className="flex justify-between items-center text-[10px] text-slate-400">
                <span>SLA Breaches</span>
                <span className={`font-bold ${statsQuery.data.sla_breaches_count > 0 ? "text-red-500" : "text-emerald-600"}`}>
                  {statsQuery.data.sla_breaches_count} Critical
                </span>
              </div>
            </Card>

            {/* Unread Notifications Alert Badge */}
            <Card className="bg-white border-slate-200/80 shadow-sm relative overflow-hidden flex flex-col justify-between p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Unread Alerts</span>
              <div className="flex items-baseline gap-1 my-2">
                <span className={`text-3xl font-black ${unreadNotifications.length > 0 ? "text-amber-500" : "text-slate-800"}`}>
                  {unreadNotifications.length}
                </span>
                <span className="text-xs text-slate-500 font-semibold">new notifications</span>
              </div>
              <div className="flex justify-between items-center text-[10px] text-slate-400">
                <span>Active role alerts</span>
                <span className="text-slate-500 font-bold">{role}</span>
              </div>
            </Card>

            {/* Pending Governance Approvals */}
            <Card className="bg-white border-slate-200/80 shadow-sm relative overflow-hidden flex flex-col justify-between p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Pending Approvals</span>
              <div className="flex items-baseline gap-1 my-2">
                <span className="text-3xl font-black text-slate-800">
                  {statsQuery.data.pending_governance_approvals + statsQuery.data.pending_reviews}
                </span>
                <span className="text-xs text-slate-500 font-semibold">docs review</span>
              </div>
              <div className="flex justify-between items-center text-[10px] text-slate-400">
                <span>Awaiting Sign-off</span>
                <span className="text-blue-600 font-bold">{statsQuery.data.pending_governance_approvals} Lead</span>
              </div>
            </Card>
          </section>

          {/* Tabbed Workspace: "My Work" Cockpit */}
          <Card className="border-slate-200 bg-white shadow-sm overflow-hidden">
            <CardHeader className="bg-slate-50 border-b border-slate-200/80 p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="space-y-0.5">
                <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <Sliders className="h-5 w-5 text-blue-500" />
                  My Work Queue
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Actionable work items assigned to your active role switch context: <span className="font-bold text-blue-600">{role}</span>
                </CardDescription>
              </div>

              {/* Tab Selector buttons */}
              <div className="flex flex-wrap gap-1 bg-slate-200/60 p-1 rounded-xl">
                <button
                  onClick={() => setActiveTab("reviews")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                    activeTab === "reviews"
                      ? "bg-white text-blue-600 shadow-sm"
                      : "text-slate-600 hover:text-slate-800 hover:bg-slate-100/50"
                  }`}
                >
                  Pending Reviews
                  <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-bold ${
                    activeTab === "reviews" ? "bg-blue-100 text-blue-700" : "bg-slate-300/60 text-slate-600"
                  }`}>
                    {pendingInboxReviews.length}
                  </span>
                </button>

                <button
                  onClick={() => setActiveTab("escalations")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                    activeTab === "escalations"
                      ? "bg-white text-blue-600 shadow-sm"
                      : "text-slate-600 hover:text-slate-800 hover:bg-slate-100/50"
                  }`}
                >
                  Assigned Escalations
                  <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-bold ${
                    activeTab === "escalations" ? "bg-blue-100 text-blue-700" : "bg-slate-300/60 text-slate-600"
                  }`}>
                    {assignedInboxEscalations.length}
                  </span>
                </button>

                <button
                  onClick={() => setActiveTab("mitigations")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                    activeTab === "mitigations"
                      ? "bg-white text-blue-600 shadow-sm"
                      : "text-slate-600 hover:text-slate-800 hover:bg-slate-100/50"
                  }`}
                >
                  Assigned Mitigations
                  <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-bold ${
                    activeTab === "mitigations" ? "bg-blue-100 text-blue-700" : "bg-slate-300/60 text-slate-600"
                  }`}>
                    {assignedInboxMitigations.length}
                  </span>
                </button>

                <button
                  onClick={() => setActiveTab("verifications")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                    activeTab === "verifications"
                      ? "bg-white text-blue-600 shadow-sm"
                      : "text-slate-600 hover:text-slate-800 hover:bg-slate-100/50"
                  }`}
                >
                  Pending Verifications
                  <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-bold ${
                    activeTab === "verifications" ? "bg-blue-100 text-blue-700" : "bg-slate-300/60 text-slate-600"
                  }`}>
                    {pendingInboxVerifications.length}
                  </span>
                </button>
              </div>
            </CardHeader>

            <CardContent className="p-5">
              {/* Reviews Tab */}
              {activeTab === "reviews" && (
                <div className="space-y-4">
                  {pendingInboxReviews.length === 0 ? (
                    <div className="py-8 text-center text-xs text-slate-450 italic space-y-1">
                      <CheckCircle className="h-7 w-7 text-emerald-500/20 mx-auto mb-1" />
                      <p>All governance reports are reviewed and clean.</p>
                      <p className="text-[10px]">No pending reviews assigned to this role scope.</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {pendingInboxReviews.map((report) => (
                        <div key={report.id} className="py-4 first:pt-0 last:pb-0 flex flex-col lg:flex-row lg:items-start justify-between gap-5 text-xs">
                          <div className="space-y-1.5 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-bold text-slate-800 text-sm">{report.filename}</span>
                              <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-100 text-[10px] font-mono">
                                V{report.version}
                              </span>
                              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] capitalize">
                                {report.document_type || "policy"}
                              </span>
                              {report.governance_relevance && (
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  report.governance_relevance === "high"
                                    ? "bg-red-50 text-red-600 border border-red-100"
                                    : report.governance_relevance === "medium"
                                    ? "bg-amber-50 text-amber-600 border border-amber-100"
                                    : "bg-blue-50 text-blue-600 border border-blue-100"
                                }`}>
                                  {report.governance_relevance} Relevance
                                </span>
                              )}
                            </div>
                            <p className="text-slate-650 leading-relaxed max-w-2xl line-clamp-2">
                              {report.executive_summary || report.summary}
                            </p>
                            <div className="text-[10px] text-slate-400 flex gap-4">
                              <span>Uploaded: {new Date(report.created_at).toLocaleString()}</span>
                              <span>Confidence: {Math.round(report.confidence_score * 100)}%</span>
                              <span>Assignee: <span className="font-semibold text-slate-600">{report.assigned_to || "Unassigned"}</span></span>
                            </div>
                          </div>

                          {/* Quick Action Forms */}
                          <div className="w-full lg:w-80 flex flex-col gap-2.5 p-3 rounded-xl border border-slate-150 bg-slate-50/50">
                            <div>
                              <label className="block text-[9px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                                Review Decision Notes
                              </label>
                              <textarea
                                placeholder="Enter notes to justify approval or describe changes requested..."
                                value={reviewNotes[report.id] || ""}
                                onChange={(e) => setReviewNotes((prev) => ({ ...prev, [report.id]: e.target.value }))}
                                className="w-full h-16 text-[11px] p-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:border-blue-500 resize-none text-slate-700"
                              />
                            </div>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                disabled={isActionLoading[`report-approve-${report.id}`]}
                                onClick={() => handleApproveReport(report.id)}
                                className="flex-1 h-8 text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center justify-center gap-1"
                              >
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={isActionLoading[`report-changes-${report.id}`]}
                                onClick={() => handleRequestChanges(report.id)}
                                className="flex-1 h-8 text-[11px] font-semibold border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100 rounded-lg flex items-center justify-center gap-1"
                              >
                                Reject
                              </Button>
                            </div>
                            <div className="flex items-center gap-2 border-t border-slate-200/60 pt-2">
                              <select
                                value={reportAssignee[report.id] || ""}
                                onChange={(e) => {
                                  const val = e.target.value;
                                  setReportAssignee((prev) => ({ ...prev, [report.id]: val }));
                                  void handleAssignReport(report.id, val);
                                }}
                                disabled={isActionLoading[`report-assign-${report.id}`]}
                                className="w-1/2 h-8 text-[10px] px-2 rounded-lg border border-slate-200 bg-white text-slate-600 focus:outline-none cursor-pointer"
                              >
                                <option value="">Assign To...</option>
                                <option value="Analyst">Analyst</option>
                                <option value="Manager">Manager</option>
                                <option value="Governance Lead">Governance Lead</option>
                              </select>

                              <Button
                                size="sm"
                                variant="outline"
                                disabled={isActionLoading[`report-escalate-${report.id}`]}
                                onClick={() => handleEscalateReport(report.id)}
                                className="w-1/2 h-8 text-[10px] border-red-200 bg-red-50 text-red-650 hover:bg-red-100/50 rounded-lg flex items-center justify-center gap-1 font-semibold"
                              >
                                <AlertTriangle className="h-3 w-3" />
                                Escalate
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Escalations Tab */}
              {activeTab === "escalations" && (
                <div className="space-y-4">
                  {assignedInboxEscalations.length === 0 ? (
                    <div className="py-8 text-center text-xs text-slate-450 italic space-y-1">
                      <CheckCircle className="h-7 w-7 text-emerald-500/20 mx-auto mb-1" />
                      <p>No active escalations assigned to your role context.</p>
                      <p className="text-[10px]">Switch roles or route unresolved risks to verify workflow states.</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {assignedInboxEscalations.map((esc) => (
                        <div key={esc.id} className="py-4 first:pt-0 last:pb-0 flex flex-col lg:flex-row lg:items-start justify-between gap-5 text-xs">
                          <div className="space-y-2 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-bold text-red-700 bg-red-50 border border-red-100 px-2 py-0.5 rounded text-[10px] uppercase font-mono">
                                Escalation
                              </span>
                              <span className="font-semibold text-slate-700">{esc.filename}</span>
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border capitalize ${
                                esc.severity === "critical"
                                  ? "bg-red-50 text-red-600 border-red-200"
                                  : esc.severity === "high"
                                  ? "bg-orange-50 text-orange-600 border-orange-200"
                                  : "bg-blue-50 text-blue-600 border-blue-200"
                              }`}>
                                {esc.severity}
                              </span>
                            </div>
                            <p className="text-slate-650 leading-relaxed font-semibold">
                              {esc.description}
                            </p>
                            {esc.remediation_plan && (
                              <div className="bg-slate-50 border border-slate-200/50 p-2.5 rounded-lg text-[11px] text-slate-600 leading-relaxed">
                                <span className="font-bold text-slate-700 block mb-0.5">Remediation Blueprint</span>
                                {esc.remediation_plan}
                              </div>
                            )}
                            <div className="text-[10px] text-slate-400 flex gap-4">
                              <span>Raised: {new Date(esc.created_at).toLocaleDateString()}</span>
                              <span>Target: <span className="font-bold text-slate-500">{esc.routing_target || "None"}</span></span>
                              <span>Assigned to: <span className="font-semibold text-slate-600">{esc.assigned_to || "Unassigned"}</span></span>
                            </div>
                          </div>

                          {/* Quick Action form */}
                          <div className="w-full lg:w-80 flex flex-col gap-2.5 p-3 rounded-xl border border-slate-150 bg-slate-50/50">
                            <div>
                              <label className="block text-[9px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                                Route Escalation Target
                              </label>
                              <select
                                value={escRoute[esc.id] || ""}
                                onChange={(e) => {
                                  const val = e.target.value;
                                  setEscRoute((prev) => ({ ...prev, [esc.id]: val }));
                                  void handleRouteEscalation(esc.id, val);
                                }}
                                disabled={isActionLoading[`esc-route-${esc.id}`]}
                                className="w-full h-8 text-[11px] px-2.5 rounded-lg border border-slate-200 bg-white text-slate-600 focus:outline-none cursor-pointer"
                              >
                                <option value="">Select routing target...</option>
                                <option value="Internal Audit Team">Internal Audit Team</option>
                                <option value="Operations Committee">Operations Committee</option>
                                <option value="Executive Governance Board">Executive Governance Board</option>
                                <option value="Legal Counsel">Legal Counsel</option>
                              </select>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                disabled={isActionLoading[`esc-resolve-${esc.id}`]}
                                onClick={() => handleResolveEscalation(esc.id)}
                                className="flex-1 h-8 text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center justify-center"
                              >
                                Resolve
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={isActionLoading[`esc-close-${esc.id}`]}
                                onClick={() => handleCloseEscalation(esc.id)}
                                className="flex-1 h-8 text-[11px] font-semibold border-slate-250 hover:bg-slate-100 rounded-lg text-slate-700 flex items-center justify-center"
                              >
                                Close
                              </Button>
                            </div>
                            <div className="border-t border-slate-200/60 pt-2">
                              <select
                                value={escAssignee[esc.id] || ""}
                                onChange={(e) => {
                                  const val = e.target.value;
                                  setEscAssignee((prev) => ({ ...prev, [esc.id]: val }));
                                  void handleAssignEscalation(esc.id, val);
                                }}
                                disabled={isActionLoading[`esc-assign-${esc.id}`]}
                                className="w-full h-8 text-[11px] px-2.5 rounded-lg border border-slate-200 bg-white text-slate-600 focus:outline-none cursor-pointer"
                              >
                                <option value="">Reassign Owner...</option>
                                <option value="Analyst">Analyst</option>
                                <option value="Manager">Manager</option>
                                <option value="Governance Lead">Governance Lead</option>
                              </select>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Mitigations Tab */}
              {activeTab === "mitigations" && (
                <div className="space-y-4">
                  {assignedInboxMitigations.length === 0 ? (
                    <div className="py-8 text-center text-xs text-slate-450 italic space-y-1">
                      <CheckCircle className="h-7 w-7 text-emerald-500/20 mx-auto mb-1" />
                      <p>All assigned mitigation tasks are complete.</p>
                      <p className="text-[10px]">No mitigation actions pending your review.</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {assignedInboxMitigations.map((task) => {
                        const progress = mitProgress[task.id] !== undefined ? mitProgress[task.id] : task.completion_percentage;
                        return (
                          <div key={task.id} className="py-4 first:pt-0 last:pb-0 flex flex-col lg:flex-row lg:items-start justify-between gap-5 text-xs">
                            <div className="space-y-2 flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className={`px-2 py-0.5 rounded text-[9px] font-bold border uppercase font-mono ${
                                  task.status === "COMPLETED"
                                    ? "bg-emerald-50 text-emerald-600 border-emerald-100"
                                    : "bg-blue-50 text-blue-600 border-blue-100"
                                }`}>
                                  {task.status}
                                </span>
                                <span className="font-bold text-slate-800 text-sm">{task.title}</span>
                                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${
                                  task.priority === "P1"
                                    ? "bg-red-50 text-red-600 border-red-200"
                                    : task.priority === "P2"
                                    ? "bg-orange-50 text-orange-600 border-orange-200"
                                    : "bg-blue-50 text-blue-600 border-blue-200"
                                }`}>
                                  {task.priority}
                                </span>
                                {task.sla_status === "OVERDUE" ? (
                                  <span className="px-1.5 py-0.5 rounded bg-red-500/10 text-red-650 border border-red-200 text-[9px] font-bold animate-pulse">
                                    Overdue
                                  </span>
                                ) : (
                                  <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 text-[9px] font-bold">
                                    {task.sla_status}
                                  </span>
                                )}
                              </div>
                              <p className="text-slate-600 leading-relaxed">
                                {task.description || "No specific details provided for this task."}
                              </p>
                              <div className="text-[10px] text-slate-400 flex gap-4">
                                <span>Due Date: {task.target_date ? new Date(task.target_date).toLocaleDateString() : "None"}</span>
                                <span>Original Risk: <span className="font-semibold text-slate-700">{task.risk_score}</span></span>
                                <span>Remediation Target: <span className="font-semibold text-slate-700">RAID-{task.related_raid_item_id}</span></span>
                              </div>
                            </div>

                            {/* Slider & Actions Panel */}
                            <div className="w-full lg:w-80 flex flex-col gap-2.5 p-3 rounded-xl border border-slate-150 bg-slate-50/50">
                              <div className="space-y-1">
                                <div className="flex justify-between text-[10px] font-bold text-slate-400">
                                  <span>Task Progress</span>
                                  <span className="text-blue-600">{progress}%</span>
                                </div>
                                <div className="flex items-center gap-3">
                                  <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    step="5"
                                    value={progress}
                                    onChange={(e) => {
                                      const val = parseInt(e.target.value);
                                      setMitProgress((prev) => ({ ...prev, [task.id]: val }));
                                    }}
                                    className="flex-1 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                  />
                                  <Button
                                    size="sm"
                                    disabled={isActionLoading[`mit-progress-${task.id}`]}
                                    onClick={() => handleUpdateMitigationProgress(task.id)}
                                    className="h-7 px-2.5 text-[10px] font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg flex items-center justify-center gap-1"
                                  >
                                    Apply
                                  </Button>
                                </div>
                              </div>
                              
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  disabled={isActionLoading[`mit-complete-${task.id}`]}
                                  onClick={() => handleCompleteMitigation(task.id)}
                                  className="flex-1 h-8 text-[11px] font-semibold bg-blue-600 hover:bg-blue-750 text-white rounded-lg flex items-center justify-center"
                                >
                                  Complete Task
                                </Button>
                              </div>

                              <div className="border-t border-slate-200/60 pt-2">
                                <select
                                  value={mitAssignee[task.id] || ""}
                                  onChange={(e) => {
                                    const val = e.target.value;
                                    setMitAssignee((prev) => ({ ...prev, [task.id]: val }));
                                    void handleReassignMitigation(task.id, val);
                                  }}
                                  disabled={isActionLoading[`mit-assign-${task.id}`]}
                                  className="w-full h-8 text-[11px] px-2.5 rounded-lg border border-slate-200 bg-white text-slate-600 focus:outline-none cursor-pointer"
                                >
                                  <option value="">Reassign Owner Role...</option>
                                  <option value="Analyst">Analyst</option>
                                  <option value="Manager">Manager</option>
                                  <option value="Governance Lead">Governance Lead</option>
                                </select>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* Verifications Tab */}
              {activeTab === "verifications" && (
                <div className="space-y-4">
                  {role !== "Governance Lead" ? (
                    <div className="py-6 text-center text-xs text-slate-400 space-y-1">
                      <Shield className="h-6 w-6 text-slate-300 mx-auto mb-1" />
                      <p>Access Denied. Only the Governance Lead can audit completed mitigation tasks.</p>
                      <p className="text-[10px]">Please toggle your Active Role to "Governance Lead" in the sidebar selector.</p>
                    </div>
                  ) : pendingInboxVerifications.length === 0 ? (
                    <div className="py-8 text-center text-xs text-slate-450 italic space-y-1">
                      <CheckCircle className="h-7 w-7 text-emerald-500/20 mx-auto mb-1" />
                      <p>No completed tasks are awaiting verification review.</p>
                      <p className="text-[10px]">When analysts or managers mark tasks as completed, they will appear here.</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {pendingInboxVerifications.map((task) => (
                        <div key={task.id} className="py-4 first:pt-0 last:pb-0 flex flex-col lg:flex-row lg:items-start justify-between gap-5 text-xs">
                          <div className="space-y-2 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="bg-amber-50 text-amber-600 border border-amber-100 px-2 py-0.5 rounded text-[9px] uppercase font-mono font-bold">
                                Pending Sign-Off
                              </span>
                              <span className="font-bold text-slate-800 text-sm">{task.title}</span>
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${
                                task.priority === "P1"
                                  ? "bg-red-50 text-red-600 border-red-200"
                                  : "bg-blue-50 text-blue-600 border-blue-200"
                              }`}>
                                {task.priority}
                              </span>
                            </div>
                            <p className="text-slate-650 leading-relaxed">
                              {task.description || "No specific details provided."}
                            </p>
                            <div className="text-[10px] text-slate-400 flex gap-4">
                              <span>Completed By: <span className="font-bold text-slate-600">{task.owner_name || task.owner_role}</span></span>
                              <span>Risk Score: <span className="font-semibold text-slate-700">{task.risk_score}</span></span>
                              <span>Target Date: {task.target_date ? new Date(task.target_date).toLocaleDateString() : "None"}</span>
                              <span>Effectiveness Bonus: <span className="font-semibold text-emerald-600">+{task.effectiveness}% Reduction</span></span>
                            </div>
                          </div>

                          {/* Action Panel */}
                          <div className="w-full lg:w-64 flex flex-col gap-2 p-3 rounded-xl border border-slate-150 bg-slate-50/50 justify-center">
                            <Button
                              size="sm"
                              disabled={isActionLoading[`mit-verify-${task.id}`]}
                              onClick={() => handleVerifyMitigation(task.id)}
                              className="w-full h-8 text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center justify-center gap-1.5"
                            >
                              <Check className="h-3.5 w-3.5" />
                              Verify Completion
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={isActionLoading[`mit-reopen-${task.id}`]}
                              onClick={() => handleReopenMitigation(task.id)}
                              className="w-full h-8 text-[11px] font-semibold border-red-200 bg-red-50 text-red-750 hover:bg-red-100/50 rounded-lg flex items-center justify-center gap-1.5"
                            >
                              <RotateCcw className="h-3 w-3" />
                              Reopen & Reject
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Attention Required Grid */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Critical Risks */}
            <Card className="border-slate-200 bg-white shadow-sm flex flex-col justify-between">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  Attention: Critical Risks
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Unresolved RAID items with risk scores &gt; 60
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto max-h-[260px] pt-1 space-y-2.5">
                {criticalRaidItems.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center py-6 text-slate-500 text-xs italic">
                    <CheckCircle className="h-7 w-7 text-emerald-500/20 mb-1" />
                    All critical risks mitigated.
                  </div>
                ) : (
                  criticalRaidItems.map((item) => (
                    <div key={item.id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60 text-xs flex justify-between gap-3 items-start">
                      <div className="space-y-1">
                        <p className="font-semibold text-slate-800 line-clamp-2 leading-relaxed">{item.description}</p>
                        <div className="flex items-center gap-2 text-[9px] font-semibold text-slate-400 capitalize">
                          <span>RAID-{item.id}</span>
                          <span>•</span>
                          <span>Owner: {item.suggested_owner_role}</span>
                        </div>
                      </div>
                      <span className="bg-red-50 text-red-750 font-bold border border-red-200 text-[9px] px-1.5 py-0.5 rounded-full flex-none">
                        Score {item.risk_score}
                      </span>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Overdue Remediation Tasks */}
            <Card className="border-slate-200 bg-white shadow-sm flex flex-col justify-between">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
                  <Clock className="h-4 w-4 text-red-500 animate-pulse" />
                  Attention: SLA Breaches
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Mitigation actions past target completion dates
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto max-h-[260px] pt-1 space-y-2.5">
                {overdueMitigations.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center py-6 text-slate-500 text-xs italic">
                    <CheckCircle className="h-7 w-7 text-emerald-500/20 mb-1" />
                    All SLAs on track.
                  </div>
                ) : (
                  overdueMitigations.slice(0, 5).map((task) => {
                    let daysLate = 0;
                    if (task.target_date) {
                      const due = new Date(task.target_date).getTime();
                      const now = new Date().getTime();
                      daysLate = Math.max(1, Math.floor((now - due) / (1000 * 60 * 60 * 24)));
                    }
                    return (
                      <div key={task.id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60 text-xs flex justify-between gap-3 items-start">
                        <div className="space-y-1">
                          <p className="font-semibold text-slate-800 line-clamp-2 leading-relaxed">{task.title}</p>
                          <div className="flex items-center gap-2 text-[9px] font-semibold text-slate-400">
                            <span>Owner: {task.owner_name || task.owner_role}</span>
                            <span>•</span>
                            <span>Due: {task.target_date ? new Date(task.target_date).toLocaleDateString() : "None"}</span>
                          </div>
                        </div>
                        <span className="bg-red-500/10 text-red-650 font-bold border border-red-200/60 text-[9px] px-1.5 py-0.5 rounded-full flex-none animate-pulse">
                          {daysLate} {daysLate === 1 ? "day" : "days"} late
                        </span>
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>

            {/* Active Escalations */}
            <Card className="border-slate-200 bg-white shadow-sm flex flex-col justify-between">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
                  <ShieldAlert className="h-4 w-4 text-orange-500" />
                  Attention: Active Escalations
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Unresolved issues routed to committee levels
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto max-h-[260px] pt-1 space-y-2.5">
                {openEscalations.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center py-6 text-slate-500 text-xs italic">
                    <CheckCircle className="h-7 w-7 text-emerald-500/20 mb-1" />
                    No active escalations.
                  </div>
                ) : (
                  openEscalations.slice(0, 5).map((e) => (
                    <div key={e.id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60 text-xs flex justify-between gap-3 items-start">
                      <div className="space-y-1">
                        <p className="font-semibold text-slate-800 line-clamp-2 leading-relaxed">{e.description}</p>
                        <div className="flex items-center gap-2 text-[9px] font-semibold text-slate-400">
                          <span>Target: {e.routing_target || "Assignee"}</span>
                          <span>•</span>
                          <span>Assigned: {e.assigned_to || "Unassigned"}</span>
                        </div>
                      </div>
                      <span className="bg-orange-50 text-orange-655 font-bold border border-orange-200 text-[9px] px-1.5 py-0.5 rounded-full flex-none capitalize">
                        {e.status}
                      </span>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity Split: Alert Feed (Left) & Audit Timeline (Right) */}
          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            {/* Live Alerts Notifications Feed */}
            <Card className="border-slate-200 bg-white shadow-sm flex flex-col">
              <CardHeader className="bg-slate-50/50 border-b border-slate-200/80 p-4 flex items-center justify-between">
                <div className="space-y-0.5">
                  <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                    <Bell className="h-4.5 w-4.5 text-blue-500" />
                    Live Notification Feed
                  </CardTitle>
                  <CardDescription className="text-[11px] text-slate-500">
                    SLA alerts, workflow assignments, and system events
                  </CardDescription>
                </div>
                {unreadNotifications.length > 0 && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleReadAll}
                    className="h-7 px-2.5 text-[10px] text-slate-650 hover:text-slate-800 border-slate-250 bg-white font-semibold rounded-lg flex items-center gap-1"
                  >
                    Dismiss All
                  </Button>
                )}
              </CardHeader>
              <CardContent className="p-4 flex-1 overflow-y-auto max-h-[360px] space-y-2.5">
                {allNotifications.length === 0 ? (
                  <div className="h-full py-12 flex flex-col items-center justify-center text-center text-slate-450 italic text-xs space-y-1">
                    <CheckCircle className="h-8 w-8 text-emerald-500/15 mb-1" />
                    <p>Alert feed is clear.</p>
                    <p className="text-[10px]">Notifications appear when workflows trigger state changes.</p>
                  </div>
                ) : (
                  allNotifications.map((n) => {
                    let sevClass = "border-slate-200 bg-slate-50 text-slate-600";
                    let dotColor = "bg-slate-400";
                    
                    if (n.severity === "CRITICAL") {
                      sevClass = "border-red-200 bg-red-50/40 text-red-800";
                      dotColor = "bg-red-500";
                    } else if (n.severity === "HIGH") {
                      sevClass = "border-orange-200 bg-orange-50/45 text-orange-850";
                      dotColor = "bg-orange-500";
                    } else if (n.severity === "MEDIUM") {
                      sevClass = "border-blue-200 bg-blue-50/30 text-blue-800";
                      dotColor = "bg-blue-500";
                    }

                    return (
                      <div
                        key={n.id}
                        className={`p-3 rounded-xl border text-xs flex gap-3 transition-all duration-200 items-start ${sevClass} ${
                          n.read_status ? "opacity-50" : ""
                        }`}
                      >
                        <div className="mt-1 flex-none h-2 w-2 rounded-full relative">
                          <span className={`absolute inset-0 rounded-full ${dotColor} ${!n.read_status ? "animate-ping opacity-75" : ""}`} />
                          <span className={`relative block h-2 w-2 rounded-full ${dotColor}`} />
                        </div>
                        <div className="flex-1 space-y-0.5">
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-bold text-[11px] tracking-tight text-slate-800 leading-tight">{n.title}</span>
                            <span className="text-[9px] text-slate-400 flex-none">{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          </div>
                          <p className="text-slate-600 text-[11px] leading-normal">{n.message}</p>
                          <div className="flex items-center justify-between text-[9px] text-slate-400 border-t border-slate-100/50 pt-1.5 mt-1">
                            <span>Role: <span className="font-bold uppercase">{n.recipient_role}</span></span>
                            {n.related_entity_type && (
                              <span className="capitalize">
                                {n.related_entity_type}: #{n.related_entity_id}
                              </span>
                            )}
                          </div>
                        </div>
                        {!n.read_status && (
                          <button
                            onClick={() => handleReadNotification(n.id)}
                            className="flex-none hover:bg-slate-200/50 p-1 rounded-full text-slate-400 hover:text-slate-600 transition-colors"
                            title="Dismiss Notification"
                          >
                            <Check className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>

            {/* Audit Trail Activity Timeline */}
            <Card className="border-slate-200 bg-white shadow-sm flex flex-col">
              <CardHeader className="bg-slate-50/50 border-b border-slate-200/80 p-4">
                <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                  <Activity className="h-4.5 w-4.5 text-blue-500" />
                  Audit Trail Chronology
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Immutable ledger of system events and workflow reviews
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 flex-1 overflow-y-auto max-h-[360px]">
                <Timeline logs={auditQuery.data ?? []} />
              </CardContent>
            </Card>
          </div>

          {/* Subsystem Metrics & Trends */}
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(340px,0.7fr)]">
            <GovernanceOverview charts={chartsQuery.data} />
            <ProcessingMetrics stats={statsQuery.data} />
          </div>

          {/* Integration & Export Controls */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Webhook Integrations Card */}
            <Card className="border-slate-200 bg-white shadow-sm flex flex-col">
              <CardHeader className="bg-slate-50/50 border-b border-slate-200/80 p-4">
                <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                  <Settings className="h-4.5 w-4.5 text-blue-500" />
                  Slack & MS Teams Webhook Integrations
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Configure real-time alerting for P1 risks, critical escalations, and SLA breaches.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 flex-1 space-y-4">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-600 block">Slack Webhook URL</label>
                  <input
                    type="text"
                    placeholder="https://hooks.slack.com/services/..."
                    value={slackWebhook}
                    onChange={(e) => setSlackWebhook(e.target.value)}
                    className="w-full h-9 text-xs px-3 rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white text-slate-700"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-600 block">MS Teams Webhook URL</label>
                  <input
                    type="text"
                    placeholder="https://outlook.office.com/webhook/..."
                    value={teamsWebhook}
                    onChange={(e) => setTeamsWebhook(e.target.value)}
                    className="w-full h-9 text-xs px-3 rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white text-slate-700"
                  />
                </div>
                <div className="flex items-center justify-between pt-2">
                  <span className="text-[10px] text-slate-400">
                    {saveSuccess && (
                      <span className="text-emerald-600 font-semibold flex items-center gap-1">
                        <Check className="h-3 w-3" /> Settings saved successfully
                      </span>
                    )}
                  </span>
                  <Button
                    size="sm"
                    disabled={isSavingWebhooks}
                    onClick={handleSaveIntegrations}
                    className="h-8 text-xs font-semibold bg-blue-600 hover:bg-blue-750 text-white px-4 rounded-lg flex items-center gap-1.5"
                  >
                    {isSavingWebhooks ? "Saving..." : "Save Configuration"}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Excel & CSV Export Engine Card */}
            <Card className="border-slate-200 bg-white shadow-sm flex flex-col justify-between">
              <CardHeader className="bg-slate-50/50 border-b border-slate-200/80 p-4">
                <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                  <Download className="h-4.5 w-4.5 text-blue-500" />
                  Governance Register Export Engine
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Download structured copies of the active risk register, mitigations, and SLA states.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 flex-1 flex flex-col justify-between gap-4">
                <p className="text-xs text-slate-650 leading-relaxed">
                  Export complete risk registers mapped under the current active organization. The Excel workbook is formatted dynamically with high-impact color coding for SLA breach indicators, priority indicators, and automated metrics dashboards.
                </p>
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={isExportingCsv}
                    onClick={handleExportCsv}
                    className="h-9 text-xs font-semibold border-slate-250 hover:bg-slate-50/50 text-slate-750 rounded-lg flex items-center justify-center gap-2"
                  >
                    <FileText className="h-4 w-4 text-slate-550" />
                    {isExportingCsv ? "Generating CSV..." : "Export raw CSV"}
                  </Button>
                  <Button
                    size="sm"
                    disabled={isExportingExcel}
                    onClick={handleExportExcel}
                    className="h-9 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center justify-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    {isExportingExcel ? "Generating XLSX..." : "Export formatted Excel"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

        </div>
      ) : (
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="p-10 text-center space-y-2">
            <Info className="h-8 w-8 text-blue-500 mx-auto" />
            <h3 className="text-sm font-bold text-slate-800">No Dashboard Data Available</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Ingest, parse, and review corporate policy documents to populate operations metrics.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
