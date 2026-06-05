import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function WorkflowPage() {
  return (
    <>
      <PageHeader
        eyebrow="Pipeline visibility"
        title="Workflow Tracker"
        description="Placeholder foundation for document processing status, execution logs, and report detail navigation."
      />
      <Card>
        <CardHeader>
          <CardTitle>Workflow tracker placeholder</CardTitle>
          <CardDescription>
            Report polling and processing-stage visualization will be connected later.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {["Uploaded", "Parsed", "Indexed", "AI Extraction", "Report Generated", "Review"].map((stage) => (
              <span key={stage} className="rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700">
                {stage}
              </span>
            ))}
          </div>
        </CardContent>
      </Card>
    </>
  );
}
