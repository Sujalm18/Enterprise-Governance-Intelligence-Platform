import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  Brain,
  CheckCircle,
  CheckSquare,
  ChevronRight,
  Clock,
  Database,
  Download,
  FileText,
  Gauge,
  Info,
  RefreshCw,
  RotateCcw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sliders,
  Sparkles,
  TrendingDown,
  TrendingUp,
  User,
  UserCheck,
  X,
  Printer,
  Send
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/PageHeader";
import { useRole } from "@/lib/context/RoleContext";
import {
  getGovernanceMaturity,
  getHealthExplanations,
  getExecutivePriorities,
  getRootCauseAnalytics,
  getPortfolioRecommendations,
  getGovernanceTrends,
  getExecutiveBriefing,
  askGovernanceCopilot
} from "@/lib/api/intelligence";

export default function ExecutiveHubPage() {
  const { role } = useRole();
  const queryClient = useQueryClient();

  const [copilotQuery, setCopilotQuery] = useState("");
  const [copilotHistory, setCopilotHistory] = useState<Array<{ sender: "user" | "copilot"; text: string }>>([
    { sender: "copilot", text: "Hello! I am your Governance Intelligence Executive Copilot. Ask me questions about RAID items, mitigations, escalations, or request a summary." }
  ]);
  const [isCopilotLoading, setIsCopilotLoading] = useState(false);
  const [isPreviewingPrint, setIsPreviewingPrint] = useState(false);

  // Queries
  const maturityQuery = useQuery({
    queryKey: ["governance", "maturity"],
    queryFn: getGovernanceMaturity,
    refetchInterval: 15_000,
  });

  const healthQuery = useQuery({
    queryKey: ["governance", "health-explanations"],
    queryFn: getHealthExplanations,
    refetchInterval: 15_000,
  });

  const prioritiesQuery = useQuery({
    queryKey: ["governance", "executive-priorities"],
    queryFn: getExecutivePriorities,
    refetchInterval: 15_000,
  });

  const rcaQuery = useQuery({
    queryKey: ["governance", "root-cause-analytics"],
    queryFn: getRootCauseAnalytics,
    refetchInterval: 15_000,
  });

  const recommendationsQuery = useQuery({
    queryKey: ["governance", "portfolio-recommendations"],
    queryFn: getPortfolioRecommendations,
    refetchInterval: 30_000,
  });

  const trendsQuery = useQuery({
    queryKey: ["governance", "trends"],
    queryFn: getGovernanceTrends,
    refetchInterval: 30_000,
  });

  const briefingQuery = useQuery({
    queryKey: ["governance", "executive-briefing"],
    queryFn: getExecutiveBriefing,
    refetchInterval: 30_000,
  });

  const handleCopilotSend = async (textToSend?: string) => {
    const query = textToSend || copilotQuery;
    if (!query.trim()) return;

    setCopilotHistory((prev) => [...prev, { sender: "user", text: query }]);
    if (!textToSend) setCopilotQuery("");
    setIsCopilotLoading(true);

    try {
      const res = await askGovernanceCopilot(query);
      setCopilotHistory((prev) => [...prev, { sender: "copilot", text: res.response }]);
    } catch (err) {
      setCopilotHistory((prev) => [
        ...prev,
        { sender: "copilot", text: "Sorry, I encountered an error while processing your request. Please try again." }
      ]);
    } finally {
      setIsCopilotLoading(false);
    }
  };

  const presetQuestions = [
    "What's my biggest governance risk?",
    "What should I focus on this week?",
    "Why is our health score declining?",
    "Why is our maturity score low?",
    "Show overdue mitigations.",
    "Summarize open escalations.",
    "What should leadership prioritize?",
    "Generate board update."
  ];

  const handlePrint = () => {
    window.print();
  };

  // Extract variables
  const maturity = maturityQuery.data;
  const healthInfo = healthQuery.data;
  const priorities = prioritiesQuery.data || [];
  const rca = rcaQuery.data;
  const recs = recommendationsQuery.data;
  const trends = trendsQuery.data?.trend_points || [];
  const briefing = briefingQuery.data;

  // Determine Severity Color
  const getSeverityColor = (severity: string) => {
    switch (severity.toUpperCase()) {
      case "CRITICAL":
        return "border-red-500 bg-red-50 text-red-700";
      case "HIGH":
        return "border-orange-500 bg-orange-50 text-orange-700";
      case "MEDIUM":
        return "border-yellow-500 bg-yellow-50 text-yellow-700";
      default:
        return "border-slate-300 bg-slate-50 text-slate-700";
    }
  };

  return (
    <div className="relative space-y-6 pb-12">
      {/* Print Overlay Hide CSS */}
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          .board-pack-print-container, .board-pack-print-container * {
            visibility: visible;
          }
          .board-pack-print-container {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            background: white;
            color: black;
            padding: 20px;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>

      <div className="no-print flex items-center justify-between">
        <PageHeader
          title="Executive Intelligence Hub"
          description="Consolidated boardroom command center for governance, risk, and maturity monitoring."
          eyebrow="Executive Intelligence"
        />
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="flex items-center gap-2"
            onClick={() => setIsPreviewingPrint(true)}
          >
            <Printer className="h-4 w-4" />
            Preview Board Pack
          </Button>
        </div>
      </div>

      {/* Main Grid: Row 1 - Health & Maturity side-by-side */}
      <div className="no-print grid gap-6 lg:grid-cols-2">
        {/* Health explanations */}
        <Card className="flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Governance Health Score</CardTitle>
                <CardDescription>Real-time corporate policy compliance rating.</CardDescription>
              </div>
              <div className="flex items-center justify-center rounded-full bg-slate-900 h-16 w-16 text-white text-2xl font-bold border-4 border-emerald-500">
                {healthInfo?.health_score ?? "..."}
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 space-y-4">
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Main Drivers</h4>
              {healthInfo?.main_drivers && healthInfo.main_drivers.length > 0 ? (
                <div className="space-y-2">
                  {healthInfo.main_drivers.map((driver, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm rounded-md bg-red-50/50 p-2 border border-red-100">
                      <span className="text-slate-700 font-medium">{driver.description}</span>
                      <span className="text-red-600 font-semibold">-{driver.impact} pts</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No negative health drivers identified.</p>
              )}
            </div>

            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Positive Contributions</h4>
              {healthInfo?.positive_contributions && healthInfo.positive_contributions.length > 0 ? (
                <div className="space-y-2">
                  {healthInfo.positive_contributions.map((bonus, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm rounded-md bg-emerald-50/50 p-2 border border-emerald-100">
                      <span className="text-slate-700 font-medium">{bonus.description}</span>
                      <span className="text-emerald-600 font-semibold">+{bonus.impact} pts</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No active mitigation bonuses currently applied.</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Maturity Score & breakdown */}
        <Card className="flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Governance Maturity Model</CardTitle>
                <CardDescription>Maturity tiering, appetite alignment, and benchmark indicators.</CardDescription>
              </div>
              <div className="text-right">
                <div className="text-2xl font-extrabold text-slate-900">{maturity?.score ?? "..."}</div>
                <div className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 inline-block uppercase mt-1">
                  {maturity?.tier ?? "..."}
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 space-y-4">
            {/* Dimensions Progress */}
            {maturity?.dimensions && (
              <div className="space-y-2">
                {[
                  { label: "Policy Ownership", value: maturity.dimensions.policy_ownership },
                  { label: "Mitigation Completion", value: maturity.dimensions.mitigation_completion },
                  { label: "SLA Compliance", value: maturity.dimensions.sla_compliance },
                  { label: "Escalation Closure", value: maturity.dimensions.escalation_closure },
                  { label: "Risk Reduction", value: maturity.dimensions.risk_reduction },
                ].map((dim) => (
                  <div key={dim.label} className="text-xs">
                    <div className="mb-1 flex items-center justify-between text-slate-600">
                      <span className="font-medium">{dim.label}</span>
                      <span className="font-semibold text-slate-900">{dim.value}%</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-blue-600" style={{ width: `${dim.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Benchmarking and Appetite */}
            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-100 text-sm">
              <div className="rounded-md bg-slate-50 p-2 border border-slate-200">
                <div className="text-xs font-semibold text-slate-500">Industry Average</div>
                <div className="text-lg font-bold text-slate-800">{maturity?.benchmark.industry_average}%</div>
                <div className="text-[10px] text-slate-500">Peer Percentile: {maturity?.benchmark.peer_percentile}th</div>
              </div>

              <div className="rounded-md bg-slate-50 p-2 border border-slate-200">
                <div className="text-xs font-semibold text-slate-500">Risk Appetite Alignment</div>
                <div className="text-lg font-bold text-slate-800">{maturity?.appetite_alignment}</div>
                <div className="text-[10px] text-slate-500">Derived from risk exposure & SLA breaches</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 2: Top Executive Priorities */}
      <div className="no-print space-y-3">
        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Sliders className="h-5 w-5 text-blue-600" />
          Top Executive Priorities
        </h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {priorities.map((item, idx) => (
            <Card key={idx} className={`border-l-4 ${getSeverityColor(item.severity)}`}>
              <CardHeader className="p-4 pb-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider">{item.severity}</span>
                  <div className="rounded-full bg-slate-900 text-white font-extrabold text-xs px-2 py-0.5">
                    Score: {item.priority_score}
                  </div>
                </div>
                <CardTitle className="text-sm font-semibold text-slate-800 mt-2">{item.title}</CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-0 text-xs text-slate-600 space-y-2">
                <p className="font-medium text-slate-700">{item.reason}</p>
                <div className="pt-2 border-t border-slate-200/50">
                  <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px] block">Impact Exposure</span>
                  <span className="text-slate-700">{item.impact}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Row 3: Briefing & Trends side-by-side */}
      <div className="no-print grid gap-6 lg:grid-cols-2">
        {/* Executive briefing */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle>Executive Briefing Summary</CardTitle>
            <CardDescription>Board-ready overview of digital portfolio governance.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto max-h-[350px] space-y-4 text-sm text-slate-700">
            {briefing ? (
              <div className="space-y-4 leading-relaxed">
                <div>
                  <h4 className="font-bold text-slate-900 border-b border-slate-100 pb-1 mb-1">Executive Summary</h4>
                  <p>{briefing.executive_summary}</p>
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 border-b border-slate-100 pb-1 mb-1">Current State</h4>
                  <p>{briefing.current_state}</p>
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 border-b border-slate-100 pb-1 mb-1">Key Portfolio Risks</h4>
                  <p>{briefing.key_risks}</p>
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 border-b border-slate-100 pb-1 mb-1">Operational Concerns</h4>
                  <p>{briefing.operational_concerns}</p>
                </div>
              </div>
            ) : (
              <p className="text-slate-400">Loading briefing summary...</p>
            )}
          </CardContent>
        </Card>

        {/* Governance Trends Chart */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle>Governance & SLA Trends</CardTitle>
            <CardDescription>Chronological 30-day view of health, maturity, and risk exposure.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-between">
            {trends.length > 0 ? (
              <>
                <SVGLineChart
                  data={trends}
                  dataKeys={["health_score", "maturity_score"]}
                  colors={["#10b981", "#3b82f6"]}
                />
                <div className="flex justify-center gap-6 text-xs font-semibold mt-4 text-slate-600">
                  <div className="flex items-center gap-1.5">
                    <div className="h-3 w-3 bg-emerald-500 rounded-full" />
                    Health Score
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="h-3 w-3 bg-blue-500 rounded-full" />
                    Maturity Score
                  </div>
                </div>
              </>
            ) : (
              <div className="flex h-48 items-center justify-center text-slate-400">Loading trend engine data...</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 4: Root Cause & Portfolio Recs */}
      <div className="no-print grid gap-6 lg:grid-cols-2">
        {/* Root Cause Analytics */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle>Root Cause & Risk Categories</CardTitle>
            <CardDescription>Vulnerabilities and failures grouped by functional domain.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 space-y-4">
            {rca ? (
              <div className="space-y-3">
                {Object.keys(rca.category_distribution).map((cat) => {
                  const count = rca.category_distribution[cat];
                  const riskScore = rca.category_risk_scores[cat] || 0;
                  const maxCount = Math.max(...Object.values(rca.category_distribution), 1);
                  const widthPercent = (count / maxCount) * 100;
                  
                  return (
                    <div key={cat} className="text-xs">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-semibold text-slate-800">{cat}</span>
                        <div className="flex gap-2">
                          <span className="text-slate-500">{count} item(s)</span>
                          {riskScore > 0 && (
                            <span className="font-bold text-red-600">Risk: {riskScore}</span>
                          )}
                        </div>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className={`h-full rounded-full ${cat === "AI Governance" ? "bg-purple-600" : cat === "Security" ? "bg-red-600" : "bg-slate-600"}`}
                          style={{ width: `${widthPercent}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-slate-400">Loading category distributions...</p>
            )}
          </CardContent>
        </Card>

        {/* Portfolio recommendations */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle>Strategic Recommendations</CardTitle>
            <CardDescription>AI-generated governance advisory guidelines.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 space-y-4 overflow-y-auto max-h-[350px]">
            {recs ? (
              <div className="space-y-4 text-xs">
                <div>
                  <h4 className="font-bold text-slate-900 flex items-center gap-1.5 mb-1.5 uppercase text-[10px] tracking-wider text-emerald-700">
                    <CheckCircle className="h-3.5 w-3.5" />
                    Quick Wins
                  </h4>
                  <ul className="list-disc pl-4 space-y-1 text-slate-700">
                    {recs.quick_wins.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-bold text-slate-900 flex items-center gap-1.5 mb-1.5 uppercase text-[10px] tracking-wider text-blue-700">
                    <Activity className="h-3.5 w-3.5" />
                    Medium-Term Actions
                  </h4>
                  <ul className="list-disc pl-4 space-y-1 text-slate-700">
                    {recs.medium_term.map((m, idx) => (
                      <li key={idx}>{m}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-bold text-slate-900 flex items-center gap-1.5 mb-1.5 uppercase text-[10px] tracking-wider text-purple-700">
                    <Sparkles className="h-3.5 w-3.5" />
                    Strategic Initiatives
                  </h4>
                  <ul className="list-disc pl-4 space-y-1 text-slate-700">
                    {recs.strategic.map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="text-slate-400">Loading portfolio advisor...</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 5: AI Copilot panel */}
      <Card className="no-print">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-600 animate-pulse" />
            <div>
              <CardTitle>Governance Executive Copilot</CardTitle>
              <CardDescription>Role-aware natural language helper powered by consolidated intelligence statistics.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Chat history */}
          <div className="rounded-md border border-slate-200 bg-slate-50/50 p-4 h-64 overflow-y-auto space-y-3">
            {copilotHistory.map((chat, idx) => (
              <div
                key={idx}
                className={`flex ${chat.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 text-sm leading-relaxed ${
                    chat.sender === "user"
                      ? "bg-purple-600 text-white"
                      : "bg-white border border-slate-200 text-slate-800 shadow-sm"
                  }`}
                  style={{ whiteSpace: "pre-wrap" }}
                >
                  {chat.text}
                </div>
              </div>
            ))}
            {isCopilotLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 text-slate-400 rounded-lg p-3 text-sm flex items-center gap-2">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Analyzing governance catalog...
                </div>
              </div>
            )}
          </div>

          {/* Preset Buttons */}
          <div className="flex flex-wrap gap-2">
            {presetQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleCopilotSend(q)}
                disabled={isCopilotLoading}
                className="text-[11px] font-semibold bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 rounded-full px-3 py-1 transition-all"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input field */}
          <div className="flex gap-2">
            <input
              type="text"
              value={copilotQuery}
              onChange={(e) => setCopilotQuery(e.target.value)}
              placeholder="Ask anything about RAID risks, mitigations, escalations, or health scores..."
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-600"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCopilotSend();
              }}
            />
            <Button
              className="bg-purple-600 hover:bg-purple-700 text-white flex items-center gap-1.5"
              onClick={() => handleCopilotSend()}
              disabled={isCopilotLoading || !copilotQuery.trim()}
            >
              <Send className="h-4 w-4" />
              Ask
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Board Pack Print Preview Modal */}
      {isPreviewingPrint && (
        <div className="no-print fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col">
            <div className="border-b border-slate-200 p-4 flex items-center justify-between bg-slate-50">
              <h3 className="font-bold text-slate-800 flex items-center gap-2">
                <Printer className="h-5 w-5 text-blue-600" />
                Board Pack Document Preview
              </h3>
              <div className="flex gap-2">
                <Button onClick={handlePrint} className="bg-blue-600 hover:bg-blue-700 text-white">
                  Print / Save PDF
                </Button>
                <Button variant="outline" onClick={() => setIsPreviewingPrint(false)}>
                  Close
                </Button>
              </div>
            </div>

            <div className="p-8 flex-1 board-pack-print-container">
              {/* Premium Print Layout Header */}
              <div className="border-b-4 border-slate-900 pb-4 mb-6 text-center">
                <h1 className="text-3xl font-extrabold text-slate-950 uppercase tracking-tight">Executive Board Pack</h1>
                <p className="text-sm text-slate-500 font-semibold uppercase tracking-wider mt-1">
                  Governance Intelligence & Risk Report
                </p>
              </div>

              {/* Score summary in print */}
              <div className="grid grid-cols-3 gap-6 mb-6">
                <div className="border border-slate-200 rounded-md p-4 text-center bg-slate-50/50">
                  <span className="text-xs text-slate-500 font-bold uppercase block mb-1">Health Score</span>
                  <span className="text-3xl font-extrabold text-emerald-600">{healthInfo?.health_score ?? "..."}</span>
                  <span className="text-[10px] text-slate-400 block mt-1">Compliance index</span>
                </div>
                <div className="border border-slate-200 rounded-md p-4 text-center bg-slate-50/50">
                  <span className="text-xs text-slate-500 font-bold uppercase block mb-1">Maturity Level</span>
                  <span className="text-2xl font-extrabold text-blue-600 mt-1 inline-block">
                    {maturity?.score ?? "..."} ({maturity?.tier ?? "..."})
                  </span>
                </div>
                <div className="border border-slate-200 rounded-md p-4 text-center bg-slate-50/50">
                  <span className="text-xs text-slate-500 font-bold uppercase block mb-1">Risk Appetite</span>
                  <span className="text-xl font-extrabold text-slate-800">{maturity?.appetite_alignment}</span>
                </div>
              </div>

              {/* Briefing text */}
              <div className="space-y-6 text-xs text-slate-800">
                <div className="border border-slate-200 rounded-md p-4 bg-slate-50/20">
                  <h3 className="font-extrabold text-slate-950 uppercase mb-2 border-b border-slate-200 pb-1">1. Executive Summary</h3>
                  <p className="leading-relaxed">{briefing?.executive_summary}</p>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div className="border border-slate-200 rounded-md p-4">
                    <h3 className="font-extrabold text-slate-950 uppercase mb-2 border-b border-slate-200 pb-1">2. Current State</h3>
                    <p className="leading-relaxed">{briefing?.current_state}</p>
                  </div>
                  <div className="border border-slate-200 rounded-md p-4">
                    <h3 className="font-extrabold text-slate-950 uppercase mb-2 border-b border-slate-200 pb-1">3. Operational SLA Status</h3>
                    <p className="leading-relaxed">{briefing?.operational_concerns}</p>
                  </div>
                </div>

                {/* Priorities Table */}
                <div className="border border-slate-200 rounded-md p-4">
                  <h3 className="font-extrabold text-slate-950 uppercase mb-3 border-b border-slate-200 pb-1">4. Critical Corporate Priorities</h3>
                  <table className="w-full text-[10px] text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-300 font-bold text-slate-700 bg-slate-50">
                        <th className="py-2 px-1">Priority Title</th>
                        <th className="py-2 px-1">Severity</th>
                        <th className="py-2 px-1">Count</th>
                        <th className="py-2 px-1">Score</th>
                        <th className="py-2 px-1">Remediation Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {priorities.slice(0, 3).map((p, idx) => (
                        <tr key={idx} className="border-b border-slate-100">
                          <td className="py-2 px-1 font-semibold text-slate-900">{p.title}</td>
                          <td className="py-2 px-1">{p.severity}</td>
                          <td className="py-2 px-1">{p.count}</td>
                          <td className="py-2 px-1 font-bold">{p.priority_score}</td>
                          <td className="py-2 px-1 text-slate-600">{p.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Recommendations */}
                <div className="grid grid-cols-2 gap-6">
                  <div className="border border-slate-200 rounded-md p-4">
                    <h3 className="font-extrabold text-slate-950 uppercase mb-2 border-b border-slate-200 pb-1">5. Strategic Recommendations</h3>
                    {recs ? (
                      <ul className="list-disc pl-4 space-y-1 mt-2">
                        {recs.quick_wins.slice(0, 1).map((w, i) => <li key={i}>{w} (Quick Win)</li>)}
                        {recs.medium_term.slice(0, 1).map((m, i) => <li key={i}>{m} (Medium Term)</li>)}
                        {recs.strategic.slice(0, 1).map((s, i) => <li key={i}>{s} (Strategic)</li>)}
                      </ul>
                    ) : (
                      <p>Loading advisor...</p>
                    )}
                  </div>
                  <div className="border border-slate-200 rounded-md p-4">
                    <h3 className="font-extrabold text-slate-950 uppercase mb-2 border-b border-slate-200 pb-1">6. 30-Day Outlook</h3>
                    <p className="leading-relaxed mt-2">{briefing?.next_30_days}</p>
                  </div>
                </div>
              </div>

              {/* Premium Printable Footer Layout */}
              <div className="border-t-2 border-slate-900 pt-3 mt-8 flex items-center justify-between text-[9px] font-semibold text-slate-500 uppercase tracking-wider">
                <div>Generated: {new Date().toISOString().slice(0, 10)}</div>
                <div>Tenant: Enterprise Demo Organization</div>
                <div>Health Score: {healthInfo?.health_score ?? "..."}</div>
                <div>Maturity Tier: {maturity?.tier ?? "..."}</div>
                <div>Generated By: Governance Intelligence Platform</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function total(items: any[]) {
  return items.reduce((sum, item) => sum + item.count, 0);
}

function SVGLineChart({
  data,
  dataKeys,
  colors,
}: {
  data: any[];
  dataKeys: string[];
  colors: string[];
}) {
  if (!data || data.length === 0) return <div className="text-xs text-slate-400">No data available</div>;

  const width = 500;
  const height = 200;
  const padding = 35;

  const maxX = data.length - 1;
  
  let maxY = 100;
  dataKeys.forEach(key => {
    data.forEach(item => {
      if (item[key] > maxY) maxY = item[key];
    });
  });
  maxY = Math.ceil(maxY * 1.1);

  const pointsForKeys = dataKeys.map((key) => {
    return data.map((item, index) => {
      const x = padding + (index / maxX) * (width - padding * 2);
      const y = height - padding - (item[key] / maxY) * (height - padding * 2);
      return { x, y, val: item[key] };
    });
  });

  return (
    <div className="relative w-full overflow-hidden">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
        {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
          const y = padding + pct * (height - padding * 2);
          const val = Math.round(maxY * (1 - pct));
          return (
            <g key={idx}>
              <line
                x1={padding}
                y1={y}
                x2={width - padding}
                y2={y}
                className="stroke-slate-100"
                strokeWidth={1}
                strokeDasharray="4 4"
              />
              <text
                x={padding - 5}
                y={y + 4}
                className="fill-slate-400 text-[10px]"
                textAnchor="end"
              >
                {val}
              </text>
            </g>
          );
        })}

        {[0, 0.5, 1].map((pct, idx) => {
          const index = Math.round(pct * maxX);
          const item = data[index];
          if (!item) return null;
          const x = padding + pct * (width - padding * 2);
          return (
            <text
              key={idx}
              x={x}
              y={height - padding + 15}
              className="fill-slate-400 text-[10px]"
              textAnchor={pct === 0 ? "start" : pct === 1 ? "end" : "middle"}
            >
              {item.date}
            </text>
          );
        })}

        {pointsForKeys.map((points, lineIdx) => {
          const pathD = points
            .map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`)
            .join(" ");
            
          return (
            <g key={lineIdx}>
              <path
                d={pathD}
                fill="none"
                stroke={colors[lineIdx]}
                strokeWidth={2.5}
                className="transition-all duration-300"
              />
              {points.map((p, idx) => {
                if (idx % 5 !== 0 && idx !== maxX) return null;
                return (
                  <circle
                    key={idx}
                    cx={p.x}
                    cy={p.y}
                    r={3}
                    className="fill-white stroke-2"
                    stroke={colors[lineIdx]}
                  />
                );
              })}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
