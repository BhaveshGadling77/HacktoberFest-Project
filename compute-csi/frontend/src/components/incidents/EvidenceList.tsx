import { CheckCircle, XCircle, Database } from 'lucide-react';
import type { EvidenceItem } from '../../types';

interface Props {
  evidence: EvidenceItem[];
}

export function EvidenceList({ evidence }: Props) {
  if (!evidence || evidence.length === 0) {
    return <p className="text-sm text-gray-600 py-4">No evidence collected.</p>;
  }

  return (
    <div className="space-y-3">
      {evidence.map((item) => (
        <div
          key={item.evidence_id}
          className={`rounded-lg border p-3 ${
            item.available
              ? 'border-csi-border bg-csi-dark'
              : 'border-gray-800 bg-gray-900/30 opacity-60'
          }`}
        >
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <Database className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
              <span className="text-xs bg-csi-surface border border-csi-border text-gray-400 px-1.5 py-0.5 rounded">
                {item.source}
              </span>
              <span className="text-xs text-gray-500">{item.evidence_type}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span title={item.verified ? 'Verified' : 'Not verified'}>
                {item.verified ? (
                  <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                ) : (
                  <XCircle className="w-3.5 h-3.5 text-gray-600" />
                )}
              </span>
              <span className="text-xs text-gray-600 font-mono">
                {new Date(item.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
          <p className="text-sm text-gray-300">{item.description}</p>
          {!item.available && (
            <p className="text-xs text-gray-600 mt-1 italic">Evidence not directly available</p>
          )}
        </div>
      ))}
    </div>
  );
}
