import React, { useState } from 'react';
import { AlertTriangle, ShieldAlert, Check, X, RefreshCw } from 'lucide-react';
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
  const [feedback, setFeedback] = useState('Authorized under Executive Disbursement Policy');

  if (!approval) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs animate-in fade-in">
      <div className="bg-[#142019] border border-[#FFC66D]/40 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
        
        {/* Header */}
        <div className="flex items-start space-x-3.5">
          <div className="p-2.5 rounded-xl bg-[#FFC66D]/15 border border-[#FFC66D]/30 text-[#FFC66D]">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-[#F0F7F2] uppercase tracking-wider">Human-in-the-Loop Sign-off Required</h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FFC66D]/20 text-[#FFC66D] border border-[#FFC66D]/40 font-mono">
                {approval.risk_level || 'HIGH'}
              </span>
            </div>
            <p className="text-xs text-[#A0B2A6] mt-0.5">
              Consequential operation paused for managerial sign-off.
            </p>
          </div>
        </div>

        {/* Risk Reason */}
        <div className="bg-[#101914] p-3.5 rounded-xl border border-[#263A2E] text-xs space-y-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#FFC66D] block">
            Governance Policy Trigger
          </span>
          <p className="text-[#F0F7F2]">{approval.risk_reason || 'Single transaction value exceeds enterprise limit.'}</p>
        </div>

        {/* Payload Preview */}
        <div className="space-y-1 text-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#718278] block">
            Pending Financial Payload ({approval.tool_name})
          </span>
          <pre className="p-3 bg-[#080D0B] border border-[#263A2E] rounded-xl font-mono text-[11px] text-[#55E6A5] overflow-x-auto max-h-36">
            {JSON.stringify(approval.pending_payload, null, 2)}
          </pre>
        </div>

        {/* Feedback Input */}
        <div className="space-y-1 text-xs">
          <label className="text-[10px] font-bold uppercase tracking-wider text-[#718278] block">
            Audit Justification & Notes
          </label>
          <input
            type="text"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            className="w-full bg-[#080D0B] border border-[#263A2E] rounded-lg px-3 py-2 text-xs text-[#F0F7F2] focus:outline-none focus:border-[#55E6A5] font-sans"
            placeholder="e.g. Authorized under departmental operating budget"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-2 border-t border-[#263A2E]">
          <button
            onClick={() => onReject(feedback)}
            disabled={isProcessing}
            className="px-4 py-2 rounded-xl text-xs font-semibold border border-[#FF7777]/30 bg-[#FF7777]/10 hover:bg-[#FF7777]/20 text-[#FF7777] transition flex items-center space-x-1.5 disabled:opacity-50"
          >
            <X className="w-3.5 h-3.5" />
            <span>Reject & Cancel</span>
          </button>

          <button
            onClick={() => onApprove(feedback)}
            disabled={isProcessing}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-[#55E6A5] hover:bg-[#35D993] text-[#080D0B] transition flex items-center space-x-1.5 shadow-glow-jade disabled:opacity-50"
          >
            {isProcessing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            <span>Approve & Commit</span>
          </button>
        </div>

      </div>
    </div>
  );
};
