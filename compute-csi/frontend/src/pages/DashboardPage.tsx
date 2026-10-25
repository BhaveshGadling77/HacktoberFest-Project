import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  PlayCircle,
  Activity,
  AlertOctagon,
  RotateCcw,
  Zap,
  TrendingUp,
  AlertTriangle,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';

import { getDashboard } from '../api/metrics';
import { MetricCard } from '../components/common/MetricCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';
import { IntegrationHealth } from '../components/dashboard/IntegrationHealth';
import { usePolling } from '../hooks/usePolling';

export function DashboardPage() {
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
  });

  // Auto-refresh every 15 seconds if there are active runs or page is open
  usePolling(refetch, 15000, true);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <LoadingSpinner message="Loading telemetry forensics..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8">
        <ErrorState
          title="Failed to Load Telemetry Overview"
          message={error ? (error as Error).message : 'Backend unreachable.'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-csi-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
            Compute CSI Console
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time AI infrastructure forensics, workflow anomaly correlation, and root-cause analysis
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-csi-surface border border-csi-border hover:border-csi-cyan text-xs text-gray-300 rounded transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-csi-cyan' : ''}`} />
            Refresh
          </button>
          <Link
            to="/workloads"
            className="px-4 py-1.5 bg-csi-cyan text-csi-dark font-semibold text-xs rounded hover:bg-cyan-400 transition flex items-center gap-1"
          >
            <PlayCircle className="w-4 h-4" /> Launch Workload
          </Link>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard
          label="Total Runs"
          value={data.total_runs}
          icon={Activity}
        />
        <MetricCard
          label="Active Workflows"
          value={data.active_runs}
          icon={PlayCircle}
          valueClassName={data.active_runs > 0 ? 'text-csi-cyan animate-pulse' : 'text-gray-400'}
        />
        <MetricCard
          label="Failed Runs"
          value={data.failed_runs}
          icon={AlertOctagon}
          valueClassName={data.failed_runs > 0 ? 'text-red-400' : 'text-gray-400'}
        />
        <MetricCard
          label="Detected Incidents"
          value={data.detected_incidents}
          icon={AlertTriangle}
          valueClassName={data.detected_incidents > 0 ? 'text-yellow-400' : 'text-gray-400'}
        />
        <MetricCard
          label="Recorded Retries"
          value={data.total_retries}
          icon={RotateCcw}
          valueClassName={data.total_retries > 0 ? 'text-orange-400' : 'text-gray-400'}
        />
        <MetricCard
          label="Kepler Profiling"
          value={data.energy_metrics_available ? 'Active' : 'Unavail'}
          icon={Zap}
          valueClassName={data.energy_metrics_available ? 'text-green-400' : 'text-gray-500'}
        />
      </div>

      {/* Integration Health Matrix */}
      <IntegrationHealth health={data.integration_health} />

      {/* Two Column Section: Recent Runs & Incidents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Runs */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
              <PlayCircle className="w-4 h-4 text-csi-cyan" /> Recent Workload Executions
            </h2>
            <Link to="/runs" className="text-xs text-csi-cyan hover:underline flex items-center gap-1">
              View All Runs <ChevronRight className="w-3 h-3" />
            </Link>
          </div>

          {data.recent_runs.length === 0 ? (
            <div className="p-6 text-center text-xs text-gray-500 border border-dashed border-csi-border rounded">
              No runs recorded yet. Start a run from the Workloads console.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-csi-border text-gray-400">
                    <th className="pb-2 font-medium">Run ID</th>
                    <th className="pb-2 font-medium">Status</th>
                    <th className="pb-2 font-medium">Attempts</th>
                    <th className="pb-2 font-medium">Duration</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-csi-border/40">
                  {data.recent_runs.map((r) => (
                    <tr key={r.run_id} className="hover:bg-csi-dark/40 transition">
                      <td className="py-2.5 font-mono text-gray-300">
                        <Link to={`/runs/${r.run_id}`} className="hover:text-csi-cyan">
                          {r.run_id.slice(0, 8)}...
                        </Link>
                      </td>
                      <td className="py-2.5">
                        <StatusBadge status={r.status} />
                      </td>
                      <td className="py-2.5 text-gray-400">
                        {r.attempt_count} {r.failure_count > 0 && `(${r.failure_count} fail)`}
                      </td>
                      <td className="py-2.5 text-gray-400">
                        {r.duration_seconds != null ? `${r.duration_seconds.toFixed(2)}s` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Incidents */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400" /> Active Anomaly Investigations
            </h2>
            <Link to="/incidents" className="text-xs text-csi-cyan hover:underline flex items-center gap-1">
              View All Incidents <ChevronRight className="w-3 h-3" />
            </Link>
          </div>

          {data.recent_incidents.length === 0 ? (
            <div className="p-6 text-center text-xs text-gray-500 border border-dashed border-csi-border rounded">
              No anomalies detected. Workloads operating within expected baseline limits.
            </div>
          ) : (
            <div className="space-y-2">
              {data.recent_incidents.map((inc) => (
                <Link
                  key={inc.incident_id}
                  to={`/incidents/${inc.incident_id}`}
                  className="block p-3 rounded bg-csi-dark/60 border border-csi-border hover:border-csi-blue/50 transition"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-white truncate max-w-[280px]">
                      {inc.title}
                    </span>
                    <StatusBadge status={inc.severity} />
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-gray-400">
                    <span>Types: {inc.finding_types.join(', ') || 'N/A'}</span>
                    <span>•</span>
                    <span>{new Date(inc.created_at).toLocaleTimeString()}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
