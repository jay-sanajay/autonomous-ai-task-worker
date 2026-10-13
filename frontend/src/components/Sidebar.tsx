import React from 'react';
import {
  Zap, PlusCircle, History, CheckCircle, FileText,
  Cpu, Brain, Award, Database, Settings, ChevronRight,
  FileSpreadsheet
} from 'lucide-react';
import { SandboxMetrics } from '../types';

interface SidebarProps {
  currentTab: string;
  onNavigate: (tab: 'studio' | 'agent' | 'sandbox' | 'history' | 'advanced', subTab?: string) => void;
  metrics: SandboxMetrics | null;
  onNewTaskClick: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onNavigate,
  metrics,
  onNewTaskClick
}) => {
  const awaitingApproval = metrics?.tasks_awaiting_approval || 0;

  return (
    <aside className="w-60 shrink-0 flex flex-col bg-[#0B110E] border-r border-[#263A2E] select-none h-screen sticky top-0 transition-colors">
      
      {/* Brand Header */}
      <div className="p-4 border-b border-[#263A2E]/80">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#FFC66D] to-[#F5B752] flex items-center justify-center shadow-glow-amber text-[#080D0B] font-black text-lg font-sans">
            A
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-base text-[#F0F7F2] tracking-tight font-sans">AgentOS</span>
            </div>
            <p className="text-[11px] text-[#718278] font-medium">Autonomous Worker</p>
          </div>
        </div>
      </div>

      {/* Navigation Stack */}
      <div className="flex-1 p-3 space-y-1 overflow-y-auto">
        
        {/* Overview */}
        <button
          onClick={() => onNavigate('studio')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition ${
            currentTab === 'studio' || currentTab === 'agent'
              ? 'bg-[#1C2D24] text-[#FFC66D] border border-[#FFC66D]/40 shadow-xs'
              : 'text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019]'
          }`}
        >
          <Zap className="w-4 h-4 text-[#FFC66D]" />
          <span>Overview</span>
        </button>

        {/* New Task */}
        <button
          onClick={onNewTaskClick}
          className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019] transition"
        >
          <PlusCircle className="w-4 h-4 text-[#718278]" />
          <span>New Task</span>
        </button>

        {/* Task History */}
        <button
          onClick={() => onNavigate('history')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
            currentTab === 'history'
              ? 'bg-[#1C2D24] text-[#55E6A5] border border-[#55E6A5]/40 shadow-xs font-semibold'
              : 'text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019]'
          }`}
        >
          <History className="w-4 h-4 text-[#718278]" />
          <span>Task History</span>
        </button>

        {/* Approvals */}
        <button
          onClick={() => onNavigate('studio', 'approvals')}
          className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019] transition"
        >
          <div className="flex items-center space-x-2.5">
            <CheckCircle className="w-4 h-4 text-[#718278]" />
            <span>Approvals</span>
          </div>
          {awaitingApproval > 0 && (
            <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FFC66D]/20 text-[#FFC66D] border border-[#FFC66D]/40 font-mono">
              {awaitingApproval}
            </span>
          )}
        </button>

        {/* Automated Reports */}
        <button
          onClick={() => onNavigate('sandbox', 'datasets_reports')}
          className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-[#A0B2A6] hover:text-[#55E6A5] hover:bg-[#142019] transition"
        >
          <FileSpreadsheet className="w-4 h-4 text-[#55E6A5]" />
          <span>Automated Reports</span>
        </button>

        {/* Files (Company Sandbox - Documents) */}
        <button
          onClick={() => onNavigate('sandbox', 'documents')}
          className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019] transition"
        >
          <FileText className="w-4 h-4 text-[#718278]" />
          <span>Files</span>
        </button>

        {/* Tools / Engine */}
        <button
          onClick={() => onNavigate('advanced', 'tools')}
          className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019] transition"
        >
          <Cpu className="w-4 h-4 text-[#718278]" />
          <span>Tools</span>
        </button>

        {/* Memory */}
        <button
          onClick={() => onNavigate('advanced', 'memory')}
          className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019] transition"
        >
          <Brain className="w-4 h-4 text-[#718278]" />
          <span>Memory</span>
        </button>

        {/* Evaluation */}
        <button
          onClick={() => onNavigate('advanced', 'benchmarks')}
          className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019] transition"
        >
          <Award className="w-4 h-4 text-[#718278]" />
          <span>Evaluation</span>
        </button>

        {/* Company Sandbox */}
        <button
          onClick={() => onNavigate('sandbox', 'invoice_hub')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
            currentTab === 'sandbox'
              ? 'bg-[#1C2D24] text-[#55E6A5] border border-[#55E6A5]/40 shadow-xs font-semibold'
              : 'text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019]'
          }`}
        >
          <Database className="w-4 h-4 text-[#718278]" />
          <span>Company Sandbox</span>
        </button>

        {/* Settings */}
        <button
          onClick={() => onNavigate('advanced', 'settings')}
          className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-[#A0B2A6] hover:text-[#F0F7F2] hover:bg-[#142019] transition"
        >
          <Settings className="w-4 h-4 text-[#718278]" />
          <span>Settings</span>
        </button>

      </div>

      {/* Mountain Landscape Silhouette & Workspace Widget */}
      <div className="p-3 border-t border-[#263A2E]/80 space-y-2">
        
        {/* Subtle Ambient Mountains & Sun Illustration */}
        <div className="relative h-20 w-full rounded-xl overflow-hidden bg-gradient-to-b from-[#142019]/60 to-[#080D0B] border border-[#263A2E] flex items-end justify-center">
          {/* Glowing Amber Sun / Moon */}
          <div className="absolute top-2.5 right-6 w-5 h-5 rounded-full bg-gradient-to-tr from-[#FFC66D] to-[#F5B752] shadow-glow-amber opacity-90" />
          
          {/* Mountain Silhouettes SVG */}
          <svg viewBox="0 0 200 80" className="w-full h-full text-[#080D0B] opacity-90 preserve-3d" fill="currentColor">
            <path d="M0 80 L35 38 L70 80 Z" fill="#142019" />
            <path d="M40 80 L105 25 L160 80 Z" fill="#101914" />
            <path d="M120 80 L165 42 L200 80 Z" fill="#142019" />
            <path d="M0 80 L60 55 L130 80 Z" fill="#0B110E" opacity="0.6" />
          </svg>

          {/* Golden highway light streak */}
          <div className="absolute bottom-1 left-2 right-2 h-[1px] bg-gradient-to-r from-transparent via-[#FFC66D]/40 to-transparent" />
        </div>

        {/* Workspace Chip */}
        <div className="p-2 rounded-xl bg-[#142019] border border-[#263A2E] flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2 min-w-0">
            <div className="w-6 h-6 rounded-lg bg-[#55E6A5]/20 text-[#55E6A5] font-bold text-[11px] flex items-center justify-center shrink-0 border border-[#55E6A5]/40 font-mono">
              J
            </div>
            <div className="truncate">
              <div className="font-semibold text-[#F0F7F2] text-[11px] truncate">Jay • Admin</div>
              <div className="text-[10px] text-[#718278] truncate">Acme Production</div>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-[#718278] shrink-0" />
        </div>

      </div>

    </aside>
  );
};
