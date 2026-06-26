// Demo hash for case GZ2025-EV-00128 (matches seeded data)
const DEMO_HASH = "8f3a21bc"; // partial - we'll compute full on load

let demoEvidenceHash = "";

function truncateHash(hash, len = 16) {
  if (!hash || hash.length <= len) return hash;
  return hash.slice(0, len) + "...";
}

function formatTime(ts) {
  return new Date(ts * 1000).toLocaleString("zh-CN");
}

function txTypeBadge(type) {
  const map = {
    genesis: "badge-purple",
    evidence_submit: "badge-blue",
    custody_transfer: "badge-yellow",
    notary_seal: "badge-green",
    evidence_verify: "badge-blue",
  };
  const cls = map[type] || "badge-blue";
  const labels = {
    genesis: "创世",
    evidence_submit: "证据提交",
    custody_transfer: "保管转移",
    notary_seal: "公证封印",
  };
  return `<span class="badge ${cls}">${labels[type] || type}</span>`;
}

function showAlert(containerId, message, type = "info") {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}

// Navigation highlight on scroll
function initNav() {
  const links = document.querySelectorAll(".nav-links a");
  const sections = document.querySelectorAll("section[id]");

  window.addEventListener("scroll", () => {
    let current = "";
    sections.forEach((section) => {
      const top = section.offsetTop - 100;
      if (window.scrollY >= top) current = section.id;
    });
    links.forEach((link) => {
      link.classList.toggle("active", link.getAttribute("href") === `#${current}`);
    });
  });
}

async function refreshStats() {
  try {
    const summary = await BlockchainAPI.summary();
    document.getElementById("stat-blocks").textContent = summary.block_height;
    document.getElementById("stat-evidence").textContent = summary.evidence_count;
    document.getElementById("stat-valid").textContent = summary.is_valid ? "✓ 有效" : "✗ 异常";
    document.getElementById("nav-chain-status").textContent =
      `区块 #${summary.block_height - 1} · ${summary.pending_transactions} 待打包`;
    document.getElementById("pending-count").textContent = summary.pending_transactions;
  } catch (e) {
    document.getElementById("nav-chain-status").textContent = "连接失败";
  }
}

async function refreshHeroChain() {
  try {
    const { blocks } = await BlockchainAPI.blocks();
    const preview = document.getElementById("hero-chain-preview");
    const recent = blocks.slice(-3);
    preview.innerHTML = recent
      .map((block) => {
        const types = block.transactions.map((t) => t.tx_type);
        const label =
          block.index === 0
            ? '<span class="badge badge-purple">Genesis</span>'
            : `<span class="badge badge-blue">${block.transactions.length} txs</span>`;
        const desc =
          block.index === 0
            ? "南方公证电子证据链创世区块"
            : types
                .map((t) => {
                  const m = {
                    evidence_submit: "证据提交",
                    custody_transfer: "保管转移",
                    notary_seal: "公证封印",
                  };
                  return m[t] || t;
                })
                .join(" + ");
        return `
          <div class="chain-block">
            <div>Block #${block.index} ${label}</div>
            <div class="hash">hash: ${truncateHash(block.hash, 20)}</div>
            <div style="color:var(--text-muted);margin-top:4px">${desc}</div>
          </div>`;
      })
      .join("");
  } catch (e) {
    console.error("Hero chain preview failed:", e);
  }
}

async function loadCaseTimeline() {
  const container = document.getElementById("case-timeline");
  try {
    const data = await BlockchainAPI.timeline("GZ2025-EV-00128");
    if (!data.events.length) {
      container.innerHTML =
        '<div class="timeline-item"><div class="time">暂无时间线数据</div></div>';
      return;
    }

    const typeLabels = {
      evidence_submit: "📹 证据提交上链",
      custody_transfer: "📦 证据保管权转移",
      notary_seal: "🔏 公证处出具封印",
      genesis: "⛓ 创世区块",
    };

    container.innerHTML = data.events
      .map((event) => {
        const meta = event.metadata || {};
        let detail = "";
        if (event.tx_type === "evidence_submit") {
          detail = `平台: ${event.platform} | 文件: ${meta.title || ""} | 房间号: ${meta.room_id || "-"}`;
          if (data.events[0] === event) demoEvidenceHash = event.evidence_hash;
        } else if (event.tx_type === "custody_transfer") {
          detail = `${meta.from_party} → ${meta.to_party} | ${meta.reason}`;
        } else if (event.tx_type === "notary_seal") {
          detail = `${meta.notary_office} | 证书号: ${meta.certificate_no}`;
        }
        return `
          <div class="timeline-item">
            <div class="time">${formatTime(event.timestamp)} · 区块 #${event.block_index}</div>
            <div><strong>${typeLabels[event.tx_type] || event.tx_type}</strong> ${txTypeBadge(event.tx_type)}</div>
            <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:0.25rem">${detail}</div>
            <div class="hash-cell" style="margin-top:0.5rem">hash: ${event.evidence_hash}</div>
          </div>`;
      })
      .join("");
  } catch (e) {
    container.innerHTML = `<div class="timeline-item"><div class="time">加载失败: ${e.message}</div></div>`;
  }
}

