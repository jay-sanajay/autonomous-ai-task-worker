import React, { useState, useEffect } from 'react';
import { Vendor, InvoiceDoc, Payable, TaskItem, SupportTicket, InventoryItem, PurchaseRequest } from '../types';
import { Building2, FileText, Receipt, CheckSquare, LifeBuoy, Boxes, ExternalLink, Upload, Play, FileSpreadsheet } from 'lucide-react';
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
  const [subTab, setSubTab] = useState<'payables' | 'tasks' | 'tickets' | 'inventory' | 'csv_reports' | 'vendors' | 'documents'>('payables');
  const [csvFiles, setCsvFiles] = useState<Array<{ filename: string; file_path: string; size_bytes: number }>>([]);
  const [reports, setReports] = useState<Array<{ filename: string; file_path: string; size_bytes: number }>>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

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
    if (subTab === 'csv_reports') {
      loadCsvAndReports();
    }
  }, [subTab]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
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
          <h2 className="text-base font-bold text-white">Simulated Enterprise Application & Database</h2>
          <p className="text-xs text-slate-400">Real SQLite tables, CSV datasets, and reports inspected and verified by AgentOS</p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex flex-wrap bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs gap-1">
            <button
              onClick={() => setSubTab('payables')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'payables' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Payables ({payables.length})
            </button>
            <button
              onClick={() => setSubTab('tasks')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'tasks' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Task List ({taskItems.length})
            </button>
            <button
              onClick={() => setSubTab('csv_reports')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'csv_reports' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              CSV Datasets & Reports
            </button>
            <button
              onClick={() => setSubTab('tickets')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'tickets' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Support ({supportTickets.length})
            </button>
            <button
              onClick={() => setSubTab('inventory')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'inventory' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Inventory ({inventory.length})
            </button>
            <button
              onClick={() => setSubTab('vendors')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'vendors' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Vendors ({vendors.length})
            </button>
            <button
              onClick={() => setSubTab('documents')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                subTab === 'documents' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Files ({invoices.length})
            </button>
          </div>

          <button
            onClick={() => {
              onRefresh();
              if (subTab === 'csv_reports') loadCsvAndReports();
            }}
            className="px-2.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold shrink-0"
          >
            Refresh
          </button>
        </div>
      </div>

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
                        p.status === 'VERIFIED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                        'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 text-[10px] truncate max-w-[140px]">
                      {p.verification_hash || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Task Items / Calendar Events */}
      {subTab === 'tasks' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-2 px-3">ID</th>
                <th className="py-2 px-3">Title</th>
                <th className="py-2 px-3">Scheduled Date / Time</th>
                <th className="py-2 px-3">Meeting Link</th>
                <th className="py-2 px-3">Priority</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {taskItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-sans text-xs">
                    No task items found. Run the HR Interview workflow to automatically extract and populate events.
                  </td>
                </tr>
              ) : (
                taskItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 px-3 text-slate-400">#{item.id}</td>
                    <td className="py-2.5 px-3 font-bold text-white font-sans">{item.title}</td>
                    <td className="py-2.5 px-3 text-sky-300 font-semibold">{item.due_date}</td>
                    <td className="py-2.5 px-3">
                      {item.meeting_link ? (
                        <a
                          href={item.meeting_link}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sky-400 hover:text-sky-300 flex items-center space-x-1 font-mono text-[11px] underline"
                        >
                          <span className="truncate max-w-[180px]">{item.meeting_link}</span>
                          <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                        </a>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.priority === 'HIGH' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {item.priority}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        {item.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 text-[11px] font-sans truncate max-w-[140px]">
                      {item.source_reference || 'HR Email'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* CSV Datasets & Generated Reports Tab */}
      {subTab === 'csv_reports' && (
        <div className="space-y-6">
          {/* Upload Dropzone */}
          <div className="border border-dashed border-slate-700 bg-slate-950/60 rounded-xl p-5 text-center space-y-3">
            <div className="mx-auto w-10 h-10 rounded-full bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Upload New CSV Dataset</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Files are automatically saved to <code className="text-sky-300 font-mono">sandbox_data/csv/</code> for autonomous analysis.
              </p>
            </div>
            <div className="flex items-center justify-center space-x-3">
              <label className="cursor-pointer px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-sky-600/20 transition flex items-center space-x-2">
                <FileSpreadsheet className="w-4 h-4" />
                <span>{isUploading ? 'Uploading CSV...' : 'Select CSV File to Upload'}</span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                  className="hidden"
                />
              </label>
            </div>
            {uploadMessage && (
              <div className="text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 rounded-lg py-1.5 px-3 max-w-md mx-auto">
                {uploadMessage}
              </div>
            )}
          </div>

          {/* Available CSV Datasets Table */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
              <FileSpreadsheet className="w-3.5 h-3.5 text-sky-400" />
              <span>Available CSV Datasets ({csvFiles.length})</span>
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2 px-3">Filename</th>
                    <th className="py-2 px-3">Disk Path</th>
                    <th className="py-2 px-3">File Size</th>
                    <th className="py-2 px-3 text-right">Autonomous Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {csvFiles.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-slate-500 font-sans">
                        No CSV files found in sandbox_data/csv/. Upload one above!
                      </td>
                    </tr>
                  ) : (
                    csvFiles.map((c, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition">
                        <td className="py-2.5 px-3 font-bold text-white flex items-center space-x-2">
                          <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          <span>{c.filename}</span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">{c.file_path}</td>
                        <td className="py-2.5 px-3 text-slate-300">{(c.size_bytes / 1024).toFixed(1)} KB</td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => {
                              if (onRunTask) {
                                onRunTask(`Analyze the sales CSV in ${c.file_path}, identify the top five products by revenue, check for missing data, and generate a report.`);
                              }
                            }}
                            className="px-3 py-1 bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/40 rounded-lg text-xs font-semibold inline-flex items-center space-x-1.5 transition"
                            title="Launch autonomous analysis on this dataset"
                          >
                            <Play className="w-3 h-3 fill-current" />
                            <span>Analyze with AgentOS</span>
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Generated Reports Table */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span>Generated Reports in sandbox_data/reports/ ({reports.length})</span>
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2 px-3">Report Filename</th>
                    <th className="py-2 px-3">Location</th>
                    <th className="py-2 px-3">Size</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {reports.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="py-6 text-center text-slate-500 font-sans">
                        No reports generated yet. Run the CSV analysis workflow to create executive markdown reports.
                      </td>
                    </tr>
                  ) : (
                    reports.map((r, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition">
                        <td className="py-2.5 px-3 font-bold text-sky-300 flex items-center space-x-2 font-mono">
                          <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                          <span>{r.filename}</span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 text-[11px]">{r.file_path}</td>
                        <td className="py-2.5 px-3 text-slate-300">{r.size_bytes} B</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Support Tickets */}
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
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {supportTickets.map((st) => (
                <tr key={st.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-2.5 px-3 font-bold text-sky-400">{st.ticket_code}</td>
                  <td className="py-2.5 px-3 font-sans text-slate-300">{st.customer_name}</td>
                  <td className="py-2.5 px-3 font-sans text-white font-medium">{st.subject}</td>
                  <td className="py-2.5 px-3 font-sans">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      st.priority === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
                      st.priority === 'HIGH' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {st.priority}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-sans">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      st.status === 'RESOLVED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                      st.status === 'IN_PROGRESS' ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {st.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Inventory & Purchase Requests */}
      {subTab === 'inventory' && (
        <div className="space-y-4">
          <div className="overflow-x-auto">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Warehouse Inventory Stock Levels</h3>
            <table className="w-full text-left text-xs font-sans">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="py-2 px-3">SKU</th>
                  <th className="py-2 px-3">Product Name</th>
                  <th className="py-2 px-3">Category</th>
                  <th className="py-2 px-3">Current Stock</th>
                  <th className="py-2 px-3">Reorder Point</th>
                  <th className="py-2 px-3">Unit Price</th>
                  <th className="py-2 px-3">Stock Health</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {inventory.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 px-3 text-sky-400 font-bold">{item.sku}</td>
                    <td className="py-2.5 px-3 font-sans text-white font-medium">{item.product_name}</td>
                    <td className="py-2.5 px-3 font-sans text-slate-400">{item.category}</td>
                    <td className="py-2.5 px-3 font-bold text-white">{item.current_stock}</td>
                    <td className="py-2.5 px-3 text-slate-400">{item.reorder_threshold}</td>
                    <td className="py-2.5 px-3 text-emerald-400">${item.unit_price.toFixed(2)}</td>
                    <td className="py-2.5 px-3 font-sans">
                      {item.is_low_stock ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/30">
                          LOW STOCK (REORDER)
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          HEALTHY
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {purchaseRequests.length > 0 && (
            <div className="overflow-x-auto pt-3 border-t border-slate-800">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Drafted Purchase Requests</h3>
              <table className="w-full text-left text-xs font-sans">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2 px-3">PR Code</th>
                    <th className="py-2 px-3">Product Name</th>
                    <th className="py-2 px-3">Quantity</th>
                    <th className="py-2 px-3">Est. Total</th>
                    <th className="py-2 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {purchaseRequests.map((pr) => (
                    <tr key={pr.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-2.5 px-3 text-sky-400 font-bold">{pr.request_code}</td>
                      <td className="py-2.5 px-3 font-sans text-white">{pr.product_name}</td>
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

      {/* Invoice Documents Table */}
      {subTab === 'documents' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-2 px-3">Filename</th>
                <th className="py-2 px-3">Format</th>
                <th className="py-2 px-3">Vendor Hint</th>
                <th className="py-2 px-3">Size</th>
                <th className="py-2 px-3">Tag</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {invoices.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-2.5 px-3 font-mono text-white font-medium">{doc.filename}</td>
                  <td className="py-2.5 px-3 uppercase text-slate-400 font-mono text-[11px]">{doc.file_type}</td>
                  <td className="py-2.5 px-3 text-slate-300">{doc.vendor_name_hint || '-'}</td>
                  <td className="py-2.5 px-3 text-slate-400 font-mono">{doc.file_size_bytes} B</td>
                  <td className="py-2.5 px-3">
                    {doc.is_latest_for_vendor ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
                        LATEST VERSION
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">
                        ARCHIVE
                      </span>
                    )}
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
