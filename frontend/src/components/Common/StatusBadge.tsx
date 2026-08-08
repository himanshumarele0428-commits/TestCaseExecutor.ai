interface StatusBadgeProps {
  status: string;
}

const statusColors: Record<string, string> = {
  PASSED: 'bg-green-900/50 text-green-400 border-green-700',
  FAILED: 'bg-red-900/50 text-red-400 border-red-700',
  RUNNING: 'bg-blue-900/50 text-blue-400 border-blue-700 animate-pulse',
  PENDING: 'bg-gray-700/50 text-gray-400 border-gray-600',
  SKIPPED: 'bg-yellow-900/50 text-yellow-400 border-yellow-700',
  QUEUED: 'bg-purple-900/50 text-purple-400 border-purple-700',
  BLOCKED: 'bg-orange-900/50 text-orange-400 border-orange-700',
  ERROR: 'bg-red-900/50 text-red-400 border-red-700',
  COMPLETED: 'bg-green-900/50 text-green-400 border-green-700',
  NOT_EXECUTED: 'bg-gray-700/50 text-gray-400 border-gray-600',
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colorClass = statusColors[status] || statusColors.NOT_EXECUTED;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClass}`}>
      {status.replace('_', ' ')}
    </span>
  );
}