async function refreshExplorer() {
  const tbody = document.getElementById("blocks-table");
  try {
    const { blocks } = await BlockchainAPI.blocks();
    tbody.innerHTML = blocks
      .slice()
      .reverse()
      .map(
        (block) => `
        <tr>
          <td><strong>#${block.index}</strong></td>
          <td>${formatTime(block.timestamp)}</td>
          <td class="hash-cell" title="${block.hash}">${truncateHash(block.hash)}</td>
          <td class="hash-cell" title="${block.previous_hash}">${truncateHash(block.previous_hash)}</td>
          <td>${block.transactions.length}</td>
          <td>${block.nonce.toLocaleString()}</td>
          <td>${block.miner}</td>
          <td><button class="btn btn-outline btn-sm" onclick="showBlockDetail(${block.index})">详情</button></td>
        </tr>`
      )
      .join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--danger)">加载失败: ${e.message}</td></tr>`;
  }
}

async function refreshPending() {
  const tbody = document.getElementById("pending-table");
  try {
    const data = await BlockchainAPI.pending();
    document.getElementById("pending-count").textContent = data.count;
    if (!data.count) {
      tbody.innerHTML =
        '<tr><td colspan="5" style="text-align:center;color:var(--text-muted)">暂无待打包交易</td></tr>';
      return;
    }
    tbody.innerHTML = data.pending
      .map(
        (tx) => `
        <tr>
          <td class="hash-cell">${truncateHash(tx.tx_id, 12)}</td>
          <td>${txTypeBadge(tx.tx_type)}</td>
          <td>${tx.case_num}</td>
          <td class="hash-cell" title="${tx.evidence_hash}">${truncateHash(tx.evidence_hash)}</td>
          <td>${tx.platform}</td>
        </tr>`
      )
      .join("");
  } catch (e) {
    console.error(e);
  }
}

async function showBlockDetail(index) {
  try {
    const block = await BlockchainAPI.block(index);
    document.getElementById("modal-title").textContent = `区块 #${block.index} 详情`;
    const txRows = block.transactions
      .map(
        (tx) => `
        <tr>
          <td class="hash-cell">${truncateHash(tx.tx_id, 12)}</td>
          <td>${txTypeBadge(tx.tx_type)}</td>
          <td>${tx.case_num}</td>
          <td>${tx.task_id}</td>
          <td class="hash-cell" title="${tx.evidence_hash}">${truncateHash(tx.evidence_hash)}</td>
          <td>${tx.submitter}</td>
        </tr>`
      )
      .join("");

    document.getElementById("modal-body").innerHTML = `
      <div class="grid-2" style="margin-bottom:1.5rem">
        <div><strong>区块哈希</strong><div class="hash-cell">${block.hash}</div></div>
        <div><strong>前置哈希</strong><div class="hash-cell">${block.previous_hash}</div></div>
        <div><strong>Merkle Root</strong><div class="hash-cell">${block.merkle_root}</div></div>
        <div><strong>Nonce / 难度</strong><div>${block.nonce.toLocaleString()} / ${block.difficulty}</div></div>
        <div><strong>时间</strong><div>${formatTime(block.timestamp)}</div></div>
        <div><strong>矿工</strong><div>${block.miner}</div></div>
      </div>
      <h4 style="margin-bottom:0.75rem">交易列表 (${block.transactions.length})</h4>
      <div class="table-wrap">
        <table>
          <thead><tr><th>TX ID</th><th>类型</th><th>案件</th><th>任务</th><th>证据哈希</th><th>提交人</th></tr></thead>
          <tbody>${txRows}</tbody>
        </table>
      </div>`;
    document.getElementById("block-modal").classList.add("open");
  } catch (e) {
    alert("加载区块详情失败: " + e.message);
  }
}

function closeModal() {
  document.getElementById("block-modal").classList.remove("open");
}

