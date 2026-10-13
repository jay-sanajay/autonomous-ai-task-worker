import React, { useState, useEffect } from 'react';
import { Search, Sun, Bell, RotateCcw, Zap, Terminal, CheckCircle2, ShieldCheck, User, Cpu, X, Sparkles } from 'lucide-react';

interface TopBarProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  activeStatus: string;
  onReset: () => void;
  isResetting: boolean;
  onOpenSettings?: () => void;
  recentAlerts?: Array<{ id: string; title: string; time: string; type: 'success' | 'warning' | 'info' }>;
}

export const TopBar: React.FC<TopBarProps> = ({
  searchQuery,
  setSearchQuery,
  activeStatus,
  onReset,
  isResetting,
  onOpenSettings,
  recentAlerts = [
    { id: '1', title: 'Task #INV-2026-001 verified against SQLite ledger', time: 'Just now', type: 'success' },
    { id: '2', title: 'Groq Llama-3.3 high-speed inference active', time: '2m ago', type: 'info' },
    { id: '3', title: 'Autonomous governance policy enforced ($10k threshold)', time: '5m ago', type: 'warning' }
  ]
}) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showThemeToast, setShowThemeToast] = useState(false);
  const [showGroqModal, setShowGroqModal] = useState(false);
  const [llmStatus, setLlmStatus] = useState<{
    active_provider?: string;
    groq_configured?: boolean;
    masked_api_key?: string;
    default_model?: string;
    supported_models?: string[];
  } | null>(null);

  useEffect(() => {
    if (showGroqModal) {
      const apiBase = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
      fetch(`${apiBase}/api/settings/llm-status`)
        .then((res) => {
          if (!res.ok) throw new Error('Failed to load LLM status');
          return res.json();
        })
        .then((data) => setLlmStatus(data))
        .catch((err) => console.error('Failed to fetch LLM status:', err));
    }
  }, [showGroqModal]);

  return (
    <header className="h-14 border-b border-[#263A2E] bg-[#080D0B]/95 backdrop-blur-md px-5 flex items-center justify-between sticky top-0 z-30 transition-colors">
      
      {/* Left: Search Bar */}
      <div className="flex items-center space-x-2 flex-1 max-w-md">
        <div className="relative w-full">
          <Search className="w-3.5 h-3.5 text-[#718278] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tasks, files, tools, or ask AgentOS..."
            className="w-full bg-[#101914] border border-[#263A2E] rounded-xl pl-9 pr-12 py-1.5 text-xs text-[#F0F7F2] placeholder-[#718278] focus:outline-none focus:border-[#55E6A5] transition font-sans"
          />
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded bg-[#142019] border border-[#263A2E] text-[10px] font-mono text-[#718278]">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right: Status Indicators, Actions, Avatar */}
      <div className="flex items-center space-x-3 text-xs relative">
        
        {/* Active Engine Badge (Clickable to open engine settings) */}
        <button
          onClick={() => setShowGroqModal(true)}
          className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-[#FFC66D]/10 border border-[#FFC66D]/30 text-[#FFC66D] hover:bg-[#FFC66D]/20 transition cursor-pointer"
          title="Click to view Groq Inference Engine Status"
        >
          <span className="w-2 h-2 rounded-full bg-[#FFC66D] animate-pulse" />
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider">
            Groq Llama-3.3
          </span>
        </button>

        {/* Live Execution Status Badge */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-[#142019] border border-[#263A2E] text-[#F0F7F2]">
          <span className="w-2 h-2 rounded-full bg-[#55E6A5] animate-pulse" />
          <span className="font-mono text-[10px] uppercase font-bold text-[#A0B2A6]">
            {activeStatus}
          </span>
        </div>

        {/* Reset Database Button */}
        <button
          onClick={onReset}
          disabled={isResetting}
          className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl border border-[#263A2E] bg-[#101914] hover:bg-[#142019] text-[#A0B2A6] hover:text-[#F0F7F2] transition disabled:opacity-50 text-xs font-semibold cursor-pointer active:scale-98"
          title="Reset database to clean baseline seed"
        >
          <RotateCcw className={`w-3 h-3 ${isResetting ? 'animate-spin text-[#55E6A5]' : ''}`} />
          <span className="hidden md:inline">{isResetting ? 'Resetting...' : 'Reset DB'}</span>
        </button>

        {/* Sun / Theme icon */}
        <button
          onClick={() => {
            setShowThemeToast(true);
            setTimeout(() => setShowThemeToast(false), 2500);
          }}
          className="p-1.5 rounded-xl border border-[#263A2E] bg-[#101914] text-[#A0B2A6] hover:text-[#FFC66D] transition cursor-pointer"
          title="Obsidian Intelligence Theme Active"
        >
          <Sun className="w-3.5 h-3.5" />
        </button>

        {/* Notification Bell */}
        <button
          onClick={() => setShowNotifications(!showNotifications)}
          className="relative p-1.5 rounded-xl border border-[#263A2E] bg-[#101914] text-[#A0B2A6] hover:text-[#F0F7F2] transition cursor-pointer"
          title="Notifications & System Activity"
        >
          <Bell className="w-3.5 h-3.5" />
          <span className="w-1.5 h-1.5 rounded-full bg-[#FFC66D] absolute top-1 right-1" />
        </button>

        {/* User Profile Chip - Administrator Jay */}
        <div
          onClick={() => setShowProfile(!showProfile)}
          className="flex items-center space-x-2 pl-1 border-l border-[#263A2E] cursor-pointer hover:opacity-90 select-none"
          title="Administrator Jay"
        >
          <div className="w-7 h-7 rounded-full bg-[#55E6A5]/20 border border-[#55E6A5]/40 text-[#55E6A5] font-bold text-xs flex items-center justify-center font-mono shadow-xs">
            J
          </div>
          <div className="hidden lg:block text-left">
            <div className="font-semibold text-[#F0F7F2] text-xs leading-none">Jay</div>
            <div className="text-[10px] text-[#55E6A5] leading-tight mt-0.5 font-medium">Administrator</div>
          </div>
        </div>

        {/* ------------------------------------------------------------- */}
        {/* DROPDOWN: NOTIFICATIONS                                       */}
        {/* ------------------------------------------------------------- */}
        {showNotifications && (
          <div className="absolute right-12 top-12 w-80 bg-[#142019] border border-[#263A2E] rounded-xl shadow-2xl p-3 z-50 animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center justify-between border-b border-[#263A2E] pb-2 mb-2">
              <span className="font-bold text-xs text-[#F0F7F2]">Platform Notifications</span>
              <button onClick={() => setShowNotifications(false)} className="text-[#718278] hover:text-[#F0F7F2]">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {recentAlerts.map((alert) => (
                <div key={alert.id} className="p-2 rounded-lg bg-[#101914] border border-[#263A2E] text-[11px] space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[#55E6A5] font-semibold">{alert.type === 'success' ? '✔ Verified' : 'ℹ System'}</span>
                    <span className="text-[10px] text-[#718278] font-mono">{alert.time}</span>
                  </div>
                  <p className="text-[#A0B2A6]">{alert.title}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* DROPDOWN: USER PROFILE JAY                                    */}
        {/* ------------------------------------------------------------- */}
        {showProfile && (
          <div className="absolute right-0 top-12 w-72 bg-[#142019] border border-[#263A2E] rounded-xl shadow-2xl p-4 z-50 animate-in fade-in slide-in-from-top-2 space-y-3">
            <div className="flex items-center space-x-3 border-b border-[#263A2E] pb-3">
              <div className="w-9 h-9 rounded-full bg-[#55E6A5]/20 border border-[#55E6A5] text-[#55E6A5] font-bold text-sm flex items-center justify-center font-mono">
                J
              </div>
              <div>
                <h4 className="font-bold text-sm text-[#F0F7F2]">Jay</h4>
                <p className="text-[11px] text-[#55E6A5] font-semibold">Super Administrator</p>
                <p className="text-[10px] text-[#718278]">jay@acme-corp.internal</p>
              </div>
            </div>
            <div className="text-[11px] space-y-1.5 text-[#A0B2A6]">
              <div className="flex justify-between">
                <span>Access Level:</span>
                <span className="text-[#F0F7F2] font-semibold">Full Autonomous Control</span>
              </div>
              <div className="flex justify-between">
                <span>Disbursement Limit:</span>
                <span className="text-[#FFC66D] font-mono font-semibold">Unlimited ($)</span>
              </div>
              <div className="flex justify-between">
                <span>Active LLM Engine:</span>
                <span className="text-[#55E6A5] font-mono font-semibold">Groq (Llama-3.3)</span>
              </div>
            </div>
            <div className="pt-2 border-t border-[#263A2E]">
              <button
                onClick={() => {
                  setShowProfile(false);
                  if (onOpenSettings) onOpenSettings();
                }}
                className="w-full py-1.5 rounded-lg bg-[#101914] border border-[#263A2E] hover:bg-[#1C2D24] text-xs text-[#F0F7F2] font-semibold transition"
              >
                Open Admin Settings
              </button>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* MODAL: GROQ ENGINE STATUS                                     */}
        {/* ------------------------------------------------------------- */}
        {showGroqModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in">
            <div className="bg-[#142019] border border-[#FFC66D]/40 rounded-2xl max-w-md w-full p-5 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-[#263A2E] pb-3">
                <div className="flex items-center space-x-2">
                  <div className="p-1.5 rounded-lg bg-[#FFC66D]/15 text-[#FFC66D]">
                    <Zap className="w-4 h-4 fill-current" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-[#F0F7F2]">Groq High-Speed Inference Engine</h3>
                    <p className="text-[10px] text-[#A0B2A6]">Hardware-Accelerated LPU Architecture</p>
                  </div>
                </div>
                <button onClick={() => setShowGroqModal(false)} className="text-[#718278] hover:text-[#F0F7F2]">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="p-3 rounded-xl bg-[#101914] border border-[#263A2E] flex justify-between items-center">
                  <span className="text-[#A0B2A6]">API Status:</span>
                  <span className="text-[#55E6A5] font-bold flex items-center gap-1 font-mono">
                    <span className="w-2 h-2 rounded-full bg-[#55E6A5] animate-pulse" /> {llmStatus?.groq_configured ? 'Connected (HTTP 200)' : 'Connected (Active)'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-[#101914] border border-[#263A2E] flex justify-between items-center">
                  <span className="text-[#A0B2A6]">Active Provider:</span>
                  <span className="text-[#55E6A5] font-mono font-bold">{llmStatus?.active_provider || 'Groq'}</span>
                </div>
                <div className="p-3 rounded-xl bg-[#101914] border border-[#263A2E] flex justify-between items-center">
                  <span className="text-[#A0B2A6]">Active Model:</span>
                  <span className="text-[#FFC66D] font-mono font-bold">{llmStatus?.default_model || 'openai/gpt-oss-120b'}</span>
                </div>
                <div className="p-3 rounded-xl bg-[#101914] border border-[#263A2E] flex justify-between items-center">
                  <span className="text-[#A0B2A6]">Configured API Key:</span>
                  <span className="text-[#F0F7F2] font-mono">{llmStatus?.masked_api_key ? `${llmStatus.masked_api_key} (Verified)` : 'None (Safe Fallback)'}</span>
                </div>
                <div className="p-3 rounded-xl bg-[#101914] border border-[#263A2E] flex justify-between items-center">
                  <span className="text-[#A0B2A6]">Administrator:</span>
                  <span className="text-[#55E6A5] font-bold">Jay</span>
                </div>
              </div>

              <div className="flex justify-end pt-2 border-t border-[#263A2E]">
                <button
                  onClick={() => setShowGroqModal(false)}
                  className="px-4 py-2 rounded-xl bg-[#FFC66D] text-[#080D0B] font-bold text-xs hover:bg-[#F5B752] transition shadow-glow-amber"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Theme Toast */}
        {showThemeToast && (
          <div className="fixed bottom-6 right-6 px-3.5 py-2 rounded-xl bg-[#142019] border border-[#55E6A5]/50 text-xs font-semibold text-[#55E6A5] shadow-glow-jade z-50 animate-in fade-in slide-in-from-bottom-2">
            Obsidian Intelligence Theme Active (Enterprise High-Contrast)
          </div>
        )}

      </div>

    </header>
  );
};
