import React from 'react';
import { Task } from '../types';
import {
  ShieldCheck, ShieldAlert, Check, X, Hash, Calendar, DollarSign,
  Building2, AlertTriangle, FileText, Video, Award, BarChart3,
  Layers, Package, Ticket, FileCode, CheckCircle2
} from 'lucide-react';

interface EvidenceCardProps {
  task: Task | null;
  onOpenSandbox?: () => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ task }) => {
  if (!task) return null;

  const verif = task.verification;
  const extracted = task.extracted_data || {};
  const goalLower = (task.goal || '').toLowerCase();
  const summaryLower = (task.final_summary || '').toLowerCase();
  const errorLower = (task.error_message || '').toLowerCase();

  const isVerified = verif?.verified === true;
  const isDuplicate = summaryLower.includes('duplicate') || errorLower.includes('duplicate');
  const isMissingFields = summaryLower.includes('missing') || errorLower.includes('missing');
  const isRejected = task.status === 'CANCELLED' || summaryLower.includes('cancelled') || summaryLower.includes('rejected');

  // Detect workflow domain
  const isCsv = extracted.target_metric !== undefined || extracted.total_metric_value !== undefined || extracted.top_products !== undefined || goalLower.includes('csv') || goalLower.includes('sales');
  const isInterview = extracted.meeting_link !== undefined || extracted.interview_date !== undefined || verif?.task_item_id !== undefined || goalLower.includes('interview') || goalLower.includes('hr');
  const isContract = extracted.contract_code !== undefined || extracted.expiry_date !== undefined || verif?.contract_id !== undefined || goalLower.includes('contract') || goalLower.includes('sla');
  const isTicket = extracted.ticket_code !== undefined || goalLower.includes('ticket');
  const isInventory = extracted.sku !== undefined || extracted.request_code !== undefined || goalLower.includes('inventory') || goalLower.includes('stock');

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
            ? isCsv ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
            : isDuplicate
            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
            : isMissingFields
            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
            : 'bg-slate-800 text-slate-400 border border-slate-700'
        }`}>
          {isVerified
            ? isCsv ? 'VERIFIED ON DISK' : 'VERIFIED IN SQLITE'
            : isDuplicate ? 'DUPLICATE HALTED'
            : isMissingFields ? 'SAFETY HALT'
            : 'UNVERIFIED / PENDING'}
        </span>
      </div>

      {/* 1. CSV Data Analytics Domain */}
      {isCsv && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <FileText className="w-4 h-4 text-sky-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Analyzed Dataset</span>
              <span className="font-mono text-white font-bold truncate block">{extracted.file_path ? extracted.file_path.split(/[\\/]/).pop() : 'Dataset.csv'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-indigo-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Primary Metric</span>
              <span className="text-white font-bold truncate block">{extracted.target_metric || 'Revenue'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Total Metric Value</span>
              <span className="font-mono text-emerald-300 font-bold truncate block">
                {extracted.total_metric_value !== undefined
                  ? Number(extracted.total_metric_value).toLocaleString(undefined, { minimumFractionDigits: 2 })
                  : extracted.total_revenue !== undefined
                  ? Number(extracted.total_revenue).toLocaleString(undefined, { minimumFractionDigits: 2 })
                  : 'N/A'}
              </span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Award className="w-4 h-4 text-amber-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Top Ranked Entity</span>
              <span className="font-mono text-white font-bold truncate block">
                {extracted.top_products && extracted.top_products.length > 0
                  ? (extracted.top_products[0].Product || extracted.top_products[0].Entity_Name || 'Rank 1')
                  : 'Analyzed'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 2. HR Interview & Task Items Domain */}
      {!isCsv && isInterview && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-sky-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Event Title</span>
              <span className="font-mono text-white font-bold truncate block">{extracted.title || 'Technical Interview'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-amber-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Interview Date</span>
              <span className="text-white font-bold truncate block">{extracted.due_date || extracted.interview_date || 'N/A'}</span>
            </div>
          </div>

          <div className="col-span-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-start space-x-2">
            <Video className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div className="truncate flex-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase text-slate-400 block font-semibold">Meeting Link (Simulated)</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  Demo Placeholder URL
                </span>
              </div>
              <span className="font-mono text-sky-300 text-xs truncate block mt-0.5">
                {extracted.meeting_link || 'https://meet.google.com/abc-defg-hij'}
              </span>
              <p className="text-[10px] text-slate-500 mt-1">
                Note: This is a placeholder link extracted from simulated inbox text. Real Google Meet rooms require an active calendar event code.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 3. Legal Contracts & SLAs Domain */}
      {!isCsv && !isInterview && isContract && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <FileCode className="w-4 h-4 text-sky-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Contract Code</span>
              <span className="font-mono text-white font-bold truncate block">{extracted.contract_code || 'N/A'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-indigo-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Parties</span>
              <span className="text-white font-bold truncate block">{extracted.parties || 'N/A'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-amber-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Expiry Date</span>
              <span className="font-mono text-white font-bold truncate block">{extracted.expiry_date || 'N/A'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Risk / Missing Clauses</span>
              <span className="font-mono text-rose-300 font-bold truncate block">
                {extracted.risk_score || 'AUDITED'} ({extracted.missing_clauses_count || (extracted.missing_clauses ? extracted.missing_clauses.length : 0)} flags)
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 4. Customer Support Tickets Domain */}
      {!isCsv && !isInterview && !isContract && isTicket && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Ticket className="w-4 h-4 text-sky-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Ticket Code</span>
              <span className="font-mono text-white font-bold truncate block">{extracted.ticket_code || 'TICK-QUEUE'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-indigo-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Customer</span>
              <span className="text-white font-bold truncate block">{extracted.customer_name || 'Enterprise Client'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Priority</span>
              <span className="font-mono text-amber-300 font-bold truncate block">{extracted.priority || 'HIGH'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Triage Status</span>
              <span className="font-mono text-emerald-300 font-bold truncate block">{extracted.status || 'IN_PROGRESS'}</span>
            </div>
          </div>
        </div>
      )}

      {/* 5. Inventory Replenishment Domain */}
      {!isCsv && !isInterview && !isContract && !isTicket && isInventory && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Package className="w-4 h-4 text-sky-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Product SKU</span>
              <span className="font-mono text-white font-bold truncate block">{extracted.sku || 'SKU-INVENTORY'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-indigo-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Current Stock</span>
              <span className="text-white font-bold truncate block">{extracted.current_stock || 'Low Stock'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <FileText className="w-4 h-4 text-amber-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Purchase Request</span>
              <span className="font-mono text-amber-300 font-bold truncate block">{extracted.request_code || 'PR-DRAFT'}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Status</span>
              <span className="font-mono text-emerald-300 font-bold truncate block">{extracted.status || 'DRAFT'}</span>
            </div>
          </div>
        </div>
      )}

      {/* 6. Default: Invoice & Payable Domain */}
      {!isCsv && !isInterview && !isContract && !isTicket && !isInventory && (
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
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Amount</span>
              <span className="font-mono text-emerald-300 font-bold truncate block">
                {extracted.amount ? `$${Number(extracted.amount).toLocaleString(undefined, {minimumFractionDigits: 2})} ${extracted.currency || 'USD'}` : 'N/A'}
              </span>
            </div>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-amber-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-slate-400 block font-semibold">Due Date</span>
              <span className="font-mono text-white font-bold truncate block">{extracted.due_date || 'N/A'}</span>
            </div>
          </div>
        </div>
      )}

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
              'This record already exists in the accounting system. AgentOS aborted record insertion to guarantee idempotency and prevent duplicate processing.'
            ) : isMissingFields ? (
              'The source document does not contain required fields. AgentOS strictly refused to hallucinate arbitrary values, stopping safely before entering corrupted records.'
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
            <span>
              {verif.payable_id ? 'Database Payable ID:' :
               verif.task_item_id ? 'Database Task Item ID:' :
               verif.contract_id ? 'Database Contract ID:' :
               isCsv ? 'Report File State:' : 'Verified Entity ID:'}
            </span>
            <span className="text-white font-bold">
              {verif.payable_id ? `#${verif.payable_id}` :
               verif.task_item_id ? `#${verif.task_item_id}` :
               verif.contract_id ? `#${verif.contract_id}` :
               isCsv ? 'Persisted & Readable' : 'Confirmed'}
            </span>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px] border-b border-emerald-900/40 pb-1.5">
            <span>Verification Token:</span>
            <span className="text-sky-300 text-[10px] truncate max-w-[210px] font-bold">{verif.verification_token || 'N/A'}</span>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px]">
            <span>Audit Proof:</span>
            <span className="text-emerald-400 font-semibold">{verif.audit_notes || 'Confirmed in database or filesystem'}</span>
          </div>
        </div>
      )}

      {/* Field-by-Field Assertions Table */}
      {verif?.field_comparisons && Object.keys(verif.field_comparisons).length > 0 && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Independent Verification Audit Matrix
          </span>
          <div className="border border-slate-800 rounded-lg overflow-hidden text-[11px] font-mono">
            {Object.entries(verif.field_comparisons).map(([field, cmp]: [string, any]) => (
              <div key={field} className="flex items-center justify-between px-3 py-1.5 bg-slate-950/70 border-b border-slate-800/80 last:border-b-0">
                <span className="text-slate-400 capitalize">{field.replace(/_/g, ' ')}:</span>
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
