import { Link } from 'react-router-dom';
import { Server, Activity, Flame, Cpu, Cloud, ChevronRight } from 'lucide-react';
import { IntegrationBadge } from '../common/IntegrationBadge';
import type { IntegrationsStatus } from '../../types';

interface Props {
  health: IntegrationsStatus;
}

export function IntegrationHealth({ health }: Props) {
  const items = [
    {
      name: 'Temporal Orchestrator',
      icon: Server,
      status: health.temporal,
      desc: health.temporal?.connected ? health.temporal.address : 'Unreachable or stopped',
    },
    {
      name: 'Prometheus TSDB',
      icon: Activity,
      status: health.prometheus,
      desc: health.prometheus?.connected ? health.prometheus.url : 'Unreachable or stopped',
    },
    {
      name: 'Kepler Energy Profiler',
      icon: Flame,
      status: health.kepler,
      desc: health.kepler?.connected
        ? `${health.kepler.available_metrics?.length || 0} metrics active`
        : health.kepler?.scrape_targets?.length
          ? health.kepler.scrape_targets.some((target) => target.up)
            ? 'Scraped; no energy metrics'
            : 'Prometheus target is DOWN'
          : 'No scrape target configured',
    },
    {
      name: 'Gemma AI Engine',
      icon: Cpu,
      status: health.gemma,
      desc: health.gemma?.connected ? health.gemma.model : 'Optional local/remote model',
    },
    {
      name: 'JarvisLabs Remote GPU',
      icon: Cloud,
      status: health.jarvislabs,
      desc: health.jarvislabs?.connected ? 'Remote cluster ready' : 'Not configured (CPU fallback)',
    },
  ];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">
          Integration Health Matrix
        </h3>
        <Link
          to="/integrations"
          className="text-xs text-csi-cyan hover:underline flex items-center gap-1"
        >
          View Diagnostics <ChevronRight className="w-3 h-3" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        {items.map((item) => {
          const Icon = item.icon;
          const isConn = item.status?.connected ?? false;
          return (
            <div
              key={item.name}
              className="p-3 bg-csi-dark/60 rounded border border-csi-border flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Icon className={`w-4 h-4 ${isConn ? 'text-csi-cyan' : 'text-gray-500'}`} />
                  <IntegrationBadge connected={isConn} />
                </div>
                <div className="text-xs font-medium text-white truncate">{item.name}</div>
              </div>
              <div className="text-[11px] text-gray-400 mt-2 truncate" title={item.desc}>
                {item.desc}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
