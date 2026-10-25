import { type LucideIcon, Inbox } from 'lucide-react';

interface Props {
  icon?: LucideIcon;
  title: string;
  description?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  message,
  actionLabel,
  onAction,
}: Props) {
  const text = message || description;
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Icon className="w-12 h-12 text-gray-700 mb-4" />
      <h3 className="text-gray-400 font-medium mb-1">{title}</h3>
      {text && <p className="text-sm text-gray-600 mb-4 max-w-sm">{text}</p>}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-1.5 bg-csi-cyan text-csi-dark font-semibold text-xs rounded hover:bg-cyan-400 transition"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
