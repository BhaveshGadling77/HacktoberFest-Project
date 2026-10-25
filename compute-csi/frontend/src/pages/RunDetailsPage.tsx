import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  PlayCircle,
  Clock,
  RotateCcw,
  AlertTriangle,
  StopCircle,
  RefreshCw,
  Search,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

import { getRun, cancelRun, getRunMetrics } from '../api/runs';
import { createIncidentForRun } from '../api/incidents';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';
import { ExecutionTimeline } from '../components/timeline/ExecutionTimeline';
import { MetricsChart } from '../components/metrics/MetricsChart';
import { usePolling } from '../hooks/usePolling';

export function RunDetailsPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    data: run,
    isLoading: runLoading,
    error: runError,
    refetch: refetchRun,
    isFetching,
  } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => getRun(runId!),
    enabled: !!runId,
  });

  const {
    data: metrics,
    isLoading: metricsLoading,
    refetch: refetchMetrics,
  } = useQuery({
    queryKey: ['run-metrics', runId],
    queryFn: () => getRunMetrics(runId!),
    enabled: !!runId,
  });

  const isRunning = run?.status === 'RUNNING' || run?.status === 'PENDING';
  usePolling(() => {
    refetchRun();
    refetchMetrics();
  }, 2500, isRunning);

  const cancelMutation = useMutation({
    mutationFn: () => cancelRun(runId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['run', runId] });
    },
  });

  const investigateMutation = useMutation({
    mutationFn: () => createIncidentForRun(runId!),
    onSuccess: (report) => {
      navigate(`/incidents/${report.incident_id}`);
    },
  });

  if (runLoading) {
    return (
      <div className="py-20 flex justify-center">
        <LoadingSpinner message="Retrieving execution ledger and Temporal history..." />
      </div>
    );
  }

  if (runError || !run) {
    return (
      <div className="p-8">
        <ErrorState
          title="Execution Record Not Found"
          message={runError ? (runError as Error).message : 'Run record could not be loaded.'}
          onRetry={() => refetchRun()}
        />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-csi-border pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link to="/runs" className="text-xs text-csi-cyan hover:underline">
              ← Executions
            </Link>
            <span className="text-xs text-gray-500">/</span>
            <span className="text-xs font-mono text-gray-400">{run.run_id}</span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-3">
            <span>Run #{run.run_id.slice(0, 8)}</span>
            <StatusBadge status={run.status} />
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              refetchRun();
              refetchMetrics();
            }}
            disabled={isFetching}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-csi-surface border border-csi-border hover:border-csi-cyan text-xs text-gray-300 rounded transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-csi-cyan' : ''}`} />
            Refresh
          </button>

          {isRunning && (
            <button
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-950/60 border border-red-700 hover:border-red-500 text-xs text-red-300 rounded transition"
            >
              <StopCircle className="w-3.5 h-3.5" />
              Cancel Run
            </button>
          )}

          <button
            onClick={() => investigateMutation.mutate()}
            disabled={investigateMutation.isPending}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-csi-cyan text-csi-dark font-bold text-xs rounded hover:bg-cyan-400 transition"
          >
            <Search className="w-3.5 h-3.5" />
            {investigateMutation.isPending ? 'Investigating...' : 'Investigate Run'}
          </button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="card">
          <div className="text-[11px] text-gray-500 uppercase">Temporal Workflow</div>
          <div className="text-xs font-mono text-white truncate mt-1" title={run.workflow_id}>
            {run.workflow_id}
          </div>
        </div>

        <div className="card">
          <div className="text-[11px] text-gray-500 uppercase">Workload Spec</div>
          <div className="text-xs font-mono text-white mt-1">
            {run.workload_type} ({run.execution_mode})
          </div>
        </div>

        <div className="card">
          <div className="text-[11px] text-gray-500 uppercase">Fault Scenario</div>
          <div className="text-xs font-mono text-yellow-400 mt-1">
            {run.fault_scenario}
          </div>
        </div>

        <div className="card">
          <div className="text-[11px] text-gray-500 uppercase">Duration</div>
          <div className="text-xs font-mono text-white mt-1">
            {run.duration_seconds != null ? `${run.duration_seconds.toFixed(2)}s` : 'Active'}
          </div>
        </div>

        <div className="card">
          <div className="text-[11px] text-gray-500 uppercase">Attempts</div>
          <div className="text-xs font-mono text-white mt-1">
            {run.attempt_count} attempt(s)
          </div>
        </div>

        <div className="card">
          <div className="text-[11px] text-gray-500 uppercase">Failures</div>
          <div className="text-xs font-mono text-red-400 mt-1">
            {run.failure_count} failure(s)
          </div>
        </div>
      </div>

      {/* Main Forensic Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Execution Timeline */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4 text-csi-cyan" /> Temporal Execution Timeline
          </h2>
          <ExecutionTimeline events={run.timeline || []} />
        </div>

        {/* Right: Metrics & Telemetry */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider mb-4">
              CPU Utilization Telemetry
            </h2>
            {metricsLoading ? (
              <LoadingSpinner message="Querying Prometheus..." />
            ) : metrics ? (
              <MetricsChart series={metrics.cpu_percent} />
            ) : (
              <div className="text-xs text-gray-500">No telemetry available</div>
            )}
          </div>

          <div className="card">
            <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider mb-4">
              Kepler Energy Telemetry
            </h2>
            {metricsLoading ? (
              <LoadingSpinner message="Querying Kepler..." />
            ) : metrics ? (
              <MetricsChart series={metrics.energy_joules} />
            ) : (
              <div className="text-xs text-gray-500">No energy metrics available</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
