import React, { useState } from 'react';
import { Play, Sparkles, AlertCircle } from 'lucide-react';

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

  const selectPreset = (p: typeof PRESETS[0]) => {
    setActivePreset(p.id);
    setGoal(p.goal);
    setAutoApprove(p.autoApprove);
    setSimulateFault(p.fault);
  };

  const handleLaunch = () => {
    if (!goal.trim() || isRunning) return;
    onRun(goal, autoApprove, simulateFault);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/40">
      
      {/* Header & Presets */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2.5">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>Select Scenario or Enter Custom Objective</span>
          </label>
        </div>

        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              onClick={() => selectPreset(p)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                activePreset === p.id
                  ? 'bg-sky-500/20 text-sky-300 border-sky-500/40 shadow-sm'
                  : 'bg-slate-800/80 text-slate-400 border-slate-700/60 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {p.title}
            </button>
          ))}
        </div>
      </div>

      {/* Goal Textarea */}
      <div className="relative mb-4">
        <textarea
          value={goal}
          onChange={(e) => {
            setGoal(e.target.value);
            setActivePreset(null);
          }}
          rows={3}
          placeholder="Describe the workflow for the autonomous AI worker..."
          className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 resize-none font-sans"
        />
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
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-sky-500/25 transition disabled:opacity-50 disabled:cursor-not-allowed select-none"
        >
          {isRunning ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span>Worker Executing...</span>
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
