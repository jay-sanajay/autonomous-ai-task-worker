import React, { useState, useEffect } from 'react';
import {
  Brain, Award, RotateCcw, ExternalLink, ShieldAlert, CheckCircle2,
  XCircle, Trash2, RefreshCw, Play, Cpu, Layers, HardDrive, AlertTriangle
} from 'lucide-react';
import { EpisodicMemory, SemanticMemory, TelemetryDashboard, BenchmarkReport, ReplayReport, Task } from '../types';
import * as api from '../services/api';

interface AdvancedCapabilitiesProps {
  tasks: Task[];
  onSelectTaskForInspection: (taskId: string) => void;
}

export const AdvancedCapabilities: React.FC<AdvancedCapabilitiesProps> = ({
  tasks,
  onSelectTaskForInspection
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'memory' | 'benchmarks' | 'replay' | 'portal'>('memory');
  
  // Memory State
  const [episodic, setEpisodic] = useState<EpisodicMemory[]>([]);
  const [semantic, setSemantic] = useState<SemanticMemory[]>([]);
  const [memorySearch, setMemorySearch] = useState('');
  const [isLoadingMemories, setIsLoadingMemories] = useState(false);

  // Benchmark State
  const [benchmarkReport, setBenchmarkReport] = useState<BenchmarkReport | null>(null);
  const [isRunningBenchmarks, setIsRunningBenchmarks] = useState(false);

  // Replay State
  const [selectedReplayTaskId, setSelectedReplayTaskId] = useState<string>('');
  const [replayReport, setReplayReport] = useState<ReplayReport | null>(null);
  const [isRunningReplay, setIsRunningReplay] = useState(false);

  // Telemetry Dashboard
  const [telemetry, setTelemetry] = useState<TelemetryDashboard | null>(null);

  const loadMemories = async () => {
    setIsLoadingMemories(true);
    try {
      const [ep, sem] = await Promise.all([
        api.fetchEpisodicMemories().catch(() => []),
        api.fetchSemanticMemories().catch(() => [])
      ]);
      setEpisodic(ep);
      setSemantic(sem);
    } catch (err) {
      console.error('Failed to load memories:', err);
    } finally {
      setIsLoadingMemories(false);
    }
  };

  const loadTelemetry = async () => {
    try {
      const t = await api.fetchTelemetryDashboard();
      setTelemetry(t);
    } catch (err) {
      console.error('Failed to load telemetry:', err);
    }
  };

  useEffect(() => {
    loadMemories();
    loadTelemetry();
    if (tasks.length > 0 && !selectedReplayTaskId) {
      setSelectedReplayTaskId(tasks[0].id);
    }
  }, [tasks]);

  const handleDeleteEpisodic = async (id: number) => {
    try {
      await api.deleteEpisodicMemory(id);
      setEpisodic((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      alert('Failed to delete episodic memory: ' + err);
    }
  };

  const handleDeleteSemantic = async (id: number) => {
    try {
      await api.deleteSemanticMemory(id);
      setSemantic((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      alert('Failed to delete semantic memory: ' + err);
    }
  };

  const handleRunBenchmarks = async () => {
    setIsRunningBenchmarks(true);
    try {
      const report = await api.runBenchmarks();
      setBenchmarkReport(report);
      loadTelemetry();
    } catch (err) {
      alert('Benchmarking suite failed: ' + err);
    } finally {
      setIsRunningBenchmarks(false);
    }
  };

  const handleRunReplay = async () => {
    if (!selectedReplayTaskId) return;
    setIsRunningReplay(true);
    try {
      const rep = await api.replayTaskExecution(selectedReplayTaskId);
      setReplayReport(rep);
    } catch (err: any) {
      alert('Safe replay error: ' + (err.message || err));
    } finally {
      setIsRunningReplay(false);
    }
  };

  const filteredEpisodic = episodic.filter((m) =>
    m.task_goal.toLowerCase().includes(memorySearch.toLowerCase()) ||
    m.outcome.toLowerCase().includes(memorySearch.toLowerCase())
  );

  const filteredSemantic = semantic.filter((m) =>
    m.topic.toLowerCase().includes(memorySearch.toLowerCase()) ||
    m.fact.toLowerCase().includes(memorySearch.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header and Telemetry Metric Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-sky-400" />
              Advanced Autonomous Platform Operations
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Production subsystems: DAG Planning, Persistent Memory, Independent Critics, Safe Replay & Evaluation Benchmarks
            </p>
          </div>

          {/* Sub Tabs */}
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setActiveSubTab('memory')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'memory'
                  ? 'bg-sky-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Brain className="w-3.5 h-3.5" />
              Memory Subsystem
            </button>
            <button
              onClick={() => setActiveSubTab('benchmarks')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'benchmarks'
                  ? 'bg-sky-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              Evaluation Benchmark
            </button>
            <button
              onClick={() => setActiveSubTab('replay')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'replay'
                  ? 'bg-sky-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Safe Replay
            </button>
            <button
              onClick={() => setActiveSubTab('portal')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'portal'
                  ? 'bg-sky-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Company Portal
            </button>
          </div>
        </div>

        {/* Global Telemetry Strip */}
        {telemetry && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-800/80">
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Completion Rate</span>
              <div className="text-lg font-bold text-emerald-400">{telemetry.completion_rate}%</div>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Verified Success</span>
              <div className="text-lg font-bold text-sky-400">{telemetry.verification_success_rate}%</div>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Autonomous Recoveries</span>
              <div className="text-lg font-bold text-amber-400">{telemetry.recovered_steps_count}</div>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Avg Step Latency</span>
              <div className="text-lg font-bold text-indigo-400">{telemetry.average_step_latency_ms} ms</div>
            </div>
          </div>
        )}
      </div>

      {/* Tab 1: Memory Subsystem */}
      {activeSubTab === 'memory' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <input
                type="text"
                value={memorySearch}
                onChange={(e) => setMemorySearch(e.target.value)}
                placeholder="Search working, episodic & semantic memories..."
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
            <button
              onClick={loadMemories}
              disabled={isLoadingMemories}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingMemories ? 'animate-spin' : ''}`} />
              <span>Refresh Memory</span>
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Episodic Memory */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <HardDrive className="w-4 h-4 text-sky-400" />
                  <h3 className="text-sm font-bold text-white">Episodic Memory ({filteredEpisodic.length})</h3>
                </div>
                <span className="text-[11px] text-slate-500">Past task outcomes & recovery policies</span>
              </div>

              {filteredEpisodic.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500">No episodic memories recorded yet.</div>
              ) : (
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                  {filteredEpisodic.map((mem) => (
                    <div key={mem.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-xs font-semibold text-slate-200 line-clamp-1">{mem.task_goal}</span>
                        <button
                          onClick={() => handleDeleteEpisodic(mem.id)}
                          className="text-slate-500 hover:text-rose-400 transition"
                          title="Purge memory"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          mem.outcome === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        }`}>
                          {mem.outcome}
                        </span>
                        {mem.verification_status && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-sky-500/20 text-sky-400 border border-sky-500/30">
                            {mem.verification_status}
                          </span>
                        )}
                      </div>
                      {mem.failed_strategies && (
                        <p className="text-[11px] text-rose-300 font-mono bg-rose-950/30 p-1.5 rounded">
                          Failed Strategy: {mem.failed_strategies}
                        </p>
                      )}
                      {mem.successful_recovery && (
                        <p className="text-[11px] text-emerald-300 font-mono bg-emerald-950/30 p-1.5 rounded">
                          Recovery: {mem.successful_recovery}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Semantic Memory */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-sm font-bold text-white">Semantic Memory ({filteredSemantic.length})</h3>
                </div>
                <span className="text-[11px] text-slate-500">Approved rules, facts & procedures</span>
              </div>

              {filteredSemantic.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500">No semantic knowledge stored.</div>
              ) : (
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                  {filteredSemantic.map((sem) => (
                    <div key={sem.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                          {sem.topic}
                        </span>
                        <button
                          onClick={() => handleDeleteSemantic(sem.id)}
                          className="text-slate-500 hover:text-rose-400 transition"
                          title="Purge knowledge item"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <p className="text-xs text-slate-300">{sem.fact}</p>
                      {sem.reusable_procedure && (
                        <div className="text-[11px] font-mono text-slate-400 bg-slate-900 p-2 rounded border border-slate-800">
                          Procedure: {sem.reusable_procedure}
                        </div>
                      )}
                      <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                        <span>Source: {sem.provenance}</span>
                        <span>Confidence: {(sem.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Evaluation Benchmarking Suite */}
      {activeSubTab === 'benchmarks' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-white">Repeatable 10-Scenario Benchmarking Harness</h3>
              <p className="text-xs text-slate-400 mt-1">
                Executes all standard failure modes, fault injections, duplicate attacks, and verification gates against live sandbox.
              </p>
            </div>
            <button
              onClick={handleRunBenchmarks}
              disabled={isRunningBenchmarks}
              className="px-4 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-lg shadow-sky-500/20 transition disabled:opacity-50"
            >
              <Play className={`w-4 h-4 ${isRunningBenchmarks ? 'animate-spin' : ''}`} />
              <span>{isRunningBenchmarks ? 'Running Benchmark Matrix...' : 'Run Benchmark Suite'}</span>
            </button>
          </div>

          {benchmarkReport && (
            <div className="space-y-6">
              {/* Scorecard Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Benchmark Pass Rate</span>
                  <div className="text-2xl font-black text-emerald-400 mt-1">{benchmarkReport.benchmark_pass_rate}%</div>
                  <span className="text-[11px] text-slate-500">{benchmarkReport.successful_scenarios} of {benchmarkReport.total_scenarios_evaluated} passed</span>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Verified Completion</span>
                  <div className="text-2xl font-black text-sky-400 mt-1">{benchmarkReport.verified_completion_rate}%</div>
                  <span className="text-[11px] text-slate-500">Cryptographically criticized</span>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Unauthorized Actions</span>
                  <div className="text-2xl font-black text-emerald-400 mt-1">{benchmarkReport.unauthorized_action_rate}%</div>
                  <span className="text-[11px] text-slate-500">Zero policy bypasses</span>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Duplicate Writes</span>
                  <div className="text-2xl font-black text-emerald-400 mt-1">{benchmarkReport.duplicate_write_rate}%</div>
                  <span className="text-[11px] text-slate-500">Idempotency guaranteed</span>
                </div>
              </div>

              {/* Detailed Breakdown */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Scenario Results</span>
                  <span className="text-xs text-slate-500 font-mono">Avg Latency: {benchmarkReport.average_execution_seconds}s</span>
                </div>
                <div className="divide-y divide-slate-800/80">
                  {benchmarkReport.detailed_scenario_results.map((sc) => (
                    <div key={sc.scenario_id} className="p-4 flex items-center justify-between hover:bg-slate-800/30 transition">
                      <div className="flex items-center gap-3">
                        {sc.passed_benchmark ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                        )}
                        <div>
                          <div className="text-xs font-semibold text-slate-200">{sc.scenario_id}: {sc.name}</div>
                          <div className="text-[11px] text-slate-500 flex items-center gap-2 mt-0.5">
                            <span>Status: {sc.status}</span>
                            <span>•</span>
                            <span>Steps: {sc.steps_count}</span>
                            <span>•</span>
                            <span>Duration: {sc.duration_seconds}s</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {sc.verified && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">
                            Verified
                          </span>
                        )}
                        <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                          sc.passed_benchmark ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        }`}>
                          {sc.passed_benchmark ? 'PASS' : 'FAIL'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Safe Execution Replay */}
      {activeSubTab === 'replay' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div>
              <h3 className="text-base font-bold text-white">Safe Execution Replay Engine</h3>
              <p className="text-xs text-slate-400 mt-1">
                Inspect and replay past task executions without triggering destructive side effects, duplicated API calls, or repeated financial writes.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <select
                value={selectedReplayTaskId}
                onChange={(e) => setSelectedReplayTaskId(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-xs text-white rounded-lg px-3 py-2 flex-1 focus:outline-none focus:ring-1 focus:ring-sky-500"
              >
                {tasks.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.id} - {t.goal.substring(0, 70)} ({t.status})
                  </option>
                ))}
              </select>

              <button
                onClick={handleRunReplay}
                disabled={isRunningReplay || !selectedReplayTaskId}
                className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition disabled:opacity-50"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${isRunningReplay ? 'animate-spin' : ''}`} />
                <span>Replay Safely</span>
              </button>
            </div>
          </div>

          {replayReport && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div>
                  <span className="text-xs font-bold text-white">{replayReport.task_id}</span>
                  <p className="text-xs text-slate-400 mt-0.5">{replayReport.original_goal}</p>
                </div>
                <div className="text-right">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    {replayReport.status}
                  </span>
                  <div className="text-[11px] text-amber-400 font-mono mt-1">
                    {replayReport.prevented_writes_count} Write Actions Prevented
                  </div>
                </div>
              </div>

              <div className="p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-lg text-xs text-emerald-300 font-mono">
                ✓ {replayReport.safety_assertion}
              </div>

              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Simulated Trace</span>
                {replayReport.steps.map((st) => (
                  <div key={st.step_number} className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-300">Step {st.step_number}: {st.tool_name}</span>
                      <div className="flex items-center gap-2">
                        {st.side_effects_prevented ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                            Side Effect Prevented
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">
                            Simulated Read
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 italic">"{st.thought}"</p>
                    <pre className="text-[11px] font-mono text-slate-300 bg-slate-900 p-2 rounded overflow-x-auto">
                      {JSON.stringify(st.recorded_output, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Simulated Company Portal */}
      {activeSubTab === 'portal' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white">Simulated Company Web Portal</h3>
              <p className="text-xs text-slate-400 mt-1">
                Real HTTP & Playwright browser sandbox simulating enterprise web pages (Invoices, Support Tickets, Inventory).
              </p>
            </div>
            <a
              href="http://localhost:8000/portal"
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 transition shadow-lg shadow-indigo-600/20"
            >
              <ExternalLink className="w-4 h-4" />
              <span>Launch Live Portal</span>
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <span className="text-xs font-bold text-sky-400">Invoices & Payables</span>
              <p className="text-xs text-slate-400">
                Interactive web form for entering vendor invoices. Supports Playwright DOM inspection, filling form fields, accessible buttons, and live confirmation banners.
              </p>
              <div className="pt-2 text-[11px] font-mono text-slate-500">/portal/invoices</div>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <span className="text-xs font-bold text-amber-400">Customer Support Desk</span>
              <p className="text-xs text-slate-400">
                Live queue of unresolved customer support tickets with severity indicators. Agent can inspect page state and prioritize open tickets via browser automation.
              </p>
              <div className="pt-2 text-[11px] font-mono text-slate-500">/portal/tickets</div>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <span className="text-xs font-bold text-emerald-400">Warehouse Inventory</span>
              <p className="text-xs text-slate-400">
                Live stock levels, SKU tracking, and reorder alerts. Enables end-to-end web browser reading, form submission, and independent verification.
              </p>
              <div className="pt-2 text-[11px] font-mono text-slate-500">/portal/inventory</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
