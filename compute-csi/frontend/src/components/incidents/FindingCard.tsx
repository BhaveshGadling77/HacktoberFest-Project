import { CheckCircle, Info, ChevronRight, AlertTriangle } from 'lucide-react';
import type { Finding } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface Props {
  finding: Finding;
}

const FINDING_TYPE_LABELS: Record<string, string> = {
  REPEATED_ATTEMPTS: 'Repeated Attempts',
  FAILED_ATTEMPTS: 'Failed Attempts',
  DURATION_ANOMALY: 'Duration Anomaly',
  ENERGY_ANOMALY: 'Energy Anomaly',
  CPU_ANOMALY: 'CPU Anomaly',
  MISSING_DATA: 'Missing Data',
};

export function FindingCard({ finding }: Props) {
  const confidencePct = Math.round(finding.confidence * 100);

  return (
    <div className="border border-csi-border rounded-lg p-4 bg-csi-dark">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <StatusBadge status={finding.severity} />
          <span className="text-sm font-medium text-gray-200">
            {FINDING_TYPE_LABELS[finding.finding_type] ?? finding.finding_type}
          </span>
          {finding.verified && (
            <span title="Verified">
              <CheckCircle className="w-4 h-4 text-green-400" />
            </span>
          )}
        </div>
        <span className="text-xs text-gray-600 font-mono">{finding.finding_id.slice(0, 8)}</span>
      </div>

      <p className="text-sm text-gray-300 mb-3">{finding.description}</p>

      {/* Confidence bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Confidence</span>
          <span className="text-csi-cyan">{confidencePct}%</span>
        </div>
        <div className="h-1.5 bg-csi-border rounded-full overflow-hidden">
          <div
            className="h-full bg-csi-cyan rounded-full transition-all"
            style={{ width: `${confidencePct}%` }}
          />
        </div>
      </div>

      {finding.uncertainty_note && (
        <div className="flex gap-2 text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-900 rounded p-2 mb-2">
          <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>{finding.uncertainty_note}</span>
        </div>
      )}

      {finding.suggested_action && (
        <div className="flex gap-2 text-xs text-csi-blue bg-blue-900/20 border border-blue-900 rounded p-2">
          <ChevronRight className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>{finding.suggested_action}</span>
        </div>
      )}

      {finding.evidence_refs.length > 0 && (
        <div className="mt-2 flex items-center gap-1 flex-wrap">
          <AlertTriangle className="w-3 h-3 text-gray-600" />
          <span className="text-xs text-gray-600">Evidence: {finding.evidence_refs.join(', ')}</span>
        </div>
      )}
    </div>
  );
}
