/**
 * 绿链溯源 GreenChain - 主交互逻辑
 */

// ============================================
// 导航栏
// ============================================

const header = document.getElementById('header');
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');

window.addEventListener('scroll', () => {
  header.classList.toggle('scrolled', window.scrollY > 50);
  updateActiveNav();
});

navToggle?.addEventListener('click', () => {
  navMenu.classList.toggle('open');
});

document.querySelectorAll('.nav-menu a').forEach(link => {
  link.addEventListener('click', () => navMenu.classList.remove('open'));
});

function updateActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const scrollPos = window.scrollY + 100;

  sections.forEach(section => {
    const top = section.offsetTop;
    const height = section.offsetHeight;
    const id = section.getAttribute('id');
    const link = document.querySelector(`.nav-menu a[href="#${id}"]`);

    if (scrollPos >= top && scrollPos < top + height) {
      document.querySelectorAll('.nav-menu a').forEach(l => l.classList.remove('active'));
      link?.classList.add('active');
    }
  });
}

// ============================================
// Hero 区块链动画
// ============================================

function initHeroChain() {
  const container = document.getElementById('heroChain');
  if (!container) return;

  const blocks = [
    { hash: '0x1a2b3c4d...e5f6', tx: 'createBatch' },
    { hash: '0x7g8h9i0j...k1l2', tx: 'addTraceRecord' },
    { hash: '0x3m4n5o6p...q7r8', tx: 'transferOwnership' },
    { hash: '0x9s0t1u2v...w3x4', tx: 'submitReport' },
  ];

  container.innerHTML = blocks.map((b, i) => `
  <div class="mini-block-item">
    <span>🔗 区块 #${i + 1}</span>
    <span style="font-family:var(--font-mono);font-size:0.7rem;color:var(--color-primary-light)">${b.hash}</span>
  </div>
`).join('');
}

// ============================================
// 业务流程时间线
// ============================================

const workflowSteps = [
  { icon: '🌱', label: '种植登记', time: '2026-03-15' },
  { icon: '🧺', label: '采收记录', time: '2026-06-01' },
  { icon: '🏭', label: '加工包装', time: '2026-06-02' },
  { icon: '🔬', label: '质量检测', time: '2026-06-03' },
  { icon: '🚚', label: '冷链物流', time: '2026-06-04' },
  { icon: '🏪', label: '零售上架', time: '2026-06-05' },
];

function initWorkflowTimeline() {
  const container = document.getElementById('workflowTimeline');
  if (!container) return;

  container.innerHTML = workflowSteps.map((step, i) => `
    <div class="workflow-step completed">
      <div class="step-circle">${step.icon}</div>
      <span class="step-label">${step.label}</span>
      <span class="step-time">${step.time}</span>
    </div>
  `).join('');
}

// ============================================
// 智能合约标签页
// ============================================

document.querySelectorAll('.contract-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const contract = tab.dataset.contract;

    document.querySelectorAll('.contract-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.contract-panel').forEach(p => p.classList.remove('active'));

    tab.classList.add('active');
    document.getElementById(`contract-${contract}`)?.classList.add('active');
  });
});

// 复制代码
document.querySelectorAll('.copy-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const id = btn.dataset.copy;
    const code = document.getElementById(`code-${id}`)?.textContent;
    if (!code) return;

    try {
      await navigator.clipboard.writeText(code);
      btn.textContent = '已复制 ✓';
      setTimeout(() => { btn.textContent = '复制代码'; }, 2000);
    } catch {
      btn.textContent = '复制失败';
      setTimeout(() => { btn.textContent = '复制代码'; }, 2000);
    }
  });
});

// ============================================
// 区块链交互演示
// ============================================

