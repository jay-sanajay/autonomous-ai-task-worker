import {
  Task, Payable, Vendor, InvoiceDoc, SandboxMetrics,
  TaskItem, SupportTicket, InventoryItem, PurchaseRequest,
  Contract, SandboxFile
} from '../types';

const API_BASE = '/api';

export async function fetchTasks(): Promise<Task[]> {
  const res = await fetch(`${API_BASE}/tasks`);
  if (!res.ok) throw new Error('Failed to fetch tasks');
  return res.json();
}

export async function fetchTaskDetails(taskId: string): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`);
  if (!res.ok) throw new Error(`Failed to fetch task ${taskId}`);
  return res.json();
}

export async function createTask(payload: {
  goal: string;
  auto_approve_high_risk?: boolean;
  simulate_fault?: boolean;
}): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to trigger task');
  return res.json();
}

export async function approveTask(taskId: string, approver = 'Finance Director', feedback = 'Approved'): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approval_id: 'auto', approved: true, approver, feedback })
  });
  if (!res.ok) throw new Error('Approval failed');
  return res.json();
}

export async function rejectTask(taskId: string, approver = 'Finance Director', feedback = 'Rejected'): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approval_id: 'auto', approved: false, approver, feedback })
  });
  if (!res.ok) throw new Error('Rejection failed');
  return res.json();
}

export async function fetchVendors(): Promise<Vendor[]> {
  const res = await fetch(`${API_BASE}/vendors`);
  if (!res.ok) throw new Error('Failed to fetch vendors');
  return res.json();
}

export async function fetchInvoices(): Promise<InvoiceDoc[]> {
  const res = await fetch(`${API_BASE}/invoices`);
  if (!res.ok) throw new Error('Failed to fetch invoices');
  return res.json();
}

export async function fetchPayables(): Promise<Payable[]> {
  const res = await fetch(`${API_BASE}/payables`);
  if (!res.ok) throw new Error('Failed to fetch payables');
  return res.json();
}

export async function fetchMetrics(): Promise<SandboxMetrics> {
  const res = await fetch(`${API_BASE}/sandbox/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function resetSandbox(): Promise<void> {
  const res = await fetch(`${API_BASE}/sandbox/reset`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to reset sandbox');
}

export async function fetchTaskItems(): Promise<TaskItem[]> {
  const res = await fetch(`${API_BASE}/task-items`);
  if (!res.ok) throw new Error('Failed to fetch task items');
  return res.json();
}

export async function fetchSupportTickets(): Promise<SupportTicket[]> {
  const res = await fetch(`${API_BASE}/support-tickets`);
  if (!res.ok) throw new Error('Failed to fetch support tickets');
  return res.json();
}

export async function fetchInventory(): Promise<InventoryItem[]> {
  const res = await fetch(`${API_BASE}/inventory`);
  if (!res.ok) throw new Error('Failed to fetch inventory');
  return res.json();
}

export async function fetchPurchaseRequests(): Promise<PurchaseRequest[]> {
  const res = await fetch(`${API_BASE}/purchase-requests`);
  if (!res.ok) throw new Error('Failed to fetch purchase requests');
  return res.json();
}

export async function fetchCSVFiles(): Promise<Array<{ filename: string; file_path: string; size_bytes: number }>> {
  const res = await fetch(`${API_BASE}/csv-files`);
  if (!res.ok) throw new Error('Failed to fetch CSV files');
  return res.json();
}

export async function uploadCSVFile(file: File): Promise<{ status: string; filename: string; file_path: string; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/upload/csv`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to upload CSV file');
  }
  return res.json();
}

export async function fetchReports(): Promise<Array<{ filename: string; file_path: string; size_bytes: number }>> {
  const res = await fetch(`${API_BASE}/reports`);
  if (!res.ok) throw new Error('Failed to fetch reports');
  return res.json();
}

export async function fetchContracts(): Promise<Contract[]> {
  const res = await fetch(`${API_BASE}/contracts`);
  if (!res.ok) throw new Error('Failed to fetch contracts');
  return res.json();
}

export async function uploadAnyFile(file: File): Promise<{
  status: string;
  filename: string;
  extension: string;
  file_path: string;
  size_bytes: number;
  suggested_prompt: string;
  message: string;
}> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/upload/file`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to upload document');
  }
  return res.json();
}

export async function fetchAllSandboxFiles(): Promise<SandboxFile[]> {
  const res = await fetch(`${API_BASE}/uploaded-files`);
  if (!res.ok) throw new Error('Failed to fetch all sandbox documents');
  return res.json();
}

export async function fetchEpisodicMemories(): Promise<import('../types').EpisodicMemory[]> {
  const res = await fetch(`${API_BASE}/memory/episodic`);
  if (!res.ok) throw new Error('Failed to fetch episodic memories');
  return res.json();
}

export async function fetchSemanticMemories(): Promise<import('../types').SemanticMemory[]> {
  const res = await fetch(`${API_BASE}/memory/semantic`);
  if (!res.ok) throw new Error('Failed to fetch semantic memories');
  return res.json();
}

export async function deleteEpisodicMemory(memoryId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/memory/episodic/${memoryId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete episodic memory');
}

export async function deleteSemanticMemory(memoryId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/memory/semantic/${memoryId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete semantic memory');
}

export async function replayTaskExecution(taskId: string): Promise<import('../types').ReplayReport> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/replay`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to replay task');
  }
  return res.json();
}

export async function fetchTelemetryDashboard(): Promise<import('../types').TelemetryDashboard> {
  const res = await fetch(`${API_BASE}/telemetry/dashboard`);
  if (!res.ok) throw new Error('Failed to fetch telemetry metrics');
  return res.json();
}

export async function runBenchmarks(): Promise<import('../types').BenchmarkReport> {
  const res = await fetch(`${API_BASE}/benchmarks/run`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run benchmarks');
  return res.json();
}

export function getInvoiceDownloadUrl(filename: string): string {
  return `${API_BASE}/invoices/download/${encodeURIComponent(filename)}`;
}

export async function createCustomInvoice(data: {
  vendor_name: string;
  invoice_number: string;
  due_date: string;
  currency?: string;
  payment_terms?: string;
  items: Array<{ description: string; quantity: number; unit_price: number }>;
  auto_run_agent?: boolean;
}): Promise<{
  status: string;
  filename: string;
  file_path: string;
  total_amount: number;
  items_count: number;
  task_id: string | null;
  download_url: string;
  message: string;
}> {
  const res = await fetch(`${API_BASE}/invoices/create-with-items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create invoice');
  }
  return res.json();
}

export async function fetchLLMStatus(): Promise<{
  active_provider: string;
  groq_configured: boolean;
  masked_api_key: string;
  default_model: string;
  supported_models: string[];
  zero_friction_mode: boolean;
}> {
  const res = await fetch(`${API_BASE}/settings/llm-status`);
  if (!res.ok) throw new Error('Failed to fetch LLM status');
  return res.json();
}

export async function setGroqAPIKey(groq_api_key: string, model = 'llama-3.3-70b-versatile'): Promise<any> {
  const res = await fetch(`${API_BASE}/settings/llm-provider`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ groq_api_key, model })
  });
  if (!res.ok) throw new Error('Failed to set Groq key');
  return res.json();
}


