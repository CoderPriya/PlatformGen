/* ============================================================
   Multi-Agent SDLC Platform — Dashboard Frontend
   ============================================================ */

const API = '';

const STAGES = [
  'requirements', 'business_analysis', 'architecture', 'task_breakdown',
  'code_generation', 'code_review', 'testing', 'security_scan',
  'ci_cd', 'deployment', 'monitoring', 'documentation', 'feedback'
];

const STAGE_LABELS = {
  requirements: 'Requirements',
  business_analysis: 'Business Analysis',
  architecture: 'Architecture',
  task_breakdown: 'Task Breakdown',
  code_generation: 'Code Generation',
  code_review: 'Code Review',
  testing: 'QA Testing',
  security_scan: 'Security Scan',
  ci_cd: 'CI/CD',
  deployment: 'Deployment',
  monitoring: 'Monitoring',
  documentation: 'Documentation',
  feedback: 'Feedback',
};

const AGENT_ICONS = {
  orchestrator: '\u{1F3AF}', requirements: '\u{1F4CB}', business_analyst: '\u{1F4CA}',
  architect: '\u{1F3D7}', code_generator: '\u{1F4BB}', code_reviewer: '\u{1F50D}',
  qa: '\u{1F9EA}', security: '\u{1F6E1}', devops: '\u{1F680}', sre: '\u{1F4E1}',
  documentation: '\u{1F4DA}',
};

// ---- Navigation ----
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => showTab(btn.dataset.tab));
});

function showTab(tab) {
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  const btn = document.querySelector(`.nav-btn[data-tab="${tab}"]`);
  if (btn) btn.classList.add('active');
  const tabEl = document.getElementById(`tab-${tab}`);
  if (tabEl) tabEl.classList.add('active');
  if (tab === 'dashboard') loadDashboard();
  if (tab === 'workflows') loadWorkflows();
  if (tab === 'approvals') loadApprovals();
  if (tab === 'agents') loadAgents();
  if (tab === 'events') loadEvents();
  if (tab === 'gateway') loadGateway();
}

// ---- API helpers ----
async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

// ---- Dashboard ----
async function loadDashboard() {
  try {
    const data = await api('/api/dashboard');
    document.getElementById('health-badge').textContent = 'Live';
    document.getElementById('health-badge').className = 'badge badge-live';

    const sg = document.getElementById('stats-grid');
    const active = data.workflows.filter(w => w.status === 'running' || w.status === 'awaiting_approval').length;
    const completed = data.workflows.filter(w => w.status === 'completed').length;
    const agentsActive = data.agent_statuses.filter(a => a.is_active).length;
    sg.innerHTML = `
      <div class="stat-card"><div class="stat-label">Total Workflows</div><div class="stat-value">${data.workflows.length}</div><div class="stat-sub">${active} active</div></div>
      <div class="stat-card"><div class="stat-label">Completed</div><div class="stat-value" style="color:var(--success)">${completed}</div><div class="stat-sub">workflows</div></div>
      <div class="stat-card"><div class="stat-label">Pending Approvals</div><div class="stat-value" style="color:var(--warning)">${data.pending_approvals.length}</div><div class="stat-sub">gates waiting</div></div>
      <div class="stat-card"><div class="stat-label">Agents Online</div><div class="stat-value" style="color:var(--primary)">${agentsActive}</div><div class="stat-sub">of ${data.agent_statuses.length} registered</div></div>
    `;

    renderDashWorkflows(data.workflows);
    renderDashApprovals(data.pending_approvals);
    renderDashEvents(data.recent_events);
  } catch (e) {
    document.getElementById('health-badge').textContent = 'Offline';
    document.getElementById('health-badge').className = 'badge badge-failed';
  }
}

