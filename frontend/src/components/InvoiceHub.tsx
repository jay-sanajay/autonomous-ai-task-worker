import React, { useState, useEffect } from 'react';
import {
  FileText, Download, Play, Plus, Trash2, CheckCircle2,
  Zap, Building2, Calendar, DollarSign, Sparkles, RefreshCw, Cpu
} from 'lucide-react';
import { InvoiceDoc, Vendor } from '../types';
import * as api from '../services/api';

interface InvoiceHubProps {
  invoices: InvoiceDoc[];
  vendors: Vendor[];
  onRefresh: () => void;
  onRunTask: (goal: string) => void;
}

interface LineItem {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
}

export const InvoiceHub: React.FC<InvoiceHubProps> = ({
  invoices,
  vendors,
  onRefresh,
  onRunTask
}) => {
  // New invoice state
  const [vendorName, setVendorName] = useState(vendors[0]?.name || 'Acme Technologies');
  const [invoiceNumber, setInvoiceNumber] = useState(`INV-2026-${Math.floor(100 + Math.random() * 900)}`);
  const [dueDate, setDueDate] = useState('2026-11-30');
  const [paymentTerms, setPaymentTerms] = useState('NET_30');
  const [currency, setCurrency] = useState('USD');
  const [items, setItems] = useState<LineItem[]>([
    { id: '1', description: 'Enterprise AI Autonomous Task Agent License', quantity: 1, unit_price: 2500.00 },
    { id: '2', description: 'Dedicated High-Throughput Compute Nodes (Q4)', quantity: 2, unit_price: 750.00 }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [creationSuccess, setCreationSuccess] = useState<string | null>(null);

  // Groq configuration state
  const [groqKey, setGroqKey] = useState('');
  const [groqModel, setGroqModel] = useState('llama-3.3-70b-versatile');
  const [llmStatus, setLlmStatus] = useState<any>(null);
  const [isSavingGroq, setIsSavingGroq] = useState(false);
  const [groqMessage, setGroqMessage] = useState<string | null>(null);

  useEffect(() => {
    loadLlmStatus();
  }, []);

  const loadLlmStatus = async () => {
    try {
      const status = await api.fetchLLMStatus();
      setLlmStatus(status);
      if (status.default_model) setGroqModel(status.default_model);
    } catch (err) {
      console.error('Failed to load LLM status:', err);
    }
  };

  const handleSaveGroq = async () => {
    if (!groqKey.trim()) return;
    setIsSavingGroq(true);
    setGroqMessage(null);
    try {
      const res = await api.setGroqAPIKey(groqKey.trim(), groqModel);
      setGroqMessage(res.message);
      await loadLlmStatus();
      setGroqKey('');
    } catch (err: any) {
      setGroqMessage(`Failed to set Groq key: ${err.message || err}`);
    } finally {
      setIsSavingGroq(false);
    }
  };

  const addItem = () => {
    setItems((prev) => [
      ...prev,
      { id: Date.now().toString(), description: 'Consulting & Implementation Services', quantity: 1, unit_price: 500.00 }
    ]);
  };

  const removeItem = (id: string) => {
    setItems((prev) => (prev.length > 1 ? prev.filter((i) => i.id !== id) : prev));
  };

  const updateItem = (id: string, field: keyof LineItem, val: any) => {
    setItems((prev) =>
      prev.map((i) => (i.id === id ? { ...i, [field]: val } : i))
    );
  };

  const totalAmount = items.reduce((sum, i) => sum + (Number(i.quantity) || 0) * (Number(i.unit_price) || 0), 0);

  const handleCreateInvoice = async (autoRun: boolean) => {
    setIsSubmitting(true);
    setCreationSuccess(null);
    try {
      const res = await api.createCustomInvoice({
        vendor_name: vendorName,
        invoice_number: invoiceNumber,
        due_date: dueDate,
        currency,
        payment_terms: paymentTerms,
        items: items.map((i) => ({
          description: i.description,
          quantity: Number(i.quantity) || 1,
          unit_price: Number(i.unit_price) || 0
        })),
        auto_run_agent: autoRun
      });

      setCreationSuccess(res.message);
      onRefresh();

      if (autoRun && res.task_id) {
        onRunTask(`Find latest invoice ${invoiceNumber} from ${vendorName}, extract amount and due date, and save in invoice system.`);
      }

      // Generate next random invoice number
      setInvoiceNumber(`INV-2026-${Math.floor(100 + Math.random() * 900)}`);
    } catch (err: any) {
      alert(`Invoice creation failed: ${err.message || err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Groq AI Engine Integration Strip */}
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-orange-500/10 border border-orange-500/30 flex items-center justify-center text-orange-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white">Groq Llama-3.3-70B Inference Engine</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                llmStatus?.groq_configured
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {llmStatus?.groq_configured ? 'GROQ ACTIVE' : 'DETERMINISTIC FALLBACK ACTIVE'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Ultra-fast tool-calling loop powered by Groq Llama 3.3 70B & 3.1 8B. Enter key to activate live inference.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="password"
            placeholder={llmStatus?.groq_configured ? `Key configured (${llmStatus.masked_api_key})` : 'Paste Groq API Key (gsk_...)'}
            value={groqKey}
            onChange={(e) => setGroqKey(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-orange-500 w-56"
          />
          <select
            value={groqModel}
            onChange={(e) => setGroqModel(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
          >
            <option value="llama-3.3-70b-versatile">Llama 3.3 70B</option>
            <option value="llama-3.1-8b-instant">Llama 3.1 8B</option>
            <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
          </select>
          <button
            onClick={handleSaveGroq}
            disabled={isSavingGroq || !groqKey.trim()}
            className="px-3 py-1.5 bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition flex items-center space-x-1 shrink-0"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{isSavingGroq ? 'Saving...' : 'Set Key'}</span>
          </button>
        </div>
      </div>

      {groqMessage && (
        <div className="p-2.5 bg-orange-950/30 border border-orange-500/30 rounded-lg text-xs text-orange-300 font-mono">
          ✓ {groqMessage}
        </div>
      )}

      {/* Grid: Left: Select & Download Invoices | Right: Create New Invoice with Items */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Col (5 cols): Select & Download Existing Invoices */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-sky-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Select & Download Invoices ({invoices.length})
              </h3>
            </div>
            <button
              onClick={onRefresh}
              className="text-slate-400 hover:text-white transition"
              title="Refresh invoices"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
            {invoices.map((inv) => {
              const downloadUrl = api.getInvoiceDownloadUrl(inv.filename);
              const isPdf = inv.filename.toLowerCase().endsWith('.pdf');
              const isHigh = inv.filename.includes('HighValue');
              const isOld = inv.filename.includes('Old');
              const isMissing = inv.filename.includes('MissingAmount');

              return (
                <div
                  key={inv.id}
                  className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70 hover:border-slate-700 transition space-y-2.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center space-x-1.5">
                        <span className={`text-[9px] font-bold uppercase px-1.5 py-0.2 rounded font-mono ${
                          isPdf ? 'bg-rose-500/20 text-rose-300' : 'bg-sky-500/20 text-sky-300'
                        }`}>
                          {isPdf ? 'PDF' : 'TXT'}
                        </span>
                        <p className="text-xs font-bold text-white font-mono truncate">{inv.filename}</p>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Vendor: <span className="text-slate-200 font-semibold">{inv.vendor_name_hint || 'Vendor'}</span> • {(inv.file_size_bytes / 1024).toFixed(1)} KB
                      </p>
                    </div>

                    <div className="shrink-0">
                      {isHigh && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                          HITL Sign-off
                        </span>
                      )}
                      {isOld && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                          Duplicate Case
                        </span>
                      )}
                      {isMissing && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                          Missing Data
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions for this invoice */}
                  <div className="flex items-center space-x-2 pt-1 border-t border-slate-800/80">
                    <a
                      href={downloadUrl}
                      download={inv.filename}
                      className="flex-1 py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold flex items-center justify-center space-x-1 transition"
                    >
                      <Download className="w-3.5 h-3.5 text-sky-400" />
                      <span>Download</span>
                    </a>

                    <button
                      onClick={() => onRunTask(`Find the invoice at ${inv.file_path}, extract its amount and due date, and save it in the invoice system.`)}
                      className="flex-1 py-1.5 px-2 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-bold flex items-center justify-center space-x-1 transition"
                    >
                      <Play className="w-3 h-3" />
                      <span>Automate</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col (7 cols): Create New Invoice with Itemized Line Items */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Plus className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Create & Automate New Itemized Invoice
              </h3>
            </div>
            <span className="text-[11px] font-mono text-emerald-400 font-bold">
              Total: ${totalAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })} {currency}
            </span>
          </div>

          {creationSuccess && (
            <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{creationSuccess}</span>
            </div>
          )}

          {/* Form Fields Header */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Vendor
              </label>
              <select
                value={vendorName}
                onChange={(e) => setVendorName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-sky-500"
              >
                {vendors.map((v) => (
                  <option key={v.id} value={v.name}>{v.name} ({v.vendor_code})</option>
                ))}
                <option value="Apex Logistics Global">Apex Logistics Global</option>
                <option value="CentrAlign Cloud Technologies">CentrAlign Cloud Technologies</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Invoice Number
              </label>
              <input
                type="text"
                value={invoiceNumber}
                onChange={(e) => setInvoiceNumber(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Due Date
              </label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
          </div>

          {/* Terms & Currency */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Payment Terms
              </label>
              <select
                value={paymentTerms}
                onChange={(e) => setPaymentTerms(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="NET_30">NET 30 Days</option>
                <option value="NET_15">NET 15 Days</option>
                <option value="NET_60">NET 60 Days</option>
                <option value="IMMEDIATE">Due Upon Receipt</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Currency
              </label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
                <option value="INR">INR (₹)</option>
              </select>
            </div>
          </div>

          {/* Dynamic Itemized Line Items */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Itemized Expenses & Products
              </span>
              <button
                onClick={addItem}
                className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs font-semibold transition"
              >
                <Plus className="w-3 h-3" />
                <span>Add Item</span>
              </button>
            </div>

            <div className="space-y-2">
              {items.map((it, idx) => (
                <div key={it.id} className="grid grid-cols-12 gap-2 items-center bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div className="col-span-6">
                    <input
                      type="text"
                      placeholder="Item Description"
                      value={it.description}
                      onChange={(e) => updateItem(it.id, 'description', e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                    />
                  </div>

                  <div className="col-span-2">
                    <input
                      type="number"
                      placeholder="Qty"
                      min="1"
                      value={it.quantity}
                      onChange={(e) => updateItem(it.id, 'quantity', parseInt(e.target.value) || 1)}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white text-center"
                    />
                  </div>

                  <div className="col-span-3">
                    <input
                      type="number"
                      placeholder="Unit Price"
                      step="0.01"
                      value={it.unit_price}
                      onChange={(e) => updateItem(it.id, 'unit_price', parseFloat(e.target.value) || 0)}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono"
                    />
                  </div>

                  <div className="col-span-1 text-center">
                    <button
                      onClick={() => removeItem(it.id)}
                      className="text-slate-500 hover:text-rose-400 transition"
                      title="Remove item"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-slate-800 flex flex-col sm:flex-row items-center gap-3">
            <button
              onClick={() => handleCreateInvoice(true)}
              disabled={isSubmitting}
              className="w-full sm:flex-1 py-2.5 px-4 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold flex items-center justify-center space-x-2 shadow-lg shadow-sky-500/20 transition disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isSubmitting ? 'Creating & Launching...' : 'Create & Automate with AgentOS'}</span>
            </button>

            <button
              onClick={() => handleCreateInvoice(false)}
              disabled={isSubmitting}
              className="w-full sm:w-auto py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Save & Download Document</span>
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};
