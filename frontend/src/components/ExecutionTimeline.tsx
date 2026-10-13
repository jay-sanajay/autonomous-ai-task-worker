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
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-10 text-center text-[#718278] shadow-card-subtle">
        <Terminal className="w-10 h-10 mx-auto mb-3 text-[#263A2E] animate-pulse" />
        <h4 className="text-sm font-bold text-[#F0F7F2] mb-1">Awaiting Autonomous Execution</h4>
        <p className="text-xs text-[#A0B2A6] max-w-md mx-auto">
          Select a preset scenario above and click <strong className="text-[#FFC66D]">Launch Autonomous Worker</strong> to watch AgentOS plan, reason, and verify in real time.
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
    <div className="space-y-4">
      
      {/* Active Inspected Task Context Banner */}
      <div className="bg-[#142019] border border-[#263A2E] rounded-xl px-4 py-2.5 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 truncate">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[#718278] shrink-0">Viewing Run:</span>
          <span className="font-mono text-[#55E6A5] font-bold shrink-0">{task.id}</span>
          <span className="text-[#263A2E] shrink-0">•</span>
          <span className="text-[#A0B2A6] truncate italic">"{task.goal}"</span>
        </div>
        <div className="flex items-center space-x-2 shrink-0 ml-3">
          <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-[#101914] text-[#A0B2A6] border border-[#263A2E]">
            {stepsCount} actions
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
            task.status === 'COMPLETED' ? 'bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30' :
            task.status === 'WAITING_FOR_APPROVAL' ? 'bg-[#FFC66D]/15 text-[#FFC66D] border border-[#FFC66D]/40 animate-pulse' :
            task.status === 'FAILED' ? 'bg-[#FF7777]/10 text-[#FF7777] border border-[#FF7777]/30' :
            'bg-[#7AB8FF]/10 text-[#7AB8FF] border border-[#7AB8FF]/30 animate-pulse'
          }`}>
            {task.status}
          </span>
        </div>
      </div>

      {/* Dynamic Execution Plan */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-4 shadow-card-subtle">
        <div className="flex items-center justify-between mb-3 border-b border-[#263A2E] pb-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[#A0B2A6] flex items-center space-x-1.5">
            <span>Dynamic Execution Plan</span>
            <span className="text-[10px] text-[#718278] font-normal">({(task.current_plan || []).length} milestones)</span>
          </span>
          <span className="text-[11px] text-[#718278] font-mono">
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
                    ? 'bg-[#142019] border-[#55E6A5]/40 text-[#F0F7F2]'
                    : isCurrent
                    ? 'bg-[#1C2D24] border-[#FFC66D] active-step-halo text-[#F0F7F2]'
                    : 'bg-[#080D0B]/60 border-[#263A2E] text-[#718278]'
                }`}
              >
                <div className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-mono mt-0.5 shrink-0 ${
                  isCompleted
                    ? 'bg-[#55E6A5]/20 text-[#55E6A5] border border-[#55E6A5]/40'
                    : isCurrent
                    ? 'bg-[#FFC66D] text-[#080D0B] font-bold animate-pulse'
                    : 'bg-[#142019] border border-[#263A2E] text-[#718278]'
                }`}>
                  {isCompleted ? <Check className="w-2.5 h-2.5" /> : step.step_id}
                </div>
                <div className="flex-1 min-w-0">
                  <div className={`font-semibold truncate ${isCompleted ? 'text-[#F0F7F2]' : isCurrent ? 'text-[#FFC66D]' : 'text-[#718278]'}`}>
                    {step.title}
                  </div>
                  <div className="text-[10px] text-[#718278] truncate">{step.description}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step-by-Step ReAct Execution Feed */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-5 shadow-card-subtle">
        <div className="flex items-center justify-between mb-4 border-b border-[#263A2E] pb-3">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-[#55E6A5]" />
            <h3 className="text-xs font-bold text-[#F0F7F2] uppercase tracking-wider">ReAct Reasoning & Tool Execution Stream</h3>
          </div>
          <span className="text-xs text-[#718278] font-mono">
            {steps.length} Step{steps.length === 1 ? '' : 's'} Logged
          </span>
        </div>

        {steps.length === 0 ? (
          <div className="p-6 text-center text-[#718278] text-xs">
            No step details recorded for this run.
          </div>
        ) : (
          <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
            {steps.map((s) => {
              const isCollapsed = expandedSteps[s.step_number] === false;

              return (
                <div
                  key={s.step_number}
                  className="bg-[#142019] border border-[#263A2E] rounded-xl p-3.5 transition hover:border-[#55E6A5]/40 text-xs font-sans shadow-xs"
                >
                  {/* Step Header */}
                  <div
                    onClick={() => toggleStep(s.step_number)}
                    className="flex items-center justify-between cursor-pointer select-none pb-1"
                  >
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded bg-[#101914] text-[#A0B2A6] font-mono text-[10px] font-bold border border-[#263A2E]">
                        STEP {s.step_number}
                      </span>
                      <span className="font-semibold text-[#F0F7F2] text-xs">
                        {s.tool_name || 'Chain of Thought Reflection'}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] text-[#A0B2A6]">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-[#718278]" />
                        <span>{s.latency_ms?.toFixed(0) || 0}ms</span>
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        s.status === 'SUCCESS' ? 'text-[#55E6A5] bg-[#55E6A5]/10 border border-[#55E6A5]/30' :
                        s.status === 'RECOVERED' ? 'text-[#FFC66D] bg-[#FFC66D]/10 border border-[#FFC66D]/30' :
                        s.status === 'WAITING_APPROVAL' ? 'text-[#FFC66D] bg-[#FFC66D]/10 border border-[#FFC66D]/30' :
                        'text-[#FF7777] bg-[#FF7777]/10 border border-[#FF7777]/30'
                      }`}>
                        {s.status}
                      </span>
                      {isCollapsed ? <ChevronRight className="w-3.5 h-3.5 text-[#718278]" /> : <ChevronDown className="w-3.5 h-3.5 text-[#718278]" />}
                    </div>
                  </div>

                  {/* Step Body (Collapsible) */}
                  {!isCollapsed && (
                    <div className="mt-2.5 space-y-2 pt-2 border-t border-[#263A2E]">
                      {/* Thought Reasoning */}
                      <div className="text-[#F0F7F2] italic border-l-2 border-[#55E6A5] pl-2.5 py-1 text-xs bg-[#080D0B] rounded-r">
                        "{s.thought}"
                      </div>

                      {/* Tool Execution Code Block */}
                      {s.tool_name && s.tool_input && (
                        <div className="rounded-lg bg-[#080D0B] border border-[#263A2E] overflow-hidden font-mono text-[11px]">
                          <div className="px-3 py-1 bg-[#101914] text-[#A99BFF] flex items-center justify-between border-b border-[#263A2E]">
                            <span className="flex items-center space-x-1.5 font-bold">
                              <ArrowRight className="w-3 h-3 text-[#A99BFF]" />
                              <span>{s.tool_name}</span>
                            </span>
                            <span className="text-[10px] text-[#718278]">Input Arguments</span>
                          </div>
                          <pre className="p-2.5 text-[#F0F7F2] overflow-x-auto whitespace-pre-wrap">
                            {JSON.stringify(s.tool_input || {}, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Tool Output & Observation */}
                      {s.tool_output && (
                        <div className="rounded-lg bg-[#080D0B] border border-[#263A2E] p-2.5 font-mono text-[11px] text-[#55E6A5]">
                          <div className="flex items-center space-x-1 text-[10px] text-[#55E6A5] font-bold mb-1">
                            <CornerDownRight className="w-3 h-3" />
                            <span>Observation / Result</span>
                          </div>
                          <pre className="overflow-x-auto text-[#A0B2A6] whitespace-pre-wrap">
                            {JSON.stringify(s.tool_output, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Error Notice */}
                      {s.error_message && (
                        <div className="rounded-lg bg-[#FF7777]/10 border border-[#FF7777]/30 p-2.5 text-[#FF7777] text-xs flex items-start space-x-2">
                          <AlertOctagon className="w-4 h-4 text-[#FF7777] shrink-0 mt-0.5" />
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
          <div className="mt-4 p-4 rounded-xl bg-[#142019] border border-[#55E6A5]/40 shadow-inner">
            <div className="flex items-center space-x-2 text-[#55E6A5] font-bold text-xs uppercase tracking-wider mb-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Executive Outcome Summary</span>
            </div>
            <p className="text-xs text-[#F0F7F2] whitespace-pre-line leading-relaxed font-sans">
              {task.final_summary}
            </p>
          </div>
        )}

      </div>

    </div>
  );
};