function renderDashWorkflows(workflows) {
  const el = document.getElementById('dash-workflows');
  if (!workflows.length) { el.innerHTML = '<div class="empty"><div class="empty-icon">\u{1F4E6}</div>No workflows yet. Create one to get started.</div>'; return; }
  el.innerHTML = workflows.map(w => `
    <div class="list-item" onclick="viewWorkflow('${w.id}')">
      <div class="list-item-info">
        <div class="list-item-title">${esc(w.title)}</div>
        <div class="list-item-sub">${w.project_name} &middot; ${STAGE_LABELS[w.current_stage] || w.current_stage}</div>
      </div>
      <span class="badge badge-${w.status}">${w.status}</span>
    </div>
  `).join('');
}

function renderDashApprovals(gates) {
  const el = document.getElementById('dash-approvals');
  if (!gates.length) { el.innerHTML = '<div class="empty"><div class="empty-icon">\u{2705}</div>No pending approvals.</div>'; return; }
  el.innerHTML = gates.map(g => `
    <div class="list-item" onclick="showTab('approvals')">
      <div class="list-item-info">
        <div class="list-item-title">${esc(g.gate_name)}</div>
        <div class="list-item-sub">${g.stage} &middot; ${g.agent_type}</div>
      </div>
      <span class="badge badge-pending">Pending</span>
    </div>
  `).join('');
}

function renderDashEvents(events) {
  const el = document.getElementById('dash-events');
  if (!events.length) { el.innerHTML = '<div class="empty">No events recorded yet.</div>'; return; }
  el.innerHTML = events.slice(-20).reverse().map(e => `
    <div class="list-item" style="cursor:default">
      <div class="list-item-info">
        <div class="list-item-title" style="color:var(--primary);font-family:var(--mono);font-size:.82rem">${esc(e.topic)}</div>
        <div class="list-item-sub">${e.source_agent} &middot; ${formatTime(e.timestamp)}</div>
      </div>
    </div>
  `).join('');
}

// ---- Workflows ----
async function loadWorkflows() {
  const workflows = await api('/api/workflows');
  const el = document.getElementById('workflows-list');
  if (!workflows.length) { el.innerHTML = '<div class="empty"><div class="empty-icon">\u{1F4E6}</div>No workflows yet.</div>'; return; }
  el.innerHTML = workflows.map(w => `
    <div class="list-item" onclick="viewWorkflow('${w.id}')">
      <div class="list-item-info">
        <div class="list-item-title">${esc(w.title)}</div>
        <div class="list-item-sub">${w.project_name} &middot; Created ${formatTime(w.created_at)}</div>
      </div>
      <span class="badge badge-${w.status}">${w.status}</span>
    </div>
  `).join('');
}

document.getElementById('create-workflow-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    title: document.getElementById('wf-title').value,
    project_name: document.getElementById('wf-project').value,
    business_brief: document.getElementById('wf-brief').value,
    description: document.getElementById('wf-desc').value || '',
  };
  try {
    const wf = await api('/api/workflows', { method: 'POST', body: JSON.stringify(payload) });
    await api(`/api/workflows/${wf.id}/run`, { method: 'POST' });
    e.target.reset();
    setTimeout(() => viewWorkflow(wf.id), 500);
  } catch (err) {
    alert('Error creating workflow: ' + err.message);
  }
});

