import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Database, Cpu, Activity, Bell, FileText, ArrowRight, Layers, Layout, AlertTriangle } from "lucide-react";

export function ArchitecturePage() {
  const pipelineStages = [
    {
      step: "01",
      title: "Document Ingestion",
      icon: FileText,
      description: "Supports parsing multi-format corporate uploads (PDF, DOCX, TXT) and saving raw documents to persistent disk storage.",
      tech: "FastAPI Upload / Python File Parsers"
    },
    {
      step: "02",
      title: "AI Extraction Pipeline",
      icon: Cpu,
      description: "Extracts structured metadata (RAID items, severity, source quotes) using advanced LLM processing chunks and retrieval context.",
      tech: "Claude 3.5 Sonnet / TF-IDF RAG Chunks"
    },
    {
      step: "03",
      title: "Governance Playbook Engine",
      icon: Shield,
      description: "Matches extracted findings against a deterministic playbook matrix to enrich risks with recommended mitigations and owner roles.",
      tech: "Deterministic Policy Mapping Engine"
    },
    {
      step: "04",
      title: "Risk Scoring Module",
      icon: AlertTriangle,
      description: "Computes original risk scores (0-100) and tracks residual risk dynamically based on active vs verified mitigations.",
      tech: "Mathematical Residual Scoring Formula"
    },
    {
      step: "05",
      title: "Workflows & Approvals",
      icon: Layout,
      description: "Coordinates state transitions across roles (Analyst draft, Manager review, Lead resolution) with strict validation blockades.",
      tech: "FastAPI Header Swapping Permission Layer"
    },
    {
      step: "06",
      title: "Mitigation Lifecycle",
      icon: Activity,
      description: "Auto-generates remediation tasks, monitors SLAs (target date thresholds), and recalculates risk exposure upon lead validation.",
      tech: "Lifecycle State Machine & SLA Monitors"
    },
    {
      step: "07",
      title: "Notification Alerts",
      icon: Bell,
      description: "Dispatches low, medium, high, and critical alerts dynamically for new actions, assigned tasks, and SLA breaches.",
      tech: "Pull-based SLA Checker & Notification Engine"
    },
    {
      step: "08",
      title: "Governance Operations",
      icon: Database,
      description: "Consolidates My Work queues, Attention Required items, audit timeline events, and quick actions into a cockpit workspace.",
      tech: "React Dashboard / Operations Center"
    }
  ];

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto text-slate-100">
      <PageHeader
        eyebrow="System Design"
        title="System Architecture Overview"
        description="Understand the end-to-end data pipeline, algorithms, and modular design of the Enterprise Governance Intelligence Platform."
      />

      {/* Visual Pipeline Flow */}
      <div className="relative border border-slate-800 bg-slate-950/40 backdrop-blur rounded-2xl p-8 overflow-hidden shadow-2xl">
        <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/5 via-transparent to-purple-500/5" />
        <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
          <Layers className="h-5 w-5 text-blue-400" />
          End-to-End Governance Data Pipeline
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
          {pipelineStages.map((stage, i) => (
            <div
              key={stage.title}
              className="group relative border border-slate-800 bg-slate-900/40 rounded-xl p-5 hover:border-slate-700 hover:bg-slate-900/80 transition-all duration-300 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold text-blue-500 bg-blue-500/10 px-2 py-1 rounded">
                    Stage {stage.step}
                  </span>
                  <stage.icon className="h-5 w-5 text-slate-400 group-hover:text-blue-400 transition-colors" />
                </div>
                <h4 className="font-semibold text-slate-200 group-hover:text-white transition-colors mb-2">
                  {stage.title}
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  {stage.description}
                </p>
              </div>
              <div className="border-t border-slate-800 pt-3 mt-2">
                <span className="text-[10px] text-slate-500 font-mono">
                  {stage.tech}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Technical Blueprint Layers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="border-slate-800 bg-slate-950/40 backdrop-blur shadow-xl lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-slate-200">Subsystem Blueprint</CardTitle>
            <CardDescription className="text-slate-400">
              Visualizing the system structure from user interaction to data persistence.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Frontend Layer */}
            <div className="relative border border-blue-500/30 bg-blue-500/5 rounded-xl p-5">
              <div className="absolute top-3 right-4 bg-blue-500/15 text-blue-400 text-xs font-semibold px-2 py-0.5 rounded">
                Presentation Layer
              </div>
              <h4 className="font-semibold text-blue-400 mb-2 flex items-center gap-2">
                <Layout className="h-4 w-4" />
                React / Vite SPA Frontend
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed mb-3">
                Renders a responsive dashboard, unified operations cockpit, workflow boards, audit timelines, and risk metrics. Interacts with backend API endpoints using dynamic role headers.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">TypeScript</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">Tailwind CSS</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">React Query</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">Lucide Icons</span>
              </div>
            </div>

            <div className="flex justify-center my-2">
              <ArrowRight className="h-5 w-5 text-slate-600 rotate-90" />
            </div>

            {/* Application API Layer */}
            <div className="relative border border-purple-500/30 bg-purple-500/5 rounded-xl p-5">
              <div className="absolute top-3 right-4 bg-purple-500/15 text-purple-400 text-xs font-semibold px-2 py-0.5 rounded">
                Application & API Layer
              </div>
              <h4 className="font-semibold text-purple-400 mb-2 flex items-center gap-2">
                <Cpu className="h-4 w-4" />
                FastAPI Gateway & Background Tasks
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed mb-3">
                Handles API requests, provides role-based permission headers verification, runs document parsing, and offloads heavy AI analysis to asynchronous background tasks.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">FastAPI</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">Pydantic validation</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">BackgroundTasks</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">Uvicorn</span>
              </div>
            </div>

            <div className="flex justify-center my-2">
              <ArrowRight className="h-5 w-5 text-slate-600 rotate-90" />
            </div>

            {/* Core Engines */}
            <div className="relative border border-emerald-500/30 bg-emerald-500/5 rounded-xl p-5">
              <div className="absolute top-3 right-4 bg-emerald-500/15 text-emerald-400 text-xs font-semibold px-2 py-0.5 rounded">
                Business & Logic Layer
              </div>
              <h4 className="font-semibold text-emerald-400 mb-2 flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Playbooks & Risk Engines
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed mb-3">
                Applies risk categorization rules, identifies recommended mitigations, maintains SLA alerts, and calculates the overall Governance Health Score.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">Playbook engine</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">Residual risk formula</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">SLA monitors</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">Audit timeline logging</span>
              </div>
            </div>

            <div className="flex justify-center my-2">
              <ArrowRight className="h-5 w-5 text-slate-600 rotate-90" />
            </div>

            {/* Database Layer */}
            <div className="relative border border-amber-500/30 bg-amber-500/5 rounded-xl p-5">
              <div className="absolute top-3 right-4 bg-amber-500/15 text-amber-400 text-xs font-semibold px-2 py-0.5 rounded">
                Data Persistence Layer
              </div>
              <h4 className="font-semibold text-amber-400 mb-2 flex items-center gap-2">
                <Database className="h-4 w-4" />
                Relational DB & RAG Vector Store
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed mb-3">
                Stores structured database records (RAID items, mitigations, logs, notifications) and indexes document chunks for retrieval-augmented generation queries.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">SQLite / PostgreSQL</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">SQLAlchemy ORM</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">TF-IDF Index</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-1 rounded">Disk persistence</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Dynamic Risk Scoring Explanation */}
        <div className="space-y-6">
          <Card className="border-slate-800 bg-slate-950/40 backdrop-blur shadow-xl">
            <CardHeader>
              <CardTitle className="text-slate-200">Algorithmic Risk Formulation</CardTitle>
              <CardDescription className="text-slate-400">
                How original and residual risks are computed.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs text-slate-300 leading-relaxed">
              <div className="border border-slate-850 bg-slate-900/60 p-4 rounded-lg">
                <h5 className="font-semibold text-slate-200 mb-1">Original Risk Score (0-100)</h5>
                <p className="text-slate-400 mb-2">
                  Determined by the Playbook Engine based on the severity of the extracted RAID item:
                </p>
                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-300">
                  <div className="bg-slate-950 p-1 rounded">Critical: 90-100</div>
                  <div className="bg-slate-950 p-1 rounded">High: 70-89</div>
                  <div className="bg-slate-950 p-1 rounded">Medium: 40-69</div>
                  <div className="bg-slate-950 p-1 rounded">Low: 0-39</div>
                </div>
              </div>

              <div className="border border-slate-850 bg-slate-900/60 p-4 rounded-lg">
                <h5 className="font-semibold text-slate-200 mb-1">Residual Risk Formulation</h5>
                <p className="text-slate-400 mb-2">
                  When a mitigation task linked to a RAID item is formally verified by the Governance Lead, the item's current risk score is dynamically reduced:
                </p>
                <div className="bg-slate-950 p-2.5 rounded font-mono text-[10px] text-blue-300 mb-2">
                  residual_mult = 1.0 - (sum(verified_task.effectiveness) / 100.0)
                  current_risk = max(0, original_risk * residual_mult)
                </div>
                <p className="text-[10px] text-amber-400">
                  Note: Total mitigation effectiveness is strictly capped at 80% to ensure a 20% residual risk floor remains until items are archived.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-950/40 backdrop-blur shadow-xl">
            <CardHeader>
              <CardTitle className="text-slate-200">Governance Health Formula</CardTitle>
              <CardDescription className="text-slate-400">
                How platform compliance metrics are calculated.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs text-slate-300 leading-relaxed">
              <div className="border border-slate-850 bg-slate-900/60 p-4 rounded-lg">
                <p className="text-slate-400 mb-3">
                  The Governance Health Score starts at a baseline of 100 and applies immediate deductions for active vulnerabilities:
                </p>
                <ul className="space-y-2 text-[10px] font-mono">
                  <li className="flex items-center justify-between text-red-400">
                    <span>Open Critical/High Risks</span>
                    <span>-5 points each</span>
                  </li>
                  <li className="flex items-center justify-between text-orange-400">
                    <span>Open Escalation Items</span>
                    <span>-8 points each</span>
                  </li>
                  <li className="flex items-center justify-between text-yellow-400">
                    <span>Overdue Mitigation Tasks</span>
                    <span>-4 points each</span>
                  </li>
                  <li className="flex items-center justify-between text-emerald-400">
                    <span>Verified Mitigations (Bonus)</span>
                    <span>+2 points each (max +15)</span>
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