const demoSteps = {
  plant: {
    icon: '🌱',
    label: '种植登记',
    action: 'createBatch',
    operator: '寿光绿野合作社 · 张农户',
    detail: '创建批次 GC-TOM-2026-SD-00421，录入有机番茄种植信息',
    data: { product: '有机番茄', quantity: '500kg', location: '山东寿光' },
  },
  harvest: {
    icon: '🧺',
    label: '采收记录',
    action: 'addTraceRecord',
    operator: '寿光绿野合作社 · 采收队',
    detail: '采收 500kg 有机番茄，农残快检合格',
    data: { quantity: '500kg', test: '农残检测 PASS' },
  },
  process: {
    icon: '🏭',
    label: '加工包装',
    action: 'transferOwnership + addTraceRecord',
    operator: '潍坊绿野加工厂',
    detail: '清洗分拣包装，拆分为 1000 盒 × 500g',
    data: { process: '清洗→分拣→包装', packages: '1000盒' },
  },
  inspect: {
    icon: '🔬',
    label: '质量检测',
    action: 'submitQualityReport',
    operator: '山东省农产品质量检测中心',
    detail: '农药残留、重金属、微生物检测全部合格',
    data: { result: 'PASS', cert: 'ORG-2026-SD-0088' },
  },
  logistics: {
    icon: '🚚',
    label: '冷链物流',
    action: 'addTraceRecord + submitIoTData',
    operator: '顺丰冷链物流',
    detail: '冷链运输至北京，全程温度 2-6°C',
    data: { temp: '4.2°C', humidity: '65%', vehicle: '鲁B·12345' },
  },
  retail: {
    icon: '🏪',
    label: '零售上架',
    action: 'confirmDelivery + generateQRCode',
    operator: '北京华联超市朝阳店',
    detail: '确认收货并上架销售，生成消费者溯源二维码',
    data: { price: '¥12.8/盒', shelf: '蔬菜区 A-03' },
  },
};

let demoState = {
  currentStep: 0,
  stepOrder: ['plant', 'harvest', 'process', 'inspect', 'logistics', 'retail'],
  blocks: [],
  traces: [],
  completed: new Set(),
};

function generateHash() {
  const chars = '0123456789abcdef';
  let hash = '0x';
  for (let i = 0; i < 8; i++) hash += chars[Math.floor(Math.random() * 16)];
  hash += '...';
  for (let i = 0; i < 4; i++) hash += chars[Math.floor(Math.random() * 16)];
  return hash;
}

function addBlock(stepKey) {
  const step = demoSteps[stepKey];
  const blockNum = demoState.blocks.length + 1;
  const hash = generateHash();
  const prevHash = demoState.blocks.length > 0
    ? demoState.blocks[demoState.blocks.length - 1].hash
    : '0x0000...genesis';

  const block = { num: blockNum, hash, prevHash, action: step.action, label: step.label };
  demoState.blocks.push(block);

  const ledger = document.getElementById('blockchainLedger');
  const blockEl = document.createElement('div');
  blockEl.className = 'block new-block';
  blockEl.innerHTML = `
    <div class="block-header">
      <span class="block-num">#${block.num}</span>
      <span class="block-label">${step.label}</span>
    </div>
    <div class="block-body">
      <div class="block-field">
        <span class="field-label">Hash</span>
        <span class="field-value">${hash}</span>
      </div>
      <div class="block-field">
        <span class="field-label">Prev</span>
        <span class="field-value">${prevHash}</span>
      </div>
      <div class="block-field">
        <span class="field-label">Tx</span>
        <span class="field-value">${step.action}</span>
      </div>
    </div>
  `;
  ledger.appendChild(blockEl);
  ledger.scrollLeft = ledger.scrollWidth;

  setTimeout(() => blockEl.classList.remove('new-block'), 1000);
}

function addTraceItem(stepKey) {
  const step = demoSteps[stepKey];
  const hash = generateHash();
  demoState.traces.push({ ...step, hash });

  const timeline = document.getElementById('demoTraceTimeline');
  const empty = timeline.querySelector('.trace-empty');
  if (empty) empty.remove();

  const item = document.createElement('div');
  item.className = 'trace-item';
  item.innerHTML = `
    <span class="trace-icon">${step.icon}</span>
    <div class="trace-info">
      <h5>${step.label} — ${step.operator}</h5>
      <p>${step.detail}</p>
      <span class="trace-hash">${hash} ✓ 已上链确认</span>
    </div>
  `;
  timeline.appendChild(item);
}

function updateDemoUI() {
  const stepKeys = demoState.stepOrder;
  const currentKey = stepKeys[demoState.currentStep];
  const startBtn = document.getElementById('demoStartBtn');

  document.querySelectorAll('.demo-step-btn').forEach(btn => {
    const key = btn.dataset.step;
    btn.classList.remove('active', 'completed');

    if (demoState.completed.has(key)) {
      btn.classList.add('completed');
    } else if (key === currentKey) {
      btn.classList.add('active');
    }
  });

  if (demoState.currentStep >= stepKeys.length) {
    startBtn.textContent = '✓ 模拟完成';
    startBtn.disabled = true;
    document.getElementById('demoQR').style.display = 'block';
  } else {
    const nextStep = demoSteps[currentKey];
    startBtn.textContent = `执行：${nextStep.label}`;
    startBtn.disabled = false;
  }
}