async function viewWorkflow(id) {
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-workflow-detail').classList.add('active');

  const wf = await api(`/api/workflows/${id}`);
  const el = document.getElementById('workflow-detail-content');

  const currentIdx = STAGES.indexOf(wf.current_stage);
  const isComplete = wf.status === 'completed';
  const pipelineHtml = STAGES.map((s, i) => {
    let cls = 'pending';
    if (isComplete || i < currentIdx) cls = 'completed';
    else if (i === currentIdx) cls = 'active';
    const arrow = i < STAGES.length - 1 ? '<span class="pipeline-arrow">\u25B6</span>' : '';
    return `<span class="pipeline-stage ${cls}">${STAGE_LABELS[s]}</span>${arrow}`;
  }).join('');

  const artifactHtml = Object.entries(wf.artifacts || {}).map(([stage, data]) => `
    <div class="artifact-section">
      <h3>${STAGE_LABELS[stage] || stage}</h3>
      <pre class="code-block">${esc(JSON.stringify(data, null, 2))}</pre>
    </div>
  `).join('');

  const outputsHtml = (wf.agent_outputs || []).map(o => `
    <div class="list-item" style="cursor:default;flex-direction:column;align-items:flex-start;gap:6px">
      <div style="display:flex;align-items:center;gap:8px;width:100%">
        <span>${AGENT_ICONS[o.agent_type] || '\u{1F916}'}</span>
        <span class="list-item-title" style="text-transform:capitalize">${o.agent_type.replace('_',' ')}</span>
        <span class="badge badge-${o.confidence_band}" style="margin-left:auto">${o.confidence_band} (${(o.confidence*100).toFixed(0)}%)</span>
      </div>
      <div class="list-item-sub">${esc(o.reasoning)}</div>
    </div>
  `).join('');

  const gatesHtml = (wf.approval_gates || []).map(g => `
    <div class="list-item" style="cursor:default">
      <div class="list-item-info">
        <div class="list-item-title">${esc(g.gate_name)}</div>
        <div class="list-item-sub">${g.stage} &middot; ${g.decided_by || 'awaiting'} ${g.reviewer_notes ? '&middot; ' + esc(g.reviewer_notes) : ''}</div>
      </div>
      <span class="badge badge-${g.status}">${g.status}</span>
    </div>
  `).join('');

  el.innerHTML = `
    <div class="card">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
        <h2 style="margin:0">${esc(wf.title)}</h2>
        <span class="badge badge-${wf.status}" style="font-size:.85rem">${wf.status}</span>
      </div>
      <div style="color:var(--text-dim);font-size:.85rem;margin-top:8px">${wf.project_name} &middot; ${wf.id}</div>
      <div class="pipeline">${pipelineHtml}</div>
    </div>
    <div class="card">
      <h2>Business Brief</h2>
      <p style="color:var(--text-dim);white-space:pre-wrap">${esc(wf.business_brief)}</p>
    </div>
    <div class="card">
      <h2>Approval Gates</h2>
      ${gatesHtml || '<div class="empty">No gates created yet.</div>'}
    </div>
    <div class="card">
      <h2>Agent Outputs</h2>
      ${outputsHtml || '<div class="empty">No agent outputs yet.</div>'}
    </div>
    <div class="card">
      <h2>Stage Artifacts</h2>
      ${artifactHtml || '<div class="empty">No artifacts generated yet.</div>'}
    </div>
  `;

  if (wf.status === 'running' || wf.status === 'awaiting_approval') {
    setTimeout(() => viewWorkflow(id), 3000);
  }
}

// ---- Approvals ----
async function loadApprovals() {
  const gates = await api('/api/approvals');
  const el = document.getElementById('approvals-list');
  if (!gates.length) { el.innerHTML = '<div class="empty"><div class="empty-icon">\u{2705}</div>No pending approvals right now.</div>'; return; }
  el.innerHTML = gates.map(g => `
    <div class="card" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
      <div>
        <div style="font-weight:700">${esc(g.gate_name)}</div>
        <div style="font-size:.85rem;color:var(--text-dim)">${g.stage} &middot; Workflow: ${g.workflow_id.substring(0,8)}...</div>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-success btn-sm" onclick="approveGate('${g.workflow_id}','${g.id}')">Approve</button>
        <button class="btn btn-danger btn-sm" onclick="rejectGate('${g.workflow_id}','${g.id}')">Reject</button>
      </div>
    </div>
  `).join('');
}

async function approveGate(wfId, gateId) {
  await api(`/api/approvals/${wfId}/${gateId}/approve`, { method: 'POST', body: JSON.stringify({ decided_by: 'dashboard-user', notes: 'Approved via dashboard' }) });
  loadApprovals();
}
async function rejectGate(wfId, gateId) {
  const reason = prompt('Rejection reason:');
  if (!reason) return;
  await api(`/api/approvals/${wfId}/${gateId}/reject`, { method: 'POST', body: JSON.stringify({ decided_by: 'dashboard-user', notes: reason }) });
  loadApprovals();
}

