# 电子证据区块链存证平台

基于区块链的**电子证据存证与溯源**完整演示系统，以「网络直播侵权取证」为使用案例，展示从取证到公证的全链路可信存证方案。

## 使用案例概述

### 场景：直播售假侵权取证

| 阶段 | 动作 | 区块链作用 |
|------|------|-------------|
| 1. 任务下发 | 公证处通过 API 创建取证任务 | — |
| 2. 自动录屏 | 系统录制抖音/快手等直播 | — |
| 3. 哈希计算 | 对视频文件计算 SHA-256 | 生成唯一「指纹」 |
| 4. 云存储 | 上传至天翼云 ZOS 对象存储 | 原始文件链下存储 |
| 5. 链上存证 | 哈希+元数据写入区块链 | **不可篡改、可验证** |
| 6. 保管转移 | 记录证据保管权变更 | **溯源时间线** |
| 7. 公证封印 | 公证处出具电子数据保管证明 | **法律效力锚定** |

### 解决的核心问题

1. **防篡改** — 文件任何改动都会导致哈希不匹配
2. **可追溯** — 每次保管转移、公证操作均上链留痕
3. **可验证** — 第三方输入哈希即可验证存证时间和链上记录
4. **低成本** — 仅存储哈希（64字节），不上链原始视频

## 技术实现

### 区块链特性

- **区块结构**：index、timestamp、previous_hash、merkle_root、nonce、hash
- **交易类型**：`evidence_submit` / `custody_transfer` / `notary_seal` / `genesis`
- **共识机制**：Proof of Work（难度 4，哈希以 4 个零开头）
- **Merkle Tree**：区块内交易完整性校验
- **交易签名**：SHA-256 防伪造
- **持久化**：JSON 文件存储（`data/chain.json`）

### 系统架构

```
┌──────────────┐    REST API    ┌──────────────────┐
│  Web 前端     │ ◄────────────► │  FastAPI 后端     │
│  存证/验证/浏览│                │  区块链引擎       │
└──────────────┘                └────────┬─────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  data/chain.json    │
                              │  (区块持久化)        │
                              └─────────────────────┘
```

## 快速启动

### 方式一：本地运行

```bash
cd blockchain-demo
pip install -r requirements.txt
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 方式二：Docker

```bash
cd blockchain-demo
docker compose up -d
```

访问：**http://localhost:8000**

## 网站功能

| 页面 | 功能 |
|------|------|
| 首页 | 链状态概览、区块结构预览 |
| 使用案例 | 完整业务场景、痛点分析、案件时间线 |
| 技术架构 | 四层架构图、区块/交易结构说明 |
| 在线演示 | 生成哈希 → 提交交易 → 挖矿上链 |
| 区块浏览器 | 查看所有区块和交易详情 |
| 证据验证 | 输入哈希验证链上存证 |
| API 文档 | RESTful 接口说明 |

## API 接口

```bash
# 链概览
curl http://localhost:8000/api/chain/summary

# 提交证据
curl -X POST http://localhost:8000/api/evidence/submit \
  -H "Content-Type: application/json" \
  -d '{"evidence_hash":"abc...","case_num":"GZ2025-EV-001","task_id":"TASK-001","platform":"Douyin","file_name":"evidence.mp4"}'

# 挖矿打包
curl -X POST http://localhost:8000/api/chain/mine \
  -H "Content-Type: application/json" \
  -d '{"miner":"my-miner"}'

# 验证证据
curl http://localhost:8000/api/evidence/verify/{hash}

# 案件时间线
curl http://localhost:8000/api/case/GZ2025-EV-00128/timeline
```

## 预置演示数据

首次启动自动创建创世区块并播种 3 条取证记录：

- `GZ2025-EV-00128` — 抖音直播售假（含保管转移 + 公证封印）
- `GZ2025-EV-00129` — 快手虚假宣传
- `GZ2025-EV-00130` — 小红书侵权笔记

## 项目结构

```
blockchain-demo/
├── backend/
│   ├── app.py              # FastAPI 入口
│   ├── services.py         # 业务逻辑与种子数据
│   └── blockchain/
│       ├── block.py        # 区块 + Merkle Tree
│       ├── chain.py        # 区块链核心
│       └── transaction.py  # 证据交易
├── frontend/
│   ├── index.html          # 单页应用
│   ├── css/styles.css      # 样式
│   └── js/                 # 交互逻辑
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 与取证系统集成

本演示系统可与 `southnotary` 取证上传服务对接：

1. 录制完成 → 计算视频 SHA-256
2. 上传 ZOS → 获取 `object_key`
3. 调用 `POST /api/evidence/submit` 将哈希上链
4. 调用 `POST /api/chain/mine` 打包上链
5. 法院/当事人通过 `GET /api/evidence/verify/{hash}` 验证

## 注意事项

- 本系统为**技术演示**，使用本地 JSON 存储，非生产级联盟链
- 生产环境建议使用 Hyperledger Fabric、FISCO BCOS 等联盟链
- 原始视频文件存储在对象存储，链上仅存哈希和元数据
