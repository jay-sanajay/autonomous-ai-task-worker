import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { MetricsOverview } from './components/MetricsOverview';
import { TaskInput } from './components/TaskInput';
import { ExecutionTimeline } from './components/ExecutionTimeline';
import { EvidenceCard } from './components/EvidenceCard';
import { ApprovalModal } from './components/ApprovalModal';
import { CompanySandbox } from './components/CompanySandbox';
import { TaskHistory } from './components/TaskHistory';
import { Task, Vendor, InvoiceDoc, Payable, SandboxMetrics, TaskItem, SupportTicket, InventoryItem, PurchaseRequest } from './types';
import * as api from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'agent' | 'sandbox' | 'history'>('agent');
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

  // Polling ref to avoid concurrent poll loops
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Refresh sandbox entities and metrics
  const refreshSandboxData = useCallback(async () => {
    try {
      const [v, inv, p, m, t, ti, st, inlist, pr] = await Promise.all([
        api.fetchVendors(),
        api.fetchInvoices(),
        api.fetchPayables(),
        api.fetchMetrics(),
        api.fetchTasks(),
        api.fetchTaskItems().catch(() => []),
        api.fetchSupportTickets().catch(() => []),
        api.fetchInventory().catch(() => []),
        api.fetchPurchaseRequests().catch(() => [])
      ]);
      setVendors(v);
      setInvoices(inv);
      setPayables(p);
      setMetrics(m);
      setTasks(t);
      setTaskItems(ti);
      setSupportTickets(st);
      setInventory(inlist);
      setPurchaseRequests(pr);
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
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
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
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 700);

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [activeTask?.id, isRunning, refreshSandboxData]);

  // Select a historical task to inspect
  const handleSelectHistoricalTask = async (taskId: string) => {
    setSelectedTaskId(taskId);
    try {
      const details = await api.fetchTaskDetails(taskId);
      setActiveTask(details);
      setCurrentTab('agent');
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
      setTasks((prev) => [newTask, ...prev]);
      setCurrentTab('agent');
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
      const updated = await api.approveTask(activeTask.id, 'Finance Director (HITL)', feedback);
      setActiveTask(updated);
      setIsRunning(true); // resume polling
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
      const updated = await api.rejectTask(activeTask.id, 'Finance Director (HITL)', feedback);
      setActiveTask(updated);
      setIsRunning(false);
      refreshSandboxData();
    } catch (err) {
      console.error('Rejection failed:', err);
    } finally {
      setIsApproving(false);
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-sky-500/30 selection:text-sky-200">
      {/* Top Navigation */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={(tab) => setCurrentTab(tab as any)}
        onReset={handleResetSandbox}
        isResetting={isResetting}
        activeStatus={activeTask?.status || 'IDLE'}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Real-time Metrics Banner */}
        <MetricsOverview metrics={metrics} />

        {/* Tab 1: Agent Operation & Live Execution */}
        {currentTab === 'agent' && (
          <div className="space-y-6">
            <TaskInput onRun={handleRunTask} isRunning={isRunning} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
              {/* Left 2 Cols: Step-by-Step Execution Plan & ReAct Trace */}
              <div className="lg:col-span-2 space-y-6">
                <ExecutionTimeline task={activeTask} />
              </div>

              {/* Right 1 Col: Ground Truth Evidence, Memory, & Quick Audit */}
              <div className="space-y-6">
                <EvidenceCard task={activeTask} />
                <TaskHistory
                  tasks={tasks}
                  selectedTaskId={selectedTaskId}
                  onSelectTask={handleSelectHistoricalTask}
                />
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Company Sandbox Database */}
        {currentTab === 'sandbox' && (
          <CompanySandbox
            vendors={vendors}
            invoices={invoices}
            payables={payables}
            taskItems={taskItems}
            supportTickets={supportTickets}
            inventory={inventory}
            purchaseRequests={purchaseRequests}
            onRefresh={refreshSandboxData}
          />
        )}

        {/* Tab 3: Detailed Task Audit Trail */}
        {currentTab === 'history' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <TaskHistory
                tasks={tasks}
                selectedTaskId={selectedTaskId}
                onSelectTask={handleSelectHistoricalTask}
              />
            </div>
            <div className="lg:col-span-2 space-y-6">
              <ExecutionTimeline task={activeTask} />
              <EvidenceCard task={activeTask} />
            </div>
          </div>
        )}
      </main>

      {/* Human-in-the-Loop Modal */}
      {activeTask?.status === 'WAITING_FOR_APPROVAL' && activeTask.pending_approval && (
        <ApprovalModal
          approval={activeTask.pending_approval}
          onApprove={handleApprove}
          onReject={handleReject}
          isProcessing={isApproving}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-4 text-center text-xs text-slate-500 font-mono">
        AgentOS v1.0.0 • Autonomous AI Task Worker • CentrAlign AI Engineering Evaluation System
      </footer>
    </div>
  );
};

export default App;
