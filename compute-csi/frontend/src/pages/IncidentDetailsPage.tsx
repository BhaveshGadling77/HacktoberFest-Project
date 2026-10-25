import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  AlertTriangle,
  FileText,
  Brain,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  Lightbulb,
  ExternalLink,
  Info,
} from 'lucide-react';

import { getIncident, investigateIncident } from '../api/incidents';
import { FindingCard } from '../components/incidents/FindingCard';
import { EvidenceList } from '../components/incidents/EvidenceList';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';

export function IncidentDetailsPage() {
  const { incidentId } = useParams<{ incidentId: string }>();

  const {
    data: report,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['incident-report', incidentId],
    queryFn: () => getIncident(incidentId!),
    enabled: !!incidentId,
  });

  const reInvestigateMutation = useMutation({
    mutationFn: () => investigateIncident(incidentId!),
    onSuccess: () => refetch(),
  });

  if (isLoading) {
    return (
      <div className="py-20 flex justify-center">
        <LoadingSpinner message="Correlating forensic telemetry, Temporal history, and anomaly models..." />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="p-8">
        <ErrorState
          title="Incident Dossier Unavailable"
          message={error ? (error as Error).message : 'Investigation report not found.'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  const gemma = report.gemma_analysis;

  return (
    <div className="p-8 space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-csi-border pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link to="/incidents" className="text-xs text-csi-cyan hover:underline">
              ← Incidents
            </Link>
            <span className="text-xs text-gray-500">/</span>
            <span className="text-xs font-mono text-gray-400">{report.incident_id}</span>
          </div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <span>{report.title}</span>
          </h1>
          {report.run_id && (
            <div className="mt-1 flex items-center gap-2 text-xs text-gray-400">
              <span>Related Run:</span>
              <Link to={`/runs/${report.run_id}`} className="font-mono text-csi-cyan hover:underline flex items-center gap-1">
                {report.run_id} <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => reInvestigateMutation.mutate()}
            disabled={reInvestigateMutation.isPending || isFetching}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-csi-cyan text-csi-dark font-bold text-xs rounded hover:bg-cyan-400 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reInvestigateMutation.isPending ? 'animate-spin' : ''}`} />
            Re-Run Forensics
          </button>
        </div>
      </div>

      {/* Summary Banner */}
      <div className="card bg-csi-surface border-l-4 border-l-csi-cyan space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
            <FileText className="w-4 h-4 text-csi-cyan" /> Executive Forensics Finding
          </span>
          <span className="text-xs font-mono text-gray-400">
            Confidence: <strong className="text-white">{(report.overall_confidence * 100).toFixed(0)}%</strong>
          </span>
        </div>
        <p className="text-sm text-gray-200 leading-relaxed font-sans">{report.summary}</p>
      </div>

      {/* AI Reasoning Section (Gemma) */}
      {gemma && (
        <div className="card border border-purple-800/60 bg-purple-950/20 space-y-4">
          <div className="flex items-center justify-between border-b border-purple-900/50 pb-2">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold text-purple-200 tracking-wide">
                {gemma.is_fallback
                  ? 'DETERMINISTIC FORENSIC SYNTHESIS (FALLBACK)'
                  : 'AI INCIDENT EXPLANATION — HYPOTHESIS ONLY'}
              </span>
            </div>
            {!gemma.is_fallback && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-purple-900/50 text-purple-300 font-mono">
                Model: Gemma 2
              </span>
            )}
          </div>

          <div className="space-y-3 text-xs text-gray-300 font-sans">
            <div>
              <span className="font-semibold text-white block mb-0.5">Synthesis:</span>
              <p className="text-gray-300 leading-relaxed">{gemma.summary}</p>
            </div>

            {gemma.possible_causes.length > 0 && (
              <div>
                <span className="font-semibold text-white block mb-1">Likely Primary Causes:</span>
                <ul className="list-disc list-inside space-y-0.5 text-gray-300">
                  {gemma.possible_causes.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            )}

            {gemma.uncertainty_note && (
              <div className="p-2.5 rounded bg-csi-dark/70 border border-purple-900/40 text-[11px] text-purple-200/90 font-mono">
                <strong>Uncertainty / Caveats:</strong> {gemma.uncertainty_note}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Two Column Section: Findings and Evidence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Deterministic Findings */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-yellow-400" /> Verified Deterministic Findings ({report.findings.length})
          </h2>
          <div className="space-y-3">
            {report.findings.map((f) => (
              <FindingCard key={f.finding_id} finding={f} />
            ))}
          </div>
        </div>

        {/* Evidence Ledger */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
            <FileText className="w-4 h-4 text-csi-cyan" /> Correlated Evidence Ledger ({report.evidence.length})
          </h2>
          <div className="card">
            <EvidenceList evidence={report.evidence} />
          </div>
        </div>
      </div>

      {/* Limitations Section */}
      {report.limitations.length > 0 && (
        <div className="card bg-gray-900/40 border border-gray-800 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            <Info className="w-4 h-4 text-gray-500" /> Documented Observability Limitations
          </div>
          <ul className="list-disc list-inside text-xs text-gray-400 space-y-1">
            {report.limitations.map((lim, i) => (
              <li key={i}>{lim}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
