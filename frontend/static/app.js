// CentraWorker Dashboard Frontend Client

let activeApprovalId = null;
let currentTaskId = null;

const SCENARIOS = {
  1: {
    title: "Standard Problem Statement",
    goal: "Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system, and tell me once it is done.",
    fault: false,
    autoApprove: true
  },
  2: {
    title: "503 Fault & Self-Correction",
    goal: "Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system, and tell me once it is done.",
    fault: true,
    autoApprove: true
  },
  3: {
    title: "High-Value HITL Approval",
    goal: "Process invoice for Nexus Technologies high value hardware from simulated_company/data_store/files/invoices/INV-2024-099_NexusTech_HighValue.txt and enter into ERP.",
    fault: false,
    autoApprove: false
  },
  4: {
    title: "Browser Web Portal Entry",
    goal: "Use browser automation on internal web portal to enter the latest Company X invoice.",
    fault: false,
    autoApprove: true
  }
};

function loadScenario(num) {
  document.querySelectorAll('.chip').forEach((c, idx) => {
    c.classList.toggle('active', idx + 1 === num);
  });
  const sc = SCENARIOS[num];
  if (sc) {
    document.getElementById('task-goal-input').value = sc.goal;
    document.getElementById('chk-simulate-fault').checked = sc.fault;
    document.getElementById('chk-auto-approve').checked = sc.autoApprove;
  }
}

async function startTask() {
  const goal = document.getElementById('task-goal-input').value.trim();
  if (!goal) return;

  const btn = document.getElementById('btn-run-task');
  const btnText = document.getElementById('btn-run-text');
  btn.disabled = true;
  btnText.innerText = 'Worker Running...';

  updateAgentBadge('RUNNING', 'badge-pulse');
  clearStreams();

  const payload = {
    goal: goal,
    simulate_fault: document.getElementById('chk-simulate-fault').checked,
    auto_approve_high_risk: document.getElementById('chk-auto-approve').checked
  };

  try {
    const res = await fetch('/api/agent/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    handleTaskResult(result);
  } catch (err) {
    console.error('Task execution error:', err);
    updateAgentBadge('ERROR', 'badge-danger');
  } finally {
    btn.disabled = false;
    btnText.innerText = 'Launch Autonomous Worker';
    loadERPInvoices();
  }
}

function handleTaskResult(result) {
  currentTaskId = result.task_id;
  document.getElementById('step-counter').innerText = `${result.steps_executed} steps executed`;

  if (result.status === 'WAITING_FOR_APPROVAL') {
    updateAgentBadge('WAITING FOR APPROVAL', 'badge-warning');
    showApprovalModal(result.pending_approval);
  } else if (result.status === 'COMPLETED') {
    updateAgentBadge('COMPLETED', 'badge-pulse');
  } else {
    updateAgentBadge(result.status, 'badge-danger');
  }

  // Render plan steps
  renderPlan(result.step_history);

  // Render reasoning & action stream
  renderStream(result.step_history);

  // Render working memory
  renderMemory(result.extracted_data);

  // Render verification receipt
  renderVerification(result.evidence);
}

function renderPlan(steps) {
  const container = document.getElementById('plan-steps-list');
  container.innerHTML = '';
  if (!steps || steps.length === 0) {
    container.innerHTML = '<div class="empty-state">No steps recorded.</div>';
    return;
  }

  steps.forEach((s) => {
    const div = document.createElement('div');
    div.className = `plan-step-item status-${s.status}`;
    div.innerHTML = `
      <span class="step-num-badge">STEP ${s.step_number}</span>
      <div style="flex:1;">
        <strong>${s.tool_name || 'Reasoning Phase'}</strong>
        <p style="font-size:12px; color:#9ca3af; margin-top:2px;">${s.thought}</p>
      </div>
      <span class="badge" style="font-size:10px;">${s.status}</span>
    `;
    container.appendChild(div);
  });
}

function renderStream(steps) {
  const container = document.getElementById('thought-stream');
  container.innerHTML = '';
  if (!steps || steps.length === 0) return;

  steps.forEach((s) => {
    const div = document.createElement('div');
    div.className = 'stream-entry';
    div.innerHTML = `
      <div class="entry-header">
        <span>Step ${s.step_number} &bull; ${s.timestamp ? s.timestamp.substring(11, 19) : ''}</span>
        <span style="color:#60a5fa;">${s.latency_ms}ms</span>
      </div>
      <div class="entry-thought">"${s.thought}"</div>
      ${s.tool_name ? `
        <div class="entry-action">
          ⚡ <strong>${s.tool_name}</strong>(${JSON.stringify(s.tool_input || {})})
        </div>
      ` : ''}
      ${s.tool_output ? `
        <div class="entry-observation">
          ✔ Output: ${JSON.stringify(s.tool_output).substring(0, 180)}...
        </div>
      ` : ''}
      ${s.error_message ? `
        <div style="background:rgba(239,68,68,0.15); border:1px solid #ef4444; color:#ef4444; padding:6px 10px; border-radius:6px; margin-top:6px; font-size:11px;">
          ⚠ ${s.error_message}
        </div>
      ` : ''}
    `;
    container.appendChild(div);
  });
  container.scrollTop = container.scrollHeight;
}

function renderMemory(extracted) {
  const container = document.getElementById('memory-entities-view');
  container.innerHTML = '';
  if (!extracted || Object.keys(extracted).length === 0) {
    container.innerHTML = '<span class="muted-text">No entities extracted yet.</span>';
    return;
  }

  const inv = extracted.extracted_invoice || {};
  const items = [
    { key: "Invoice #", val: inv.invoice_number || "None" },
    { key: "Vendor", val: inv.vendor_name || "None" },
    { key: "Amount", val: inv.amount ? `$${inv.amount.toLocaleString(undefined, {minimumFractionDigits: 2})}` : "None" },
    { key: "Due Date", val: inv.due_date || "None" },
    { key: "PO Ref", val: inv.po_number || "None" },
    { key: "Source File", val: extracted.latest_file || "None" }
  ];

  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'memory-item';
    div.innerHTML = `
      <span class="memory-key">${item.key}</span>
      <span class="memory-val">${item.val}</span>
    `;
    container.appendChild(div);
  });
}

