const API_BASE = window.location.origin;

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

const BlockchainAPI = {
  health: () => api("/api/health"),
  summary: () => api("/api/chain/summary"),
  validate: () => api("/api/chain/validate"),
  blocks: () => api("/api/chain/blocks"),
  block: (index) => api(`/api/chain/blocks/${index}`),
  pending: () => api("/api/chain/pending"),
  mine: (miner = "web-miner") =>
    api("/api/chain/mine", { method: "POST", body: JSON.stringify({ miner }) }),
  submitEvidence: (data) =>
    api("/api/evidence/submit", { method: "POST", body: JSON.stringify(data) }),
  verify: (hash) => api(`/api/evidence/verify/${hash}`),
  timeline: (caseNum) => api(`/api/case/${caseNum}/timeline`),
  computeHash: (fileName, content = "") =>
    api("/api/tools/hash", {
      method: "POST",
      body: JSON.stringify({ file_name: fileName, simulated_content: content }),
    }),
};
