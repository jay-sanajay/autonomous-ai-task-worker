import React from 'react';
import { Task } from '../types';
import { ShieldCheck, ShieldAlert, Check, X, Hash, Calendar, DollarSign, Building2, AlertTriangle, ArrowUpRight } from 'lucide-react';

interface EvidenceCardProps {
  task: Task | null;
  onOpenSandbox?: () => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ task, onOpenSandbox }) => {
  if (!task) return null;

  const verif = task.verification;
  const extracted = task.extracted_data || {};
  const isVerified = verif?.verified === true;
  const isDuplicate = task.final_summary?.toLowerCase().includes('duplicate') || task.error_message?.toLowerCase().includes('duplicate');
  const isMissingFields = task.final_summary?.toLowerCase().includes('missing') || task.error_message?.toLowerCase().includes('missing');
  const isRejected = task.status === 'CANCELLED' || task.final_summary?.toLowerCase().includes('cancelled') || task.final_summary?.toLowerCase().includes('rejected');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/40 space-y-4">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          {isVerified ? (
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          ) : (
            <ShieldAlert className="w-5 h-5 text-amber-400" />
          )}
          <h3 className="text-sm font-bold text-slate-200">Independent Ground-Truth Evidence</h3>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase ${
          isVerified
            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
            : isDuplicate
            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
            : isMissingFields
            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
            : 'bg-slate-800 text-slate-400 border border-slate-700'
        }`}>
          {isVerified ? 'VERIFIED IN SQLITE' : isDuplicate ? 'DUPLICATE HALTED' : isMissingFields ? 'SAFETY HALT' : 'UNVERIFIED / PENDING'}
        </span>
      </div>

      {/* Extracted Metadata Grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
          <Hash className="w-4 h-4 text-sky-400 shrink-0" />
          <div className="truncate">
            <span className="text-[10px] uppercase text-slate-400 block font-semibold">Invoice #</span>
            <span className="font-mono text-white font-bold truncate block">{extracted.invoice_number || 'N/A'}</span>
          </div>
        </div>

        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
          <Building2 className="w-4 h-4 text-indigo-400 shrink-0" />
          <div className="truncate">
            <span className="text-[10px] uppercase text-slate-400 block font-semibold">Vendor</span>
            <span className="text-white font-bold truncate block">{extracted.vendor_name || 'N/A'}</span>
          </div>
        </div>

        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
          <DollarSign className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <span className="text-[10px] uppercase text-slate-400 block font-semibold">Amount</span>
            <span className="font-mono text-emerald-300 font-bold">
              {extracted.amount ? `$${extracted.amount.toLocaleString(undefined, {minimumFractionDigits: 2})} ${extracted.currency || 'USD'}` : 'N/A'}
            </span>
          </div>
        </div>

        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
          <Calendar className="w-4 h-4 text-amber-400 shrink-0" />
          <div>
            <span className="text-[10px] uppercase text-slate-400 block font-semibold">Due Date</span>
            <span className="font-mono text-white font-bold">{extracted.due_date || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Rationale Notice when Unverified */}
      {!isVerified && (
        <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-3 text-xs space-y-1.5">
          <div className="flex items-center space-x-1.5 text-amber-400 font-bold text-[11px] uppercase tracking-wider">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>
              {isDuplicate ? 'Idempotency Protection Active' :
               isMissingFields ? 'Hallucination Prevention Active' :
               isRejected ? 'Human Oversight Cancellation' :
               'Database Mutation Status'}
            </span>
          </div>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            {isDuplicate ? (
              'This invoice is already entered in the accounting system. AgentOS aborted record insertion to guarantee idempotency and prevent double-payment.'
            ) : isMissingFields ? (
              'The source document does not contain an invoice amount. AgentOS strictly refused to hallucinate arbitrary financial values, stopping safely before entering corrupted records.'
            ) : isRejected ? (
              'A reviewer rejected this transaction during human-in-the-loop review. Execution was halted safely.'
            ) : (
              'Record has not yet been registered or confirmed against the SQLite ledger for this task.'
            )}
          </p>
        </div>
      )}

      {/* Verification Receipt Details */}
      {verif && (
        <div className="bg-emerald-950/25 border border-emerald-500/30 rounded-xl p-3.5 text-xs space-y-2 font-mono">
          <div className="flex justify-between items-center text-slate-400 text-[11px] border-b border-emerald-900/40 pb-1.5">
            <span>Database Payable ID:</span>
            <span className="text-white font-bold">#{verif.payable_id || 'N/A'}</span>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px] border-b border-emerald-900/40 pb-1.5">
            <span>Verification Token:</span>
            <span className="text-sky-300 text-[10px] truncate max-w-[210px] font-bold">{verif.verification_token || 'N/A'}</span>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px]">
            <span>Audit Proof:</span>
            <span className="text-emerald-400 font-semibold">{verif.audit_notes || 'Confirmed in SQLite database'}</span>
          </div>
        </div>
      )}

      {/* Field-by-Field Assertions Table */}
      {verif?.field_comparisons && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Independent SQLite Field Audit Matrix
          </span>
          <div className="border border-slate-800 rounded-lg overflow-hidden text-[11px] font-mono">
            {Object.entries(verif.field_comparisons).map(([field, cmp]: [string, any]) => (
              <div key={field} className="flex items-center justify-between px-3 py-1.5 bg-slate-950/70 border-b border-slate-800/80 last:border-b-0">
                <span className="text-slate-400 capitalize">{field}:</span>
                <div className="flex items-center space-x-2">
                  <span className="text-slate-300 font-medium">{String(cmp.actual)}</span>
                  {cmp.match ? (
                    <span className="flex items-center text-emerald-400 text-[10px] font-bold">
                      <Check className="w-3.5 h-3.5 mr-0.5 inline" /> MATCH
                    </span>
                  ) : (
                    <span className="flex items-center text-rose-400 text-[10px] font-bold">
                      <X className="w-3.5 h-3.5 mr-0.5 inline" /> MISMATCH
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
