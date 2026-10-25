import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { AlertTriangle, RefreshCw, ChevronLeft, ChevronRight, Eye, ShieldAlert } from 'lucide-react';

import { getIncidents } from '../api/incidents';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import type { Severity } from '../types';

export function IncidentsPage() {
  const [page, setPage] = useState<number>(1);
  const [severityFilter, setSeverityFilter] = useState<Severity | undefined>(undefined);
  const pageSize = 15;

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['incidents', page, severityFilter],
    queryFn: () => getIncidents({ page, page_size: pageSize, severity: severityFilter }),
  });

  return (
    <div className="p-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-csi-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-yellow-400" /> Forensic Incident Ledger
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Catalogue of detected infrastructure anomalies, activity retry cascades, and forensic dossiers.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Severity Filter */}
          <select
            value={severityFilter || ''}
            onChange={(e) => {
              setSeverityFilter(e.target.value ? (e.target.value as Severity) : undefined);
              setPage(1);
            }}
            className="bg-csi-surface border border-csi-border rounded px-3 py-1.5 text-xs text-gray-300 font-mono focus:border-csi-cyan focus:outline-none"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>

          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-csi-surface border border-csi-border hover:border-csi-cyan text-xs text-gray-300 rounded transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-csi-cyan' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="py-20 flex justify-center">
          <LoadingSpinner message="Auditing forensic incident registry..." />
        </div>
      ) : error ? (
        <ErrorState
          title="Failed to Load Incidents"
          message={(error as Error).message}
          onRetry={() => refetch()}
        />
      ) : data?.items.length === 0 ? (
        <EmptyState
          title="No Incidents Logged"
          message="No anomalous executions or infrastructure deviations meet the current filter criteria."
        />
      ) : (
        <div className="space-y-4">
          <div className="card overflow-hidden p-0 border border-csi-border">
            <table className="w-full text-left text-xs">
              <thead className="bg-csi-dark/80 border-b border-csi-border text-gray-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4 font-semibold">Incident ID</th>
                  <th className="py-3 px-4 font-semibold">Title</th>
                  <th className="py-3 px-4 font-semibold">Severity</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Anomalies Detected</th>
                  <th className="py-3 px-4 font-semibold">Detected At</th>
                  <th className="py-3 px-4 text-right">Dossier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-csi-border/40 font-mono">
                {data?.items.map((inc) => (
                  <tr key={inc.incident_id} className="hover:bg-csi-dark/40 transition">
                    <td className="py-3 px-4 font-bold text-white">
                      <Link to={`/incidents/${inc.incident_id}`} className="hover:text-csi-cyan">
                        {inc.incident_id.slice(0, 8)}...
                      </Link>
                    </td>
                    <td className="py-3 px-4 text-gray-200 font-semibold truncate max-w-[280px]">
                      {inc.title}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={inc.severity} />
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[11px] bg-gray-800 text-gray-300 border border-gray-700">
                        {inc.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-400 text-[11px]">
                      {inc.finding_types.join(', ') || 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-gray-500 text-[11px]">
                      {new Date(inc.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/incidents/${inc.incident_id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 bg-csi-surface border border-csi-border hover:border-csi-cyan text-[11px] text-csi-cyan rounded transition"
                      >
                        <Eye className="w-3 h-3" /> View Report
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
                Showing page {data.page} of {data.total_pages} ({data.total} total incidents)
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
