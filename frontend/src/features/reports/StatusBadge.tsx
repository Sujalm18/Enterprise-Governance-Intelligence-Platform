type StatusBadgeProps = {
  status: string;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toLowerCase();
  const className =
    normalized === "approved"
      ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
      : normalized === "changes_requested"
        ? "bg-red-50 text-red-700 ring-red-200"
        : "bg-amber-50 text-amber-700 ring-amber-200";

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold capitalize ring-1 ${className}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
