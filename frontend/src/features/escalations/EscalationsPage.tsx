import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function EscalationsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Executive action"
        title="Escalation Management"
        description="Placeholder foundation for escalation filtering, severity summaries, and stakeholder routing."
      />
      <Card>
        <CardHeader>
          <CardTitle>Escalation workspace placeholder</CardTitle>
          <CardDescription>
            Escalation listing and routing mutations will be connected after API integration begins.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {["Total", "Open", "Routed"].map((label) => (
              <div key={label} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-500">{label}</p>
                <p className="mt-3 text-2xl font-semibold text-slate-900">--</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </>
  );
}
