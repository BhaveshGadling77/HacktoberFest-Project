import { useQuery } from '@tanstack/react-query';
import {
  Server,
  Activity,
  Flame,
  Cpu,
  Cloud,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  Terminal,
} from 'lucide-react';

import { getIntegrationsStatus } from '../api/metrics';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';

export function IntegrationsPage() {
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['integrations-status'],
    queryFn: getIntegrationsStatus,
  });

  if (isLoading) {
    return (
      <div className="py-20 flex justify-center">
        <LoadingSpinner message="Probing integration endpoints and discovery APIs..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8">
        <ErrorState
          title="Failed to Probe Integrations"
          message={error ? (error as Error).message : 'Status query failed.'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  const integrations = [
    {
      id: 'temporal',
      name: 'Temporal Workflow Orchestration',
      icon: Server,
      connected: data.temporal.connected,
      details: [
        { label: 'Address', value: data.temporal.address || 'localhost:7233' },
        { label: 'Namespace', value: data.temporal.namespace || 'default' },
        { label: 'Task Queue', value: data.temporal.task_queue || 'compute-csi-queue' },
      ],
      error: data.temporal.error,
      setupHelp: 'Run `temporal server start-dev` or start via docker-compose (`make dev-start`).',
    },
    {
      id: 'prometheus',
      name: 'Prometheus Time Series Database',
      icon: Activity,
      connected: data.prometheus.connected,
      details: [
        { label: 'Server URL', value: data.prometheus.url || 'http://localhost:9090' },
      ],
      error: data.prometheus.error,
      setupHelp: 'Ensure Prometheus is running at the configured URL or start with docker compose.',
    },
    {
      id: 'kepler',
      name: 'Kepler Energy Profiler (eBPF)',
      icon: Flame,
      connected: data.kepler.connected,
      details: [
        {
          label: 'Discovered Metrics',
          value:
            data.kepler.available_metrics && data.kepler.available_metrics.length > 0
              ? data.kepler.available_metrics.join(', ')
              : 'None detected',
        },
      ],
      error: data.kepler.error,
      setupHelp:
        'Kepler requires a Kubernetes cluster with Linux kernel eBPF support and RAPL energy counters. In pure local Docker, energy telemetry honestly reports unavailable.',
    },
    {
      id: 'gemma',
      name: 'Gemma 2 Model Serving Adapter',
      icon: Cpu,
      connected: data.gemma.connected,
      details: [
        { label: 'Model Tag', value: data.gemma.model || 'gemma2-2b-it' },
        { label: 'Endpoint', value: data.gemma.endpoint || 'Not configured' },
      ],
      error: data.gemma.error,
      setupHelp:
        'Configure GEMMA_ENDPOINT and GEMMA_API_KEY in .env. When unconfigured, Compute CSI runs deterministic forensics fallback.',
    },
    {
      id: 'jarvislabs',
      name: 'JarvisLabs Remote GPU Cluster',
      icon: Cloud,
      connected: data.jarvislabs.connected,
      details: [
        { label: 'Instance URL', value: data.jarvislabs.instance_url || 'Not configured' },
      ],
      error: data.jarvislabs.error,
      setupHelp:
        'Configure JARVISLABS_API_KEY and JARVISLABS_INSTANCE_URL for remote GPU execution. Local CPU inference is available without credentials.',
    },
  ];

  return (
    <div className="p-8 space-y-6 max-w-5xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-csi-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
            Integration Connectivity Matrix
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time live probe results for orchestrators, metric scrapers, model endpoints, and accelerators.
          </p>
        </div>
        <div>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-csi-surface border border-csi-border hover:border-csi-cyan text-xs text-gray-300 rounded transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-csi-cyan' : ''}`} />
            Re-probe Subsystems
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {integrations.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.id} className="card space-y-3">
              <div className="flex items-center justify-between border-b border-csi-border pb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded ${item.connected ? 'bg-green-950/40 text-green-400' : 'bg-gray-800 text-gray-400'}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-white">{item.name}</h2>
                    <span className="text-[11px] font-mono text-gray-400">{item.id}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {item.connected ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-green-900/40 border border-green-800 text-green-400 text-xs font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5" /> ONLINE & VERIFIED
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-gray-800 border border-gray-700 text-gray-400 text-xs font-semibold">
                      <XCircle className="w-3.5 h-3.5 text-gray-500" /> DISCONNECTED / FALLBACK
                    </span>
                  )}
                </div>
              </div>

              {/* Details table */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
                {item.details.map((d, i) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded bg-csi-dark/50">
                    <span className="text-gray-500">{d.label}:</span>
                    <span className="text-gray-200 font-medium truncate max-w-[280px]" title={d.value}>
                      {d.value}
                    </span>
                  </div>
                ))}
              </div>

              {/* Error or Disconnected Notice */}
              {item.error && (
                <div className="p-2.5 rounded bg-red-950/30 border border-red-900/40 text-xs text-red-300">
                  <strong>Notice:</strong> {item.error}
                </div>
              )}

              {/* Setup Guidance */}
              {!item.connected && (
                <div className="p-2.5 rounded bg-csi-dark/70 border border-csi-border text-[11px] text-gray-400 flex items-start gap-2">
                  <Terminal className="w-4 h-4 text-csi-cyan flex-shrink-0 mt-0.5" />
                  <span>{item.setupHelp}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
