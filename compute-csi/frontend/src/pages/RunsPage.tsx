import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { PlayCircle, RefreshCw, ChevronLeft, ChevronRight, Eye } from 'lucide-react';

import { getRuns } from '../api/runs';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { usePolling } from '../hooks/usePolling';

export function RunsPage() {
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['runs', page],
    queryFn: () => getRuns(page, pageSize),
  });

  const hasActive = data?.items.some((r) => r.status === 'RUNNING' || r.status === 'PENDING') ?? false;
  usePolling(refetch, 3000, hasActive);

  return (
    <div className="p-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-csi-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
            <PlayCircle className="w-6 h-6 text-csi-cyan" /> Workload Execution Records
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Authoritative history of all scheduled inference workflows and temporal activity executions.
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
            className="px-4 py-1.5 bg-csi-cyan text-csi-dark font-semibold text-xs rounded hover:bg-cyan-400 transition"
          >
            + New Run
          </Link>
        </div>
      </div>

      {isLoading ? (
        <div className="py-20 flex justify-center">
          <LoadingSpinner message="Querying execution ledger..." />
        </div>
      ) : error ? (
        <ErrorState
          title="Failed to Load Executions"
          message={(error as Error).message}
          onRetry={() => refetch()}
        />
      ) : data?.items.length === 0 ? (
        <EmptyState
          title="No Workload Runs Found"
          message="No workloads have been dispatched yet. Launch one from the Workloads console."
          actionLabel="Launch Workload"
          onAction={() => window.location.assign('/workloads')}
        />
      ) : (
        <div className="space-y-4">
          <div className="card overflow-hidden p-0 border border-csi-border">
            <table className="w-full text-left text-xs">
              <thead className="bg-csi-dark/80 border-b border-csi-border text-gray-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4 font-semibold">Run ID</th>
                  <th className="py-3 px-4 font-semibold">Temporal Workflow ID</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Attempts</th>
                  <th className="py-3 px-4 font-semibold">Duration</th>
                  <th className="py-3 px-4 font-semibold">Dispatched</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-csi-border/40 font-mono">
                {data?.items.map((run) => (
                  <tr key={run.run_id} className="hover:bg-csi-dark/40 transition">
                    <td className="py-3 px-4 font-bold text-white">
                      <Link to={`/runs/${run.run_id}`} className="hover:text-csi-cyan">
                        {run.run_id.slice(0, 8)}...
                      </Link>
                    </td>
                    <td className="py-3 px-4 text-gray-400 truncate max-w-[200px]" title={run.workflow_id}>
                      {run.workflow_id}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="py-3 px-4 text-gray-300">
                      {run.attempt_count}
                      {run.failure_count > 0 && (
                        <span className="text-red-400 ml-1.5 font-bold">
                          ({run.failure_count} fail)
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-gray-300">
                      {run.duration_seconds != null ? `${run.duration_seconds.toFixed(2)}s` : '—'}
                    </td>
                    <td className="py-3 px-4 text-gray-500 text-[11px]">
                      {run.start_time ? new Date(run.start_time).toLocaleString() : '—'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/runs/${run.run_id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 bg-csi-surface border border-csi-border hover:border-csi-cyan text-[11px] text-csi-cyan rounded transition"
                      >
                        <Eye className="w-3 h-3" /> Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between text-xs text-gray-400">
              <div>
                Showing page {data.page} of {data.total_pages} ({data.total} total runs)
              </div>
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="p-1.5 rounded bg-csi-surface border border-csi-border disabled:opacity-40"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={page >= data.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                  className="p-1.5 rounded bg-csi-surface border border-csi-border disabled:opacity-40"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
