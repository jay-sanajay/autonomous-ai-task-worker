import React, { useState, useEffect } from 'react';
import { Vendor, InvoiceDoc, Payable, TaskItem, SupportTicket, InventoryItem, PurchaseRequest, Contract, SandboxFile } from '../types';
import {
  Building2, FileText, Receipt, CheckSquare, LifeBuoy, Boxes,
  ExternalLink, Upload, Play, FileSpreadsheet, ShieldCheck,
  AlertTriangle, FileCode, Clock, CheckCircle2, ShieldAlert, BarChart3
} from 'lucide-react';
import { InvoiceHub } from './InvoiceHub';
import { DatasetReportHub } from './DatasetReportHub';
import * as api from '../services/api';

interface CompanySandboxProps {
  vendors: Vendor[];
  invoices: InvoiceDoc[];
  payables: Payable[];
  taskItems?: TaskItem[];
  supportTickets?: SupportTicket[];
  inventory?: InventoryItem[];
  purchaseRequests?: PurchaseRequest[];
  onRefresh: () => void;
  onRunTask?: (goal: string) => void;
}

export const CompanySandbox: React.FC<CompanySandboxProps> = ({
  vendors,
  invoices,
  payables,
  taskItems = [],
  supportTickets = [],
  inventory = [],
  purchaseRequests = [],
  onRefresh,
  onRunTask
}) => {
  const [subTab, setSubTab] = useState<'invoice_hub' | 'datasets_reports' | 'payables' | 'tasks' | 'contracts' | 'csv_reports' | 'tickets' | 'inventory' | 'vendors' | 'documents'>('invoice_hub');
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [allFiles, setAllFiles] = useState<SandboxFile[]>([]);
  const [csvFiles, setCsvFiles] = useState<Array<{ filename: string; file_path: string; size_bytes: number }>>([]);
  const [reports, setReports] = useState<Array<{ filename: string; file_path: string; size_bytes: number }>>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [suggestedUploadPrompt, setSuggestedUploadPrompt] = useState<string | null>(null);

  const loadContracts = async () => {
    try {
      const data = await api.fetchContracts();
      setContracts(data);
    } catch (err) {
      console.error('Failed to load contracts:', err);
    }
  };

  const loadAllFiles = async () => {
    try {
      const data = await api.fetchAllSandboxFiles();
      setAllFiles(data);
    } catch (err) {
      console.error('Failed to load files:', err);
    }
  };

  const loadCsvAndReports = async () => {
    try {
      const [c, r] = await Promise.all([api.fetchCSVFiles(), api.fetchReports()]);
      setCsvFiles(c);
      setReports(r);
    } catch (err) {
      console.error('Failed to load CSV/reports:', err);
    }
  };

  useEffect(() => {
    if (subTab === 'contracts') {
      loadContracts();
    } else if (subTab === 'documents') {
      loadAllFiles();
    } else if (subTab === 'csv_reports') {
      loadCsvAndReports();
    }
  }, [subTab]);

  const handleUniversalUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setUploadMessage(null);
    setSuggestedUploadPrompt(null);
    try {
      const res = await api.uploadAnyFile(file);
      setUploadMessage(res.message);
      setSuggestedUploadPrompt(res.suggested_prompt);
      await loadAllFiles();
      await loadContracts();
    } catch (err: any) {
      setUploadMessage(`Upload failed: ${err.message || err}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setUploadMessage(null);
    try {
      const res = await api.uploadCSVFile(file);
      setUploadMessage(res.message);
      await loadCsvAndReports();
    } catch (err: any) {
      setUploadMessage(`Upload failed: ${err.message || err}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/40 space-y-5">
      
      {/* Header & Sub-Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <span>Simulated Enterprise Application & Database</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              Live SQLite Sandbox
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Real relational ledger, contracts audit, CSV analytics, and universal file processing
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex flex-wrap bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs gap-1">
            <button
              onClick={() => setSubTab('invoice_hub')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition flex items-center space-x-1 ${
                subTab === 'invoice_hub' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Receipt className="w-3 h-3" />
              <span>Invoices & Items ({invoices.length})</span>
            </button>
            <button
              onClick={() => setSubTab('datasets_reports')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition flex items-center space-x-1 ${
                subTab === 'datasets_reports' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              <BarChart3 className="w-3 h-3" />
              <span>Datasets & Reports</span>
            </button>
            <button
              onClick={() => setSubTab('payables')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'payables' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Payables ({payables.length})
            </button>
            <button
              onClick={() => setSubTab('tasks')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'tasks' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Task List ({taskItems.length})
            </button>
            <button
              onClick={() => setSubTab('contracts')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'contracts' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Contracts & SLAs ({contracts.length})
            </button>
            <button
              onClick={() => setSubTab('csv_reports')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'csv_reports' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              CSV Analytics
            </button>
            <button
              onClick={() => setSubTab('tickets')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'tickets' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Support ({supportTickets.length})
            </button>
            <button
              onClick={() => setSubTab('inventory')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'inventory' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Inventory ({inventory.length})
            </button>
            <button
              onClick={() => setSubTab('documents')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'documents' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Files & Uploads ({allFiles.length || invoices.length})
            </button>
            <button
              onClick={() => setSubTab('vendors')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'vendors' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Vendors ({vendors.length})
            </button>
          </div>

          <button
            onClick={() => {
              onRefresh();
              if (subTab === 'contracts') loadContracts();
              if (subTab === 'documents') loadAllFiles();
              if (subTab === 'csv_reports') loadCsvAndReports();
            }}
            className="px-2.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold shrink-0 transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* SubTab 0: Interactive Invoice & Items Automation Studio */}
      {subTab === 'invoice_hub' && (
        <InvoiceHub
          invoices={invoices}
          vendors={vendors}
          onRefresh={onRefresh}
          onRunTask={onRunTask || (() => {})}
        />
      )}

      {/* SubTab: CSV Datasets & Automated Executive Reports Studio */}
      {subTab === 'datasets_reports' && (
        <DatasetReportHub
          onRefresh={onRefresh}
          onRunTask={onRunTask || (() => {})}
        />
      )}

      {/* Payables Table */}
      {subTab === 'payables' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-2 px-3">ID</th>
                <th className="py-2 px-3">Invoice #</th>
                <th className="py-2 px-3">Vendor</th>
                <th className="py-2 px-3">Amount</th>
                <th className="py-2 px-3">Due Date</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Verification Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {payables.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-sans text-xs">
                    No payable records created yet. Run an autonomous invoice task to populate.
                  </td>
                </tr>
              ) : (
                payables.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 px-3 text-slate-400">#{p.id}</td>
                    <td className="py-2.5 px-3 font-bold text-white">{p.invoice_number}</td>
                    <td className="py-2.5 px-3 font-sans text-slate-300">{p.vendor_name}</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-bold">
                      ${p.amount.toLocaleString(undefined, {minimumFractionDigits: 2})} {p.currency}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{p.due_date}</td>
                    <td className="py-2.5 px-3 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        p.status === 'VERIFIED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 text-[10px] truncate max-w-[140px]" title={p.verification_hash}>
                      {p.verification_hash ? p.verification_hash.substring(0, 16) + '...' : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Task Items Table (HR Interview Events) */}
      {subTab === 'tasks' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-2 px-3">ID</th>
                <th className="py-2 px-3">Event / Task Title</th>
                <th className="py-2 px-3">Scheduled Date</th>
                <th className="py-2 px-3">Meeting Link</th>
                <th className="py-2 px-3">Priority</th>
                <th className="py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {taskItems.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans text-xs">
                    No task items created yet. Run the HR email prompt to extract interview date and meeting link.
                  </td>
                </tr>
              ) : (
                taskItems.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 px-3 text-slate-400">#{t.id}</td>
                    <td className="py-2.5 px-3 font-sans font-bold text-white">{t.title}</td>
                    <td className="py-2.5 px-3 text-sky-400 font-bold">{t.due_date}</td>
                    <td className="py-2.5 px-3">
                      {t.meeting_link ? (
                        <a
                          href={t.meeting_link}
                          target="_blank"
                          rel="noreferrer"
                          className="text-indigo-400 hover:text-indigo-300 underline flex items-center space-x-1"
                        >
                          <span className="truncate max-w-[180px]">{t.meeting_link}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      ) : (
                        <span className="text-slate-500 font-sans">-</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                        {t.priority}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        {t.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Contracts & SLAs Table */}
      {subTab === 'contracts' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Audited legal contracts, service level agreements (SLAs), and verified compliance checks in SQLite.
            </p>
            {onRunTask && (
              <button
                onClick={() => onRunTask("Read a contract, extract its expiry date, and flag missing information.")}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-sky-500/20 text-sky-300 hover:bg-sky-500/30 border border-sky-500/40 text-xs font-semibold transition"
              >
                <Play className="w-3 h-3" />
                <span>Run Autonomous Contract Audit</span>
              </button>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="py-2 px-3">Contract Code</th>
                  <th className="py-2 px-3">Agreement Title</th>
                  <th className="py-2 px-3">Parties</th>
                  <th className="py-2 px-3">Expiry Date</th>
                  <th className="py-2 px-3">Value</th>
                  <th className="py-2 px-3">Missing Clauses</th>
                  <th className="py-2 px-3">Risk Rating</th>
                  <th className="py-2 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {contracts.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500 font-sans text-xs">
                      No contracts audited in database yet. Click "Run Autonomous Contract Audit" or select the contract preset.
                    </td>
                  </tr>
                ) : (
                  contracts.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-2.5 px-3 text-sky-400 font-bold">{c.contract_code}</td>
                      <td className="py-2.5 px-3 font-sans font-bold text-white max-w-[200px] truncate" title={c.title}>
                        {c.title}
                      </td>
                      <td className="py-2.5 px-3 font-sans text-slate-300 max-w-[180px] truncate" title={c.parties}>
                        {c.parties}
                      </td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">
                        <div className="flex items-center space-x-1">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          <span>{c.expiry_date}</span>
                        </div>
                      </td>
                      <td className="py-2.5 px-3 text-white">
                        {c.contract_value > 0 ? `$${c.contract_value.toLocaleString(undefined, {minimumFractionDigits: 2})}` : 'Retainer'}
                      </td>
                      <td className="py-2.5 px-3 font-sans">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          c.missing_clauses_count > 0
                            ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                            : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        }`}>
                          {c.missing_clauses_count} flagged
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-sans">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          c.risk_score === 'CRITICAL'
                            ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                            : c.risk_score === 'HIGH'
                            ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                            : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        }`}>
                          {c.risk_score}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-sans">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
                          {c.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* CSV Datasets & Reports Tab */}
      {subTab === 'csv_reports' && (
        <div className="space-y-6">
          {/* Upload Box */}
          <div className="border border-dashed border-slate-700 hover:border-sky-500/50 bg-slate-950/40 rounded-xl p-4 transition text-center space-y-2">
            <div className="flex items-center justify-center space-x-2 text-slate-300 font-semibold text-xs">
              <Upload className="w-4 h-4 text-sky-400" />
              <span>Upload New CSV Dataset for Autonomous Analysis</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Drag and drop or select any tabular dataset (.csv). AgentOS dynamically identifies columns and computes rankings.
            </p>
            <div className="pt-2">
              <label className="cursor-pointer inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-xs font-semibold transition">
                <span>{isUploading ? 'Uploading...' : 'Choose CSV File'}</span>
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={handleCsvUpload}
                  disabled={isUploading}
                />
              </label>
            </div>
            {uploadMessage && (
              <p className="text-xs font-semibold text-emerald-400 pt-1">{uploadMessage}</p>
            )}
          </div>

          {/* CSV Files List */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
              <FileSpreadsheet className="w-4 h-4 text-sky-400" />
              <span>Available CSV Datasets</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {csvFiles.map((f) => (
                <div key={f.filename} className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-white font-mono">{f.filename}</p>
                    <p className="text-[10px] text-slate-400 font-mono">{(f.size_bytes / 1024).toFixed(1)} KB • {f.file_path}</p>
                  </div>
                  {onRunTask && (
                    <button
                      onClick={() => onRunTask(`Analyze the CSV dataset at ${f.file_path}, identify top products, and save a report.`)}
                      className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-semibold transition"
                    >
                      <Play className="w-3 h-3" />
                      <span>Analyze</span>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Generated Reports List */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
              <FileText className="w-4 h-4 text-emerald-400" />
              <span>Generated Executive Reports</span>
            </h3>
            {reports.length === 0 ? (
              <p className="text-xs text-slate-500">No reports generated yet. Run a CSV analysis task to produce one.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {reports.map((r) => (
                  <div key={r.filename} className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-bold text-white font-mono">{r.filename}</p>
                      <p className="text-[10px] text-emerald-400 font-mono">{r.size_bytes} bytes • Generated to disk</p>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      PERSISTED
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Support Tickets Table */}
      {subTab === 'tickets' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-2 px-3">Ticket Code</th>
                <th className="py-2 px-3">Customer</th>
                <th className="py-2 px-3">Subject</th>
                <th className="py-2 px-3">Priority</th>
                <th className="py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {supportTickets.map((t) => (
                <tr key={t.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-2.5 px-3 font-mono font-bold text-sky-400">{t.ticket_code}</td>
                  <td className="py-2.5 px-3 font-bold text-white">{t.customer_name}</td>
                  <td className="py-2.5 px-3 text-slate-300">{t.subject}</td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      t.priority === 'CRITICAL'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    }`}>
                      {t.priority}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      t.status === 'IN_PROGRESS'
                        ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                        : 'bg-slate-700 text-slate-300'
                    }`}>
                      {t.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Inventory & Supply Chain Table */}
      {subTab === 'inventory' && (
        <div className="space-y-6">
          <div className="overflow-x-auto">
            <h3 className="text-xs font-bold text-slate-400 uppercase mb-2">Warehouse Product Catalog</h3>
            <table className="w-full text-left text-xs font-sans">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="py-2 px-3">SKU</th>
                  <th className="py-2 px-3">Product Name</th>
                  <th className="py-2 px-3">Current Stock</th>
                  <th className="py-2 px-3">Reorder Threshold</th>
                  <th className="py-2 px-3">Unit Price</th>
                  <th className="py-2 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {inventory.map((i) => (
                  <tr key={i.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 px-3 font-bold text-sky-400">{i.sku}</td>
                    <td className="py-2.5 px-3 font-sans font-bold text-white">{i.product_name}</td>
                    <td className={`py-2.5 px-3 font-bold ${i.is_low_stock ? 'text-rose-400' : 'text-slate-300'}`}>
                      {i.current_stock} units
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">{i.reorder_threshold} units</td>
                    <td className="py-2.5 px-3 text-slate-300">${i.unit_price.toFixed(2)}</td>
                    <td className="py-2.5 px-3 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        i.is_low_stock
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30 animate-pulse'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      }`}>
                        {i.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {purchaseRequests.length > 0 && (
            <div className="overflow-x-auto pt-4 border-t border-slate-800">
              <h3 className="text-xs font-bold text-slate-400 uppercase mb-2">Drafted Purchase Requests (Replenishment Orders)</h3>
              <table className="w-full text-left text-xs font-sans">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2 px-3">Request Code</th>
                    <th className="py-2 px-3">Product</th>
                    <th className="py-2 px-3">Quantity</th>
                    <th className="py-2 px-3">Estimated Total</th>
                    <th className="py-2 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {purchaseRequests.map((pr) => (
                    <tr key={pr.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-2.5 px-3 font-bold text-indigo-400">{pr.request_code}</td>
                      <td className="py-2.5 px-3 font-sans font-bold text-white">{pr.product_name}</td>
                      <td className="py-2.5 px-3">{pr.quantity}</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">${pr.estimated_total.toFixed(2)}</td>
                      <td className="py-2.5 px-3 font-sans">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                          {pr.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Universal Documents & Uploads Tab */}
      {subTab === 'documents' && (
        <div className="space-y-6">
          {/* Universal Drag & Drop / Upload Card */}
          <div className="border border-dashed border-slate-700 hover:border-indigo-500/50 bg-slate-950/40 rounded-xl p-5 transition text-center space-y-3">
            <div className="flex items-center justify-center space-x-2 text-white font-bold text-sm">
              <Upload className="w-5 h-5 text-indigo-400" />
              <span>Universal Document & File Ingestion</span>
            </div>
            <p className="text-xs text-slate-400 max-w-xl mx-auto">
              Upload any document format (<span className="text-white font-semibold">.pdf, .csv, .txt, .json, .md, .tsv</span>).
              AgentOS automatically inspects document structures, audits contracts, analyzes datasets, or enters invoices.
            </p>
            <div className="pt-1">
              <label className="cursor-pointer inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition shadow-lg shadow-indigo-600/20">
                <span>{isUploading ? 'Uploading & Parsing...' : 'Upload Any File'}</span>
                <input
                  type="file"
                  accept=".pdf,.csv,.tsv,.txt,.json,.md,.log"
                  className="hidden"
                  onChange={handleUniversalUpload}
                  disabled={isUploading}
                />
              </label>
            </div>
            {uploadMessage && (
              <div className="p-3 bg-indigo-950/40 border border-indigo-500/30 rounded-xl text-left max-w-lg mx-auto space-y-1">
                <p className="text-xs font-semibold text-emerald-400 flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{uploadMessage}</span>
                </p>
                {suggestedUploadPrompt && onRunTask && (
                  <div className="pt-1 flex items-center justify-between">
                    <p className="text-[11px] text-slate-300 italic truncate max-w-[340px]">"{suggestedUploadPrompt}"</p>
                    <button
                      onClick={() => onRunTask(suggestedUploadPrompt)}
                      className="px-2 py-1 bg-sky-500 text-white text-[10px] font-bold rounded hover:bg-sky-400 transition shrink-0"
                    >
                      Run Now
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Files List Across All Folders */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <FileCode className="w-4 h-4 text-sky-400" />
              <span>Sandbox Documents & Datasets</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(allFiles.length > 0 ? allFiles : invoices.map(inv => ({
                category: 'Invoices',
                filename: inv.filename,
                extension: inv.file_type,
                file_path: inv.file_path,
                size_bytes: inv.file_size_bytes,
                modified_time: Date.now(),
                suggested_prompt: `Process invoice ${inv.filename} and register in accounting system.`
              }))).map((f) => (
                <div key={f.filename} className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-slate-800 text-sky-400 font-mono">
                        {f.extension}
                      </span>
                      <p className="text-xs font-bold text-white font-mono truncate">{f.filename}</p>
                    </div>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">
                      {f.category} • {(f.size_bytes / 1024).toFixed(1)} KB • {f.file_path}
                    </p>
                  </div>

                  {onRunTask && (
                    <button
                      onClick={() => onRunTask(f.suggested_prompt)}
                      className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-semibold shrink-0 transition"
                      title={f.suggested_prompt}
                    >
                      <Play className="w-3 h-3" />
                      <span>Run Task</span>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Vendors Table */}
      {subTab === 'vendors' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-2 px-3">Code</th>
                <th className="py-2 px-3">Vendor Name</th>
                <th className="py-2 px-3">Aliases</th>
                <th className="py-2 px-3">Category</th>
                <th className="py-2 px-3">Terms</th>
                <th className="py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {vendors.map((v) => (
                <tr key={v.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-2.5 px-3 font-mono font-bold text-sky-400">{v.vendor_code}</td>
                  <td className="py-2.5 px-3 font-bold text-white">{v.name}</td>
                  <td className="py-2.5 px-3 text-slate-400 text-[11px]">{v.aliases || '-'}</td>
                  <td className="py-2.5 px-3 text-slate-300">{v.category}</td>
                  <td className="py-2.5 px-3 text-slate-300 font-mono">{v.payment_terms}</td>
                  <td className="py-2.5 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      {v.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

    </div>
  );
};
