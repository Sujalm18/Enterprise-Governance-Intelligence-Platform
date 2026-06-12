import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { EscalationsPage } from "@/features/escalations/EscalationsPage";
import { ReportDetailPage } from "@/features/reports/ReportDetailPage";
import { ReportsPage } from "@/features/reports/ReportsPage";
import { ReviewQueuePage } from "@/features/review/ReviewQueuePage";
import { UploadPage } from "@/features/upload/UploadPage";
import { WorkflowPage } from "@/features/workflow/WorkflowPage";
import { MitigationsPage } from "@/features/workflow/MitigationsPage";
import { ArchitecturePage } from "@/features/architecture/ArchitecturePage";
import ExecutiveHubPage from "@/features/intelligence/ExecutiveHubPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/workflow" element={<WorkflowPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/reports/:reportId" element={<ReportDetailPage />} />
        <Route path="/review" element={<ReviewQueuePage />} />
        <Route path="/escalations" element={<EscalationsPage />} />
        <Route path="/mitigations" element={<MitigationsPage />} />
        <Route path="/architecture" element={<ArchitecturePage />} />
        <Route path="/intelligence" element={<ExecutiveHubPage />} />
      </Route>
    </Routes>
  );
}
