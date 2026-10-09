import React from 'react';
import { Task } from '../types';
import { History, CheckCircle2, XCircle, Clock, ShieldCheck, ArrowRight } from 'lucide-react';

interface TaskHistoryProps {
  tasks: Task[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
}

export const TaskHistory: React.FC<TaskHistoryProps> = ({
  tasks,
  selectedTaskId,
  onSelectTask,
}) => {
  if (tasks.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center text-slate-500">
        <History className="w-7 h-7 mx-auto mb-2 text-slate-600" />
        <p className="text-xs">No task runs recorded yet. Execute an objective to see its audit history here.</p>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">COMPLETED</span>;
      case 'FAILED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">FAILED</span>;
      case 'WAITING_FOR_APPROVAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">NEEDS APPROVAL</span>;
      case 'RUNNING':
      case 'PLANNING':
      case 'VERIFYING':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20 animate-pulse">{status}</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">{status}</span>;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/40 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <History className="w-5 h-5 text-sky-400" />
          <h3 className="text-sm font-bold text-white">Execution Audit Trail</h3>
        </div>
        <span className="text-xs font-mono text-slate-400">{tasks.length} Run{tasks.length === 1 ? '' : 's'}</span>
      </div>

      <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
        {tasks.map((task) => {
          const isSelected = task.id === selectedTaskId;
          const isVerified = task.verification?.verified;
          const formattedDate = new Date(task.created_at).toLocaleTimeString();

          return (
            <button
              key={task.id}
              onClick={() => onSelectTask(task.id)}
              className={`w-full text-left p-3.5 rounded-xl border transition flex items-center justify-between group ${
                isSelected
                  ? 'bg-sky-500/10 border-sky-500/50 shadow-sm shadow-sky-500/10'
                  : 'bg-slate-950/60 border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700'
              }`}
            >
              <div className="space-y-1.5 flex-1 pr-3 min-w-0">
                <div className="flex items-center space-x-2">
                  {getStatusBadge(task.status)}
                  {isVerified && (
                    <span className="flex items-center text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                      <ShieldCheck className="w-3 h-3 mr-1 inline" /> Verified
                    </span>
                  )}
                  <span className="text-[11px] font-mono text-slate-500">{formattedDate}</span>
                </div>
                <p className="text-xs text-slate-200 font-medium truncate group-hover:text-white transition">
                  {task.goal}
                </p>
                <div className="flex items-center space-x-3 text-[10px] text-slate-400 font-mono">
                  <span>ID: {task.id.slice(0, 8)}...</span>
                  <span>•</span>
                  <span>{task.steps_count} steps</span>
                  {task.extracted_data?.invoice_number && (
                    <>
                      <span>•</span>
                      <span className="text-sky-400">{task.extracted_data.invoice_number}</span>
                    </>
                  )}
                </div>
              </div>

              <div className="text-slate-600 group-hover:text-sky-400 transition pl-2">
                <ArrowRight className="w-4 h-4" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
