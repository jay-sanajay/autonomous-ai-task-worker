import React, { useState, useEffect } from 'react';
import {
  FileText, Download, Play, Plus, Trash2, CheckCircle2,
  Zap, Building2, Sparkles, RefreshCw, Cpu, Eye, X,
  Printer, Search, ArrowRight, Tag
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
  hsn_sac?: string;
}

export const formatInr = (num: number): string => {
  const parts = Math.abs(num).toFixed(2).split('.');
  let integerPart = parts[0];
  const decimalPart = parts[1];
  if (integerPart.length > 3) {
    const last3 = integerPart.slice(-3);
    const rest = integerPart.slice(0, -3);
    const grouped = [];
    let rem = rest;
    while (rem.length > 2) {
      grouped.unshift(rem.slice(-2));
      rem = rem.slice(0, -2);
    }
    if (rem.length > 0) grouped.unshift(rem);
    integerPart = grouped.join(',') + ',' + last3;
  }
  return (num < 0 ? '-' : '') + integerPart + '.' + decimalPart;
};

export const InvoiceHub: React.FC<InvoiceHubProps> = ({
  invoices,
  vendors,
  onRefresh,
  onRunTask
}) => {
  // Form fields (Indian standard corporate defaults)
  const [vendorName, setVendorName] = useState(vendors[0]?.name || 'Acme Technologies India Pvt. Ltd.');
  const [vendorAddress, setVendorAddress] = useState('Prestige Tech Park, Outer Ring Road, Bengaluru, Karnataka 560103');
  const [vendorTaxId, setVendorTaxId] = useState('29AABCU9603R1ZM'); // Indian GSTIN
  const [clientName, setClientName] = useState('AgentOS Enterprise Systems India Pvt. Ltd.');
  const [clientEmail, setClientEmail] = useState('ap-india@agentos.internal');
  const [invoiceNumber, setInvoiceNumber] = useState(`INV-2026-${Math.floor(100 + Math.random() * 900)}`);
  const [issueDate, setIssueDate] = useState('2026-10-14');
  const [dueDate, setDueDate] = useState('2026-11-13');
  const [paymentTerms, setPaymentTerms] = useState('NET_30');
  const [currency, setCurrency] = useState('INR');
  const [taxRate, setTaxRate] = useState<number>(18);
  const [discount, setDiscount] = useState<number>(0);
  const [notes, setNotes] = useState('Remit via NEFT / RTGS / IMPS to Vendor Current Account. IFSC: HDFC0000123');

  // Items write option & mode
  const [itemsMode, setItemsMode] = useState<'grid' | 'write'>('grid');
  const [rawItemsText, setRawItemsText] = useState(
    'Enterprise AI Autonomous Task Agent License, SAC: 998313, Qty: 1, Rate: 50000\nDedicated Cloud GPU Compute Nodes, SAC: 998314, Qty: 2, Rate: 25000'
  );

  // Itemized line items
  const [items, setItems] = useState<LineItem[]>([
    { id: '1', description: 'Enterprise AI Autonomous Task Agent License', quantity: 1, unit_price: 50000.00, hsn_sac: '998313' },
    { id: '2', description: 'Dedicated Cloud GPU Compute Nodes (Monthly)', quantity: 2, unit_price: 25000.00, hsn_sac: '998314' }
  ]);

  // Submission & Feedback
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [downloadingFn, setDownloadingFn] = useState<string | null>(null);
  const [creationSuccess, setCreationSuccess] = useState<string | null>(null);
  const [creationError, setCreationError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Search & Filter for Invoice List
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'ALL' | 'PDF' | 'TXT'>('ALL');

  // Preview Modal
  const [previewData, setPreviewData] = useState<{
    filename: string;
    type: string;
    content: string;
    size_bytes?: number;
    download_url?: string;
  } | null>(null);

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
    const keyToUse = groqKey.trim() || (llmStatus?.groq_configured ? 'KEEP_EXISTING' : '');
    if (!keyToUse) return;
    setIsSavingGroq(true);
    setGroqMessage(null);
    try {
      const res = await api.setGroqAPIKey(keyToUse, groqModel);
      setGroqMessage(res.message);
      await loadLlmStatus();
      setGroqKey('');
    } catch (err: any) {
      setGroqMessage(`Failed to set Groq key: ${err.message || err}`);
    } finally {
      setIsSavingGroq(false);
    }
  };

  // Upload Invoice Handler
  const handleUploadInvoice = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setCreationError(null);
    setCreationSuccess(null);
    try {
      const res = await api.uploadAnyFile(file);
      setCreationSuccess(`Uploaded '${res.filename}' successfully! Ready for automated processing.`);
      onRefresh();
    } catch (err: any) {
      setCreationError(`Upload failed: ${err.message || err}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Line items actions
  const addItem = () => {
    setItems((prev) => [
      ...prev,
      { id: Date.now().toString(), description: 'Enterprise AI Implementation & Support Services', quantity: 1, unit_price: 25000.00, hsn_sac: '998313' }
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

  // Parse written / freeform text items directly into grid
  const parseWrittenItemsToGrid = () => {
    if (!rawItemsText.trim()) return;
    const lines = rawItemsText.trim().split('\n');
    const newItems: LineItem[] = [];

    for (const rawLine of lines) {
      let line = rawLine.trim();
      if (!line || line.startsWith('#') || line.startsWith('//')) continue;

      let hsn = '998313';
      const hsnMatch = line.match(/(?:HSN|SAC)[:\s]+([0-9]{4,8})/i);
      if (hsnMatch) {
        hsn = hsnMatch[1];
        line = line.replace(hsnMatch[0], '').trim();
      }

      // Pattern 1: e.g. "AI Model Support x 2 @ 15000" or "Service x 3 @ Rs. 5000"
      const m1 = line.match(/^(.*?)\s+[xX*]\s*([0-9]+)\s*[@atAT:]+\s*(?:₹|Rs\.?|INR|\$)?\s*([0-9,.]+)/);
      if (m1) {
        newItems.push({
          id: Date.now().toString() + Math.random().toString().slice(2, 6),
          description: m1[1].trim().replace(/^[-:,]+|[-:,]+$/g, ''),
          quantity: parseInt(m1[2]) || 1,
          unit_price: parseFloat(m1[3].replace(/,/g, '')) || 0,
          hsn_sac: hsn
        });
        continue;
      }

      // Pattern 2: Comma separated: "Description, Qty, Rate"
      const parts = line.split(',').map((p) => p.trim()).filter(Boolean);
      if (parts.length >= 3) {
        const pQty = parseInt(parts[1].replace(/[^\d]/g, '')) || 1;
        const pRate = parseFloat(parts[2].replace(/[^\d.]/g, '')) || 0;
        newItems.push({
          id: Date.now().toString() + Math.random().toString().slice(2, 6),
          description: parts[0],
          quantity: Math.max(1, pQty),
          unit_price: pRate,
          hsn_sac: hsn
        });
        continue;
      }

      // Pattern 3: "Description - Rate"
      const m3 = line.match(/^(.*?)\s*[-:]\s*(?:₹|Rs\.?|INR|\$)?\s*([0-9,.]+)\s*$/);
      if (m3) {
        newItems.push({
          id: Date.now().toString() + Math.random().toString().slice(2, 6),
          description: m3[1].trim(),
          quantity: 1,
          unit_price: parseFloat(m3[2].replace(/,/g, '')) || 0,
          hsn_sac: hsn
        });
        continue;
      }

      // Fallback: single item description
      newItems.push({
        id: Date.now().toString() + Math.random().toString().slice(2, 6),
        description: line,
        quantity: 1,
        unit_price: 25000.0,
        hsn_sac: hsn
      });
    }

    if (newItems.length > 0) {
      setItems(newItems);
      setItemsMode('grid');
    }
  };

  // Financial calculations
  const subtotal = items.reduce((sum, i) => sum + (Number(i.quantity) || 0) * (Number(i.unit_price) || 0), 0);
  const taxAmount = (subtotal * (Number(taxRate) || 0)) / 100;
  const netTotal = Math.max(0, subtotal + taxAmount - (Number(discount) || 0));

  // Preset Template Loader (Indian Standard Corporate Vendors)
  const loadPreset = (type: 'ai' | 'consulting' | 'hardware') => {
    if (type === 'ai') {
      setVendorName('Acme Technologies India Pvt. Ltd.');
      setVendorAddress('Prestige Tech Park, Outer Ring Road, Bengaluru, Karnataka 560103');
      setVendorTaxId('29AABCU9603R1ZM');
      setPaymentTerms('NET_30');
      setItems([
        { id: '1', description: 'Enterprise AI Autonomous Task Worker Platform License', quantity: 1, unit_price: 50000.00, hsn_sac: '998313' },
        { id: '2', description: 'Dedicated High-Throughput Inference Compute Cluster (Q4)', quantity: 2, unit_price: 25000.00, hsn_sac: '998314' },
        { id: '3', description: 'Secure Sandbox Container Isolation Addon', quantity: 1, unit_price: 15000.00, hsn_sac: '998313' }
      ]);
      setNotes('Remit via NEFT / RTGS / IMPS to HDFC Bank Current Account. IFSC: HDFC0000123');
    } else if (type === 'consulting') {
      setVendorName('Apex Logistics India Pvt. Ltd.');
      setVendorAddress('Bandra-Kurla Complex (BKC), Bandra East, Mumbai, Maharashtra 400051');
      setVendorTaxId('27AABCA1234F1Z8');
      setPaymentTerms('NET_15');
      setItems([
        { id: '1', description: 'ERP Accounting Integration Architecture Consulting', quantity: 10, unit_price: 4500.00, hsn_sac: '998313' },
        { id: '2', description: 'Autonomous Agent Verification Workflow Audit', quantity: 1, unit_price: 35000.00, hsn_sac: '998313' }
      ]);
      setNotes('Remit payment via direct corporate NEFT/RTGS to ICICI Bank. IFSC: ICIC0000001');
    } else {
      setVendorName('CentrAlign Cloud Technologies India Pvt. Ltd.');
      setVendorAddress('HITEC City, Madhapur, Hyderabad, Telangana 500081');
      setVendorTaxId('36AABCC5678K1Z2');
      setPaymentTerms('NET_30');
      setItems([
        { id: '1', description: 'Bare-Metal Inference Server Node (128GB RAM, NVMe RAID)', quantity: 1, unit_price: 120000.00, hsn_sac: '847150' },
        { id: '2', description: 'Dual 10Gbps SFP+ Fiber Network Interface Cards', quantity: 2, unit_price: 12500.00, hsn_sac: '847180' }
      ]);
      setNotes('Remittance reference must include invoice number on NEFT memo. IFSC: SBIN0001234');
    }
  };

  // Direct Download Trigger
  const handleDownload = async (filename: string) => {
    setDownloadingFn(filename);
    try {
      await api.downloadInvoiceFile(filename);
    } catch (err: any) {
      setCreationError(`Download failed: ${err.message || err}`);
    } finally {
      setTimeout(() => setDownloadingFn(null), 800);
    }
  };

  // In-browser preview
  const handlePreviewDocument = async (filename: string) => {
    try {
      const data = await api.fetchInvoicePreview(filename);
      setPreviewData(data);
    } catch (err: any) {
      setCreationError(`Preview failed: ${err.message || err}`);
    }
  };

  // Live in-memory preview of the current form as Indian Tax Invoice
  const handlePreviewCurrentForm = () => {
    const pad = (s: string | number, n: number, right = false) => {
      const str = String(s);
      return right ? str.padStart(n) : str.padEnd(n);
    };

    const formattedRows = items.map((it, idx) => {
      const q = Number(it.quantity) || 1;
      const r = Number(it.unit_price) || 0;
      const t = q * r;
      const hsn = it.hsn_sac || '998313';
      const desc = it.description.length > 36 ? it.description.slice(0, 36) + '..' : it.description;
      return `${pad(idx + 1, 3)} ${pad(desc, 38)} ${pad(hsn, 8)} ${pad(q, 3, true)}   ₹${pad(formatInr(r), 10, true)}   ₹${pad(formatInr(t), 11, true)}`;
    }).join('\n');

    const cgstAmount = taxAmount / 2.0;
    const sgstAmount = taxAmount / 2.0;

    const previewText = `================================================================================
                    TAX INVOICE / OFFICIAL COMMERCIAL INVOICE
                  (Issued as per Section 31 of CGST Act, 2017)
================================================================================
SUPPLIER / VENDOR DETAILS:              BILL TO / RECIPIENT:
${pad(vendorName, 40)} ${clientName}
${pad(vendorAddress, 40)} Cyber City, DLF Phase 2, Gurugram, Haryana 122002
GSTIN / UIN : ${pad(vendorTaxId, 26)} GSTIN / UIN : 06AAICA4589K1Z4
State / Code: Karnataka (29)             State / Code: Haryana (06)
--------------------------------------------------------------------------------
Invoice Number: ${pad(invoiceNumber, 24)} Invoice Date: ${issueDate} (IST)
Payment Terms : ${pad(paymentTerms, 24)} Due Date    : ${dueDate} (IST)
Currency      : ${pad(currency, 24)} Status      : UNPAID / DUE
================================================================================
ITEMIZED TAXABLE GOODS & SERVICES BREAKDOWN:
--------------------------------------------------------------------------------
#   Description                            HSN/SAC   Qty     Unit Price          Total
--  ------------------------------------  --------  ---  --------------  -------------
${formattedRows}
--------------------------------------------------------------------------------
Taxable Subtotal Amount                   :     ₹ ${pad(formatInr(subtotal), 14, true)} ${currency}
CGST (${(taxRate / 2.0).toFixed(1)}%)                                  :     ₹ ${pad(formatInr(cgstAmount), 14, true)} ${currency}
SGST (${(taxRate / 2.0).toFixed(1)}%)                                  :     ₹ ${pad(formatInr(sgstAmount), 14, true)} ${currency}
Total GST (${taxRate.toFixed(1)}%)                            :     ₹ ${pad(formatInr(taxAmount), 14, true)} ${currency}
Discount Applied                          :    -₹ ${pad(formatInr(discount || 0), 14, true)} ${currency}
--------------------------------------------------------------------------------
TOTAL INVOICE AMOUNT (INR)                :     ₹ ${pad(formatInr(netTotal), 14, true)} ${currency}
================================================================================
BANK REMITTANCE & PAYMENT INSTRUCTIONS:
• Bank Name: HDFC Bank Ltd. | Current Account: 50200048192019 | IFSC: HDFC0000123
• Mode: NEFT / RTGS / IMPS / UPI
• ${notes}
• Remittance Reference: ${invoiceNumber} / ${vendorName}
================================================================================`;

    setPreviewData({
      filename: `${invoiceNumber}_${vendorName.replace(/[\s.,]/g, '')}.txt`,
      type: 'TXT',
      content: previewText,
      size_bytes: previewText.length
    });
  };

  // Create Invoice Handler
  const handleCreateInvoice = async (autoRun: boolean) => {
    setIsSubmitting(true);
    setCreationSuccess(null);
    setCreationError(null);
    try {
      const res = await api.createCustomInvoice({
        vendor_name: vendorName,
        vendor_address: vendorAddress,
        vendor_tax_id: vendorTaxId,
        client_name: clientName,
        client_email: clientEmail,
        invoice_number: invoiceNumber,
        issue_date: issueDate,
        due_date: dueDate,
        currency,
        payment_terms: paymentTerms,
        tax_rate: taxRate,
        discount: discount,
        notes: notes,
        items: items.map((i) => ({
          description: i.description,
          quantity: Number(i.quantity) || 1,
          unit_price: Number(i.unit_price) || 0,
          hsn_sac: i.hsn_sac || '998313'
        })),
        raw_items_text: itemsMode === 'write' ? rawItemsText : undefined,
        auto_run_agent: false // We trigger agent via onRunTask so frontend streams live timeline
      });

      // 1. Immediately trigger real browser file download
      await api.downloadInvoiceFile(res.filename);

      setCreationSuccess(`Tax Invoice '${res.filename}' created and downloaded! Total: ₹${formatInr(res.total_amount)} ${currency}`);
      onRefresh();

      // 2. If automate requested, immediately transition to Task Studio and launch the autonomous agent!
      if (autoRun) {
        const goal = `Find the invoice at ${res.file_path}, extract its amount and due date, and save it in the invoice system.`;
        onRunTask(goal);
      }

      // Generate next random invoice number
      setInvoiceNumber(`INV-2026-${Math.floor(100 + Math.random() * 900)}`);
    } catch (err: any) {
      setCreationError(`Invoice creation failed: ${err.message || err}. Please ensure backend services are reachable.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filtered invoices
  const filteredInvoices = invoices.filter((inv) => {
    const matchesSearch = inv.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (inv.vendor_name_hint || '').toLowerCase().includes(searchQuery.toLowerCase());
    const isPdf = inv.filename.toLowerCase().endsWith('.pdf');
    if (filterType === 'PDF') return matchesSearch && isPdf;
    if (filterType === 'TXT') return matchesSearch && !isPdf;
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
      
      {/* Groq AI Engine Banner */}
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-card-subtle">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-[#142019] border border-[#263A2E] flex items-center justify-center text-[#55E6A5] shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-bold text-[#F0F7F2]">
                Groq Autonomous Inference Engine
              </span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                llmStatus?.groq_configured
                  ? 'bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30'
                  : 'bg-[#142019] text-[#718278] border border-[#263A2E]'
              }`}>
                {llmStatus?.groq_configured ? 'GROQ ACTIVE' : 'DETERMINISTIC FALLBACK ACTIVE'}
              </span>
            </div>
            <p className="text-xs text-[#A0B2A6] mt-0.5">
              High-throughput function calling with instant response times (~300ms). Active model: <span className="font-mono text-[#FFC66D] font-bold">{llmStatus?.default_model || groqModel}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <a
            href="https://console.groq.com/keys"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-[#55E6A5] hover:text-[#35D993] underline underline-offset-2 flex items-center space-x-0.5"
            title="Get a free Groq API key from Groq Console"
          >
            <span>Get Free Key ↗</span>
          </a>
          <input
            type="password"
            autoComplete="off"
            data-lpignore="true"
            name="groq_api_token_no_autofill"
            placeholder={llmStatus?.groq_configured ? `Configured (${llmStatus.masked_api_key})` : 'Paste Groq Key (gsk_...)'}
            value={groqKey}
            onChange={(e) => setGroqKey(e.target.value)}
            className="bg-[#080D0B] border border-[#263A2E] rounded-lg px-3 py-1.5 text-xs text-[#F0F7F2] placeholder-[#718278] focus:outline-none focus:border-[#55E6A5] w-52 font-mono"
          />
          <select
            value={groqModel}
            onChange={(e) => setGroqModel(e.target.value)}
            className="bg-[#080D0B] border border-[#263A2E] rounded-lg px-2.5 py-1.5 text-xs text-[#F0F7F2] font-mono focus:outline-none focus:border-[#55E6A5]"
          >
            <option value="openai/gpt-oss-120b">GPT-OSS 120B (High Capacity)</option>
            <option value="llama-3.3-70b-versatile">Llama 3.3 70B</option>
            <option value="llama-3.1-8b-instant">Llama 3.1 8B (Fast)</option>
            <option value="qwen/qwen3.8-27b">Qwen 3.8 27B</option>
          </select>
          <button
            onClick={handleSaveGroq}
            disabled={isSavingGroq || (!groqKey.trim() && !llmStatus?.groq_configured)}
            className="px-3 py-1.5 bg-[#55E6A5] hover:bg-[#35D993] disabled:opacity-50 text-[#080D0B] rounded-lg text-xs font-bold transition flex items-center space-x-1 shrink-0 shadow-glow-jade"
          >
            <Zap className="w-3.5 h-3.5 fill-current" />
            <span>{isSavingGroq ? 'Saving...' : 'Set Model / Key'}</span>
          </button>
        </div>
      </div>

      {groqMessage && (
        <div className="p-2.5 bg-[#142019] border border-[#55E6A5]/40 rounded-lg text-xs text-[#55E6A5] font-mono flex items-center gap-2">
          <span>✓</span>
          <span>{groqMessage}</span>
        </div>
      )}

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Col (5 cols): Select, Preview & Download Invoices */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-sky-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Select & Download Invoices ({filteredInvoices.length})
              </h3>
            </div>
            <button
              onClick={onRefresh}
              className="text-slate-400 hover:text-white transition p-1 rounded hover:bg-slate-800"
              title="Refresh repository"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Search & Filter Controls */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search invoice number, vendor..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
            <div className="flex items-center space-x-1.5">
              {(['ALL', 'PDF', 'TXT'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setFilterType(t)}
                  className={`px-2 py-0.5 rounded text-[10px] font-bold transition ${
                    filterType === t
                      ? 'bg-sky-500 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Invoice Cards List */}
          <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
            {filteredInvoices.map((inv) => {
              const isPdf = inv.filename.toLowerCase().endsWith('.pdf');
              const isHigh = inv.filename.includes('HighValue');
              const isOld = inv.filename.includes('Old');
              const isMissing = inv.filename.includes('MissingAmount');
              const isDownloading = downloadingFn === inv.filename;

              return (
                <div
                  key={inv.id}
                  className="p-3 rounded-xl border border-slate-800 bg-slate-950/80 hover:border-slate-700 transition space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center space-x-1.5">
                        <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded font-mono ${
                          isPdf ? 'bg-rose-500/20 text-rose-300' : 'bg-sky-500/20 text-sky-300'
                        }`}>
                          {isPdf ? 'PDF' : 'TXT'}
                        </span>
                        <p className="text-xs font-bold text-white font-mono truncate" title={inv.filename}>
                          {inv.filename}
                        </p>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Vendor: <span className="text-slate-200 font-semibold">{inv.vendor_name_hint || 'Vendor'}</span> • {(inv.file_size_bytes / 1024).toFixed(1)} KB
                      </p>
                    </div>

                    <div className="shrink-0 flex flex-col items-end gap-1">
                      {isHigh && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                          HITL Approval
                        </span>
                      )}
                      {isOld && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                          Duplicate Check
                        </span>
                      )}
                      {isMissing && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                          Fault Simulation
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions for this invoice */}
                  <div className="grid grid-cols-3 gap-1.5 pt-1.5 border-t border-slate-800/80">
                    {/* 1. Download to local disk */}
                    <button
                      onClick={() => handleDownload(inv.filename)}
                      disabled={isDownloading}
                      className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold flex items-center justify-center space-x-1 transition"
                      title="Download file directly to your computer"
                    >
                      <Download className={`w-3 h-3 ${isDownloading ? 'text-emerald-400 animate-bounce' : 'text-sky-400'}`} />
                      <span>{isDownloading ? 'Saved!' : 'Download'}</span>
                    </button>

                    {/* 2. Visual in-browser Preview */}
                    <button
                      onClick={() => handlePreviewDocument(inv.filename)}
                      className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold flex items-center justify-center space-x-1 transition"
                      title="Preview invoice text and commercial details"
                    >
                      <Eye className="w-3 h-3 text-slate-400" />
                      <span>Preview</span>
                    </button>

                    {/* 3. 1-Click Autonomous Loop */}
                    <button
                      onClick={() => onRunTask(`Find the invoice at ${inv.file_path}, extract its amount and due date, and save it in the invoice system.`)}
                      className="py-1.5 px-2 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-bold flex items-center justify-center space-x-1 transition"
                      title="Run AgentOS autonomous ReAct loop with verification"
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

        {/* Right Col (7 cols): Create New Invoice with Items & Full Details */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Plus className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Commercial Invoice Builder & Automation Studio
              </h3>
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handlePreviewCurrentForm}
                className="text-xs text-sky-400 hover:text-sky-300 flex items-center space-x-1 px-2.5 py-1 rounded bg-sky-500/10 border border-sky-500/20"
              >
                <Eye className="w-3 h-3" />
                <span>Preview Draft</span>
              </button>
              <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
                Total: ₹{formatInr(netTotal)} {currency}
              </span>
            </div>
          </div>

          {/* Quick Preset Buttons */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[10px] font-bold uppercase text-slate-400">Quick Templates:</span>
            <button
              type="button"
              onClick={() => loadPreset('ai')}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-1 transition"
            >
              <span>🚀 AI Platform & GPUs</span>
            </button>
            <button
              type="button"
              onClick={() => loadPreset('consulting')}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-1 transition"
            >
              <span>💼 ERP Architecture Consulting</span>
            </button>
            <button
              type="button"
              onClick={() => loadPreset('hardware')}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-1 transition"
            >
              <span>🖥️ Compute & Network Nodes</span>
            </button>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleUploadInvoice}
              accept=".pdf,.txt,.json"
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center space-x-1 transition sm:ml-auto"
            >
              <span>{isUploading ? 'Uploading...' : '📤 Upload Invoice File (.pdf / .txt)'}</span>
            </button>
          </div>

          {creationSuccess && (
            <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{creationSuccess}</span>
            </div>
          )}

          {creationError && (
            <div className="p-3 bg-rose-950/40 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <X className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{creationError}</span>
              </div>
              <button
                type="button"
                onClick={() => setCreationError(null)}
                className="text-xs text-rose-400 hover:text-white px-2 py-0.5 rounded bg-rose-500/10"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Section 1: Header / Parties Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {/* Vendor (Issuer) */}
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400 block flex items-center space-x-1">
                <Building2 className="w-3 h-3" />
                <span>Vendor / Remit-To Party (Supplier)</span>
              </span>
              <div>
                <label className="text-[9px] uppercase text-slate-400 block mb-0.5">Vendor Name</label>
                <select
                  value={vendorName}
                  onChange={(e) => setVendorName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white focus:outline-none"
                >
                  <option value="Acme Technologies India Pvt. Ltd.">Acme Technologies India Pvt. Ltd. (Bengaluru)</option>
                  <option value="Apex Logistics India Pvt. Ltd.">Apex Logistics India Pvt. Ltd. (Mumbai)</option>
                  <option value="CentrAlign Cloud Technologies India Pvt. Ltd.">CentrAlign Cloud Technologies India Pvt. Ltd. (Hyderabad)</option>
                  <option value="Nexus Hardware Systems India Pvt. Ltd.">Nexus Hardware Systems India Pvt. Ltd. (Chennai)</option>
                  {vendors.map((v) => (
                    <option key={v.id} value={v.name}>{v.name} ({v.vendor_code})</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[9px] uppercase text-slate-400 block mb-0.5">Tax / VAT ID</label>
                  <input
                    type="text"
                    value={vendorTaxId}
                    onChange={(e) => setVendorTaxId(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-[9px] uppercase text-slate-400 block mb-0.5">Vendor Address</label>
                  <input
                    type="text"
                    value={vendorAddress}
                    onChange={(e) => setVendorAddress(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                  />
                </div>
              </div>
            </div>

            {/* Client (Bill-To) */}
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 block flex items-center space-x-1">
                <Building2 className="w-3 h-3" />
                <span>Bill To / Client Party</span>
              </span>
              <div>
                <label className="text-[9px] uppercase text-slate-400 block mb-0.5">Client Company Name</label>
                <input
                  type="text"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[9px] uppercase text-slate-400 block mb-0.5">AP Billing Email</label>
                  <input
                    type="email"
                    value={clientEmail}
                    onChange={(e) => setClientEmail(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-[9px] uppercase text-slate-400 block mb-0.5">Headquarters</label>
                  <input
                    type="text"
                    defaultValue="500 Autonomous Way, Bldg 2"
                    readOnly
                    className="w-full bg-slate-900/60 border border-slate-800 rounded px-2 py-1 text-xs text-slate-400"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Invoice Metadata (Dates, Terms, Number) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 bg-slate-950/40 p-3 rounded-xl border border-slate-800">
            <div>
              <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Invoice Number
              </label>
              <input
                type="text"
                value={invoiceNumber}
                onChange={(e) => setInvoiceNumber(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white font-mono focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Issue Date
              </label>
              <input
                type="date"
                value={issueDate}
                onChange={(e) => setIssueDate(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none"
              />
            </div>

            <div>
              <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Due Date
              </label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none"
              />
            </div>

            <div>
              <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Payment Terms
              </label>
              <select
                value={paymentTerms}
                onChange={(e) => setPaymentTerms(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none"
              >
                <option value="NET_30">NET 30 Days</option>
                <option value="NET_15">NET 15 Days</option>
                <option value="NET_60">NET 60 Days</option>
                <option value="DUE_ON_RECEIPT">Due on Receipt</option>
              </select>
            </div>
          </div>

          {/* Section 3: Itemized Expenses & Write Option */}
          <div className="space-y-2 pt-1 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Tag className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Taxable Goods & Services (HSN / SAC)
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {/* Mode Selector */}
                <div className="bg-slate-950 p-0.5 rounded-lg border border-slate-800 flex items-center">
                  <button
                    type="button"
                    onClick={() => setItemsMode('grid')}
                    className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                      itemsMode === 'grid'
                        ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    📋 Grid Editor
                  </button>
                  <button
                    type="button"
                    onClick={() => setItemsMode('write')}
                    className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                      itemsMode === 'write'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    ✍️ Write Items (Freeform)
                  </button>
                </div>
                {itemsMode === 'grid' && (
                  <button
                    type="button"
                    onClick={addItem}
                    className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/20 text-xs font-semibold transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Item</span>
                  </button>
                )}
              </div>
            </div>

            {/* Write Mode Option */}
            {itemsMode === 'write' ? (
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-emerald-400 flex items-center space-x-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Freeform Written Items Input (Indian Standard Multi-line)</span>
                  </span>
                  <button
                    type="button"
                    onClick={parseWrittenItemsToGrid}
                    className="px-2.5 py-1 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center space-x-1 transition shadow-sm"
                  >
                    <Zap className="w-3 h-3 fill-current" />
                    <span>⚡ Parse & Sync to Grid</span>
                  </button>
                </div>
                <textarea
                  rows={4}
                  value={rawItemsText}
                  onChange={(e) => setRawItemsText(e.target.value)}
                  placeholder="Enter items in any written format:
Enterprise AI Autonomous Task Agent License, SAC: 998313, Qty: 1, Rate: 50000
Dedicated Cloud GPU Compute Nodes, SAC: 998314, Qty: 2, Rate: 25000
AI Technical Advisory x 10 @ ₹4500
Server Node - 120000"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white font-mono focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <p className="text-[10px] text-slate-400 leading-tight">
                  Format tips: Supports <code className="text-emerald-300">Name, SAC: 998313, Qty: 2, Rate: 25000</code> or <code className="text-emerald-300">Service x 2 @ ₹15000</code> or simple <code className="text-emerald-300">Item - 50000</code>. Items can be parsed into the grid or saved directly.
                </p>
              </div>
            ) : (
              /* Grid Table Mode */
              <>
                {/* Explicit Column Headers with HSN/SAC & Rupees */}
                <div className="grid grid-cols-12 gap-2 px-3 py-1 bg-slate-950 rounded-lg text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  <div className="col-span-5">Item / Service Description</div>
                  <div className="col-span-2 text-center">HSN / SAC</div>
                  <div className="col-span-1 text-center">Qty</div>
                  <div className="col-span-2 text-right">Unit Rate (₹)</div>
                  <div className="col-span-1 text-right">Total (₹)</div>
                  <div className="col-span-1 text-center">Action</div>
                </div>

                {/* Item Rows */}
                <div className="space-y-2">
                  {items.map((it) => {
                    const lineTotal = (Number(it.quantity) || 0) * (Number(it.unit_price) || 0);

                    return (
                      <div
                        key={it.id}
                        className="grid grid-cols-12 gap-2 items-center bg-slate-950 p-2 rounded-lg border border-slate-800 hover:border-slate-700 transition"
                      >
                        <div className="col-span-5">
                          <input
                            type="text"
                            placeholder="e.g. Enterprise AI Agent License"
                            value={it.description}
                            onChange={(e) => updateItem(it.id, 'description', e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white focus:outline-none focus:ring-1 focus:ring-sky-500"
                          />
                        </div>

                        <div className="col-span-2">
                          <input
                            type="text"
                            placeholder="998313"
                            value={it.hsn_sac || '998313'}
                            onChange={(e) => updateItem(it.id, 'hsn_sac', e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded px-1.5 py-1 text-xs text-white text-center font-mono focus:outline-none focus:ring-1 focus:ring-sky-500"
                          />
                        </div>

                        <div className="col-span-1">
                          <input
                            type="number"
                            min="1"
                            placeholder="Qty"
                            value={it.quantity}
                            onChange={(e) => updateItem(it.id, 'quantity', parseInt(e.target.value) || 1)}
                            className="w-full bg-slate-900 border border-slate-700 rounded px-1 py-1 text-xs text-white text-center focus:outline-none focus:ring-1 focus:ring-sky-500"
                          />
                        </div>

                        <div className="col-span-2">
                          <input
                            type="number"
                            step="100"
                            min="0"
                            placeholder="0.00"
                            value={it.unit_price}
                            onChange={(e) => updateItem(it.id, 'unit_price', parseFloat(e.target.value) || 0)}
                            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono text-right focus:outline-none focus:ring-1 focus:ring-sky-500"
                          />
                        </div>

                        <div className="col-span-1 text-right font-mono text-xs text-emerald-400 font-semibold truncate">
                          ₹{formatInr(lineTotal)}
                        </div>

                        <div className="col-span-1 text-center">
                          <button
                            type="button"
                            onClick={() => removeItem(it.id)}
                            className="text-slate-500 hover:text-rose-400 transition p-1"
                            title="Remove item"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          {/* Section 4: Indian GST Taxes, Discounts & Remittance Advice */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-800">
            {/* Notes & Bank Remittance Info */}
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Bank Remittance & Payment Instructions (NEFT / RTGS / IMPS)
              </label>
              <textarea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Bank Name, Current Account No, IFSC Code, Mode..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-sky-500 resize-none font-mono"
              />
            </div>

            {/* Financial Summary with CGST / SGST */}
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1.5 text-xs font-mono">
              <div className="flex justify-between text-slate-300">
                <span>Taxable Subtotal:</span>
                <span>₹{formatInr(subtotal)} {currency}</span>
              </div>
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span>CGST ({(taxRate / 2).toFixed(1)}%):</span>
                <span>+₹{formatInr(taxAmount / 2)}</span>
              </div>
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span>SGST ({(taxRate / 2).toFixed(1)}%):</span>
                <span>+₹{formatInr(taxAmount / 2)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400 pt-1 border-t border-slate-800">
                <span className="flex items-center space-x-1">
                  <span>GST Slab:</span>
                  <select
                    value={taxRate}
                    onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
                    className="bg-slate-900 border border-slate-700 text-[10px] rounded px-1 py-0.5 text-white"
                  >
                    <option value={0}>0% (Exempt)</option>
                    <option value={5}>5% (Basic)</option>
                    <option value={12}>12% (Standard I)</option>
                    <option value={18}>18% (Standard II - Services)</option>
                    <option value={28}>28% (Luxury / Tech)</option>
                  </select>
                </span>
                <span>Total GST: +₹{formatInr(taxAmount)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Discount (₹):</span>
                <input
                  type="number"
                  min="0"
                  step="500"
                  value={discount}
                  onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                  className="w-24 bg-slate-900 border border-slate-700 text-[10px] rounded px-1 py-0.5 text-white text-right font-mono"
                />
              </div>
              <div className="flex justify-between pt-1.5 border-t border-slate-800 text-sm font-bold text-emerald-400">
                <span>TOTAL PAYABLE (INR):</span>
                <span>₹{formatInr(netTotal)} {currency}</span>
              </div>
            </div>
          </div>

          {/* Section 5: Action Buttons */}
          <div className="pt-3 border-t border-slate-800 flex flex-col sm:flex-row items-center gap-3">
            {/* Primary Action: Create, Download, and Automate via AgentOS */}
            <button
              onClick={() => handleCreateInvoice(true)}
              disabled={isSubmitting}
              className="w-full sm:flex-1 py-2.5 px-4 bg-gradient-to-r from-sky-500 via-indigo-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold flex items-center justify-center space-x-2 shadow-lg shadow-sky-500/20 transition disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isSubmitting ? 'Creating & Launching Agent...' : 'Create & Automate with AgentOS'}</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </button>

            {/* Secondary Action: Save to Repository & Trigger Direct File Download */}
            <button
              onClick={() => handleCreateInvoice(false)}
              disabled={isSubmitting}
              className="w-full sm:w-auto py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
              title="Save invoice file in sandbox and download directly to computer"
            >
              <Download className="w-3.5 h-3.5 text-sky-400" />
              <span>Save & Download Document</span>
            </button>
          </div>
        </div>

      </div>

      {/* Invoice Document Preview Modal */}
      {previewData && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
            {/* Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-white font-mono truncate">
                  {previewData.filename}
                </h3>
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">
                  {previewData.type}
                </span>
              </div>
              <button
                onClick={() => setPreviewData(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content Display */}
            <div className="p-5 flex-1 overflow-y-auto font-mono text-xs text-slate-200 bg-slate-950/90 whitespace-pre leading-relaxed select-text">
              {previewData.content}
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-slate-900/50">
              <span className="text-xs text-slate-400">
                {previewData.size_bytes ? `${(previewData.size_bytes / 1024).toFixed(1)} KB` : ''} • Verified Commercial Document
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => window.print()}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center space-x-1.5 transition"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print Document</span>
                </button>
                <button
                  onClick={() => handleDownload(previewData.filename)}
                  className="px-3.5 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold flex items-center space-x-1.5 transition shadow-sm shadow-sky-500/30"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download File</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