function executeDemoStep() {
  const stepKeys = demoState.stepOrder;
  if (demoState.currentStep >= stepKeys.length) return;

  const key = stepKeys[demoState.currentStep];
  const startBtn = document.getElementById('demoStartBtn');

  startBtn.disabled = true;
  startBtn.textContent = '上链中...';

  setTimeout(() => {
    addBlock(key);
    addTraceItem(key);
    demoState.completed.add(key);
    demoState.currentStep++;
    updateDemoUI();
  }, 800);
}

function resetDemo() {
  demoState = {
    currentStep: 0,
    stepOrder: ['plant', 'harvest', 'process', 'inspect', 'logistics', 'retail'],
    blocks: [],
    traces: [],
    completed: new Set(),
  };

  const ledger = document.getElementById('blockchainLedger');
  ledger.innerHTML = `
    <div class="genesis-block block">
      <div class="block-header">
        <span class="block-num">#0</span>
        <span class="block-label">创世区块</span>
      </div>
      <div class="block-body">
        <div class="block-field">
          <span class="field-label">Hash</span>
          <span class="field-value">0x0000...genesis</span>
        </div>
        <div class="block-field">
          <span class="field-label">Prev</span>
          <span class="field-value">null</span>
        </div>
      </div>
    </div>
  `;

  const timeline = document.getElementById('demoTraceTimeline');
  timeline.innerHTML = '<div class="trace-empty">点击左侧按钮开始模拟上链操作</div>';

  document.getElementById('demoQR').style.display = 'none';
  document.getElementById('demoStartBtn').disabled = false;
  updateDemoUI();
}

document.getElementById('demoStartBtn')?.addEventListener('click', executeDemoStep);
document.getElementById('demoResetBtn')?.addEventListener('click', resetDemo);

// ============================================
// 消费者溯源查询
// ============================================

const traceData = [
  { icon: '🌱', title: '种植登记', org: '寿光绿野合作社', detail: '地块 SD-042，有机番茄，种植日期 2026-03-15', time: '2026-03-15 08:30' },
  { icon: '🧺', title: '采收记录', org: '寿光绿野合作社', detail: '采收 500kg，农残快检合格', time: '2026-06-01 06:00' },
  { icon: '🏭', title: '加工包装', org: '潍坊绿野加工厂', detail: '清洗分拣包装，1000 盒 × 500g', time: '2026-06-02 10:15' },
  { icon: '🔬', title: '质量检测', org: '山东省农产品质量检测中心', detail: '农药残留、重金属、微生物 — 全部合格', time: '2026-06-03 14:20' },
  { icon: '🚚', title: '冷链物流', org: '顺丰冷链物流', detail: '全程温控 2-6°C，GPS 实时追踪', time: '2026-06-04 08:00' },
  { icon: '🏪', title: '零售上架', org: '北京华联超市朝阳店', detail: '已上架销售，售价 ¥12.8/盒', time: '2026-06-05 09:30' },
];

function queryTrace() {
  const input = document.getElementById('queryInput');
  const result = document.getElementById('queryResult');
  const batchId = input?.value.trim();

  if (!batchId) return;

  result.style.display = 'block';
  result.innerHTML = `
    <div class="query-result-header">
      <span class="product-emoji">🍅</span>
      <div>
        <h4>有机番茄</h4>
        <p style="color:var(--color-text-muted);font-size:0.85rem">批次号：${batchId}</p>
        <span class="verified">✓ 链上数据已验证 · 未被篡改</span>
      </div>
    </div>
    <div class="query-timeline">
      ${traceData.map(item => `
        <div class="query-timeline-item">
          <span class="qt-icon">${item.icon}</span>
          <div class="qt-content">
            <h5>${item.title}</h5>
            <p>${item.org} — ${item.detail}</p>
            <span class="qt-time">${item.time} · 区块 #${traceData.indexOf(item) + 1}</span>
          </div>
        </div>
      `).join('')}
    </div>
  `;

  result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

document.getElementById('queryBtn')?.addEventListener('click', queryTrace);
document.getElementById('queryInput')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') queryTrace();
});

// ============================================
// 滚动动画
// ============================================

const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px',
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, observerOptions);

function initScrollAnimations() {
  const animatedElements = document.querySelectorAll(
    '.overview-card, .feature-card, .stakeholder, .event-card, .roi-card, .workflow-step-detail, .faq-item'
  );

  animatedElements.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });
}

// ============================================
// 初始化
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  initHeroChain();
  initWorkflowTimeline();
  updateDemoUI();
  initScrollAnimations();
  updateActiveNav();
});
