# Demo Walkthrough Script — Enterprise Governance Intelligence Platform

This document describes the step-by-step user journey and script to demonstrate the platform's core capabilities (v1.0.0-rc1) to stakeholders.

---

## Prerequisite: Seed the Demo Environment
1. Log in to the application and navigate to the sidebar.
2. Select the **Dashboard** link.
3. Locate the **Demo Seeder Panel** in the command cockpit.
4. Select the **Global Enterprise** size preset and click **Generate Demo Data**.
5. Confirm the system is populated with documents, audit logs, and notifications.

---

## Journey 1: The Analyst (Upload & Identify)
- **Role Switcher**: Set active role to **Analyst** in the sidebar.
- **Objective**: Ingest a new steering committee document and review the initial drafts.
- **Actions**:
  1. Navigate to the **Upload** page.
  2. Select a text file or PDF (e.g., `project_aurora_risk_register.txt` from uploads).
  3. Set chunk configuration parameter sliders and click **Upload & Process**.
  4. Wait for the extraction pipeline to complete, then navigate to the **Reports** page.
  5. Select the newly generated draft report.
  6. Review the extracted AI Insights (relevance, suggested mitigations, impact estimates, and explainability traces).

---

## Journey 2: The Manager (Approve & Escalate)
- **Role Switcher**: Set active role to **Manager** in the sidebar.
- **Objective**: Review the Analyst's draft report, verify issues, and assign mitigations.
- **Actions**:
  1. Navigate to the **Review Queue** tab on the main dashboard cockpit.
  2. Select the report draft uploaded by the Analyst.
  3. Read through the findings. Click **Request Changes** or **Approve Report** (entering audit notes).
  4. Identify a critical security finding and click **Escalate to Lead**.
  5. Enter the escalation description and target group, and submit.
  6. Locate the generated mitigation tasks and assign specific team owners.

---

## Journey 3: The Governance Lead (Resolve & Verify)
- **Role Switcher**: Set active role to **Governance Lead** in the sidebar.
- **Objective**: Resolve escalations, audit active mitigations, and verify completions.
- **Actions**:
  1. Navigate to the **Escalations** page.
  2. Locate the critical security escalation item submitted by the Manager.
  3. Route the escalation to the security team and set the status to **ROUTED**.
  4. Investigate the issue, enter resolution details, and click **Resolve Escalation**.
  5. Navigate to the **Mitigations** page.
  6. Select a mitigation task that is marked as **COMPLETED**.
  7. Audit the owner's explanation, then click **Verify Completion**.
  8. Confirm that the associated RAID item's current risk score decreases, and overall Governance Health increases.

---

## Journey 4: The Executive (Review Hub & Board Pack)
- **Role Switcher**: Set active role to **Governance Lead** or choose **Executive** (represented by access to the intelligence center).
- **Objective**: Review portfolio health, consult the AI Copilot, and export the board pack.
- **Actions**:
  1. Navigate to the **Executive Hub** link in the sidebar.
  2. Review the **Health Score** deductions list and the **Maturity Model** dimensions.
  3. Review the **Top Executive Priorities** alert cards.
  4. Review the 30-day historical trend lines.
  5. Scroll to the **Governance Executive Copilot** at the bottom of the page.
  6. Click the preset button: **"What's my biggest governance risk?"** and review the response.
  7. Click the preset button: **"Generate board update."** and review.
  8. Click the **Preview Board Pack** button at the top of the page.
  9. Review the printable board pack layout.
  10. Click **Print / Save PDF** to trigger the browser's PDF save dialog.
