import React from 'react';
import { Task, TaskStep } from '../types';
import { Terminal, CheckCircle2, AlertOctagon, RotateCw, Clock, ArrowRight, CornerDownRight } from 'lucide-react';

interface ExecutionTimelineProps {
  task: Task | null;
}

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({ task }) => {
  if (!task) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-slate-500">
        <Terminal className="w-8 h-8 mx-auto mb-2 text-slate-600" />
        <p className="text-sm">Awaiting task launch. Select a scenario above and click Run.</p>
      </div>
    );
  }

  const steps = task.steps || [];

  return (
    <div className="space-y-6">
      
      {/* Dynamic Plan Bar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Dynamic Execution Plan
          </span>
          <span className="text-xs font-mono text-sky-400">
            {task.steps_count} actions logged
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
          {(task.current_plan || []).map((step, idx) => (
            <div
              key={idx}
              className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5 flex items-start space-x-2 text-xs"
            >
              <div className="w-4 h-4 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-mono text-slate-300 mt-0.5">
                {step.step_id}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-slate-200 truncate">{step.title}</div>
                <div className="text-[11px] text-slate-400 truncate">{step.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Step-by-Step ReAct Execution Feed */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/40">
        <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-sky-400" />
            <h3 className="text-sm font-bold text-slate-200">ReAct Reasoning & Tool Execution Stream</h3>
          </div>
          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase ${
            task.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
            task.status === 'WAITING_FOR_APPROVAL' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
            task.status === 'FAILED' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
            'bg-sky-500/10 text-sky-400 border border-sky-500/30'
          }`}>
            Status: {task.status}
          </span>
        </div>

        <div className="space-y-4 max-h-[540px] overflow-y-auto pr-2">
          {steps.map((s, idx) => (
            <div
              key={idx}
              className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 transition hover:border-slate-700 text-xs font-sans"
            >
              {/* Step Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] font-bold">
                    STEP {s.step_number}
                  </span>
                  <span className="font-semibold text-slate-200 text-xs">
                    {s.tool_name || 'Chain of Thought'}
                  </span>
                </div>
                <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>{s.latency_ms}ms</span>
                  </span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                    s.status === 'SUCCESS' ? 'text-emerald-400 bg-emerald-500/10' :
                    s.status === 'RECOVERED' ? 'text-amber-400 bg-amber-500/10' :
                    s.status === 'WAITING_APPROVAL' ? 'text-indigo-400 bg-indigo-500/10' :
                    'text-rose-400 bg-rose-500/10'
                  }`}>
                    {s.status}
                  </span>
                </div>
              </div>

              {/* Thought Reasoning */}
              <div className="mb-2 text-slate-300 italic border-l-2 border-sky-500/60 pl-2.5 py-0.5 text-xs bg-sky-950/10 rounded-r">
                "{s.thought}"
              </div>

              {/* Tool Execution Code Block */}
              {s.tool_name && (
                <div className="mt-2.5 rounded-lg bg-slate-900 border border-slate-800 overflow-hidden font-mono text-[11px]">
                  <div className="px-3 py-1.5 bg-slate-800/60 text-sky-300 flex items-center justify-between border-b border-slate-800">
                    <span className="flex items-center space-x-1.5">
                      <ArrowRight className="w-3 h-3 text-sky-400" />
                      <span>{s.tool_name}</span>
                    </span>
                    <span className="text-[10px] text-slate-400">Arguments</span>
                  </div>
                  <pre className="p-2.5 text-slate-300 overflow-x-auto">
                    {JSON.stringify(s.tool_input || {}, null, 2)}
                  </pre>
                </div>
              )}

              {/* Tool Output & Observation */}
              {s.tool_output && (
                <div className="mt-2 rounded-lg bg-emerald-950/10 border border-emerald-900/40 p-2.5 font-mono text-[11px] text-emerald-300">
                  <div className="flex items-center space-x-1 text-[10px] text-emerald-400 font-bold mb-1">
                    <CornerDownRight className="w-3 h-3" />
                    <span>Observation / Output</span>
                  </div>
                  <pre className="overflow-x-auto text-emerald-200/90 whitespace-pre-wrap">
                    {JSON.stringify(s.tool_output, null, 2)}
                  </pre>
                </div>
              )}

              {/* Error Notice */}
              {s.error_message && (
                <div className="mt-2 rounded-lg bg-rose-950/20 border border-rose-900/50 p-2.5 text-rose-300 text-xs flex items-start space-x-2">
                  <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Error intercepted:</span> {s.error_message}
                  </div>
                </div>
              )}

            </div>
          ))}
        </div>

        {/* Final Executive Summary */}
        {task.final_summary && (
          <div className="mt-5 p-4 rounded-xl bg-slate-950 border border-emerald-500/40 shadow-inner">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs uppercase tracking-wider mb-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Final Executive Completion Summary</span>
            </div>
            <p className="text-xs text-slate-200 whitespace-pre-line leading-relaxed font-sans">
              {task.final_summary}
            </p>
          </div>
        )}

      </div>

    </div>
  );
};
