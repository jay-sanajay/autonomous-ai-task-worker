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
  task_item_id?: number;
  contract_id?: number;
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

export interface TaskItem {
  id: number;
  title: string;
  due_date: string;
  meeting_link?: string;
  description?: string;
  priority: string;
  status: string;
  source_reference?: string;
  created_at?: string;
}

export interface SupportTicket {
  id: number;
  ticket_code: string;
  customer_name: string;
  subject: string;
  description: string;
  priority: string;
  status: string;
  created_at?: string;
}

export interface InventoryItem {
  id: number;
  sku: string;
  product_name: string;
  category: string;
  current_stock: number;
  reorder_threshold: number;
  unit_price: number;
  status: string;
  is_low_stock: boolean;
}

export interface PurchaseRequest {
  id: number;
  request_code: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  estimated_total: number;
  status: string;
  created_at?: string;
}

export interface Contract {
  id: number;
  contract_code: string;
  title: string;
  parties: string;
  effective_date?: string;
  expiry_date: string;
  contract_value: number;
  governing_law?: string;
  missing_clauses: Array<{ clause: string; severity: string; description: string }>;
  missing_clauses_count: number;
  risk_score: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: string;
  source_file?: string;
  created_at?: string;
}

export interface SandboxFile {
  category: string;
  filename: string;
  extension: string;
  file_path: string;
  size_bytes: number;
  modified_time: number;
  suggested_prompt: string;
}

export interface EpisodicMemory {
  id: number;
  task_id: string;
  goal: string;
  outcome: string;
  failed_strategies: string[];
  recovery_methods: string[];
  verification_token?: string;
  created_at: string;
}

export interface SemanticMemory {
  id: number;
  category: string;
  fact_key: string;
  fact_content: string;
  provenance: string;
  verified: boolean;
  created_at: string;
}

export interface TelemetryDashboard {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  completion_rate: number;
  failure_rate: number;
  recovered_steps_count: number;
  verified_outcomes_count: number;
  verification_success_rate: number;
  average_step_latency_ms: number;
}

export interface BenchmarkScenarioResult {
  scenario_id: string;
  name: string;
  status: string;
  passed_benchmark: boolean;
  verified: boolean;
  duration_seconds: number;
  steps_count: number;
}

export interface BenchmarkReport {
  total_scenarios_evaluated: number;
  successful_scenarios: number;
  benchmark_pass_rate: number;
  verified_completion_rate: number;
  unauthorized_action_rate: number;
  duplicate_write_rate: number;
  average_execution_seconds: number;
  average_steps_per_task: number;
  detailed_scenario_results: BenchmarkScenarioResult[];
}

export interface ReplayStep {
  step_number: number;
  tool_name: string;
  was_simulated: boolean;
  side_effects_prevented: boolean;
  recorded_output: Record<string, any>;
  thought: string;
}

export interface ReplayReport {
  status: string;
  task_id: string;
  original_goal: string;
  original_status: string;
  replayed_steps_count: number;
  prevented_writes_count: number;
  safety_assertion: string;
  steps: ReplayStep[];
}

