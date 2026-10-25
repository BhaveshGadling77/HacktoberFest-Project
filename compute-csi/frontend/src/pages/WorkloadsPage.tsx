import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Play,
  Cpu,
  AlertTriangle,
  Flame,
  Clock,
  Layers,
  CheckCircle,
  HelpCircle,
} from 'lucide-react';
import { startRun } from '../api/workloads';
import type { WorkloadType, ExecutionMode, FaultScenario } from '../types';

export function WorkloadsPage() {
  const navigate = useNavigate();

  const [workloadType, setWorkloadType] = useState<WorkloadType>('LOCAL_CPU');
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('NORMAL');
  const [faultScenario, setFaultScenario] = useState<FaultScenario>('NONE');
  const [inputSize, setInputSize] = useState<number>(100);
  const [delaySeconds, setDelaySeconds] = useState<number>(2);
  const [maxRetries, setMaxRetries] = useState<number>(3);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const res = await startRun({
        workload_spec: {
          workload_type: workloadType,
          execution_mode: executionMode,
          fault_scenario: faultScenario,
          input_size: inputSize,
          delay_seconds: executionMode === 'DELAY' ? delaySeconds : 0,
          max_retries: maxRetries,
        },
      });
      navigate(`/runs/${res.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to launch workload run');
      setIsSubmitting(false);
    }
  };

  const isFaultInjected = faultScenario !== 'NONE' || executionMode === 'FAULT_RETRY';

  return (
    <div className="p-8 max-w-4xl space-y-6">
      <div className="border-b border-csi-border pb-4">
        <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
          <Cpu className="w-6 h-6 text-csi-cyan" /> Workload Dispatch & Experiment Console
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Configure inference specifications, execute baseline runs, or trigger controlled fault-injection scenarios.
        </p>
      </div>

      {isFaultInjected && (
        <div className="p-4 rounded-lg bg-orange-950/40 border border-orange-700/60 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-orange-200">
            <span className="font-semibold block mb-0.5">Controlled Fault Injection Active</span>
            The dispatched activity will intentionally simulate failures or anomalous delays.
            Temporal orchestration will record all retries in execution history for forensic correlation.
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-700/60 text-xs text-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Workload Environment */}
        <div className="card space-y-3">
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">
            Target Execution Subsystem
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setWorkloadType('LOCAL_CPU')}
              className={`p-4 rounded border text-left transition ${
                workloadType === 'LOCAL_CPU'
                  ? 'border-csi-cyan bg-csi-cyan/10 text-white'
                  : 'border-csi-border bg-csi-dark/60 text-gray-400 hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-sm">Local CPU Inference</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-300">Default</span>
              </div>
              <p className="text-xs text-gray-400">
                Matrix operations executed in local worker without requiring paid GPU instances.
              </p>
            </button>

            <button
              type="button"
              onClick={() => setWorkloadType('REMOTE_GPU')}
              className={`p-4 rounded border text-left transition ${
                workloadType === 'REMOTE_GPU'
                  ? 'border-csi-cyan bg-csi-cyan/10 text-white'
                  : 'border-csi-border bg-csi-dark/60 text-gray-400 hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-sm">JarvisLabs Remote GPU</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-900/60 text-purple-300">Cloud GPU</span>
              </div>
              <p className="text-xs text-gray-400">
                Dispatches inference payload to configured JarvisLabs cluster (requires credentials).
              </p>
            </button>
          </div>
        </div>

        {/* Execution Mode */}
        <div className="card space-y-3">
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">
            Execution Mode
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            {[
              { id: 'NORMAL', label: 'Normal Baseline', desc: 'Standard single pass execution' },
              { id: 'FAULT_RETRY', label: 'Injected Fault', desc: 'Simulate activity failure and retry' },
              { id: 'DELAY', label: 'Artificial Delay', desc: 'Inject processing latency' },
              { id: 'REPEATED', label: 'Repeated Cycles', desc: 'Execute multiple internal compute loops' },
            ].map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => {
                  setExecutionMode(m.id as ExecutionMode);
                  if (m.id === 'FAULT_RETRY') {
                    setFaultScenario('FIRST_ATTEMPT_FAIL');
                  } else if (m.id === 'NORMAL') {
                    setFaultScenario('NONE');
                  }
                }}
                className={`p-3 rounded border text-left transition ${
                  executionMode === m.id
                    ? 'border-csi-blue bg-csi-blue/20 text-white'
                    : 'border-csi-border bg-csi-dark/60 text-gray-400 hover:border-gray-600'
                }`}
              >
                <div className="font-medium text-white mb-0.5">{m.label}</div>
                <div className="text-[11px] text-gray-400">{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Fault Scenario & Parameters */}
        <div className="card space-y-4">
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">
            Fault Injection Details & Tuning
          </label>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-gray-400 mb-1">Fault Scenario Strategy</label>
              <select
                value={faultScenario}
                onChange={(e) => setFaultScenario(e.target.value as FaultScenario)}
                className="w-full bg-csi-dark border border-csi-border rounded p-2 text-white font-mono focus:border-csi-cyan focus:outline-none"
              >
                <option value="NONE">NONE — Clean execution</option>
                <option value="FIRST_ATTEMPT_FAIL">FIRST_ATTEMPT_FAIL — Fail attempt 1, succeed on retry</option>
                <option value="TIMEOUT_THEN_RETRY">TIMEOUT_THEN_RETRY — Upstream timeout simulation</option>
                <option value="REPEATED_PROCESSING">REPEATED_PROCESSING — Loop resource anomaly</option>
              </select>
            </div>

            <div>
              <label className="block text-gray-400 mb-1">Max Activity Retries ({maxRetries})</label>
              <input
                type="range"
                min="1"
                max="5"
                value={maxRetries}
                onChange={(e) => setMaxRetries(Number(e.target.value))}
                className="w-full accent-csi-cyan"
              />
              <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
                <span>1 (No retry)</span>
                <span>3 (Recommended)</span>
                <span>5 (High)</span>
              </div>
            </div>

            <div>
              <label className="block text-gray-400 mb-1">Compute Input Size: {inputSize}</label>
              <input
                type="range"
                min="20"
                max="500"
                step="20"
                value={inputSize}
                onChange={(e) => setInputSize(Number(e.target.value))}
                className="w-full accent-csi-cyan"
              />
              <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
                <span>20 (Fast)</span>
                <span>100 (Standard)</span>
                <span>500 (Heavy)</span>
              </div>
            </div>

            {executionMode === 'DELAY' && (
              <div>
                <label className="block text-gray-400 mb-1">Artificial Latency: {delaySeconds}s</label>
                <input
                  type="range"
                  min="1"
                  max="15"
                  value={delaySeconds}
                  onChange={(e) => setDelaySeconds(Number(e.target.value))}
                  className="w-full accent-csi-cyan"
                />
              </div>
            )}
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2.5 bg-csi-cyan text-csi-dark font-bold text-xs rounded hover:bg-cyan-400 transition flex items-center gap-2 shadow-lg shadow-cyan-950/50 disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-current" />
            {isSubmitting ? 'Starting Workflow...' : 'Launch Workload Run'}
          </button>
        </div>
      </form>
    </div>
  );
}
