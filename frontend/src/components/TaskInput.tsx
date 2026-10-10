import React, { useState } from 'react';
import { Play, Sparkles, AlertCircle, ArrowRight, CornerDownLeft } from 'lucide-react';

interface TaskInputProps {
  onRun: (goal: string, autoApprove: boolean, simulateFault: boolean) => void;
  isRunning: boolean;
}

const PRESETS = [
  {
    id: 1,
    title: 'Primary Acme Workflow',
    goal: 'Find the latest invoice from Acme Technologies, extract the invoice number, amount, due date, and vendor, create a payable record in the company system, verify that the record was saved correctly, and summarize the result.',
    autoApprove: true,
    fault: false
  },
  {
    id: 2,
    title: 'Alternative Phrasing',
    goal: 'Find the newest Acme invoice and register it as a payable.',
    autoApprove: true,
    fault: false
  },
  {
    id: 3,
    title: '503 Fault & Auto-Recovery',
    goal: 'Process latest invoice from Acme Technologies and register as payable.',
    autoApprove: true,
    fault: true
  },
  {
    id: 4,
    title: 'High-Value ($48k) HITL Sign-off',
    goal: 'Process high value invoice INV-2024-099 from Nexus Hardware Systems ($48,500.00).',
    autoApprove: false,
    fault: false
  },
  {
    id: 5,
    title: 'Duplicate Invoice Check',
    goal: 'Process old invoice INV-2023-042 from Acme Technologies and register as payable.',
    autoApprove: true,
    fault: false
  },
  {
    id: 6,
    title: 'Missing Required Amount',
    goal: 'Process incomplete invoice INV-2024-002 from Acme Technologies.',
    autoApprove: true,
    fault: false
  }
];

export const TaskInput: React.FC<TaskInputProps> = ({ onRun, isRunning }) => {
  const [goal, setGoal] = useState(PRESETS[0].goal);
  const [autoApprove, setAutoApprove] = useState(true);
  const [simulateFault, setSimulateFault] = useState(false);
  const [activePreset, setActivePreset] = useState<number | null>(1);

  const selectPreset = (p: typeof PRESETS[0], executeNow = false) => {
    setActivePreset(p.id);
    setGoal(p.goal);
    setAutoApprove(p.autoApprove);
    setSimulateFault(p.fault);

    if (executeNow && !isRunning) {
      onRun(p.goal, p.autoApprove, p.fault);
    }
  };

  const handleLaunch = () => {
    if (!goal.trim() || isRunning) return;
    onRun(goal, autoApprove, simulateFault);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleLaunch();
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/40 space-y-4">
      
      {/* Header & Presets */}
      <div>
        <div className="flex items-center justify-between mb-2.5">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>Select Scenario Preset or Enter Custom Goal</span>
          </label>
          <span className="text-[11px] text-slate-500 font-mono hidden sm:inline">
            Double-click preset to run immediately
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => {
            const isSelected = activePreset === p.id;
            return (
              <button
                key={p.id}
                onClick={() => selectPreset(p, false)}
                onDoubleClick={() => selectPreset(p, true)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 border ${
                  isSelected
                    ? 'bg-sky-500/20 text-sky-300 border-sky-500/50 shadow-sm shadow-sky-500/20'
                    : 'bg-slate-800/70 text-slate-400 border-slate-700/60 hover:text-slate-200 hover:bg-slate-800'
                }`}
                title="Click to load prompt, double-click to execute immediately"
              >
                <span>{p.title}</span>
                {isSelected && (
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      selectPreset(p, true);
                    }}
                    className="p-0.5 rounded hover:bg-sky-500 hover:text-white transition"
                    title="Run Now"
                  >
                    <Play className="w-3 h-3 fill-current inline ml-1" />
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Goal Textarea */}
      <div className="relative">
        <textarea
          value={goal}
          onChange={(e) => {
            setGoal(e.target.value);
            setActivePreset(null);
          }}
          onKeyDown={handleKeyDown}
          rows={3}
          placeholder="Describe the workflow for the autonomous AI worker..."
          className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 resize-none font-sans"
        />
        <span className="absolute bottom-2.5 right-3 text-[10px] text-slate-500 font-mono flex items-center space-x-1 pointer-events-none">
          <span>Ctrl + Enter to run</span>
          <CornerDownLeft className="w-3 h-3 inline" />
        </span>
      </div>

      {/* Options & Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1 border-t border-slate-800/80">
        
        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
          <label className="flex items-center space-x-2 cursor-pointer select-none hover:text-slate-200">
            <input
              type="checkbox"
              checked={simulateFault}
              onChange={(e) => setSimulateFault(e.target.checked)}
              className="rounded border-slate-700 bg-slate-800 text-sky-500 focus:ring-sky-500/30"
            />
            <span>Simulate 503 Gateway Fault (Test Recovery)</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer select-none hover:text-slate-200">
            <input
              type="checkbox"
              checked={autoApprove}
              onChange={(e) => setAutoApprove(e.target.checked)}
              className="rounded border-slate-700 bg-slate-800 text-sky-500 focus:ring-sky-500/30"
            />
            <span>Auto-Approve High Value (&gt; $10k)</span>
          </label>
        </div>

        <button
          onClick={handleLaunch}
          disabled={isRunning || !goal.trim()}
          className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-sky-500/25 transition disabled:opacity-50 disabled:cursor-not-allowed select-none cursor-pointer"
        >
          {isRunning ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Executing Autonomous Loop...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Launch Autonomous Worker</span>
            </>
          )}
        </button>

      </div>

    </div>
  );
};
