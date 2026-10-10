import {
  Task, Payable, Vendor, InvoiceDoc, SandboxMetrics,
  TaskItem, SupportTicket, InventoryItem, PurchaseRequest
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

