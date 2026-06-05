import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { MeetingActionResponse } from "@/types/api";

type MeetingActionsPanelProps = {
  actions?: MeetingActionResponse[];
};

export function MeetingActionsPanel({ actions }: MeetingActionsPanelProps) {
  const hasContractField = Array.isArray(actions);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Meeting Actions</CardTitle>
        <CardDescription>Accountable actions extracted from meeting or governance workflows.</CardDescription>
      </CardHeader>
      <CardContent>
        {!hasContractField ? (
          <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
            Meeting actions are not exposed by the current report API response.
          </div>
        ) : actions.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
            No meeting actions were returned for this report.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-md border border-slate-200">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">Owner</th>
                  <th className="px-4 py-3 font-semibold">Task</th>
                  <th className="px-4 py-3 font-semibold">Due Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {actions.map((action, index) => (
                  <tr key={action.id ?? `${action.owner}-${index}`}>
                    <td className="px-4 py-3 font-medium text-slate-900">{action.owner}</td>
                    <td className="px-4 py-3 text-slate-700">{action.task}</td>
                    <td className="px-4 py-3 text-slate-600">{action.due_date ?? "Not specified"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
