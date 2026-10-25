import type { RunStatus, Severity } from '../../types';

interface Props {
  status: RunStatus | Severity | string;
  className?: string;
}

const STATUS_CLASSES: Record<string, string> = {
  PENDING: 'bg-gray-800 text-gray-400 border-gray-700',
  RUNNING: 'bg-cyan-900/50 text-csi-cyan border-cyan-800',
  COMPLETED: 'bg-green-900/50 text-green-400 border-green-800',
  FAILED: 'bg-red-900/50 text-red-400 border-red-800',
  CANCELLED: 'bg-gray-800 text-gray-500 border-gray-700',
  TIMED_OUT: 'bg-orange-900/50 text-orange-400 border-orange-800',
  CRITICAL: 'bg-red-900/50 text-red-400 border-red-800',
  HIGH: 'bg-orange-900/50 text-orange-400 border-orange-800',
  MEDIUM: 'bg-yellow-900/50 text-yellow-400 border-yellow-800',
  LOW: 'bg-blue-900/50 text-blue-400 border-blue-800',
};

export function StatusBadge({ status, className = '' }: Props) {
  const classes = STATUS_CLASSES[status] ?? 'bg-gray-800 text-gray-400 border-gray-700';
  return (
    <span className={`inline-flex items-center text-xs px-2 py-0.5 rounded border font-mono ${classes} ${className}`}>
      {status}
    </span>
  );
}
