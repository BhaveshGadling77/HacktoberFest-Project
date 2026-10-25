import { Link } from 'react-router-dom';
import { AlertOctagon, ArrowLeft } from 'lucide-react';

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center p-8">
      <AlertOctagon className="w-12 h-12 text-gray-600 mb-4" />
      <h1 className="text-xl font-bold text-white mb-2">404 — Ledger Node Not Found</h1>
      <p className="text-xs text-gray-400 mb-6 max-w-sm">
        The requested forensics ledger node or investigation report does not exist in the database.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 px-4 py-2 bg-csi-surface border border-csi-border hover:border-csi-cyan text-xs text-csi-cyan rounded transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Return to Dashboard
      </Link>
    </div>
  );
}
