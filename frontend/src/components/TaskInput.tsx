import React, { useState } from 'react';
import { Play, Sparkles, AlertCircle, ArrowRight, CornerDownLeft, RefreshCw } from 'lucide-react';

interface TaskInputProps {
  onRun: (goal: string, autoApprove: boolean, simulateFault: boolean) => void;
  isRunning: boolean;
}

const PRESETS = [
  {
    id: 1,
    title: 'Process latest invoice',
    goal: 'Find the latest invoice from Acme Technologies, extract the invoice number, amount, due date, and vendor, create a payable record in the company system, verify that the record was saved correctly, and summarize the result.',
    autoApprove: true,
    fault: false
  },
  {
    id: 2,
    title: 'HR email to task list',
    goal: 'Find the latest email from HR, extract the interview date and meeting link, and add the event to my task list',
    autoApprove: true,
    fault: false
  },
  {
    id: 3,
    title: 'Sales data analysis',
    goal: 'Analyze the sales CSV, identify the top five products by revenue, check for missing data, and generate a report.',
    autoApprove: true,
    fault: false
  },
  {
    id: 4,
    title: 'Customer ticket triage',
    goal: 'Find unresolved customer tickets, prioritize them, and update their statuses.',
    autoApprove: true,
    fault: false
  },
  {
    id: 5,
    title: 'Inventory & reorder',
    goal: 'Check inventory, identify low-stock products, and create draft purchase requests.',
    autoApprove: true,
    fault: false
  },
  {
    id: 6,
    title: '503 Fault Recovery',
    goal: 'Process latest invoice from Acme Technologies and register as payable.',
    autoApprove: true,
    fault: true
  },
  {
    id: 7,
    title: 'High-Value ($48k HITL)',
    goal: 'Process high value invoice INV-2024-099 from Nexus Hardware Systems ($48,500.00).',
    autoApprove: false,
    fault: false
  },
  {
    id: 8,
    title: 'Duplicate Check',
    goal: 'Process old invoice INV-2023-042 from Acme Technologies and register as payable.',
    autoApprove: true,
    fault: false
  },
  {
    id: 9,
    title: 'Missing Fields Halt',
    goal: 'Process incomplete invoice INV-2024-002 from Acme Technologies.',
    autoApprove: true,
    fault: false
  },
  {
    id: 10,
    title: 'Contract Audit & Expiry',
    goal: 'Read a contract, extract its expiry date, and flag missing information.',
    autoApprove: true,
    fault: false
  },
  {
    id: 11,
    title: 'Document Inspection',
    goal: 'Inspect the document at sandbox_data/contracts/Master_Services_Agreement_CentrAlign_Acme.pdf and summarize its structure.',
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
    <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-5 shadow-card-subtle space-y-4">
      
      {/* Header & Presets */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-xs font-bold text-[#F0F7F2] uppercase tracking-wider flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-[#FFC66D]" />
            <span>Describe your task</span>
          </label>
          <span className="text-[11px] text-[#A0B2A6] hover:text-[#55E6A5] transition cursor-pointer flex items-center gap-1 font-medium">
            <span>Browse more examples</span>
            <span>→</span>
          </span>
        </div>

        {/* Goal Textarea */}
        <div className="relative mb-3.5">
          <textarea
            value={goal}
            onChange={(e) => {
              setGoal(e.target.value);
              setActivePreset(null);
            }}
            onKeyDown={handleKeyDown}
            rows={3}
            placeholder="What would you like AgentOS to accomplish?"
            className="w-full bg-[#080D0B] border border-[#263A2E] rounded-xl px-4 py-3 text-sm text-[#F0F7F2] placeholder-[#718278] focus:outline-none focus:border-[#55E6A5] focus:ring-1 focus:ring-[#55E6A5] resize-none font-sans leading-relaxed"
          />
          <span className="absolute bottom-2.5 right-3 text-[10px] text-[#718278] font-mono flex items-center space-x-1 pointer-events-none">
            <span>Ctrl + Enter</span>
            <CornerDownLeft className="w-3 h-3 inline ml-0.5" />
          </span>
        </div>

        {/* Preset Chips */}
        <div className="flex flex-wrap gap-2 items-center">
          {PRESETS.map((p) => {
            const isSelected = activePreset === p.id;
            return (
              <button
                key={p.id}
                onClick={() => selectPreset(p, false)}
                onDoubleClick={() => selectPreset(p, true)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 border ${
                  isSelected
                    ? 'bg-[#1C2D24] text-[#F0F7F2] border-[#55E6A5] shadow-xs'
                    : 'bg-[#142019] text-[#A0B2A6] border-[#263A2E] hover:text-[#F0F7F2] hover:bg-[#1C2D24] hover:border-[#55E6A5]/40'
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
                    className="p-0.5 rounded hover:bg-[#55E6A5] hover:text-[#080D0B] transition"
                    title="Run Now"
                  >
                    <Play className="w-3 h-3 fill-current inline ml-0.5" />
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Options & Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-[#263A2E]">
        
        <div className="flex flex-wrap items-center gap-4 text-xs text-[#A0B2A6]">
          <label className="flex items-center space-x-2 cursor-pointer select-none hover:text-[#F0F7F2]">
            <input
              type="checkbox"
              checked={simulateFault}
              onChange={(e) => setSimulateFault(e.target.checked)}
              className="rounded border-[#263A2E] bg-[#080D0B] text-[#55E6A5] focus:ring-[#55E6A5]/30 w-3.5 h-3.5"
            />
            <span>Simulate 503 Gateway Fault (Test Recovery)</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer select-none hover:text-[#F0F7F2]">
            <input
              type="checkbox"
              checked={autoApprove}
              onChange={(e) => setAutoApprove(e.target.checked)}
              className="rounded border-[#263A2E] bg-[#080D0B] text-[#55E6A5] focus:ring-[#55E6A5]/30 w-3.5 h-3.5"
            />
            <span>Auto-Approve High Value (&gt; $10k)</span>
          </label>
        </div>

        {/* Primary Action Button (Solar Amber with Reserved Glow) */}
        <button
          onClick={handleLaunch}
          disabled={isRunning || !goal.trim()}
          className="px-6 py-2.5 rounded-xl bg-[#FFC66D] hover:bg-[#F5B752] text-[#080D0B] font-bold text-xs flex items-center justify-center space-x-2 shadow-glow-amber transition active:scale-98 disabled:opacity-50 disabled:cursor-not-allowed select-none cursor-pointer"
        >
          {isRunning ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Executing Autonomous Loop...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-[#080D0B]" />
              <span>Launch Autonomous Worker</span>
            </>
          )}
        </button>

      </div>

    </div>
  );
};
