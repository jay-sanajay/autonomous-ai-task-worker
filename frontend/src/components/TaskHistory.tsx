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
      <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-6 text-center text-[#718278]">
        <History className="w-7 h-7 mx-auto mb-2 text-[#263A2E]" />
        <p className="text-xs">No task runs recorded yet. Execute an objective to see its audit history here.</p>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#55E6A5]/10 text-[#55E6A5] border border-[#55E6A5]/30">
            COMPLETED
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FF7777]/10 text-[#FF7777] border border-[#FF7777]/30">
            FAILED
          </span>
        );
      case 'WAITING_FOR_APPROVAL':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FFC66D]/15 text-[#FFC66D] border border-[#FFC66D]/40 animate-pulse">
            NEEDS APPROVAL
          </span>
        );
      case 'RUNNING':
      case 'PLANNING':
      case 'VERIFYING':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#7AB8FF]/10 text-[#7AB8FF] border border-[#7AB8FF]/30 animate-pulse">
            {status}
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#142019] text-[#718278] border border-[#263A2E]">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-[#101914] border border-[#263A2E] rounded-xl p-5 shadow-card-subtle space-y-4">
      <div className="flex items-center justify-between border-b border-[#263A2E] pb-3">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-[#55E6A5]" />
          <h3 className="text-xs font-bold text-[#F0F7F2] uppercase tracking-wider">Execution Audit Trail</h3>
        </div>
        <span className="text-xs font-mono text-[#718278]">{tasks.length} Run{tasks.length === 1 ? '' : 's'}</span>
      </div>

      <div className="space-y-2.5 max-h-[480px] overflow-y-auto pr-1">
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
                  ? 'bg-[#1C2D24] border-[#55E6A5] shadow-xs'
                  : 'bg-[#142019] border-[#263A2E] hover:bg-[#1C2D24] hover:border-[#55E6A5]/40'
              }`}
            >
              <div className="space-y-1.5 flex-1 pr-3 min-w-0">
                <div className="flex items-center space-x-2">
                  {getStatusBadge(task.status)}
                  {isVerified && (
                    <span className="flex items-center text-[10px] font-semibold text-[#55E6A5] bg-[#55E6A5]/10 px-1.5 py-0.5 rounded border border-[#55E6A5]/30">
                      <ShieldCheck className="w-3 h-3 mr-1 inline" /> Verified
                    </span>
                  )}
                  <span className="text-[11px] font-mono text-[#718278]">{formattedDate}</span>
                </div>
                <p className="text-xs text-[#F0F7F2] font-medium truncate group-hover:text-white transition">
                  {task.goal}
                </p>
                <div className="flex items-center space-x-2.5 text-[10px] text-[#A0B2A6] font-mono">
                  <span>ID: {task.id.slice(0, 12)}...</span>
                  <span className="text-[#263A2E]">•</span>
                  <span>{task.steps_count} steps</span>
                  {task.extracted_data?.invoice_number && (
                    <>
                      <span className="text-[#263A2E]">•</span>
                      <span className="text-[#55E6A5] font-semibold">{task.extracted_data.invoice_number}</span>
                    </>
                  )}
                </div>
              </div>

              <div className="text-[#718278] group-hover:text-[#55E6A5] transition pl-2">
                <ArrowRight className="w-4 h-4" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
