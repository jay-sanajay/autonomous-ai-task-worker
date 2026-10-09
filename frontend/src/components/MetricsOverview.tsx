import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Database, ShieldCheck, Layers } from 'lucide-react';
import { SandboxMetrics } from '../types';

interface MetricsOverviewProps {
  metrics: SandboxMetrics | null;
}

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({ metrics }) => {
  if (!metrics) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
      
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-[11px] font-semibold uppercase tracking-wider">Total Tasks</span>
          <Layers className="w-4 h-4 text-sky-400" />
        </div>
        <div className="mt-2 text-xl font-bold font-mono text-white">{metrics.total_tasks}</div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-[11px] font-semibold uppercase tracking-wider">Completed</span>
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="mt-2 text-xl font-bold font-mono text-emerald-400">{metrics.tasks_completed}</div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-[11px] font-semibold uppercase tracking-wider">Failed</span>
          <XCircle className="w-4 h-4 text-rose-400" />
        </div>
        <div className="mt-2 text-xl font-bold font-mono text-rose-400">{metrics.tasks_failed}</div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-[11px] font-semibold uppercase tracking-wider">Awaiting Sign-off</span>
          <AlertTriangle className="w-4 h-4 text-amber-400" />
        </div>
        <div className="mt-2 text-xl font-bold font-mono text-amber-400">{metrics.tasks_awaiting_approval}</div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-[11px] font-semibold uppercase tracking-wider">Payables in DB</span>
          <Database className="w-4 h-4 text-indigo-400" />
        </div>
        <div className="mt-2 text-xl font-bold font-mono text-indigo-300">{metrics.total_payables}</div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-[11px] font-semibold uppercase tracking-wider">Verification Rate</span>
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="mt-2 text-xl font-bold font-mono text-emerald-300">{metrics.verification_success_rate}%</div>
      </div>

    </div>
  );
};
