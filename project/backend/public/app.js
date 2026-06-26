const API = '/api';

function toast(msg, isError = false) {
  const el = document.createElement('div');
  el.className = `toast${isError ? ' error' : ''}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || '请求失败');
  return data;
}

async function loadStats() {
  const { batchCount, traceCount, blockCount, chainLength, chainValid } = await fetchJSON(`${API}/stats`);
  document.getElementById('statBatches').textContent = batchCount;
  document.getElementById('statTraces').textContent = traceCount;
  document.getElementById('statBlocks').textContent = blockCount || chainLength;
  document.getElementById('statChainValid').textContent = chainValid ? '✓ 有效' : '✗ 异常';
  document.getElementById('statValid').classList.toggle('valid', chainValid);
}

async function loadChain() {
  const { data } = await fetchJSON(`${API}/chain`);
  const list = document.getElementById('chainList');
  list.innerHTML = data.map((block) => `
    <div class="block-card ${block.index === 0 ? 'genesis' : ''}">
      <div class="block-title">
        <span>区块 #${block.index}</span>
        <span>${new Date(block.timestamp).toLocaleString('zh-CN')}</span>
      </div>
      <div class="hash">Hash: ${block.hash}</div>
      <div class="hash">Prev: ${block.previousHash}</div>
      <div class="data-preview">${JSON.stringify(block.data, null, 0)}</div>
    </div>
  `).join('');
}

async function loadBatches() {
  const { data } = await fetchJSON(`${API}/batches`);
  const tbody = document.querySelector('#batchTable tbody');
  tbody.innerHTML = data.map((b) => `
    <tr>
      <td><code>${b.batch_id}</code></td>
      <td>${b.product_name}</td>
      <td>${b.quantity} ${b.unit}</td>
      <td>${b.status}</td>
      <td>${b.operator || '-'}</td>
      <td><button class="btn small" onclick="queryBatch('${b.batch_id}')">溯源</button></td>
    </tr>
  `).join('');
  if (data.length && !document.getElementById('traceBatchId').value) {
    document.getElementById('traceBatchId').value = data[0].batch_id;
    document.getElementById('queryBatchId').value = data[0].batch_id;
  }
}

window.queryBatch = async function (batchId) {
  document.getElementById('queryBatchId').value = batchId;
  document.getElementById('queryForm').dispatchEvent(new Event('submit'));
};

document.getElementById('batchForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const body = Object.fromEntries(form);
  body.quantity = Number(body.quantity);
  try {
    const { data } = await fetchJSON(`${API}/batches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    toast(`批次 ${data.batch.batch_id} 创建成功，区块 #${data.block.index} 已生成`);
    document.getElementById('traceBatchId').value = data.batch.batch_id;
    document.getElementById('queryBatchId').value = data.batch.batch_id;
    await refresh();
  } catch (err) {
    toast(err.message, true);
  }
});

document.getElementById('traceForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const body = Object.fromEntries(form);
  try {
    const { data } = await fetchJSON(`${API}/traces`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    toast(`溯源记录已上链，区块 #${data.block.index}`);
    await refresh();
  } catch (err) {
    toast(err.message, true);
  }
});

document.getElementById('queryForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const batchId = new FormData(e.target).get('batchId');
  try {
    const { data } = await fetchJSON(`${API}/trace/${batchId}`);
    const el = document.getElementById('queryResult');
    el.innerHTML = `
      <p><strong>${data.batch.product_name}</strong> · 批次 <code>${data.batch.batch_id}</code></p>
      <p class="verified">${data.chainValid ? '✓ 区块链完整性验证通过' : '✗ 链验证失败'}</p>
      <p>数据库记录 ${data.dbRecords.length} 条 · 链上记录 ${data.chainRecords.length} 条</p>
      <div class="timeline">
        ${data.dbRecords.map((r) => `
          <div class="timeline-item">
            <strong>${r.stage}</strong> — ${r.action}
            <br/><small>${r.operator} · ${r.location || ''} · ${new Date(r.created_at).toLocaleString('zh-CN')}</small>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    toast(err.message, true);
  }
});

document.getElementById('refreshChain').addEventListener('click', refresh);

async function refresh() {
  await Promise.all([loadStats(), loadChain(), loadBatches()]);
}

refresh();
