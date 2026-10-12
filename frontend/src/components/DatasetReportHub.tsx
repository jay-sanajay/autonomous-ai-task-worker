import React, { useState, useEffect, useRef } from 'react';
import {
  Table, FileSpreadsheet, Download, Play, Plus, Trash2, CheckCircle2,
  Sparkles, RefreshCw, Eye, X, Printer, Search, ArrowRight, BarChart3,
  TrendingUp, FileText, Upload, FileCode2, Database, AlertCircle
} from 'lucide-react';
import * as api from '../services/api';

interface DatasetReportHubProps {
  onRefresh: () => void;
  onRunTask: (goal: string) => void;
}

export const DatasetReportHub: React.FC<DatasetReportHubProps> = ({
  onRefresh,
  onRunTask
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'datasets' | 'reports' | 'create_dataset'>('datasets');

  // Datasets State
  const [datasets, setDatasets] = useState<api.DatasetItem[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [datasetPreview, setDatasetPreview] = useState<{
    filename: string;
    columns: string[];
    rows: Record<string, string>[];
    total_rows: number;
  } | null>(null);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(false);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  // Reports State
  const [reports, setReports] = useState<api.ReportItem[]>([]);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [reportPreview, setReportPreview] = useState<{
    filename: string;
    content: string;
    size_bytes: number;
  } | null>(null);
  const [isLoadingReports, setIsLoadingReports] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  // New Dataset Creation Form State
  const [newDatasetName, setNewDatasetName] = useState(`dataset_${new Date().toISOString().slice(0, 10)}.csv`);
  const [csvRawContent, setCsvRawContent] = useState(`Product,Category,Units_Sold,Unit_Price,Revenue,Region
Enterprise Cloud Cluster,Infrastructure,120,450.00,54000.00,North America
AI Inference Accelerator,Compute,85,600.00,51000.00,Europe
Vector Database Appliance,Database,210,180.00,37800.00,Asia Pacific
Autonomous Agent Worker,Software,340,95.00,32300.00,North America
Security Firewall Appliance,Security,95,210.00,19950.00,Europe`);

  // Notifications & Uploads
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initial load
  useEffect(() => {
    loadDatasets();
    loadReports();
  }, []);

  const loadDatasets = async () => {
    setIsLoadingDatasets(true);
    try {
      const data = await api.fetchDatasets();
      setDatasets(data);
      if (data.length > 0 && !selectedDataset) {
        handleSelectDataset(data[0].filename);
      }
    } catch (err: any) {
      console.error('Failed to load datasets:', err);
    } finally {
      setIsLoadingDatasets(false);
    }
  };

  const loadReports = async () => {
    setIsLoadingReports(true);
    try {
      const data = await api.fetchReports();
      setReports(data);
      if (data.length > 0 && !selectedReport) {
        handleSelectReport(data[0].filename);
      }
    } catch (err: any) {
      console.error('Failed to load reports:', err);
    } finally {
      setIsLoadingReports(false);
    }
  };

  const handleSelectDataset = async (filename: string) => {
    setSelectedDataset(filename);
    setIsLoadingPreview(true);
    try {
      const preview = await api.fetchDatasetPreview(filename, 50);
      setDatasetPreview(preview);
    } catch (err: any) {
      setErrorMessage(`Failed to preview dataset: ${err.message || err}`);
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleSelectReport = async (filename: string) => {
    setSelectedReport(filename);
    try {
      const preview = await api.fetchReportPreview(filename);
      setReportPreview(preview);
    } catch (err: any) {
      setErrorMessage(`Failed to load report: ${err.message || err}`);
    }
  };

  // Direct Dataset Download
  const handleDownloadDataset = async (filename: string) => {
    try {
      await api.downloadDatasetFile(filename);
      setSuccessMessage(`Dataset '${filename}' downloaded to your device!`);
    } catch (err: any) {
      setErrorMessage(`Download failed: ${err.message || err}`);
    }
  };

  // Direct Report Download
  const handleDownloadReport = async (filename: string) => {
    try {
      await api.downloadReportFile(filename);
      setSuccessMessage(`Executive report '${filename}' downloaded to your device!`);
    } catch (err: any) {
      setErrorMessage(`Download failed: ${err.message || err}`);
    }
  };

  // 1-Click Automated Report Generation
  const handleGenerateReport = async (targetDataset: string, autoDispatch = false) => {
    setIsGeneratingReport(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      const res = await api.generateAutomatedReport({
        source_dataset: targetDataset,
        report_title: `Executive Intelligence Audit: ${targetDataset}`
      });

      // 1. Immediately trigger download of report
      await api.downloadReportFile(res.filename);

      setSuccessMessage(`Report '${res.filename}' generated and downloaded to your computer!`);
      await loadReports();
      setSelectedReport(res.filename);
      setActiveSubTab('reports');

      // 2. If auto-dispatch to Task Studio requested
      if (autoDispatch) {
        onRunTask(`Analyze the dataset at sandbox_data/csv/${targetDataset}, aggregate top revenue drivers, and verify report at ${res.file_path}.`);
      }
    } catch (err: any) {
      setErrorMessage(`Report generation failed: ${err.message || err}`);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  // Create New Dataset
  const handleCreateDataset = async (autoReport = false) => {
    if (!newDatasetName.trim() || !csvRawContent.trim()) {
      setErrorMessage('Please provide a dataset filename and CSV content.');
      return;
    }
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      const res = await api.createCustomDataset({
        filename: newDatasetName.trim(),
        csv_content: csvRawContent.trim()
      });

      // 1. Immediately trigger download
      await api.downloadDatasetFile(res.filename);

      setSuccessMessage(`Dataset '${res.filename}' created and downloaded!`);
      await loadDatasets();
      setSelectedDataset(res.filename);
      setActiveSubTab('datasets');

      // 2. If autoReport requested, run analysis immediately
      if (autoReport) {
        await handleGenerateReport(res.filename, true);
      }
    } catch (err: any) {
      setErrorMessage(`Dataset creation failed: ${err.message || err}`);
    }
  };

  // Upload CSV or Document
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      const res = await api.uploadAnyFile(file);
      setSuccessMessage(`Uploaded '${res.filename}' (${(res.size_bytes / 1024).toFixed(1)} KB) successfully!`);
      await loadDatasets();
      await loadReports();
      onRefresh();
    } catch (err: any) {
      setErrorMessage(`Upload failed: ${err.message || err}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Preset CSV templates
  const loadPresetCsv = (type: 'sales' | 'churn' | 'servers') => {
    if (type === 'sales') {
      setNewDatasetName(`q4_global_sales_${Date.now().toString().slice(-4)}.csv`);
      setCsvRawContent(`Product,Category,Units_Sold,Unit_Price,Revenue,Region
Enterprise Cloud Cluster,Infrastructure,140,450.00,63000.00,North America
AI Inference Accelerator,Compute,95,600.00,57000.00,Europe
Vector Database Appliance,Database,250,180.00,45000.00,Asia Pacific
Autonomous Agent Platform,Software,410,95.00,38950.00,North America
Secure Gateway Appliance,Security,110,210.00,23100.00,Europe
Edge Analytics Node,Infrastructure,85,250.00,21250.00,Asia Pacific`);
    } else if (type === 'churn') {
      setNewDatasetName(`saas_customer_retention_${Date.now().toString().slice(-4)}.csv`);
      setCsvRawContent(`Account_Name,Tier,Monthly_ARR,Health_Score,NPS_Score,Churn_Risk
Alpha Corp,Enterprise,4500.00,92,9,Low
Beta Global,Enterprise,3800.00,64,6,High
Gamma Tech,Mid-Market,1200.00,88,8,Low
Delta Labs,Mid-Market,950.00,48,4,Critical
Omega Retail,Enterprise,5200.00,95,10,Low`);
    } else {
      setNewDatasetName(`datacenter_gpu_metrics_${Date.now().toString().slice(-4)}.csv`);
      setCsvRawContent(`Node_ID,GPU_Model,Utilization_Pct,Power_Watts,Temperature_C,Status
node-us-east-01,NVIDIA H100,94.5,680.0,62.0,Optimal
node-us-east-02,NVIDIA H100,98.2,710.0,66.5,Optimal
node-eu-west-01,NVIDIA A100,88.0,390.0,58.0,Optimal
node-ap-south-01,NVIDIA L40S,72.1,320.0,54.0,Optimal
node-us-west-04,NVIDIA H100,99.1,725.0,71.0,Warning`);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Sub-Navigation Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          <button
            onClick={() => setActiveSubTab('datasets')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition shrink-0 ${
              activeSubTab === 'datasets'
                ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Table className="w-3.5 h-3.5" />
            <span>CSV Datasets & Analytics ({datasets.length})</span>
          </button>

          <button
            onClick={() => setActiveSubTab('reports')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition shrink-0 ${
              activeSubTab === 'reports'
                ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Executive Reports ({reports.length})</span>
          </button>

          <button
            onClick={() => setActiveSubTab('create_dataset')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition shrink-0 ${
              activeSubTab === 'create_dataset'
                ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add / Create Dataset</span>
          </button>
        </div>

        {/* Global Action: Upload CSV or Document */}
        <div className="flex items-center space-x-2 shrink-0">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv,.tsv,.txt,.pdf,.json"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center space-x-1.5 transition border border-slate-700"
          >
            <Upload className="w-3.5 h-3.5 text-sky-400" />
            <span>{isUploading ? 'Uploading...' : 'Upload File (.csv / .pdf / .txt)'}</span>
          </button>

          <button
            onClick={() => { loadDatasets(); loadReports(); onRefresh(); }}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
            title="Refresh datasets & reports"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-white text-xs">
            Dismiss
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="p-3 bg-rose-950/40 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* TAB 1: CSV Datasets & Analytics Grid */}
      {activeSubTab === 'datasets' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column (4 cols): Select Dataset */}
          <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                <FileSpreadsheet className="w-4 h-4 text-sky-400" />
                <span>Available Datasets ({datasets.length})</span>
              </span>
              <button
                onClick={() => setActiveSubTab('create_dataset')}
                className="text-[11px] text-sky-400 hover:text-sky-300 font-semibold flex items-center space-x-0.5"
              >
                <Plus className="w-3 h-3" />
                <span>Add</span>
              </button>
            </div>

            <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
              {datasets.map((ds) => {
                const isSelected = selectedDataset === ds.filename;
                return (
                  <div
                    key={ds.filename}
                    onClick={() => handleSelectDataset(ds.filename)}
                    className={`p-3 rounded-xl border transition cursor-pointer space-y-2 ${
                      isSelected
                        ? 'bg-sky-500/10 border-sky-500/50 shadow-sm'
                        : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-white font-mono truncate">{ds.filename}</p>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {ds.rows_count} rows • {(ds.size_bytes / 1024).toFixed(1)} KB
                        </p>
                      </div>
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">
                        CSV
                      </span>
                    </div>

                    {/* Column tags preview */}
                    <div className="flex flex-wrap gap-1">
                      {ds.columns.slice(0, 4).map((col) => (
                        <span key={col} className="text-[9px] bg-slate-900 border border-slate-800 text-slate-300 px-1.5 py-0.2 rounded font-mono">
                          {col}
                        </span>
                      ))}
                      {ds.columns.length > 4 && (
                        <span className="text-[9px] text-slate-500 font-mono">+{ds.columns.length - 4}</span>
                      )}
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center space-x-1.5 pt-1.5 border-t border-slate-800/80">
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleDownloadDataset(ds.filename); }}
                        className="flex-1 py-1 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-semibold flex items-center justify-center space-x-1 transition"
                      >
                        <Download className="w-3 h-3 text-sky-400" />
                        <span>Download</span>
                      </button>

                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleGenerateReport(ds.filename, false); }}
                        disabled={isGeneratingReport}
                        className="flex-1 py-1 px-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 text-[11px] font-bold flex items-center justify-center space-x-1 transition"
                      >
                        <Sparkles className="w-3 h-3" />
                        <span>Report</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column (8 cols): Data Table Previewer & Action Bar */}
          <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            
            {/* Header info & action triggers */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-bold text-white font-mono">
                    {selectedDataset || 'Select a dataset'}
                  </span>
                  {datasetPreview && (
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      {datasetPreview.total_rows} Total Records
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Interactive dataset inspector. Click below to automate strategic report analysis.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                {selectedDataset && (
                  <button
                    onClick={() => handleDownloadDataset(selectedDataset)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center space-x-1 transition"
                  >
                    <Download className="w-3.5 h-3.5 text-sky-400" />
                    <span>Download CSV</span>
                  </button>
                )}

                {selectedDataset && (
                  <button
                    onClick={() => handleGenerateReport(selectedDataset, true)}
                    disabled={isGeneratingReport}
                    className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-bold flex items-center space-x-1.5 transition shadow-sm shadow-sky-500/20 disabled:opacity-50"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{isGeneratingReport ? 'Generating...' : 'Automate Executive Report'}</span>
                  </button>
                )}
              </div>
            </div>

            {/* Tabular Grid View */}
            {isLoadingPreview ? (
              <div className="p-12 text-center text-slate-500 text-xs font-mono">
                Loading dataset preview records...
              </div>
            ) : datasetPreview ? (
              <div className="overflow-x-auto border border-slate-800 rounded-xl bg-slate-950">
                <table className="w-full text-left text-xs text-slate-200 border-collapse">
                  <thead>
                    <tr className="bg-slate-900 border-b border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                      <th className="py-2.5 px-3 w-10 text-center">#</th>
                      {datasetPreview.columns.map((col) => (
                        <th key={col} className="py-2.5 px-3 whitespace-nowrap">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {datasetPreview.rows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/60 transition">
                        <td className="py-2 px-3 text-center text-slate-500">{idx + 1}</td>
                        {datasetPreview.columns.map((col) => {
                          const val = row[col] || '';
                          const isNumeric = !isNaN(Number(val.replace(/[$,]/g, ''))) && val !== '';
                          return (
                            <td
                              key={col}
                              className={`py-2 px-3 whitespace-nowrap ${
                                isNumeric ? 'text-right text-emerald-400 font-semibold' : 'text-slate-200'
                              }`}
                            >
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs">
                No dataset selected. Select a dataset on the left or add a new one.
              </div>
            )}

          </div>

        </div>
      )}

      {/* TAB 2: Executive Reports Hub */}
      {activeSubTab === 'reports' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column (4 cols): Select Report */}
          <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                <FileText className="w-4 h-4 text-emerald-400" />
                <span>Executive Reports ({reports.length})</span>
              </span>
            </div>

            <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
              {reports.map((rep) => {
                const isSelected = selectedReport === rep.filename;
                return (
                  <div
                    key={rep.filename}
                    onClick={() => handleSelectReport(rep.filename)}
                    className={`p-3 rounded-xl border transition cursor-pointer space-y-2 ${
                      isSelected
                        ? 'bg-emerald-500/10 border-emerald-500/50 shadow-sm'
                        : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-white font-mono truncate">{rep.title}</p>
                        <p className="text-[10px] font-mono text-slate-400 mt-0.5">{rep.filename}</p>
                      </div>
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono shrink-0">
                        MD
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-400 line-clamp-2">
                      {rep.summary || 'Empirical metrics, top drivers, and strategic automated insights.'}
                    </p>

                    <div className="flex items-center space-x-2 pt-1 border-t border-slate-800/80">
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleDownloadReport(rep.filename); }}
                        className="flex-1 py-1 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold flex items-center justify-center space-x-1 transition"
                      >
                        <Download className="w-3 h-3 text-sky-400" />
                        <span>Download</span>
                      </button>

                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); window.print(); }}
                        className="py-1 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-semibold flex items-center justify-center space-x-1 transition"
                        title="Print / Export PDF"
                      >
                        <Printer className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column (8 cols): Rendered Markdown Viewer */}
          <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-sm font-bold text-white font-mono">
                  {selectedReport || 'Select an executive report'}
                </span>
                <p className="text-xs text-slate-400 mt-0.5">
                  Autonomous analysis report generated from empirical ground truth data.
                </p>
              </div>

              {selectedReport && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => window.print()}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center space-x-1.5 transition"
                  >
                    <Printer className="w-3.5 h-3.5" />
                    <span>Print / Export PDF</span>
                  </button>

                  <button
                    onClick={() => handleDownloadReport(selectedReport)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-white text-xs font-bold flex items-center space-x-1.5 transition shadow-sm shadow-emerald-500/20"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Report</span>
                  </button>
                </div>
              )}
            </div>

            {/* Document Body */}
            {reportPreview ? (
              <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 font-sans text-xs text-slate-200 space-y-4 whitespace-pre-wrap leading-relaxed select-text overflow-y-auto max-h-[650px]">
                {reportPreview.content}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs">
                No report selected. Select a report from the list on the left.
              </div>
            )}

          </div>

        </div>
      )}

      {/* TAB 3: Create Custom CSV Dataset */}
      {activeSubTab === 'create_dataset' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5 max-w-4xl mx-auto">
          
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <FileCode2 className="w-4 h-4 text-sky-400" />
                <span>Create & Publish Custom CSV Dataset</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Define tabular data, download immediately, and automate strategic reporting with AgentOS.
              </p>
            </div>

            {/* Presets */}
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-bold uppercase text-slate-400">Presets:</span>
              <button
                type="button"
                onClick={() => loadPresetCsv('sales')}
                className="text-[11px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              >
                Q4 Sales
              </button>
              <button
                type="button"
                onClick={() => loadPresetCsv('churn')}
                className="text-[11px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              >
                Customer Retention
              </button>
              <button
                type="button"
                onClick={() => loadPresetCsv('servers')}
                className="text-[11px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              >
                GPU Metrics
              </button>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Dataset Filename (.csv)
              </label>
              <input
                type="text"
                value={newDatasetName}
                onChange={(e) => setNewDatasetName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:ring-1 focus:ring-sky-500"
                placeholder="e.g. quarterly_financial_metrics.csv"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Raw CSV Content (First line must be Column Headers)
                </label>
                <span className="text-[10px] text-slate-500 font-mono">
                  {csvRawContent.split('\n').filter(Boolean).length} rows detected
                </span>
              </div>
              <textarea
                rows={10}
                value={csvRawContent}
                onChange={(e) => setCsvRawContent(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-xs text-emerald-300 font-mono focus:outline-none focus:ring-1 focus:ring-sky-500 leading-relaxed resize-y"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 flex flex-col sm:flex-row items-center gap-3">
            <button
              type="button"
              onClick={() => handleCreateDataset(true)}
              className="w-full sm:flex-1 py-2.5 px-4 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold flex items-center justify-center space-x-2 shadow-lg shadow-sky-500/20 transition"
            >
              <Sparkles className="w-4 h-4" />
              <span>Save & Automate Analysis Report</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </button>

            <button
              type="button"
              onClick={() => handleCreateDataset(false)}
              className="w-full sm:w-auto py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition"
            >
              <Download className="w-3.5 h-3.5 text-sky-400" />
              <span>Save & Download CSV</span>
            </button>
          </div>

        </div>
      )}

    </div>
  );
};
