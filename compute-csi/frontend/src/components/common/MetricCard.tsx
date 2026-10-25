import type { LucideIcon } from 'lucide-react';

interface Props {
  label: string;
  value: string | number;
  unit?: string;
  icon?: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  valueClassName?: string;
}

export function MetricCard({ label, value, unit, icon: Icon, trend, trendValue, valueClassName }: Props) {
  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-gray-500',
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
        {Icon && <Icon className="w-4 h-4 text-gray-600" />}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className={`text-2xl font-bold text-white ${valueClassName ?? ''}`}>{value}</span>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
      </div>
      {trend && trendValue && (
        <p className={`text-xs mt-1 ${trendColors[trend]}`}>{trendValue}</p>
      )}
    </div>
  );
}
