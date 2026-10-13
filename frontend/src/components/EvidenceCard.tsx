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
    <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-5 shadow-card-subtle space-y-4">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#263A2E] pb-3">
        <div className="flex items-center space-x-2">
          {isVerified ? (
            <ShieldCheck className="w-5 h-5 text-[#55E6A5]" />
          ) : (
            <ShieldAlert className="w-5 h-5 text-[#FFC66D]" />
          )}
          <h3 className="text-xs font-bold text-[#F0F7F2] uppercase tracking-wider">Independent Ground-Truth Evidence</h3>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase ${
          isVerified
            ? 'bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30'
            : isDuplicate
            ? 'bg-[#FFC66D]/10 text-[#FFC66D] border border-[#FFC66D]/30'
            : isMissingFields
            ? 'bg-[#FF7777]/10 text-[#FF7777] border border-[#FF7777]/30'
            : 'bg-[#142019] text-[#718278] border border-[#263A2E]'
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
          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <FileText className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Analyzed Dataset</span>
              <span className="font-mono text-[#F0F7F2] font-bold truncate block">{extracted.file_path ? extracted.file_path.split(/[\\/]/).pop() : 'Dataset.csv'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Primary Metric</span>
              <span className="text-[#F0F7F2] font-bold truncate block">{extracted.target_metric || 'Revenue'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-[#55E6A5] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Total Metric Value</span>
              <span className="font-mono text-[#55E6A5] font-bold truncate block">
                {extracted.total_metric_value !== undefined
                  ? Number(extracted.total_metric_value).toLocaleString(undefined, { minimumFractionDigits: 2 })
                  : extracted.total_revenue !== undefined
                  ? Number(extracted.total_revenue).toLocaleString(undefined, { minimumFractionDigits: 2 })
                  : 'N/A'}
              </span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Award className="w-4 h-4 text-[#FFC66D] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Top Ranked Entity</span>
              <span className="font-mono text-[#F0F7F2] font-bold truncate block">
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
          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Event Title</span>
              <span className="font-mono text-[#F0F7F2] font-bold truncate block">{extracted.title || 'Technical Interview'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-[#FFC66D] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Interview Date</span>
              <span className="text-[#F0F7F2] font-bold truncate block">{extracted.due_date || extracted.interview_date || 'N/A'}</span>
            </div>
          </div>

          <div className="col-span-2 bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-start space-x-2">
            <Video className="w-4 h-4 text-[#55E6A5] shrink-0 mt-0.5" />
            <div className="truncate flex-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase text-[#718278] block font-semibold">Meeting Link (Simulated)</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#FFC66D]/10 text-[#FFC66D] border border-[#FFC66D]/30">
                  Demo Placeholder URL
                </span>
              </div>
              <span className="font-mono text-[#55E6A5] text-xs truncate block mt-0.5">
                {extracted.meeting_link || 'https://meet.google.com/abc-defg-hij'}
              </span>
              <p className="text-[10px] text-[#718278] mt-1">
                Note: Placeholder link extracted from simulated inbox text.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 3. Legal Contracts & SLAs Domain */}
      {!isCsv && !isInterview && isContract && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <FileCode className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Contract Code</span>
              <span className="font-mono text-[#F0F7F2] font-bold truncate block">{extracted.contract_code || 'N/A'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Parties</span>
              <span className="text-[#F0F7F2] font-bold truncate block">{extracted.parties || 'N/A'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-[#FFC66D] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Expiry Date</span>
              <span className="font-mono text-[#55E6A5] font-bold truncate block">{extracted.expiry_date || 'N/A'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-[#FF7777] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Risk / Missing Clauses</span>
              <span className="font-mono text-[#FF7777] font-bold truncate block">
                {extracted.risk_score || 'AUDITED'} ({extracted.missing_clauses_count || (extracted.missing_clauses ? extracted.missing_clauses.length : 0)} flags)
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 4. Customer Support Tickets Domain */}
      {!isCsv && !isInterview && !isContract && isTicket && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Ticket className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Ticket Code</span>
              <span className="font-mono text-[#F0F7F2] font-bold truncate block">{extracted.ticket_code || 'TICK-QUEUE'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Customer</span>
              <span className="text-[#F0F7F2] font-bold truncate block">{extracted.customer_name || 'Enterprise Client'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-[#FFC66D] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Priority</span>
              <span className="font-mono text-[#FFC66D] font-bold truncate block">{extracted.priority || 'HIGH'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-[#55E6A5] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Triage Status</span>
              <span className="font-mono text-[#55E6A5] font-bold truncate block">{extracted.status || 'IN_PROGRESS'}</span>
            </div>
          </div>
        </div>
      )}

      {/* 5. Inventory Replenishment Domain */}
      {!isCsv && !isInterview && !isContract && !isTicket && isInventory && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Package className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Product SKU</span>
              <span className="font-mono text-[#F0F7F2] font-bold truncate block">{extracted.sku || 'SKU-INVENTORY'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Current Stock</span>
              <span className="text-[#F0F7F2] font-bold truncate block">{extracted.current_stock || 'Low Stock'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <FileText className="w-4 h-4 text-[#FFC66D] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Purchase Request</span>
              <span className="font-mono text-[#FFC66D] font-bold truncate block">{extracted.request_code || 'PR-DRAFT'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-[#55E6A5] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Status</span>
              <span className="font-mono text-[#55E6A5] font-bold truncate block">{extracted.status || 'DRAFT'}</span>
            </div>
          </div>
        </div>
      )}

      {/* 6. Default: Invoice & Payable Domain */}
      {!isCsv && !isInterview && !isContract && !isTicket && !isInventory && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Hash className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Invoice #</span>
              <span className="font-mono text-[#55E6A5] font-bold truncate block">{extracted.invoice_number || 'N/A'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-[#A99BFF] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Vendor</span>
              <span className="text-[#F0F7F2] font-bold truncate block">{extracted.vendor_name || 'N/A'}</span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-[#55E6A5] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Amount</span>
              <span className="font-mono text-[#55E6A5] font-bold truncate block">
                {extracted.amount ? `$${Number(extracted.amount).toLocaleString(undefined, {minimumFractionDigits: 2})} ${extracted.currency || 'USD'}` : 'N/A'}
              </span>
            </div>
          </div>

          <div className="bg-[#142019] p-2.5 rounded-lg border border-[#263A2E] flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-[#FFC66D] shrink-0" />
            <div className="truncate">
              <span className="text-[10px] uppercase text-[#718278] block font-semibold">Due Date</span>
              <span className="font-mono text-[#F0F7F2] font-bold truncate block">{extracted.due_date || 'N/A'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Rationale Notice when Unverified */}
      {!isVerified && (
        <div className="bg-[#080D0B] border border-[#263A2E] rounded-xl p-3 text-xs space-y-1.5">
          <div className="flex items-center space-x-1.5 text-[#FFC66D] font-bold text-[11px] uppercase tracking-wider">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>
              {isDuplicate ? 'Idempotency Protection Active' :
               isMissingFields ? 'Hallucination Prevention Active' :
               isRejected ? 'Human Oversight Cancellation' :
               'Database Mutation Status'}
            </span>
          </div>
          <p className="text-[#A0B2A6] text-[11px] leading-relaxed">
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
        <div className="bg-[#142019] border border-[#55E6A5]/30 rounded-xl p-3.5 text-xs space-y-2 font-mono">
          <div className="flex justify-between items-center text-[#718278] text-[11px] border-b border-[#263A2E] pb-1.5">
            <span>
              {verif.payable_id ? 'Database Payable ID:' :
               verif.task_item_id ? 'Database Task Item ID:' :
               verif.contract_id ? 'Database Contract ID:' :
               isCsv ? 'Report File State:' : 'Verified Entity ID:'}
            </span>
            <span className="text-[#F0F7F2] font-bold">
              {verif.payable_id ? `#${verif.payable_id}` :
               verif.task_item_id ? `#${verif.task_item_id}` :
               verif.contract_id ? `#${verif.contract_id}` :
               isCsv ? 'Persisted & Readable' : 'Confirmed'}
            </span>
          </div>
          <div className="flex justify-between items-center text-[#718278] text-[11px] border-b border-[#263A2E] pb-1.5">
            <span>Verification Token (SHA-256):</span>
            <span className="text-[#55E6A5] text-[10px] truncate max-w-[210px] font-bold">{verif.verification_token || 'N/A'}</span>
          </div>
          <div className="flex justify-between items-center text-[#718278] text-[11px]">
            <span>Audit Proof:</span>
            <span className="text-[#55E6A5] font-semibold">{verif.audit_notes || 'Confirmed in database or filesystem'}</span>
          </div>
        </div>
      )}

      {/* Field-by-Field Assertions Table */}
      {verif?.field_comparisons && Object.keys(verif.field_comparisons).length > 0 && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#718278] block">
            Independent Verification Audit Matrix
          </span>
          <div className="border border-[#263A2E] rounded-lg overflow-hidden text-[11px] font-mono">
            {Object.entries(verif.field_comparisons).map(([field, cmp]: [string, any]) => (
              <div key={field} className="flex items-center justify-between px-3 py-1.5 bg-[#080D0B] border-b border-[#263A2E] last:border-b-0">
                <span className="text-[#718278] capitalize">{field.replace(/_/g, ' ')}:</span>
                <div className="flex items-center space-x-2">
                  <span className="text-[#F0F7F2] font-medium">{String(cmp.actual)}</span>
                  {cmp.match ? (
                    <span className="flex items-center text-[#55E6A5] text-[10px] font-bold">
                      <Check className="w-3.5 h-3.5 mr-0.5 inline" /> MATCH
                    </span>
                  ) : (
                    <span className="flex items-center text-[#FF7777] text-[10px] font-bold">
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
