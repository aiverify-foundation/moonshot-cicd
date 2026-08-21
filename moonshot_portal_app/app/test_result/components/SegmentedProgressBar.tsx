export function SegmentedProgressBar({
  completed,
  errored,
  total,
}: {
  completed: number;
  errored: number;
  total: number;
}) {
  if (total <= 0) {
    return <div className="flex-1 h-4 bg-slate-200 rounded-full" />;
  }
  const completedPct = (completed / total) * 100;
  const erroredPct = (errored / total) * 100;
  return (
    <div className="flex flex-1 h-4 rounded-full overflow-hidden bg-slate-200">
      {completedPct > 0 ? (
        <div className="bg-blue-500 h-full" style={{ width: `${completedPct}%` }} />
      ) : null}
      {erroredPct > 0 ? (
        <div className="bg-red-500 h-full" style={{ width: `${erroredPct}%` }} />
      ) : null}
    </div>
  );
}
