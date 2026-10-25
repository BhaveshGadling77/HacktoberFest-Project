import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { AlertCircle } from 'lucide-react';
import type { MetricSeries } from '../../types';

interface Props {
  series: MetricSeries;
  color?: string;
  title?: string;
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
}

export function MetricsChart({ series, color = '#06b6d4', title }: Props) {
  if (!series.available) {
    return (
      <div className="flex flex-col items-center justify-center h-40 gap-2 text-center">
        <AlertCircle className="w-8 h-8 text-gray-700" />
        <p className="text-sm text-gray-500">Data unavailable</p>
        {series.unavailability_reason && (
          <p className="text-xs text-gray-600 max-w-xs">{series.unavailability_reason}</p>
        )}
      </div>
    );
  }

  const chartData = series.points.map((p) => ({
    time: formatTime(p.timestamp),
    value: p.value,
  }));

  return (
    <div>
      {title && (
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium text-gray-300">{title}</p>
          <span className="text-xs text-gray-500">{series.unit}</span>
        </div>
      )}
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${series.name}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="time" stroke="#374151" tick={{ fill: '#6b7280', fontSize: 10 }} />
          <YAxis stroke="#374151" tick={{ fill: '#6b7280', fontSize: 10 }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '6px', fontSize: '12px' }}
            labelStyle={{ color: '#9ca3af' }}
            itemStyle={{ color }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#grad-${series.name})`}
            dot={false}
            activeDot={{ r: 4, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
