import { CheckCircle, XCircle, Clock, AlertTriangle, Play, Cpu } from 'lucide-react';
import type { ActivityEvent } from '../../types';

interface Props {
  events: ActivityEvent[];
}

function getEventIcon(eventType: string) {
  if (eventType.includes('START') || eventType.includes('STARTED')) return Play;
  if (eventType.includes('FAIL') || eventType.includes('ERROR')) return XCircle;
  if (eventType.includes('COMPLETE') || eventType.includes('SUCCESS')) return CheckCircle;
  if (eventType.includes('TIMEOUT')) return Clock;
  if (eventType.includes('RETRY')) return AlertTriangle;
  return Cpu;
}

function getEventColor(eventType: string) {
  if (eventType.includes('FAIL') || eventType.includes('ERROR')) return 'text-red-400 border-red-800 bg-red-900/20';
  if (eventType.includes('COMPLETE') || eventType.includes('SUCCESS')) return 'text-green-400 border-green-800 bg-green-900/20';
  if (eventType.includes('TIMEOUT')) return 'text-orange-400 border-orange-800 bg-orange-900/20';
  if (eventType.includes('RETRY')) return 'text-yellow-400 border-yellow-800 bg-yellow-900/20';
  return 'text-csi-cyan border-csi-border bg-csi-surface';
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function ExecutionTimeline({ events }: Props) {
  if (!events || events.length === 0) {
    return <p className="text-sm text-gray-600 py-4">No timeline events available.</p>;
  }

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-5 top-2 bottom-2 w-px bg-csi-border" />

      <div className="space-y-4">
        {events.map((event, idx) => {
          const Icon = getEventIcon(event.event_type);
          const colorClass = getEventColor(event.event_type);

          return (
            <div key={event.event_id ?? idx} className="relative flex gap-4">
              {/* Dot */}
              <div className={`relative z-10 flex-shrink-0 w-10 h-10 rounded-full border flex items-center justify-center ${colorClass}`}>
                <Icon className="w-4 h-4" />
              </div>

              {/* Content */}
              <div className="flex-1 pb-1">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-200">{event.activity_name}</span>
                  <span className="text-xs text-gray-600">{event.event_type}</span>
                  {event.attempt > 1 && (
                    <span className="text-xs bg-yellow-900/40 text-yellow-400 border border-yellow-800 px-1.5 py-0.5 rounded">
                      Attempt #{event.attempt}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                  <span>{formatTime(event.timestamp)}</span>
                  {event.duration_ms !== undefined && (
                    <span className="text-csi-cyan">{event.duration_ms}ms</span>
                  )}
                </div>
                {event.failure_reason && (
                  <p className="mt-1 text-xs text-red-400 bg-red-900/20 border border-red-900 rounded px-2 py-1">
                    ✗ {event.failure_reason}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
