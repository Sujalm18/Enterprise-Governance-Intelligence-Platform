type ConfidenceBadgeProps = {
  score: number;
};

export function ConfidenceBadge({ score }: ConfidenceBadgeProps) {
  const normalized = Math.max(0, Math.min(score, 1));
  const label = normalized >= 0.8 ? "High" : normalized >= 0.5 ? "Medium" : "Low";
  const className =
    normalized >= 0.8
      ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
      : normalized >= 0.5
        ? "bg-amber-50 text-amber-700 ring-amber-200"
        : "bg-red-50 text-red-700 ring-red-200";

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${className}`}>
      {label} {Math.round(normalized * 100)}%
    </span>
  );
}