// ---- Agents ----
async function loadAgents() {
  const agents = await api('/api/agents');
  const el = document.getElementById('agents-grid');
  el.innerHTML = agents.map(a => `
    <div class="agent-card">
      <div style="display:flex;align-items:center;gap:8px">
        <span style="font-size:1.4rem">${AGENT_ICONS[a.agent_type] || '\u{1F916}'}</span>
        <div class="agent-name">${a.agent_type.replace(/_/g, ' ')}</div>
      </div>
      <div class="agent-meta" style="margin-top:8px">
        Status: ${a.is_active ? '<span style="color:var(--success)">Active</span>' : '<span style="color:var(--text-dim)">Inactive</span>'}
        &middot; Tasks: ${a.tasks_completed}
        ${a.last_active ? '&middot; Last: ' + formatTime(a.last_active) : ''}
      </div>
    </div>
  `).join('');
}

// ---- Events ----
async function loadEvents() {
  const events = await api('/api/events?limit=200');
  const el = document.getElementById('events-table');
  const header = `<div class="event-row"><span>Time</span><span>Topic</span><span>Agent</span><span>Workflow</span></div>`;
  if (!events.length) { el.innerHTML = header + '<div class="empty">No events yet.</div>'; return; }
  el.innerHTML = header + events.reverse().map(e => `
    <div class="event-row">
      <span class="event-time">${formatTime(e.timestamp)}</span>
      <span class="event-topic">${esc(e.topic)}</span>
      <span class="event-agent">${e.source_agent.replace(/_/g, ' ')}</span>
      <span style="color:var(--text-dim);font-size:.78rem">${e.workflow_id.substring(0,8)}...</span>
    </div>
  `).join('');
}

// ---- Gateway ----
async function loadGateway() {
  const manifests = await api('/api/gateway/manifests');
  const audit = await api('/api/gateway/audit?limit=50');

  const mEl = document.getElementById('manifests-content');
  mEl.innerHTML = Object.entries(manifests).map(([agent, tools]) => `
    <div class="manifest-agent">
      <h3>${AGENT_ICONS[agent] || '\u{1F916}'} ${agent.replace(/_/g, ' ')}</h3>
      <div class="manifest-tools">${tools.map(t => `<span class="manifest-tool">${esc(t)}</span>`).join('')}</div>
    </div>
  `).join('');

  const aEl = document.getElementById('audit-log');
  if (!audit.length) { aEl.innerHTML = '<div class="empty">No tool invocations yet.</div>'; return; }
  aEl.innerHTML = '<div class="scroll-list">' + audit.reverse().map(e => `
    <div class="list-item" style="cursor:default">
      <div class="list-item-info">
        <div class="list-item-title" style="font-family:var(--mono);font-size:.82rem">${esc(e.tool)}</div>
        <div class="list-item-sub">${e.agent} &middot; ${formatTime(e.timestamp)}</div>
      </div>
      <span class="badge badge-completed">${e.result_status}</span>
    </div>
  `).join('') + '</div>';

  const sel = document.getElementById('tool-agent');
  sel.innerHTML = Object.keys(manifests).map(a => `<option value="${a}">${a.replace(/_/g, ' ')}</option>`).join('');
}

document.getElementById('tool-invoke-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    agent_type: document.getElementById('tool-agent').value,
    tool_name: document.getElementById('tool-name').value,
    parameters: {},
  };
  try {
    const res = await api('/api/gateway/invoke', { method: 'POST', body: JSON.stringify(payload) });
    document.getElementById('tool-result').textContent = JSON.stringify(res, null, 2);
    loadGateway();
  } catch (err) {
    document.getElementById('tool-result').textContent = 'Error: ' + err.message;
  }
});

// ---- Helpers ----
function esc(str) {
  if (!str) return '';
  const d = document.createElement('div');
  d.textContent = String(str);
  return d.innerHTML;
}

function formatTime(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// ---- Init ----
loadDashboard();
setInterval(loadDashboard, 10000);
