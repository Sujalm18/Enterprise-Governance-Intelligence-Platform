import type { AuditLogResponse } from "@/types/api";

type TimelineProps = {
  logs: AuditLogResponse[];
};

export function Timeline({ logs }: TimelineProps) {
  if (logs.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
        No recent audit history. Upload a document to trigger the workflow.
      </div>
    );
  }

  return (
    <div className="flow-root">
      <ul role="list" className="-mb-8">
        {logs.map((log, logIdx) => (
          <li key={log.id}>
            <div className="relative pb-8">
              {logIdx !== logs.length - 1 ? (
                <span
                  className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-slate-200"
                  aria-hidden="true"
                />
              ) : null}
              <div className="relative flex space-x-3">
                <div>
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 ring-8 ring-white">
                    <span className="text-sm">{getIconForAction(log.action)}</span>
                  </span>
                </div>
                <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                  <div>
                    <p className="text-sm text-slate-600">
                      <span className="font-semibold text-slate-900 capitalize">
                        {log.user_role}
                      </span>{" "}
                      performed{" "}
                      <span className="font-medium text-blue-600">{log.action || log.event}</span>
                    </p>
                    {log.details ? (
                      <p className="mt-1 text-xs text-slate-500 leading-relaxed bg-slate-50 rounded p-1.5 border border-slate-100">
                        {log.details}
                      </p>
                    ) : null}
                  </div>
                  <div className="whitespace-nowrap text-right text-xs text-slate-500">
                    <time dateTime={log.timestamp}>{formatTime(log.timestamp)}</time>
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function getIconForAction(action: string): string {
  const act = (action || "").toLowerCase();
  if (act.includes("upload")) return "📤";
  if (act.includes("generation") || act.includes("ai")) return "🤖";
  if (act.includes("assign")) return "👤";
  if (act.includes("approve")) return "✅";
  if (act.includes("escalat")) return "🚨";
  if (act.includes("resolve")) return "🔧";
  if (act.includes("close")) return "🔒";
  return "📝";
}

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
