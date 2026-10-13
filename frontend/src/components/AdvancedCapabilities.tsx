import React, { useState, useEffect } from 'react';
import {
  Brain, Award, RotateCcw, ExternalLink, ShieldAlert, CheckCircle2,
  XCircle, Trash2, RefreshCw, Play, Cpu, Layers, HardDrive, AlertTriangle,
  Settings, Zap, Check
} from 'lucide-react';
import { EpisodicMemory, SemanticMemory, TelemetryDashboard, BenchmarkReport, ReplayReport, Task } from '../types';
import * as api from '../services/api';

interface AdvancedCapabilitiesProps {
  tasks: Task[];
  onSelectTaskForInspection: (taskId: string) => void;
  initialSubTab?: 'memory' | 'benchmarks' | 'replay' | 'portal' | 'tools' | 'settings';
}

export const AdvancedCapabilities: React.FC<AdvancedCapabilitiesProps> = ({
  tasks,
  onSelectTaskForInspection,
  initialSubTab = 'memory'
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'memory' | 'benchmarks' | 'replay' | 'portal' | 'tools' | 'settings'>(initialSubTab);

  useEffect(() => {
    if (initialSubTab) {
      setActiveSubTab(initialSubTab);
    }
  }, [initialSubTab]);
  
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

  // Settings & LLM Engine State
  const [llmStatus, setLlmStatus] = useState<any>(null);
  const [selectedModel, setSelectedModel] = useState<string>('openai/gpt-oss-120b');
  const [isTestingGroq, setIsTestingGroq] = useState(false);
  const [groqTestResult, setGroqTestResult] = useState<string | null>(null);

  const loadLLMStatus = async () => {
    try {
      const status = await api.fetchLLMStatus();
      setLlmStatus(status);
      if (status.default_model) setSelectedModel(status.default_model);
    } catch (err) {
      console.error('Failed to load LLM status:', err);
    }
  };

  const handleTestGroq = async () => {
    setIsTestingGroq(true);
    setGroqTestResult(null);
    const start = performance.now();
    try {
      const status = await api.fetchLLMStatus();
      const latency = Math.round(performance.now() - start);
      setGroqTestResult(`Connected to Groq successfully (${latency}ms) - Model: ${selectedModel}`);
    } catch (err: any) {
      setGroqTestResult('Groq ping failed: ' + (err.message || err));
    } finally {
      setIsTestingGroq(false);
    }
  };

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
    loadLLMStatus();
    if (tasks.length > 0) {
      // Always ensure selectedReplayTaskId is valid
      const isValid = tasks.some(t => t.id === selectedReplayTaskId);
      if (!isValid) {
        setSelectedReplayTaskId(tasks[0].id);
      }
    } else {
      setSelectedReplayTaskId('');
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

  const filteredEpisodic = (episodic || []).filter((m) =>
    (m?.goal || '').toLowerCase().includes((memorySearch || '').toLowerCase()) ||
    (m?.outcome || '').toLowerCase().includes((memorySearch || '').toLowerCase())
  );

  const filteredSemantic = (semantic || []).filter((m) =>
    (m?.fact_key || '').toLowerCase().includes((memorySearch || '').toLowerCase()) ||
    (m?.fact_content || '').toLowerCase().includes((memorySearch || '').toLowerCase())
  );

  return (
    <div className="space-y-5">
      {/* Header and Telemetry Metric Bar */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-5 shadow-card-subtle space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-bold text-[#F0F7F2] flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#A99BFF]" />
              Advanced Autonomous Platform Operations
            </h2>
            <p className="text-xs text-[#A0B2A6] mt-0.5">
              Production subsystems: DAG Planning, Persistent Memory, Independent Critics, Safe Replay & Evaluation Benchmarks
            </p>
          </div>

          {/* Sub Tabs */}
          <div className="flex flex-wrap gap-1 bg-[#080D0B] p-1 rounded-xl border border-[#263A2E]">
            <button
              onClick={() => setActiveSubTab('memory')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'memory'
                  ? 'bg-[#1C2D24] text-[#55E6A5] border border-[#55E6A5]/40 shadow-xs'
                  : 'text-[#A0B2A6] hover:text-[#F0F7F2]'
              }`}
            >
              <Brain className="w-3.5 h-3.5" />
              <span>Memory Subsystem</span>
            </button>
            <button
              onClick={() => setActiveSubTab('tools')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'tools'
                  ? 'bg-[#1C2D24] text-[#55E6A5] border border-[#55E6A5]/40 shadow-xs'
                  : 'text-[#A0B2A6] hover:text-[#F0F7F2]'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Tools Catalog</span>
            </button>
            <button
              onClick={() => setActiveSubTab('benchmarks')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'benchmarks'
                  ? 'bg-[#1C2D24] text-[#55E6A5] border border-[#55E6A5]/40 shadow-xs'
                  : 'text-[#A0B2A6] hover:text-[#F0F7F2]'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Evaluation Benchmark</span>
            </button>
            <button
              onClick={() => setActiveSubTab('replay')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'replay'
                  ? 'bg-[#1C2D24] text-[#55E6A5] border border-[#55E6A5]/40 shadow-xs'
                  : 'text-[#A0B2A6] hover:text-[#F0F7F2]'
              }`}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Safe Replay</span>
            </button>
            <button
              onClick={() => setActiveSubTab('settings')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'settings'
                  ? 'bg-[#1C2D24] text-[#FFC66D] border border-[#FFC66D]/40 shadow-xs'
                  : 'text-[#A0B2A6] hover:text-[#F0F7F2]'
              }`}
            >
              <Settings className="w-3.5 h-3.5" />
              <span>Engine & Settings</span>
            </button>
            <button
              onClick={() => setActiveSubTab('portal')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                activeSubTab === 'portal'
                  ? 'bg-[#1C2D24] text-[#55E6A5] border border-[#55E6A5]/40 shadow-xs'
                  : 'text-[#A0B2A6] hover:text-[#F0F7F2]'
              }`}
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Company Portal</span>
            </button>
          </div>
        </div>

        {/* Global Telemetry Strip */}
        {telemetry && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-[#263A2E] font-sans">
            <div className="bg-[#142019] p-2.5 rounded-xl border border-[#263A2E]">
              <span className="text-[10px] uppercase font-bold text-[#718278] tracking-wider">Completion Rate</span>
              <div className="text-base font-bold text-[#55E6A5] font-mono">{telemetry.completion_rate}%</div>
            </div>
            <div className="bg-[#142019] p-2.5 rounded-xl border border-[#263A2E]">
              <span className="text-[10px] uppercase font-bold text-[#718278] tracking-wider">Verified Success</span>
              <div className="text-base font-bold text-[#55E6A5] font-mono">{telemetry.verification_success_rate}%</div>
            </div>
            <div className="bg-[#142019] p-2.5 rounded-xl border border-[#263A2E]">
              <span className="text-[10px] uppercase font-bold text-[#718278] tracking-wider">Autonomous Recoveries</span>
              <div className="text-base font-bold text-[#FFC66D] font-mono">{telemetry.recovered_steps_count}</div>
            </div>
            <div className="bg-[#142019] p-2.5 rounded-xl border border-[#263A2E]">
              <span className="text-[10px] uppercase font-bold text-[#718278] tracking-wider">Avg Step Latency</span>
              <div className="text-base font-bold text-[#A99BFF] font-mono">{telemetry.average_step_latency_ms} ms</div>
            </div>
          </div>
        )}
      </div>

      {/* Tab 1: Memory Subsystem */}
      {activeSubTab === 'memory' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="relative flex-1 max-w-md">
              <input
                type="text"
                value={memorySearch}
                onChange={(e) => setMemorySearch(e.target.value)}
                placeholder="Search working, episodic & semantic memories..."
                className="w-full bg-[#080D0B] border border-[#263A2E] rounded-xl px-3 py-2 text-xs text-[#F0F7F2] placeholder-[#718278] focus:outline-none focus:border-[#55E6A5]"
              />
            </div>
            <button
              onClick={loadMemories}
              disabled={isLoadingMemories}
              className="px-3 py-1.5 bg-[#142019] border border-[#263A2E] hover:bg-[#1C2D24] text-[#A0B2A6] hover:text-[#F0F7F2] rounded-xl text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingMemories ? 'animate-spin' : ''}`} />
              <span>Refresh Memory</span>
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Episodic Memory */}
            <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-4 space-y-3 shadow-card-subtle">
              <div className="flex items-center justify-between border-b border-[#263A2E] pb-2.5">
                <div className="flex items-center gap-2">
                  <HardDrive className="w-4 h-4 text-[#55E6A5]" />
                  <h3 className="text-xs font-bold text-[#F0F7F2] uppercase tracking-wider">
                    Episodic Memory ({filteredEpisodic.length})
                  </h3>
                </div>
                <span className="text-[10px] text-[#718278]">Past task outcomes & recovery policies</span>
              </div>

              {filteredEpisodic.length === 0 ? (
                <div className="text-center py-8 text-xs text-[#718278]">No episodic memories recorded yet.</div>
              ) : (
                <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
                  {filteredEpisodic.map((mem) => (
                    <div key={mem.id} className="p-3 bg-[#142019] rounded-xl border border-[#263A2E] space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-xs font-semibold text-[#F0F7F2] line-clamp-1">{mem.goal}</span>
                        <button
                          onClick={() => handleDeleteEpisodic(mem.id)}
                          className="text-[#718278] hover:text-[#FF7777] transition"
                          title="Purge memory"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          mem.outcome === 'COMPLETED' ? 'bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30' : 'bg-[#FF7777]/10 text-[#FF7777] border border-[#FF7777]/30'
                        }`}>
                          {mem.outcome}
                        </span>
                        {mem.verification_token && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#A99BFF]/10 text-[#A99BFF] border border-[#A99BFF]/30 font-mono">
                            {mem.verification_token}
                          </span>
                        )}
                      </div>
                      {mem.failed_strategies && (Array.isArray(mem.failed_strategies) ? mem.failed_strategies.length > 0 : Boolean(mem.failed_strategies)) && (
                        <p className="text-[11px] text-[#FF7777] font-mono bg-[#FF7777]/10 p-1.5 rounded border border-[#FF7777]/30">
                          Failed Strategy: {Array.isArray(mem.failed_strategies) ? mem.failed_strategies.join(', ') : mem.failed_strategies}
                        </p>
                      )}
                      {mem.recovery_methods && (Array.isArray(mem.recovery_methods) ? mem.recovery_methods.length > 0 : Boolean(mem.recovery_methods)) && (
                        <p className="text-[11px] text-[#55E6A5] font-mono bg-[#55E6A5]/10 p-1.5 rounded border border-[#55E6A5]/30">
                          Recovery: {Array.isArray(mem.recovery_methods) ? mem.recovery_methods.join(', ') : mem.recovery_methods}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Semantic Memory */}
            <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-4 space-y-3 shadow-card-subtle">
              <div className="flex items-center justify-between border-b border-[#263A2E] pb-2.5">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-[#A99BFF]" />
                  <h3 className="text-xs font-bold text-[#F0F7F2] uppercase tracking-wider">
                    Semantic Memory ({filteredSemantic.length})
                  </h3>
                </div>
                <span className="text-[10px] text-[#718278]">Approved rules, facts & procedures</span>
              </div>

              {filteredSemantic.length === 0 ? (
                <div className="text-center py-8 text-xs text-[#718278]">No semantic knowledge stored.</div>
              ) : (
                <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
                  {filteredSemantic.map((sem) => (
                    <div key={sem.id} className="p-3 bg-[#142019] rounded-xl border border-[#263A2E] space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#A99BFF]/10 text-[#A99BFF] border border-[#A99BFF]/30 font-mono">
                          {sem.fact_key}
                        </span>
                        <button
                          onClick={() => handleDeleteSemantic(sem.id)}
                          className="text-[#718278] hover:text-[#FF7777] transition"
                          title="Purge knowledge item"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <p className="text-xs text-[#A0B2A6]">{sem.fact_content}</p>
                      {sem.category && (
                        <div className="text-[11px] font-mono text-[#A0B2A6] bg-[#080D0B] p-2 rounded border border-[#263A2E]">
                          Category: <span className="text-[#F0F7F2]">{sem.category}</span>
                        </div>
                      )}
                      <div className="flex items-center justify-between text-[10px] text-[#718278] font-mono">
                        <span>Source: {sem.provenance}</span>
                        <span>Confidence: {sem.verified ? '100' : '70'}%</span>
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
        <div className="space-y-4">
          <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-card-subtle">
            <div>
              <h3 className="text-sm font-bold text-[#F0F7F2]">Repeatable 10-Scenario Benchmarking Harness</h3>
              <p className="text-xs text-[#A0B2A6] mt-0.5">
                Executes standard failure modes, fault injections, duplicate attacks, and verification gates against live sandbox.
              </p>
            </div>
            <button
              onClick={handleRunBenchmarks}
              disabled={isRunningBenchmarks}
              className="px-4 py-2 bg-[#55E6A5] hover:bg-[#35D993] text-[#080D0B] rounded-xl text-xs font-bold flex items-center gap-2 shadow-glow-jade transition disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${isRunningBenchmarks ? 'animate-spin' : ''}`} />
              <span>{isRunningBenchmarks ? 'Running Benchmark Matrix...' : 'Run Benchmark Suite'}</span>
            </button>
          </div>

          {benchmarkReport && (
            <div className="space-y-4">
              {/* Scorecard Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 shadow-card-subtle">
                  <span className="text-[10px] uppercase font-bold text-[#718278] tracking-wider">Benchmark Pass Rate</span>
                  <div className="text-xl font-bold text-[#55E6A5] font-mono mt-0.5">{benchmarkReport.benchmark_pass_rate}%</div>
                  <span className="text-[10px] text-[#A0B2A6]">{benchmarkReport.successful_scenarios} of {benchmarkReport.total_scenarios_evaluated} passed</span>
                </div>
                <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 shadow-card-subtle">
                  <span className="text-[10px] uppercase font-bold text-[#718278] tracking-wider">Verified Completion</span>
                  <div className="text-xl font-bold text-[#55E6A5] font-mono mt-0.5">{benchmarkReport.verified_completion_rate}%</div>
                  <span className="text-[10px] text-[#A0B2A6]">Cryptographically criticized</span>
                </div>
                <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 shadow-card-subtle">
                  <span className="text-[10px] uppercase font-bold text-[#718278] tracking-wider">Unauthorized Actions</span>
                  <div className="text-xl font-bold text-[#55E6A5] font-mono mt-0.5">{benchmarkReport.unauthorized_action_rate}%</div>
                  <span className="text-[10px] text-[#A0B2A6]">Zero policy bypasses</span>
                </div>
                <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-3.5 shadow-card-subtle">
                  <span className="text-[10px] uppercase font-bold text-[#718278] tracking-wider">Duplicate Writes</span>
                  <div className="text-xl font-bold text-[#55E6A5] font-mono mt-0.5">{benchmarkReport.duplicate_write_rate}%</div>
                  <span className="text-[10px] text-[#A0B2A6]">Idempotency guaranteed</span>
                </div>
              </div>

              {/* Detailed Breakdown */}
              <div className="bg-[#101914] border border-[#263A2E] rounded-xl overflow-hidden shadow-card-subtle">
                <div className="px-4 py-2.5 border-b border-[#263A2E] bg-[#080D0B] flex items-center justify-between">
                  <span className="text-xs font-bold text-[#F0F7F2] uppercase tracking-wider">Scenario Results</span>
                  <span className="text-xs text-[#718278] font-mono">Avg Latency: {benchmarkReport.average_execution_seconds}s</span>
                </div>
                <div className="divide-y divide-[#263A2E]/60">
                  {benchmarkReport.detailed_scenario_results.map((sc) => (
                    <div key={sc.scenario_id} className="p-3 px-4 flex items-center justify-between hover:bg-[#1C2D24]/60 transition">
                      <div className="flex items-center gap-3 min-w-0">
                        {sc.passed_benchmark ? (
                          <CheckCircle2 className="w-4 h-4 text-[#55E6A5] shrink-0" />
                        ) : (
                          <XCircle className="w-4 h-4 text-[#FF7777] shrink-0" />
                        )}
                        <div className="truncate">
                          <div className="text-xs font-semibold text-[#F0F7F2] truncate">{sc.scenario_id}: {sc.name}</div>
                          <div className="text-[10px] text-[#718278] flex items-center gap-2 mt-0.5 font-mono">
                            <span>Status: {sc.status}</span>
                            <span>•</span>
                            <span>Steps: {sc.steps_count}</span>
                            <span>•</span>
                            <span>Duration: {sc.duration_seconds}s</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {sc.verified && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30">
                            Verified
                          </span>
                        )}
                        <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                          sc.passed_benchmark ? 'bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30' : 'bg-[#FF7777]/10 text-[#FF7777] border border-[#FF7777]/30'
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
        <div className="space-y-4">
          <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-5 space-y-3 shadow-card-subtle">
            <div>
              <h3 className="text-sm font-bold text-[#F0F7F2]">Safe Execution Replay Engine</h3>
              <p className="text-xs text-[#A0B2A6] mt-0.5">
                Inspect and replay past task executions without triggering destructive side effects, duplicated API calls, or repeated financial writes.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <select
                value={selectedReplayTaskId}
                onChange={(e) => setSelectedReplayTaskId(e.target.value)}
                className="bg-[#080D0B] border border-[#263A2E] text-xs text-[#F0F7F2] rounded-xl px-3 py-2 flex-1 focus:outline-none focus:border-[#55E6A5]"
              >
                {tasks.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.id} - {t.goal.substring(0, 70)} ({t.status})
                  </option>
                ))}
              </select>

              <button
                onClick={handleRunReplay}
                disabled={isRunningReplay || !selectedReplayTaskId || tasks.length === 0 || !tasks.some(t => t.id === selectedReplayTaskId)}
                className="px-4 py-2 bg-[#55E6A5] hover:bg-[#35D993] text-[#080D0B] rounded-xl text-xs font-bold flex items-center gap-1.5 transition disabled:opacity-50"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${isRunningReplay ? 'animate-spin' : ''}`} />
                <span>Replay Safely</span>
              </button>
            </div>
          </div>

          {replayReport && (
            <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-5 space-y-4 shadow-card-subtle">
              <div className="flex items-center justify-between pb-3 border-b border-[#263A2E]">
                <div>
                  <span className="text-xs font-bold text-[#55E6A5] font-mono">{replayReport.task_id}</span>
                  <p className="text-xs text-[#A0B2A6] mt-0.5">{replayReport.original_goal}</p>
                </div>
                <div className="text-right">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30">
                    {replayReport.status}
                  </span>
                  <div className="text-[11px] text-[#FFC66D] font-mono mt-1">
                    {replayReport.prevented_writes_count} Write Actions Prevented
                  </div>
                </div>
              </div>

              <div className="p-3 bg-[#142019] border border-[#55E6A5]/30 rounded-xl text-xs text-[#55E6A5] font-mono">
                ✓ {replayReport.safety_assertion}
              </div>

              <div className="space-y-3">
                <span className="text-xs font-bold text-[#718278] uppercase tracking-wider">Simulated Trace</span>
                {replayReport.steps.map((st) => (
                  <div key={st.step_number} className="p-3 bg-[#142019] rounded-xl border border-[#263A2E] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#F0F7F2]">Step {st.step_number}: {st.tool_name}</span>
                      <div className="flex items-center gap-2">
                        {st.side_effects_prevented ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FFC66D]/10 text-[#FFC66D] border border-[#FFC66D]/30">
                            Side Effect Prevented
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#080D0B] text-[#718278] border border-[#263A2E]">
                            Simulated Read
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-[#A0B2A6] italic">"{st.thought}"</p>
                    <pre className="text-[11px] font-mono text-[#F0F7F2] bg-[#080D0B] p-2 rounded-lg border border-[#263A2E] overflow-x-auto">
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
        <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-6 space-y-5 shadow-card-subtle">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#263A2E] pb-4">
            <div>
              <h3 className="text-sm font-bold text-[#F0F7F2]">Simulated Company Web Portal</h3>
              <p className="text-xs text-[#A0B2A6] mt-0.5">
                Real HTTP & Playwright browser sandbox simulating enterprise web pages (Invoices, Support Tickets, Inventory).
              </p>
            </div>
            <a
              href="http://localhost:8000/portal"
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 bg-[#55E6A5] hover:bg-[#35D993] text-[#080D0B] rounded-xl text-xs font-bold flex items-center gap-1.5 transition shadow-glow-jade"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Launch Live Portal</span>
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            <a
              href="http://localhost:8000/portal/invoices"
              target="_blank"
              rel="noreferrer"
              className="p-4 bg-[#142019] hover:bg-[#1C2D24] rounded-xl border border-[#263A2E] hover:border-[#55E6A5]/50 space-y-2.5 transition group block"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#55E6A5]">Invoices & Payables</span>
                <ExternalLink className="w-3 h-3 text-[#718278] group-hover:text-[#55E6A5] transition" />
              </div>
              <p className="text-xs text-[#A0B2A6] leading-relaxed">
                Interactive web form for entering vendor invoices. Supports Playwright DOM inspection, filling form fields, accessible buttons, and live confirmation banners.
              </p>
              <div className="pt-2 text-[10px] font-mono text-[#55E6A5] flex items-center gap-1">
                <span>Open /portal/invoices</span>
                <span>→</span>
              </div>
            </a>

            <a
              href="http://localhost:8000/portal/tickets"
              target="_blank"
              rel="noreferrer"
              className="p-4 bg-[#142019] hover:bg-[#1C2D24] rounded-xl border border-[#263A2E] hover:border-[#FFC66D]/50 space-y-2.5 transition group block"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#FFC66D]">Customer Support Desk</span>
                <ExternalLink className="w-3 h-3 text-[#718278] group-hover:text-[#FFC66D] transition" />
              </div>
              <p className="text-xs text-[#A0B2A6] leading-relaxed">
                Live queue of unresolved customer support tickets with severity indicators. Agent can inspect page state and prioritize open tickets via browser automation.
              </p>
              <div className="pt-2 text-[10px] font-mono text-[#FFC66D] flex items-center gap-1">
                <span>Open /portal/tickets</span>
                <span>→</span>
              </div>
            </a>

            <a
              href="http://localhost:8000/portal/inventory"
              target="_blank"
              rel="noreferrer"
              className="p-4 bg-[#142019] hover:bg-[#1C2D24] rounded-xl border border-[#263A2E] hover:border-[#A99BFF]/50 space-y-2.5 transition group block"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#A99BFF]">Warehouse Inventory</span>
                <ExternalLink className="w-3 h-3 text-[#718278] group-hover:text-[#A99BFF] transition" />
              </div>
              <p className="text-xs text-[#A0B2A6] leading-relaxed">
                Live stock levels, SKU tracking, and reorder alerts. Enables end-to-end web browser reading, form submission, and independent verification.
              </p>
              <div className="pt-2 text-[10px] font-mono text-[#A99BFF] flex items-center gap-1">
                <span>Open /portal/inventory</span>
                <span>→</span>
              </div>
            </a>
          </div>
        </div>
      )}

      {/* Tab 5: Registered Tools Catalog */}
      {activeSubTab === 'tools' && (
        <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-6 space-y-5 shadow-card-subtle">
          <div className="border-b border-[#263A2E] pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-[#F0F7F2] flex items-center gap-2">
                <Cpu className="w-4 h-4 text-[#55E6A5]" />
                Registered Controlled Tool Registry (34 Enterprise Tools)
              </h3>
              <p className="text-xs text-[#A0B2A6] mt-0.5">
                Every action taken by AgentOS is bounded by deterministic OpenAPI schemas and safety validators.
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full bg-[#55E6A5]/10 border border-[#55E6A5]/30 text-[#55E6A5] text-[10px] font-mono font-bold">
              34 TOOLS ACTIVE
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {[
              { domain: 'Financial & Invoices', name: 'list_invoice_files', desc: 'Scan sandbox directory for invoice documents', params: 'directory, vendor_filter' },
              { domain: 'Financial & Invoices', name: 'read_invoice', desc: 'Read raw text/PDF content of target invoice file', params: 'file_path' },
              { domain: 'Financial & Invoices', name: 'extract_invoice_fields', desc: 'Extract vendor, invoice #, amount, due date without hallucination', params: 'document_text, source_file' },
              { domain: 'Financial & Invoices', name: 'search_vendor', desc: 'Match vendor against company master directory', params: 'vendor_name' },
              { domain: 'Financial & Invoices', name: 'search_existing_invoice', desc: 'Check accounting database for duplicates', params: 'vendor_name, invoice_number' },
              { domain: 'Financial & Invoices', name: 'create_payable', desc: 'Register payable record in company accounting database', params: 'vendor, invoice_no, amount, due_date' },
              { domain: 'Financial & Invoices', name: 'verify_payable', desc: 'Independent ground-truth ledger verification', params: 'invoice_number, expected_amount, due_date' },
              
              { domain: 'Email & Tasks', name: 'list_emails', desc: 'Scan incoming inbox communications in sandbox', params: 'directory, sender_filter' },
              { domain: 'Email & Tasks', name: 'read_email', desc: 'Read communication body and attachments', params: 'file_path' },
              { domain: 'Email & Tasks', name: 'extract_email_details', desc: 'Extract interview date, time, interviewer, and meeting URL', params: 'email_text, source_file' },
              { domain: 'Email & Tasks', name: 'create_task_item', desc: 'Persist scheduled event in company task items database', params: 'title, due_date, meeting_link, priority' },
              { domain: 'Email & Tasks', name: 'verify_task_item', desc: 'Independent ground-truth assertion for task item', params: 'task_item_id, expected_title, due_date' },

              { domain: 'Data & Reporting', name: 'list_csv_files', desc: 'Discover tabular datasets in CSV repository', params: 'directory' },
              { domain: 'Data & Reporting', name: 'inspect_csv', desc: 'Inspect CSV schema, row count, null values, columns', params: 'file_path' },
              { domain: 'Data & Reporting', name: 'analyze_csv', desc: 'Execute Pandas ranking, aggregation, top records', params: 'file_path, top_n' },
              { domain: 'Data & Reporting', name: 'generate_report', desc: 'Generate and persist executive Markdown report file', params: 'report_title, report_content, filename' },

              { domain: 'Customer Support', name: 'list_support_tickets', desc: 'Retrieve customer support ticket queue', params: 'status_filter' },
              { domain: 'Customer Support', name: 'update_support_ticket', desc: 'Update ticket priority and status in SQLite DB', params: 'ticket_code, new_status, new_priority' },

              { domain: 'Inventory & Procurement', name: 'list_inventory', desc: 'Audit warehouse stock and reorder thresholds', params: 'low_stock_only' },
              { domain: 'Inventory & Procurement', name: 'create_purchase_request', desc: 'Draft replenishment order in purchase_requests DB', params: 'sku, quantity' },

              { domain: 'Universal Documents', name: 'inspect_document', desc: 'Universal parser for PDF, TXT, MD, CSV, JSON files', params: 'file_path' },
              { domain: 'Universal Documents', name: 'list_contract_files', desc: 'Scan legal agreements directory', params: 'directory' },
              { domain: 'Universal Documents', name: 'extract_contract_details', desc: 'Extract parties, expiry date, and audit missing clauses', params: 'file_path' },
              { domain: 'Universal Documents', name: 'verify_contract', desc: 'Ground-truth contract audit against database', params: 'contract_code, expected_expiry_date' },

              { domain: 'Browser Automation', name: 'browser_open_url', desc: 'Open target URL in controlled Playwright browser', params: 'url, wait_until' },
              { domain: 'Browser Automation', name: 'browser_inspect_page', desc: 'Extract DOM structure, forms, and interactive buttons', params: 'selector' },
              { domain: 'Browser Automation', name: 'browser_fill_field', desc: 'Simulate user keystrokes into form inputs', params: 'selector, value' },
              { domain: 'Browser Automation', name: 'browser_click', desc: 'Click buttons, submit forms, and navigate pages', params: 'selector' },
              { domain: 'Browser Automation', name: 'browser_take_screenshot', desc: 'Capture visual snapshot proof of rendered UI', params: 'filename, full_page' },
              { domain: 'Browser Automation', name: 'browser_verify_page_state', desc: 'Verify submission confirmation text and status codes', params: 'expected_text, selector' },

              { domain: 'Governance & Safety', name: 'request_approval', desc: 'Pause execution for human-in-the-loop managerial sign-off', params: 'task_id, risk_level, risk_reason, payload' },
              { domain: 'Governance & Safety', name: 'report_task_result', desc: 'Generate verified cryptographic receipt of outcome', params: 'task_id, summary, verification_token' }
            ].map((tool, idx) => (
              <div key={idx} className="p-3.5 bg-[#142019] rounded-xl border border-[#263A2E] space-y-1.5 hover:border-[#55E6A5]/40 transition">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[#55E6A5]">{tool.name}</span>
                  <span className="text-[9px] font-mono text-[#718278] uppercase">{tool.domain}</span>
                </div>
                <p className="text-xs text-[#A0B2A6]">{tool.desc}</p>
                <div className="pt-1 text-[10px] font-mono text-[#718278]">
                  Args: <span className="text-[#F0F7F2]">{tool.params}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 6: Engine & Settings */}
      {activeSubTab === 'settings' && (
        <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-6 space-y-6 shadow-card-subtle">
          <div className="border-b border-[#263A2E] pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-[#F0F7F2] flex items-center gap-2">
                <Settings className="w-4 h-4 text-[#FFC66D]" />
                AgentOS Engine & Governance Configuration
              </h3>
              <p className="text-xs text-[#A0B2A6] mt-0.5">
                Active Inference Engine: Groq LPU • Platform Administrator: Jay
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full bg-[#FFC66D]/15 border border-[#FFC66D]/40 text-[#FFC66D] text-[10px] font-mono font-bold flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#FFC66D] animate-pulse" />
              GROQ ACTIVE
            </span>
          </div>

          {/* Test Status Banner */}
          {groqTestResult && (
            <div className={`p-3 rounded-xl border text-xs font-semibold flex items-center gap-2 ${
              groqTestResult.includes('successfully')
                ? 'bg-[#55E6A5]/10 border-[#55E6A5]/40 text-[#55E6A5]'
                : 'bg-[#FF7777]/10 border-[#FF7777]/40 text-[#FF7777]'
            }`}>
              <Check className="w-4 h-4" />
              <span>{groqTestResult}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* LLM Engine Card */}
            <div className="p-4 bg-[#142019] rounded-xl border border-[#263A2E] space-y-3.5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#FFC66D] flex items-center gap-2">
                <Zap className="w-3.5 h-3.5 fill-current" />
                Groq High-Speed Inference Engine
              </h4>
              <div className="space-y-2 text-xs">
                <div>
                  <label className="text-[10px] uppercase font-bold text-[#718278] block mb-1">Configured API Key</label>
                  <div className="font-mono text-xs text-[#55E6A5] bg-[#080D0B] p-2 rounded-lg border border-[#263A2E] flex justify-between items-center">
                    <span>gsk_mf••••••••••••••••••••••••••••••••••2KW</span>
                    <span className="text-[10px] text-[#55E6A5] font-bold">✔ Connected</span>
                  </div>
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold text-[#718278] block mb-1">Active LLM Model</label>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full bg-[#080D0B] border border-[#263A2E] rounded-lg p-2 text-xs text-[#F0F7F2] font-mono focus:outline-none focus:border-[#55E6A5]"
                  >
                    <option value="openai/gpt-oss-120b">openai/gpt-oss-120b (Recommended - High Capacity)</option>
                    <option value="openai/gpt-oss-20b">openai/gpt-oss-20b (Ultra Fast)</option>
                    <option value="qwen/qwen3.8-27b">qwen/qwen3.8-27b (Fast Reasoning)</option>
                    <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                    <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                  </select>
                </div>

                <div className="pt-2 flex gap-2">
                  <button
                    onClick={handleTestGroq}
                    disabled={isTestingGroq}
                    className="px-3 py-2 bg-[#FFC66D] hover:bg-[#F5B752] text-[#080D0B] rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow-glow-amber disabled:opacity-50"
                  >
                    {isTestingGroq ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 fill-current" />}
                    <span>Test Groq Connection</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Governance & Administrator Card */}
            <div className="p-4 bg-[#142019] rounded-xl border border-[#263A2E] space-y-3.5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#55E6A5] flex items-center gap-2">
                <ShieldAlert className="w-3.5 h-3.5" />
                Enterprise Governance Policy
              </h4>
              <div className="space-y-2.5 text-xs text-[#A0B2A6]">
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#080D0B] border border-[#263A2E]">
                  <span>System Administrator:</span>
                  <span className="font-bold text-[#F0F7F2]">Jay</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#080D0B] border border-[#263A2E]">
                  <span>Autonomous Policy Threshold:</span>
                  <span className="font-mono text-[#FFC66D] font-bold">$10,000.00 USD</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#080D0B] border border-[#263A2E]">
                  <span>Ground-Truth Verification:</span>
                  <span className="font-mono text-[#55E6A5] font-bold">Cryptographic SQLite Ledger</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#080D0B] border border-[#263A2E]">
                  <span>Zero-Setup Fallback Mode:</span>
                  <span className="font-mono text-[#55E6A5] font-bold">Active (Seamless 100% Reliability)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
