import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { MetricsOverview } from './components/MetricsOverview';
import { TaskInput } from './components/TaskInput';
import { ExecutionTimeline } from './components/ExecutionTimeline';
import { EvidenceCard } from './components/EvidenceCard';
import { ApprovalModal } from './components/ApprovalModal';
import { CompanySandbox } from './components/CompanySandbox';
import { TaskHistory } from './components/TaskHistory';
import { AdvancedCapabilities } from './components/AdvancedCapabilities';
import {
  Task, Vendor, InvoiceDoc, Payable, SandboxMetrics,
  TaskItem, SupportTicket, InventoryItem, PurchaseRequest
} from './types';
import * as api from './services/api';
import {
  Sparkles, CheckCircle2, ArrowRight, FileText,
  Clock, ShieldCheck, Check, ChevronRight, Play, Terminal, Database, ShieldAlert
} from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'studio' | 'agent' | 'sandbox' | 'history' | 'advanced'>('studio');
  const [sandboxSubTab, setSandboxSubTab] = useState<'invoice_hub' | 'datasets_reports' | 'payables' | 'tasks' | 'contracts' | 'csv_reports' | 'tickets' | 'inventory' | 'vendors' | 'documents'>('invoice_hub');
  const [advancedSubTab, setAdvancedSubTab] = useState<'memory' | 'benchmarks' | 'replay' | 'portal' | 'tools' | 'settings'>('memory');
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [invoices, setInvoices] = useState<InvoiceDoc[]>([]);
  const [payables, setPayables] = useState<Payable[]>([]);
  const [taskItems, setTaskItems] = useState<TaskItem[]>([]);
  const [supportTickets, setSupportTickets] = useState<SupportTicket[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [purchaseRequests, setPurchaseRequests] = useState<PurchaseRequest[]>([]);
  const [metrics, setMetrics] = useState<SandboxMetrics | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Polling ref to avoid concurrent poll loops
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const taskInputRef = useRef<HTMLDivElement | null>(null);

  // Refresh sandbox entities and metrics
  const refreshSandboxData = useCallback(async () => {
    try {
      const [v, inv, p, m, t, ti, st, inlist, pr] = await Promise.all([
        api.fetchVendors().catch(() => []),
        api.fetchInvoices().catch(() => []),
        api.fetchPayables().catch(() => []),
        api.fetchMetrics().catch(() => ({
          total_tasks: 0,
          tasks_completed: 0,
          tasks_failed: 0,
          tasks_awaiting_approval: 0,
          total_payables: 0,
          verified_payables: 0,
          verification_success_rate: 100.0
        })),
        api.fetchTasks().catch(() => []),
        api.fetchTaskItems().catch(() => []),
        api.fetchSupportTickets().catch(() => []),
        api.fetchInventory().catch(() => []),
        api.fetchPurchaseRequests().catch(() => [])
      ]);
      setVendors(v || []);
      setInvoices(inv || []);
      setPayables(p || []);
      if (m) setMetrics(m);
      setTasks(t || []);
      setTaskItems(ti || []);
      setSupportTickets(st || []);
      setInventory(inlist || []);
      setPurchaseRequests(pr || []);

      // Default active task to the most recent run if none selected
      setActiveTask((prev) => {
        if (!prev && t && t.length > 0) {
          setSelectedTaskId(t[0].id);
          return t[0];
        }
        return prev;
      });
    } catch (err) {
      console.error('Failed to refresh sandbox data:', err);
    }
  }, []);

  // Initial data load
  useEffect(() => {
    refreshSandboxData();
  }, [refreshSandboxData]);

  // Poller for active task
  useEffect(() => {
    if (!activeTask || !isRunning) {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      return;
    }

    const taskId = activeTask.id;
    pollTimerRef.current = setInterval(async () => {
      try {
        const updated = await api.fetchTaskDetails(taskId);
        setActiveTask(updated);

        // Update task in tasks list
        setTasks((prev) =>
          prev.map((t) => (t.id === updated.id ? updated : t))
        );

        // Check if finished or waiting for approval
        const isTerminal = ['COMPLETED', 'FAILED', 'CANCELLED'].includes(updated.status);
        if (isTerminal) {
          setIsRunning(false);
          refreshSandboxData();
          if (pollTimerRef.current) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 700);

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [activeTask?.id, isRunning, refreshSandboxData]);

  // Select a historical task to inspect
  const handleSelectHistoricalTask = async (taskId: string) => {
    setSelectedTaskId(taskId);
    try {
      const details = await api.fetchTaskDetails(taskId);
      setActiveTask(details);
    } catch (err) {
      console.error('Failed to load historical task:', err);
    }
  };

  // Run new task
  const handleRunTask = async (goal: string, autoApprove: boolean, simulateFault: boolean) => {
    setIsRunning(true);
    try {
      const newTask = await api.createTask({
        goal,
        auto_approve_high_risk: autoApprove,
        simulate_fault: simulateFault
      });
      setActiveTask(newTask);
      setSelectedTaskId(newTask.id);
      setTasks((prev) => [newTask, ...prev.filter((t) => t.id !== newTask.id)]);
      setCurrentTab('studio');

      const isTerminal = ['COMPLETED', 'FAILED', 'CANCELLED'].includes(newTask.status);
      if (isTerminal) {
        setIsRunning(false);
      }
      refreshSandboxData();
    } catch (err) {
      console.error('Failed to start task:', err);
      setIsRunning(false);
    }
  };

  // Human approval handlers
  const handleApprove = async (feedback: string) => {
    if (!activeTask) return;
    setIsApproving(true);
    try {
      const updated = await api.approveTask(activeTask.id, 'Jay (Administrator)', feedback);
      setActiveTask(updated);
      const isTerminal = ['COMPLETED', 'FAILED', 'CANCELLED'].includes(updated.status);
      if (isTerminal) {
        setIsRunning(false);
      } else {
        setIsRunning(true);
      }
      refreshSandboxData();
    } catch (err) {
      console.error('Approval failed:', err);
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async (feedback: string) => {
    if (!activeTask) return;
    setIsApproving(true);
    try {
      const updated = await api.rejectTask(activeTask.id, 'Jay (Administrator)', feedback);
      setActiveTask(updated);
      setIsRunning(false);
      refreshSandboxData();
    } catch (err) {
      console.error('Rejection failed:', err);
    } finally {
      setIsApproving(false);
    }
  };

  // Centralized Navigation Handler for Sidebar and TopBar
  const handleNavigate = (tab: 'studio' | 'agent' | 'sandbox' | 'history' | 'advanced', subTab?: string) => {
    setCurrentTab(tab);
    if (tab === 'sandbox' && subTab) {
      setSandboxSubTab(subTab as any);
    } else if (tab === 'advanced' && subTab) {
      setAdvancedSubTab(subTab as any);
    } else if (tab === 'studio' && subTab === 'approvals') {
      const pendingTask = tasks.find(t => t.status === 'WAITING_FOR_APPROVAL');
      if (pendingTask) {
        api.fetchTaskDetails(pendingTask.id).then(fullTask => {
          setActiveTask(fullTask);
          setSelectedTaskId(fullTask.id);
        }).catch(() => {
          setActiveTask(pendingTask);
          setSelectedTaskId(pendingTask.id);
        });
      }
    }
  };

  // Sandbox reset
  const handleResetSandbox = async () => {
    setIsResetting(true);
    try {
      await api.resetSandbox();
      await refreshSandboxData();
      setActiveTask(null);
      setSelectedTaskId(null);
    } catch (err) {
      console.error('Reset failed:', err);
    } finally {
      setIsResetting(false);
    }
  };

  const scrollToTaskInput = () => {
    setCurrentTab('studio');
    if (taskInputRef.current) {
      taskInputRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const filteredTasks = tasks.filter(t =>
    !searchQuery.trim() ||
    t.goal.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#080D0B] text-[#F0F7F2] flex font-sans selection:bg-[#55E6A5]/25 selection:text-[#55E6A5]">
      
      {/* Obsidian Left Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onNavigate={handleNavigate}
        metrics={metrics}
        onNewTaskClick={scrollToTaskInput}
      />

      {/* Main Workspace Column */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        
        {/* Top Header Bar */}
        <TopBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          activeStatus={activeTask?.status || 'IDLE'}
          onReset={handleResetSandbox}
          isResetting={isResetting}
          onOpenSettings={() => handleNavigate('advanced', 'settings')}
        />

        {/* Constrained Main Workspace Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5 space-y-5">
          
          {/* ========================================================================= */}
          {/* TAB 1: STUDIO / OVERVIEW (Obsidian Intelligence Flagship Experience)      */}
          {/* ========================================================================= */}
          {(currentTab === 'studio' || currentTab === 'agent') && (
            <div className="space-y-5">
              
              {/* Hero Banner: Autonomous AI Worker */}
              <div className="relative overflow-hidden rounded-2xl border border-[#263A2E] bg-gradient-to-r from-[#101914] via-[#142019] to-[#080D0B] p-6 lg:p-7 shadow-card-subtle">
                
                {/* Background Fluid Light Waves */}
                <div className="absolute right-0 top-0 bottom-0 w-1/2 pointer-events-none opacity-40 overflow-hidden">
                  <div className="absolute -top-12 -right-12 w-96 h-96 rounded-full bg-gradient-to-br from-[#55E6A5]/20 via-[#FFC66D]/15 to-transparent blur-3xl" />
                  <div className="absolute top-20 right-32 w-64 h-64 rounded-full bg-gradient-to-tr from-[#A99BFF]/20 to-transparent blur-2xl" />
                </div>

                <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                  
                  {/* Left Column: Heading & Value Proposition */}
                  <div className="max-w-2xl space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#FFC66D] px-2 py-0.5 rounded-full bg-[#FFC66D]/10 border border-[#FFC66D]/30 font-mono">
                        Autonomous AI Worker
                      </span>
                    </div>

                    <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F0F7F2] tracking-tight font-sans">
                      From instructions to <span className="text-[#FFC66D]">verified outcomes</span>
                    </h1>

                    <p className="text-xs sm:text-sm text-[#A0B2A6] leading-relaxed">
                      Give AgentOS a goal. It plans, uses tools, adapts, verifies results, and handles the work for you.
                    </p>

                    {/* Action Buttons */}
                    <div className="pt-2 flex flex-wrap items-center gap-3">
                      <button
                        onClick={scrollToTaskInput}
                        className="px-4 py-2 rounded-xl bg-[#FFC66D] hover:bg-[#F5B752] text-[#080D0B] font-bold text-xs flex items-center space-x-1.5 shadow-glow-amber transition active:scale-98 cursor-pointer"
                      >
                        <Sparkles className="w-3.5 h-3.5 fill-[#080D0B]" />
                        <span>New Task</span>
                      </button>

                      <button
                        onClick={() => {
                          scrollToTaskInput();
                        }}
                        className="px-4 py-2 rounded-xl border border-[#263A2E] bg-[#142019] hover:bg-[#1C2D24] text-[#A0B2A6] hover:text-[#F0F7F2] font-semibold text-xs transition cursor-pointer"
                      >
                        View Examples
                      </button>
                    </div>
                  </div>

                  {/* Right Column: Workflow Stage Pills (Plan, Execute, Verify) */}
                  <div className="flex md:flex-col items-center gap-2.5 shrink-0">
                    
                    {/* Plan Pill */}
                    <button
                      onClick={() => {
                        const el = document.getElementById('execution-section');
                        if (el) el.scrollIntoView({ behavior: 'smooth' });
                      }}
                      className="px-3 py-1.5 rounded-xl bg-[#142019]/90 border border-[#263A2E] text-xs font-semibold text-[#A99BFF] flex items-center space-x-2 shadow-xs hover:border-[#A99BFF]/60 transition cursor-pointer"
                      title="Inspect dynamic multi-step plan"
                    >
                      <span className="w-2 h-2 rounded-full bg-[#A99BFF]" />
                      <span>Plan</span>
                    </button>

                    {/* Execute Pill */}
                    <button
                      onClick={() => {
                        const el = document.getElementById('execution-snapshot-card');
                        if (el) el.scrollIntoView({ behavior: 'smooth' });
                      }}
                      className="px-3.5 py-1.5 rounded-xl bg-[#1C2D24] border border-[#FFC66D]/50 text-xs font-bold text-[#FFC66D] flex items-center space-x-2 shadow-glow-amber active-step-halo hover:border-[#FFC66D] transition cursor-pointer"
                      title="Inspect live execution trace"
                    >
                      <span className="w-2 h-2 rounded-full bg-[#FFC66D] animate-pulse" />
                      <span>Execute</span>
                    </button>

                    {/* Verify Pill */}
                    <button
                      onClick={() => {
                        const el = document.getElementById('evidence-section');
                        if (el) el.scrollIntoView({ behavior: 'smooth' });
                      }}
                      className="px-3 py-1.5 rounded-xl bg-[#142019]/90 border border-[#55E6A5]/50 text-xs font-bold text-[#55E6A5] flex items-center space-x-2 shadow-glow-jade hover:border-[#55E6A5] transition cursor-pointer"
                      title="Inspect independent cryptographic assertions"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#55E6A5]" />
                      <span>Verify</span>
                    </button>

                  </div>

                </div>
              </div>

              {/* Real-time KPI Metric Cards */}
              <MetricsOverview metrics={metrics} />

              {/* Describe Your Task Card */}
              <div ref={taskInputRef}>
                <TaskInput onRun={handleRunTask} isRunning={isRunning} />
              </div>

              {/* Three-Card Bottom Workspace: Recent Tasks, Execution Snapshot, Audit Trail */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
                
                {/* ------------------------------------------------------------- */}
                {/* CARD 1: RECENT TASKS                                          */}
                {/* ------------------------------------------------------------- */}
                <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-4 shadow-card-subtle space-y-3">
                  <div className="flex items-center justify-between border-b border-[#263A2E] pb-2.5">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-[#F0F7F2]">
                        Recent Tasks
                      </span>
                    </div>
                    <button
                      onClick={() => setCurrentTab('history')}
                      className="text-[11px] text-[#A0B2A6] hover:text-[#55E6A5] transition flex items-center space-x-0.5"
                    >
                      <span>View all</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>

                  <div className="space-y-2 max-h-[440px] overflow-y-auto pr-0.5">
                    {filteredTasks.slice(0, 6).map((t) => {
                      const isSelected = activeTask?.id === t.id;
                      const formattedTime = new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                      const isCompleted = t.status === 'COMPLETED';
                      const isWaiting = t.status === 'WAITING_FOR_APPROVAL';
                      const isRunningTask = t.status === 'RUNNING';

                      return (
                        <div
                          key={t.id}
                          onClick={() => handleSelectHistoricalTask(t.id)}
                          className={`p-2.5 rounded-xl border transition cursor-pointer flex items-center justify-between gap-2.5 ${
                            isSelected
                              ? 'bg-[#1C2D24] border-[#55E6A5] shadow-xs'
                              : 'bg-[#142019] border-[#263A2E] hover:border-[#55E6A5]/40 hover:bg-[#1C2D24]/60'
                          }`}
                        >
                          <div className="flex items-start space-x-2.5 min-w-0">
                            <div className="p-1.5 rounded-lg bg-[#101914] border border-[#263A2E] text-[#55E6A5] shrink-0 mt-0.5">
                              <FileText className="w-3.5 h-3.5" />
                            </div>
                            <div className="min-w-0">
                              <div className="text-xs font-semibold text-[#F0F7F2] truncate" title={t.goal}>
                                {t.goal}
                              </div>
                              <div className="text-[10px] font-mono text-[#718278] truncate mt-0.5 flex items-center space-x-1.5">
                                <span>{t.extracted_data?.invoice_number || t.id.slice(0, 10)}</span>
                                <span>•</span>
                                <span>{t.steps_count} steps</span>
                              </div>
                            </div>
                          </div>

                          <div className="text-right shrink-0">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold block ${
                              isCompleted
                                ? 'bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30'
                                : isWaiting
                                ? 'bg-[#FFC66D]/15 text-[#FFC66D] border border-[#FFC66D]/40'
                                : isRunningTask
                                ? 'bg-[#7AB8FF]/10 text-[#7AB8FF] border border-[#7AB8FF]/30'
                                : 'bg-[#101914] text-[#718278] border border-[#263A2E]'
                            }`}>
                              {isCompleted ? 'Completed' : isWaiting ? 'Needs Input' : t.status}
                            </span>
                            <span className="text-[10px] font-mono text-[#718278] mt-1 block">
                              {formattedTime}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* ------------------------------------------------------------- */}
                {/* CARD 2: EXECUTION SNAPSHOT • LIVE                             */}
                {/* ------------------------------------------------------------- */}
                <div id="execution-snapshot-card" className="bg-[#101914] border border-[#263A2E] rounded-xl p-4 shadow-card-subtle space-y-3">
                  <div className="flex items-center justify-between border-b border-[#263A2E] pb-2.5">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-[#F0F7F2]">
                        Execution Snapshot
                      </span>
                      <span className="flex items-center text-[10px] font-bold text-[#55E6A5] bg-[#55E6A5]/10 border border-[#55E6A5]/30 px-1.5 py-0.2 rounded-full">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#55E6A5] animate-pulse mr-1" /> Live
                      </span>
                    </div>

                    <span className="text-[10px] font-mono text-[#718278]">
                      {activeTask ? new Date(activeTask.created_at).toLocaleTimeString() : '00:00:00'}
                    </span>
                  </div>

                  {/* Connected Step Stream */}
                  {activeTask && (activeTask.steps || []).length > 0 ? (
                    <div className="space-y-3 max-h-[440px] overflow-y-auto pr-0.5">
                      {(activeTask.steps || []).map((step, idx, arr) => {
                        const isLast = idx === arr.length - 1;
                        const isActiveStep = isLast && isRunning;
                        const isSuccess = step.status === 'SUCCESS';

                        return (
                          <div key={step.step_number} className="relative flex items-start space-x-3 text-xs">
                            
                            {/* Connected vertical line */}
                            {!isLast && (
                              <div className="absolute left-2.5 top-6 bottom-0 w-[1px] bg-[#263A2E] -mb-3" />
                            )}

                            {/* Node icon */}
                            <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 z-10 ${
                              isActiveStep
                                ? 'bg-[#FFC66D] text-[#080D0B] font-bold active-step-halo'
                                : isSuccess
                                ? 'bg-[#55E6A5]/20 text-[#55E6A5] border border-[#55E6A5]/40'
                                : 'bg-[#142019] text-[#718278] border border-[#263A2E]'
                            }`}>
                              {isSuccess ? <Check className="w-3 h-3 stroke-[2.5]" /> : step.step_number}
                            </div>

                            {/* Step content */}
                            <div className={`flex-1 p-2 rounded-xl border transition ${
                              isActiveStep
                                ? 'bg-[#1C2D24] border-[#FFC66D]/60'
                                : 'bg-[#142019] border-[#263A2E]'
                            }`}>
                              <div className="flex items-center justify-between">
                                <span className={`font-semibold ${isActiveStep ? 'text-[#FFC66D]' : 'text-[#F0F7F2]'}`}>
                                  {step.tool_name || 'Autonomous Reasoning'}
                                </span>
                                <span className="font-mono text-[10px] text-[#718278]">
                                  {step.latency_ms?.toFixed(0) || 0}ms
                                </span>
                              </div>
                              <p className="text-[11px] text-[#A0B2A6] mt-0.5 line-clamp-2 italic">
                                "{step.thought}"
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="p-8 text-center text-xs text-[#718278] space-y-2">
                      <Terminal className="w-6 h-6 mx-auto text-[#263A2E]" />
                      <p>Awaiting task execution</p>
                      <p className="text-[11px]">Click "Launch Autonomous Worker" above to stream live steps.</p>
                    </div>
                  )}
                </div>

                {/* ------------------------------------------------------------- */}
                {/* CARD 3: EXECUTION AUDIT TRAIL                                 */}
                {/* ------------------------------------------------------------- */}
                <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-4 shadow-card-subtle space-y-3">
                  <div className="flex items-center justify-between border-b border-[#263A2E] pb-2.5">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#F0F7F2]">
                      Execution Audit Trail
                    </span>
                    <span className="text-[10px] font-mono text-[#718278] bg-[#142019] px-2 py-0.5 rounded-full border border-[#263A2E]">
                      {tasks.length} Runs
                    </span>
                  </div>

                  <div className="space-y-2 max-h-[440px] overflow-y-auto pr-0.5">
                    {tasks.slice(0, 6).map((t) => {
                      const isVerified = t.verification?.verified;
                      const formattedTime = new Date(t.created_at).toLocaleTimeString();

                      return (
                        <div
                          key={t.id}
                          onClick={() => handleSelectHistoricalTask(t.id)}
                          className="p-2.5 rounded-xl border border-[#263A2E] bg-[#142019] hover:bg-[#1C2D24]/60 hover:border-[#55E6A5]/40 transition cursor-pointer flex items-center justify-between group"
                        >
                          <div className="min-w-0 flex-1 pr-2">
                            <div className="flex items-center space-x-2">
                              <span className="text-[10px] font-bold uppercase px-1.5 py-0.2 rounded bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30">
                                {t.status}
                              </span>
                              <span className="text-[10px] font-mono text-[#718278]">{formattedTime}</span>
                            </div>

                            <div className="text-xs font-medium text-[#F0F7F2] truncate mt-1 group-hover:text-[#55E6A5] transition">
                              {t.goal}
                            </div>

                            <div className="flex items-center space-x-2 text-[10px] font-mono text-[#718278] mt-0.5">
                              <span>ID: {t.id.slice(0, 8)}...</span>
                              <span>•</span>
                              <span>{t.steps_count} steps</span>
                              {t.extracted_data?.invoice_number && (
                                <>
                                  <span>•</span>
                                  <span className="text-[#55E6A5] font-semibold">{t.extracted_data.invoice_number}</span>
                                </>
                              )}
                            </div>
                          </div>

                          <div className="text-[#718278] group-hover:text-[#55E6A5] transition pl-1">
                            <ArrowRight className="w-3.5 h-3.5" />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>

              {/* Full Ground Truth Evidence & Detailed Plan for active task */}
              {activeTask && (
                <div id="evidence-section" className="grid grid-cols-1 lg:grid-cols-2 gap-5 pt-2">
                  <div id="execution-section">
                    <ExecutionTimeline task={activeTask} />
                  </div>
                  <div>
                    <EvidenceCard task={activeTask} />
                  </div>
                </div>
              )}

            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 2: COMPANY SANDBOX DATABASE                                           */}
          {/* ========================================================================= */}
          {currentTab === 'sandbox' && (
            <CompanySandbox
              vendors={vendors}
              invoices={invoices}
              payables={payables}
              taskItems={taskItems}
              supportTickets={supportTickets}
              inventory={inventory}
              purchaseRequests={purchaseRequests}
              initialSubTab={sandboxSubTab}
              onRefresh={refreshSandboxData}
              onRunTask={(goal) => {
                setCurrentTab('studio');
                handleRunTask(goal, true, false);
              }}
            />
          )}

          {/* ========================================================================= */}
          {/* TAB 3: DETAILED TASK AUDIT TRAIL                                          */}
          {/* ========================================================================= */}
          {currentTab === 'history' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              <div className="lg:col-span-1">
                <TaskHistory
                  tasks={tasks}
                  selectedTaskId={selectedTaskId}
                  onSelectTask={handleSelectHistoricalTask}
                />
              </div>
              <div className="lg:col-span-2 space-y-5">
                <ExecutionTimeline task={activeTask} />
                <EvidenceCard task={activeTask} />
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 4: ADVANCED ENGINE & BENCHMARKS                                        */}
          {/* ========================================================================= */}
          {currentTab === 'advanced' && (
            <AdvancedCapabilities
              tasks={tasks}
              initialSubTab={advancedSubTab}
              onSelectTaskForInspection={handleSelectHistoricalTask}
            />
          )}

        </main>

        {/* Global Human-in-the-Loop Sign-off Modal */}
        {activeTask?.status === 'WAITING_FOR_APPROVAL' && activeTask.pending_approval && (
          <ApprovalModal
            approval={activeTask.pending_approval}
            onApprove={handleApprove}
            onReject={handleReject}
            isProcessing={isApproving}
          />
        )}

        {/* Footer */}
        <footer className="border-t border-[#263A2E] bg-[#080D0B] py-3 text-center text-[11px] text-[#718278] font-mono">
          AgentOS • Obsidian Intelligence • Autonomous AI Task Worker
        </footer>

      </div>

    </div>
  );
};

export default App;
