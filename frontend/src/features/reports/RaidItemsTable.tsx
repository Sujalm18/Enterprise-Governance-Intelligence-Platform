import { ConfidenceBadge } from "@/features/reports/ConfidenceBadge";
import type { RaidItemResponse } from "@/types/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type RaidItemsTableProps = {
  items: RaidItemResponse[];
};

export function RaidItemsTable({ items }: RaidItemsTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>RAID Items</CardTitle>
        <CardDescription>Risks, actions, issues, and dependencies extracted from the source.</CardDescription>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyPanel message="No RAID items were extracted for this report." />
        ) : (
          <div className="overflow-x-auto rounded-md border border-slate-200">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">Type</th>
                  <th className="px-4 py-3 font-semibold">Description</th>
                  <th className="px-4 py-3 font-semibold">Severity</th>
                  <th className="px-4 py-3 font-semibold">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {items.map((item) => (
                  <tr key={item.id}>
                    <td className="whitespace-nowrap px-4 py-3 font-medium capitalize text-slate-900">
                      {item.type}
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      <div>{item.description}</div>
                      {item.source_excerpt ? (
                        <div className="mt-2 text-xs text-slate-500">Source: {item.source_excerpt}</div>
                      ) : null}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 capitalize text-slate-600">
                      {item.severity}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <ConfidenceBadge score={item.confidence_score} />
                    </td>
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

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}
