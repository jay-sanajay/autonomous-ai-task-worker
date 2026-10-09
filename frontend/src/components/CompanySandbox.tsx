import React, { useState } from 'react';
import { Vendor, InvoiceDoc, Payable } from '../types';
import { Building2, FileText, Receipt, CheckCircle, Clock } from 'lucide-react';

interface CompanySandboxProps {
  vendors: Vendor[];
  invoices: InvoiceDoc[];
  payables: Payable[];
  onRefresh: () => void;
}

export const CompanySandbox: React.FC<CompanySandboxProps> = ({
  vendors,
  invoices,
  payables,
  onRefresh
}) => {
  const [subTab, setSubTab] = useState<'payables' | 'vendors' | 'documents'>('payables');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/40 space-y-5">
      
      {/* Header & Sub-Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white">Simulated Enterprise Application & Database</h2>
          <p className="text-xs text-slate-400">Real SQLite tables inspected and written to by AgentOS</p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setSubTab('payables')}
              className={`px-3 py-1 rounded-lg font-semibold transition ${
                subTab === 'payables' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Payables ({payables.length})
            </button>
            <button
              onClick={() => setSubTab('vendors')}
              className={`px-3 py-1 rounded-lg font-semibold transition ${
                subTab === 'vendors' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Vendors ({vendors.length})
            </button>
            <button
              onClick={() => setSubTab('documents')}
              className={`px-3 py-1 rounded-lg font-semibold transition ${
                subTab === 'documents' ? 'bg-sky-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Repository ({invoices.length})
            </button>
          </div>

          <button
            onClick={onRefresh}
            className="px-2.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold"
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
