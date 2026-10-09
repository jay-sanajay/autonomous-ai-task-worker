import React, { useState } from 'react';
import { AlertTriangle, ShieldAlert, Check, X } from 'lucide-react';
import { ApprovalRequest } from '../types';

interface ApprovalModalProps {
  approval: ApprovalRequest | null;
  onApprove: (feedback: string) => void;
  onReject: (feedback: string) => void;
  isProcessing: boolean;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  approval,
  onApprove,
  onReject,
  isProcessing
}) => {
  const [feedback, setFeedback] = useState('Authorized under Q4 Compute Expansion Budget');

  if (!approval) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-slate-900 border border-amber-500/40 rounded-2xl max-w-lg w-full p-6 shadow-2xl shadow-amber-500/10 space-y-4">
        
        {/* Header */}
        <div className="flex items-start space-x-3.5">
          <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-bold text-white">Human-in-the-Loop Approval Required</h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                {approval.risk_level} RISK
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Consequential operation paused for executive authorization
            </p>
          </div>
        </div>

        {/* Risk Reason */}
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs space-y-1.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400 block">
            Governance Policy Trigger
          </span>
          <p className="text-slate-300">{approval.risk_reason}</p>
        </div>

        {/* Payload Preview */}
        <div className="space-y-1 text-xs">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Pending Financial Payload
          </span>
          <pre className="p-3 bg-slate-950 border border-slate-800 rounded-xl font-mono text-[11px] text-sky-300 overflow-x-auto max-h-36">
            {JSON.stringify(approval.pending_payload, null, 2)}
          </pre>
        </div>

        {/* Feedback Input */}
        <div className="space-y-1 text-xs">
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Executive Sign-off Notes / Justification
          </label>
          <input
            type="text"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 font-sans"
            placeholder="e.g. Approved under approved capital project"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-2 border-t border-slate-800">
          <button
            onClick={() => onReject(feedback)}
            disabled={isProcessing}
            className="px-4 py-2 rounded-xl text-xs font-semibold border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 transition flex items-center space-x-1.5 disabled:opacity-50"
          >
            <X className="w-3.5 h-3.5" />
            <span>Reject & Cancel Task</span>
          </button>

          <button
            onClick={() => onApprove(feedback)}
            disabled={isProcessing}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center space-x-1.5 shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Approve & Commit Payable</span>
          </button>
        </div>

      </div>
    </div>
  );
};
