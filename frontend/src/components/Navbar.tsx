import React from 'react';
import { Zap, RotateCcw, Activity, ShieldCheck, Database, ListChecks } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onReset: () => void;
  isResetting: boolean;
  activeStatus: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  onReset,
  isResetting,
  activeStatus,
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white font-bold">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold tracking-tight text-white">AgentOS</span>
              <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-sky-500/10 text-sky-400 border border-sky-500/30 rounded-md">
                Autonomous Worker
              </span>
            </div>
            <p className="text-xs text-slate-400">From instructions to verified outcomes</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1">
          <button
            onClick={() => setCurrentTab('studio')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              currentTab === 'studio' || currentTab === 'agent'
                ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Task Studio</span>
          </button>

          <button
            onClick={() => setCurrentTab('sandbox')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              currentTab === 'sandbox'
                ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Company Sandbox</span>
          </button>

          <button
            onClick={() => setCurrentTab('history')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              currentTab === 'history'
                ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <ListChecks className="w-3.5 h-3.5" />
            <span>Execution Audit</span>
          </button>

          <button
            onClick={() => setCurrentTab('advanced')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              currentTab === 'advanced'
                ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Advanced Engine</span>
          </button>
        </nav>

        {/* Actions & Status */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setCurrentTab('sandbox')}
            className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-orange-500/10 border border-orange-500/30 text-orange-400 text-xs hover:bg-orange-500/20 transition"
            title="Groq Llama-3.3-70B AI Engine • Click to configure"
          >
            <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse"></span>
            <span className="font-mono text-[10px] font-bold uppercase tracking-wider">
              Groq Llama-3.3
            </span>
          </button>

          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-300 font-mono text-[11px] uppercase tracking-wider">
              {activeStatus}
            </span>
          </div>

          <button
            onClick={onReset}
            disabled={isResetting}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white flex items-center space-x-1.5 transition disabled:opacity-50"
            title="Reset sandbox database to baseline seed"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
            <span>Reset DB</span>
          </button>
        </div>

      </div>
    </header>
  );
};
