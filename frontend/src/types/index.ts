export interface TaskStep {
  id?: number;
  step_number: number;
  thought: string;
  tool_name?: string;
  tool_input?: Record<string, any>;
  tool_output?: Record<string, any>;
  status: 'SUCCESS' | 'FAILED' | 'RETRYING' | 'RECOVERED' | 'WAITING_APPROVAL';
  error_message?: string;
  latency_ms: number;
  created_at?: string;
}

export interface ApprovalRequest {
  approval_id: string;
  tool_name: string;
  action_description: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_reason: string;
  pending_payload: Record<string, any>;
}

export interface VerificationDetails {
  verified: boolean;
  payable_id?: number;
  verification_token?: string;
  audit_notes?: string;
  field_comparisons?: Record<string, any>;
}

export interface Task {
  id: string;
  goal: string;
  status: 'PLANNING' | 'RUNNING' | 'WAITING_FOR_APPROVAL' | 'WAITING_FOR_INPUT' | 'RETRYING' | 'VERIFYING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  current_plan: Array<{
    step_id: number;
    title: string;
    description: string;
    expected_tool?: string;
    status: string;
  }>;
  working_memory: Record<string, any>;
  extracted_data: Record<string, any>;
  final_summary?: string;
  error_message?: string;
  steps_count: number;
  created_at: string;
  updated_at: string;
  steps?: TaskStep[];
  pending_approval?: ApprovalRequest;
  verification?: VerificationDetails;
}

export interface Payable {
  id: number;
  vendor_id?: number;
  vendor_name: string;
  invoice_number: string;
  amount: number;
  currency: string;
  invoice_date?: string;
  due_date: string;
  payment_terms: string;
  po_number?: string;
  idempotency_key: string;
  status: string;
  created_by: string;
  verification_hash?: string;
  created_at: string;
  verified_at?: string;
}

export interface Vendor {
  id: number;
  vendor_code: string;
  name: string;
  aliases?: string;
  payment_terms: string;
  category: string;
  status: string;
  created_at: string;
}

export interface InvoiceDoc {
  id: number;
  filename: string;
  file_path: string;
  file_type: string;
  file_size_bytes: number;
  vendor_name_hint?: string;
  is_latest_for_vendor: boolean;
}

export interface SandboxMetrics {
  total_tasks: number;
  tasks_completed: number;
  tasks_failed: number;
  tasks_awaiting_approval: number;
  total_payables: number;
  verified_payables: number;
  verification_success_rate: number;
}