async function generateHash() {
  const fileName = document.getElementById("demo-filename").value;
  const content = document.getElementById("demo-content").value;
  try {
    const result = await BlockchainAPI.computeHash(fileName, content);
    document.getElementById("submit-hash").value = result.sha256;
    showAlert(
      "hash-result",
      `<strong>SHA-256 计算完成</strong><br><code style="word-break:break-all">${result.sha256}</code>`,
      "success"
    );
  } catch (e) {
    showAlert("hash-result", `计算失败: ${e.message}`, "error");
  }
}

async function submitEvidence() {
  const data = {
    evidence_hash: document.getElementById("submit-hash").value.trim(),
    case_num: document.getElementById("submit-case").value,
    task_id: document.getElementById("submit-task").value,
    platform: document.getElementById("submit-platform").value,
    submitter: document.getElementById("submit-submitter").value,
    file_name: document.getElementById("submit-filename").value,
    file_size: 1024000,
    title: "演示取证视频",
    room_id: "demo-room",
  };

  try {
    const result = await BlockchainAPI.submitEvidence(data);
    showAlert(
      "submit-result",
      `✅ 交易已加入待打包池<br>TX ID: <code>${result.tx_id}</code><br>待打包: ${result.pending_count} 笔`,
      "success"
    );
    await refreshPending();
    await refreshStats();
  } catch (e) {
    showAlert("submit-result", `提交失败: ${e.message}`, "error");
  }
}

async function mineBlock() {
  const resultEl = document.getElementById("mine-result");
  resultEl.innerHTML = '<div class="loading"></div> 挖矿中...';

  try {
    const result = await BlockchainAPI.mine();
    const block = result.block;
    const mining = result.mining;
    resultEl.innerHTML = `
      <div class="alert alert-success">
        ⛏ 挖矿成功！区块 #${block.index} 已上链<br>
        哈希: <code>${block.hash}</code><br>
        尝试次数: ${mining.attempts.toLocaleString()} · 耗时: ${mining.elapsed_seconds}s
      </div>`;
    await refreshStats();
    await refreshExplorer();
    await refreshPending();
    await refreshHeroChain();
    await loadCaseTimeline();
  } catch (e) {
    resultEl.innerHTML = `<div class="alert alert-error">挖矿失败: ${e.message}</div>`;
  }
}

async function verifyEvidence() {
  const hash = document.getElementById("verify-hash").value.trim().toLowerCase();
  if (!hash) {
    showAlert("verify-result", "请输入证据哈希", "error");
    return;
  }

  try {
    const result = await BlockchainAPI.verify(hash);
    if (!result.found) {
      showAlert("verify-result", `❌ ${result.message}`, "error");
      return;
    }

    const records = result.all_records
      .map(
        (r) => `
        <div class="timeline-item" style="margin-top:0.75rem">
          <div class="time">${formatTime(r.block_timestamp)} · 区块 #${r.block_index}</div>
          <div>${txTypeBadge(r.transaction.tx_type)} 案件: ${r.transaction.case_num} | 任务: ${r.transaction.task_id}</div>
          <div style="font-size:0.85rem;color:var(--text-secondary)">提交人: ${r.transaction.submitter} | 平台: ${r.transaction.platform}</div>
        </div>`
      )
      .join("");

    document.getElementById("verify-result").innerHTML = `
      <div class="alert alert-success">
        ✅ 证据已在链上存证 · 共 ${result.on_chain_count} 条记录 · 链完整性: ${result.chain_valid ? "有效" : "异常"}
      </div>
      <h4 style="margin:1rem 0 0.5rem">溯源记录</h4>
      <div class="timeline">${records}</div>`;
  } catch (e) {
    showAlert("verify-result", `验证失败: ${e.message}`, "error");
  }
}

function fillDemoHash() {
  if (demoEvidenceHash) {
    document.getElementById("verify-hash").value = demoEvidenceHash;
  } else {
    document.getElementById("verify-hash").value =
      "8f3a21bc"; // fallback hint
    showAlert("verify-result", "演示哈希加载中，请稍后重试或从时间线复制完整哈希", "info");
    loadCaseTimeline();
  }
}

function switchTab(panelId) {
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  document.getElementById(panelId).classList.add("active");
  event.target.classList.add("active");
}

// Close modal on overlay click
document.getElementById("block-modal").addEventListener("click", (e) => {
  if (e.target.id === "block-modal") closeModal();
});

// Init
document.addEventListener("DOMContentLoaded", async () => {
  initNav();
  await refreshStats();
  await refreshHeroChain();
  await loadCaseTimeline();
  await refreshExplorer();
  await refreshPending();

  setInterval(refreshStats, 15000);
});