function renderVerification(evidence) {
  const badge = document.getElementById('verification-badge');
  const body = document.getElementById('verification-body');

  if (!evidence) {
    badge.innerText = 'PENDING';
    badge.className = 'badge';
    body.innerHTML = '<p class="muted-text">Awaiting task completion.</p>';
    return;
  }

  if (evidence.verified) {
    badge.innerText = 'VERIFIED';
    badge.className = 'badge badge-pulse';
    body.innerHTML = `
      <div class="verification-receipt">
        <div class="receipt-row">
          <span class="receipt-label">Ground-Truth Status</span>
          <span class="receipt-val" style="color:#10b981;">VERIFIED & MATCHED</span>
        </div>
        <div class="receipt-row">
          <span class="receipt-label">ERP Record ID</span>
          <span class="receipt-val">${evidence.record_id || 'N/A'}</span>
        </div>
        <div class="receipt-row">
          <span class="receipt-label">Invoice Number</span>
          <span class="receipt-val">${evidence.invoice_number}</span>
        </div>
        <div class="receipt-row">
          <span class="receipt-label">Amount Confirmed</span>
          <span class="receipt-val" style="color:#38bdf8;">$${evidence.amount ? evidence.amount.toLocaleString(undefined, {minimumFractionDigits: 2}) : '0.00'} USD</span>
        </div>
        <div class="receipt-row">
          <span class="receipt-label">Due Date Confirmed</span>
          <span class="receipt-val">${evidence.due_date}</span>
        </div>
        <div class="receipt-row">
          <span class="receipt-label">Verification Hash</span>
          <span class="receipt-val" style="font-size:10px;">${evidence.verification_hash || 'SHA-256'}</span>
        </div>
        <div class="receipt-row">
          <span class="receipt-label">Timestamp</span>
          <span class="receipt-val" style="font-size:10px;">${evidence.verified_at}</span>
        </div>
      </div>
    `;
  } else {
    badge.innerText = 'UNVERIFIED';
    badge.className = 'badge badge-danger';
    body.innerHTML = `<p style="color:#ef4444; font-size:13px;">${evidence.audit_notes || 'Verification failed.'}</p>`;
  }
}

function showApprovalModal(appReq) {
  if (!appReq) return;
  activeApprovalId = appReq.approval_id;
  document.getElementById('modal-risk-level').innerText = appReq.risk_level;
  document.getElementById('modal-approval-id').innerText = appReq.approval_id;
  document.getElementById('modal-risk-reason').innerText = appReq.risk_reason;
  document.getElementById('modal-payload-code').innerText = JSON.stringify(appReq.pending_payload, null, 2);
  document.getElementById('approval-modal').classList.add('open');
}

async function resolveApproval(approved) {
  document.getElementById('approval-modal').classList.remove('open');
  const feedback = document.getElementById('modal-feedback-input').value;

  try {
    const res = await fetch('/api/agent/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        approval_id: activeApprovalId,
        approved: approved,
        approver: "Finance Director",
        feedback: feedback || (approved ? "Approved by Executive Sign-off" : "Rejected by Executive")
      })
    });
    const result = await res.json();
    handleTaskResult(result);
  } catch (err) {
    console.error("Failed to submit approval", err);
  }
}

async function loadERPInvoices() {
  try {
    const res = await fetch('/api/erp/invoices');
    const data = await res.json();
    const tbody = document.getElementById('erp-invoices-body');
    tbody.innerHTML = '';
    data.forEach(inv => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><code>${inv.id}</code></td>
        <td><strong>${inv.invoice_number}</strong></td>
        <td>${inv.vendor_name}</td>
        <td style="color:#38bdf8; font-weight:600;">$${inv.amount.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
        <td>${inv.due_date}</td>
        <td><span style="color:#10b981; font-weight:600;">${inv.status}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load ERP invoices", err);
  }
}

async function resetDatabase() {
  await fetch('/api/erp/reset', { method: 'POST' });
  loadERPInvoices();
  clearStreams();
  updateAgentBadge('IDLE', 'badge-pulse');
}

function clearStreams() {
  document.getElementById('plan-steps-list').innerHTML = '<div class="empty-state">Synthesizing execution plan...</div>';
  document.getElementById('thought-stream').innerHTML = '<div class="empty-state">Beginning autonomous ReAct cycle...</div>';
}

function updateAgentBadge(text, cls) {
  const b = document.getElementById('agent-state-badge');
  b.className = `badge ${cls}`;
  b.innerText = `Status: ${text}`;
}

// Initial setup
window.addEventListener('DOMContentLoaded', () => {
  loadScenario(1);
  loadERPInvoices();
});
