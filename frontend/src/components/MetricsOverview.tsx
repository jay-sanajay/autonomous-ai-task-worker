import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Database, ShieldCheck, Layers } from 'lucide-react';
import { SandboxMetrics } from '../types';

interface MetricsOverviewProps {
  metrics: SandboxMetrics | null;
}

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({ metrics }) => {
  if (!metrics) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      
      {/* Total Tasks */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#55E6A5]/40 transition shadow-card-subtle">
        <div className="flex items-center justify-between text-[#A0B2A6]">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#718278]">Total Tasks</span>
          <div className="p-1 rounded-md bg-[#FFC66D]/10 text-[#FFC66D]">
            <Layers className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2.5">
          <div className="text-2xl font-bold font-mono text-[#F0F7F2] tracking-tight">{metrics.total_tasks}</div>
        </div>
      </div>

      {/* Completed */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#55E6A5]/40 transition shadow-card-subtle">
        <div className="flex items-center justify-between text-[#A0B2A6]">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#718278]">Completed</span>
          <div className="p-1 rounded-md bg-[#55E6A5]/10 text-[#55E6A5]">
            <CheckCircle2 className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2.5">
          <div className="text-2xl font-bold font-mono text-[#55E6A5] tracking-tight">{metrics.tasks_completed}</div>
          <span className="text-[10px] text-[#A0B2A6] font-medium flex items-center gap-1 mt-0.5">
            {metrics.total_tasks > 0 ? Math.round((metrics.tasks_completed / metrics.total_tasks) * 100) : 0}% success rate
          </span>
        </div>
      </div>

      {/* Failed */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#FF7777]/40 transition shadow-card-subtle">
        <div className="flex items-center justify-between text-[#A0B2A6]">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#718278]">Failed</span>
          <div className="p-1 rounded-md bg-[#FF7777]/10 text-[#FF7777]">
            <XCircle className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2.5">
          <div className="text-2xl font-bold font-mono text-[#FF7777] tracking-tight">{metrics.tasks_failed}</div>
          <span className="text-[10px] text-[#718278] font-medium flex items-center gap-1 mt-0.5">
            {metrics.tasks_failed === 0 ? 'No failures' : 'Critical halts'}
          </span>
        </div>
      </div>

      {/* Awaiting Sign-off */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#FFC66D]/40 transition shadow-card-subtle">
        <div className="flex items-center justify-between text-[#A0B2A6]">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#718278]">Awaiting Sign-Off</span>
          <div className="p-1 rounded-md bg-[#FFC66D]/10 text-[#FFC66D]">
            <AlertTriangle className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2.5">
          <div className="text-2xl font-bold font-mono text-[#FFC66D] tracking-tight">{metrics.tasks_awaiting_approval}</div>
          <span className="text-[10px] text-[#A0B2A6] font-medium flex items-center gap-1 mt-0.5">
            {metrics.tasks_awaiting_approval === 0 ? 'All clear' : 'Action needed'}
          </span>
        </div>
      </div>

      {/* Payables in DB */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#A99BFF]/40 transition shadow-card-subtle">
        <div className="flex items-center justify-between text-[#A0B2A6]">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#718278]">Payables in DB</span>
          <div className="p-1 rounded-md bg-[#A99BFF]/10 text-[#A99BFF]">
            <Database className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2.5">
          <div className="text-2xl font-bold font-mono text-[#A99BFF] tracking-tight">{metrics.total_payables}</div>
        </div>
      </div>

      {/* Verification Rate */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#55E6A5]/40 transition shadow-card-subtle">
        <div className="flex items-center justify-between text-[#A0B2A6]">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#718278]">Verification Rate</span>
          <div className="p-1 rounded-md bg-[#55E6A5]/10 text-[#55E6A5]">
            <ShieldCheck className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2.5">
          <div className="text-2xl font-bold font-mono text-[#55E6A5] tracking-tight">{metrics.verification_success_rate}%</div>
          <span className="text-[10px] text-[#55E6A5] font-medium flex items-center gap-1 mt-0.5">
            Fully verified
          </span>
        </div>
      </div>

    </div>
  );
};
