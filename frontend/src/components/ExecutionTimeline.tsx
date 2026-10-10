import React, { useState } from 'react';
import { Task, TaskStep } from '../types';
import { Terminal, CheckCircle2, AlertOctagon, RotateCw, Clock, ArrowRight, CornerDownRight, Check, ChevronDown, ChevronRight, Info } from 'lucide-react';

interface ExecutionTimelineProps {
  task: Task | null;
}

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({ task }) => {
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({});

  if (!task) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-10 text-center text-slate-500 shadow-xl">
        <Terminal className="w-10 h-10 mx-auto mb-3 text-slate-600 animate-pulse" />
        <h4 className="text-base font-bold text-slate-300 mb-1">Awaiting Autonomous Execution</h4>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Select a preset scenario above (e.g. Primary Acme Workflow) and click <strong className="text-sky-400">Launch Autonomous Worker</strong> to watch AgentOS plan, reason, and verify in real time.
        </p>
      </div>
    );
  }

  const steps = task.steps || [];
  const stepsCount = steps.length || task.steps_count || 0;

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps(prev => ({
      ...prev,
      [stepNumber]: prev[stepNumber] !== undefined ? !prev[stepNumber] : false
    }));
  };

  return (
    <div className="space-y-5">
      
      {/* Active Inspected Task Context Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-2.5 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 truncate">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 shrink-0">Viewing Run:</span>
          <span className="font-mono text-sky-400 font-bold shrink-0">{task.id}</span>
          <span className="text-slate-600 shrink-0">•</span>
          <span className="text-slate-300 truncate italic">"{task.goal}"</span>
        </div>
        <div className="flex items-center space-x-2 shrink-0 ml-3">
          <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-slate-800 text-slate-300 border border-slate-700">
            {stepsCount} actions logged
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
            task.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' :
            task.status === 'WAITING_FOR_APPROVAL' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse' :
            task.status === 'FAILED' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' :
            'bg-sky-500/20 text-sky-300 border border-sky-500/40 animate-pulse'
          }`}>
            {task.status}
          </span>
        </div>
      </div>

      {/* Dynamic Execution Plan */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg shadow-black/30">
        <div className="flex items-center justify-between mb-3 border-b border-slate-800/80 pb-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <span>Dynamic Execution Plan</span>
            <span className="text-[10px] text-slate-500 font-normal">({(task.current_plan || []).length} milestones)</span>
          </span>
          <span className="text-[11px] text-slate-400 font-mono">
            {stepsCount} executed
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
          {(task.current_plan || []).map((step, idx) => {
            const isCompleted = stepsCount >= step.step_id || step.status === 'COMPLETED';
            const isCurrent = stepsCount + 1 === step.step_id && task.status === 'RUNNING';

            return (
              <div
                key={idx}
                className={`border rounded-lg p-2.5 flex items-start space-x-2 text-xs transition ${
                  isCompleted
                    ? 'bg-slate-950/80 border-emerald-500/30'
                    : isCurrent
                    ? 'bg-sky-950/30 border-sky-500/50 shadow-sm shadow-sky-500/20'
                    : 'bg-slate-950/40 border-slate-800/70 opacity-60'
                }`}
              >
                <div className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-mono mt-0.5 shrink-0 ${
                  isCompleted
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : isCurrent
                    ? 'bg-sky-500 text-white font-bold animate-pulse'
                    : 'bg-slate-800 border border-slate-700 text-slate-400'
                }`}>
                  {isCompleted ? <Check className="w-2.5 h-2.5" /> : step.step_id}
                </div>
                <div className="flex-1 min-w-0">
                  <div className={`font-semibold truncate ${isCompleted ? 'text-slate-200' : isCurrent ? 'text-sky-300' : 'text-slate-400'}`}>
                    {step.title}
                  </div>
                  <div className="text-[10px] text-slate-500 truncate">{step.description}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step-by-Step ReAct Execution Feed */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/40">
        <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-sky-400" />
            <h3 className="text-sm font-bold text-slate-200">ReAct Reasoning & Tool Execution Stream</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {steps.length} Step{steps.length === 1 ? '' : 's'} Logged
          </span>
        </div>

        {steps.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-xs">
            No step details recorded for this run.
          </div>
        ) : (
          <div className="space-y-3.5 max-h-[560px] overflow-y-auto pr-1">
            {steps.map((s) => {
              const isCollapsed = expandedSteps[s.step_number] === false; // default expanded

              return (
                <div
                  key={s.step_number}
                  className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-3.5 transition hover:border-slate-700 text-xs font-sans shadow-sm"
                >
                  {/* Step Header */}
                  <div
                    onClick={() => toggleStep(s.step_number)}
                    className="flex items-center justify-between cursor-pointer select-none pb-1"
                  >
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] font-bold">
                        STEP {s.step_number}
                      </span>
                      <span className="font-semibold text-slate-200 text-xs">
                        {s.tool_name || 'Chain of Thought Reflection'}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>{s.latency_ms}ms</span>
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        s.status === 'SUCCESS' ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20' :
                        s.status === 'RECOVERED' ? 'text-amber-400 bg-amber-500/10 border border-amber-500/20' :
                        s.status === 'WAITING_APPROVAL' ? 'text-indigo-400 bg-indigo-500/10 border border-indigo-500/20' :
                        'text-rose-400 bg-rose-500/10 border border-rose-500/20'
                      }`}>
                        {s.status}
                      </span>
                      {isCollapsed ? <ChevronRight className="w-3.5 h-3.5 text-slate-500" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-500" />}
                    </div>
                  </div>

                  {/* Step Body (Collapsible) */}
                  {!isCollapsed && (
                    <div className="mt-2.5 space-y-2 pt-1 border-t border-slate-900">
                      {/* Thought Reasoning */}
                      <div className="text-slate-300 italic border-l-2 border-sky-500/70 pl-2.5 py-1 text-xs bg-sky-950/20 rounded-r">
                        "{s.thought}"
                      </div>

                      {/* Tool Execution Code Block */}
                      {s.tool_name && s.tool_input && (
                        <div className="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden font-mono text-[11px]">
                          <div className="px-3 py-1 bg-slate-800/80 text-sky-300 flex items-center justify-between border-b border-slate-800">
                            <span className="flex items-center space-x-1.5 font-bold">
                              <ArrowRight className="w-3 h-3 text-sky-400" />
                              <span>{s.tool_name}</span>
                            </span>
                            <span className="text-[10px] text-slate-400">Parameters</span>
                          </div>
                          <pre className="p-2.5 text-slate-300 overflow-x-auto whitespace-pre-wrap">
                            {JSON.stringify(s.tool_input || {}, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Tool Output & Observation */}
                      {s.tool_output && (
                        <div className="rounded-lg bg-emerald-950/15 border border-emerald-900/50 p-2.5 font-mono text-[11px] text-emerald-300">
                          <div className="flex items-center space-x-1 text-[10px] text-emerald-400 font-bold mb-1">
                            <CornerDownRight className="w-3 h-3" />
                            <span>Observation / Result</span>
                          </div>
                          <pre className="overflow-x-auto text-emerald-200/90 whitespace-pre-wrap">
                            {JSON.stringify(s.tool_output, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Error Notice */}
                      {s.error_message && (
                        <div className="rounded-lg bg-rose-950/30 border border-rose-900/60 p-2.5 text-rose-300 text-xs flex items-start space-x-2">
                          <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-bold">Error intercepted:</span> {s.error_message}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                </div>
              );
            })}
          </div>
        )}

        {/* Final Executive Summary */}
        {task.final_summary && (
          <div className="mt-5 p-4 rounded-xl bg-slate-950 border border-emerald-500/40 shadow-inner">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs uppercase tracking-wider mb-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Executive Outcome Summary</span>
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
