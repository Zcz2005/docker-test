# GreenChain 区块链溯源学习项目

一个**可一键部署**的完整区块链学习项目，包含 PostgreSQL 数据库、区块链核心实现、REST API 和可视化前端。

---

## 一、区块链是什么？有什么作用？

### 1.1 简单理解

区块链是一种**分布式账本技术**。可以把数据按时间顺序打包成「区块」，每个区块通过密码学哈希与前一个区块链接，形成一条**不可篡改的链**。

```
区块 #0 (创世)  →  区块 #1  →  区块 #2  →  区块 #3  → ...
  hash: abc       prev: abc     prev: def     prev: ghi
                  hash: def     hash: ghi     hash: jkl
```

一旦数据写入区块链，任何人（包括系统管理员）都**无法单独修改**历史记录，因为修改任何一个区块会导致后续所有区块的哈希失效。

### 1.2 区块链的核心作用

| 作用 | 说明 | 本项目中体现 |
|------|------|-------------|
| **不可篡改** | 历史数据写入后无法修改 | 溯源记录上链后，篡改会被 `verify` 检测到 |
| **可追溯** | 完整保留操作历史 | 每个环节生成一个区块，可回溯全链路 |
| **去中心化信任** | 多方共同见证，无需信任单一机构 | 链上数据独立于数据库，可交叉验证 |
| **透明可审计** | 授权方可查验完整记录 | `/api/chain` 可查看完整账本 |
| **防抵赖** | 操作有时间戳和哈希存证 | 每步操作绑定区块哈希 |

### 1.3 区块链 vs 传统数据库

| 对比项 | 传统数据库 | 区块链 |
|--------|-----------|--------|
| 数据修改 | 管理员可直接 UPDATE/DELETE | 只能追加，不能修改历史 |
| 信任模型 | 信任数据库管理员 | 信任密码学和链式结构 |
| 查询性能 | 极快 | 相对较慢 |
| 适用场景 | 日常业务读写 | 关键存证、审计、溯源 |

**最佳实践（本项目采用）**：**数据库负责高效读写，区块链负责关键数据存证**，两者双写、交叉验证。

### 1.4 常见应用场景

- **供应链溯源**：食品、药品从生产到销售全链路追溯
- **版权存证**：作品发布时间证明
- **电子合同**：签名和时间戳不可篡改
- **跨境支付**：无需中间机构的价值转移
- **数字身份**：去中心化身份认证

---

## 二、项目架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Web 前端    │────▶│  Express API │────▶│ PostgreSQL  │
│  (可视化)    │     │  (业务逻辑)   │     │  (业务数据)  │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  区块链模块   │
                    │  SHA256 + PoW │
                    │  (存证账本)   │
                    └──────────────┘
```

### 技术栈

- **后端**：Node.js + Express
- **数据库**：PostgreSQL 15（4 张表）
- **区块链**：自研 SHA256 哈希链 + 简单工作量证明
- **前端**：原生 HTML/CSS/JS
- **部署**：Docker Compose 一键启动

### 数据库表

| 表名 | 用途 |
|------|------|
| `product_batches` | 产品批次信息 |
| `trace_records` | 溯源环节记录 |
| `blocks` | 区块链持久化存储 |
| `users` | 用户（预留扩展） |

---

## 三、快速部署（推荐 Docker）

### 前置要求

- 安装 [Docker](https://docs.docker.com/get-docker/) 和 Docker Compose

### 一键启动

```bash
cd project
docker compose up --build
```

启动后访问：

- **前端界面**：http://localhost:3000
- **API 健康检查**：http://localhost:3000/api/health
- **区块链验证**：http://localhost:3000/api/chain/verify

### 停止服务

```bash
docker compose down
```

### 清除数据重新来过

```bash
docker compose down -v
docker compose up --build
```

---

## 四、本地开发（不用 Docker）

### 1. 启动 PostgreSQL

确保本地有 PostgreSQL，或使用 Docker 只启动数据库：

```bash
docker run -d --name gc-db \
  -e POSTGRES_DB=greenchain \
  -e POSTGRES_USER=greenchain \
  -e POSTGRES_PASSWORD=greenchain123 \
  -p 5432:5432 \
  postgres:15-alpine
```

### 2. 初始化并启动后端

```bash
cd project/backend
npm install
npm start
```

### 3. 访问

打开 http://localhost:3000

---

## 五、API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/stats` | 系统统计 |
| POST | `/api/batches` | 创建批次（上链） |
| GET | `/api/batches` | 批次列表 |
| GET | `/api/batches/:id` | 批次详情 |
| POST | `/api/traces` | 添加溯源记录（上链） |
| GET | `/api/trace/:batchId` | 完整溯源查询 |
| GET | `/api/chain` | 查看完整区块链 |
| GET | `/api/chain/verify` | 验证链完整性 |

### 示例：创建批次

```bash
curl -X POST http://localhost:3000/api/batches \
  -H "Content-Type: application/json" \
  -d '{
    "productName": "有机番茄",
    "category": "蔬菜",
    "quantity": 100,
    "unit": "kg",
    "operator": "张农户",
    "description": "我的第一个区块链批次"
  }'
```

### 示例：添加溯源记录

```bash
curl -X POST http://localhost:3000/api/traces \
  -H "Content-Type: application/json" \
  -d '{
    "batchId": "GC-xxx",
    "stage": "PLANTING",
    "action": "完成有机番茄种植登记",
    "operator": "张农户",
    "location": "山东寿光"
  }'
```

### 示例：溯源查询

```bash
curl http://localhost:3000/api/trace/GC-DEMO-001
```

---

## 六、学习路径建议

1. **阅读** `backend/src/blockchain/Block.js` — 理解区块结构和哈希计算
2. **阅读** `backend/src/blockchain/Blockchain.js` — 理解链式结构和验证逻辑
3. **阅读** `backend/src/services/traceService.js` — 理解数据库 + 区块链双写
4. **动手** 在前端创建批次、添加溯源、查看区块链
5. **实验** 直接修改数据库中 `blocks` 表的 hash 字段，再调用 `/api/chain/verify` 看验证失败
6. **扩展** 尝试添加用户登录、更多溯源环节、对接 IPFS 存储图片

---

## 七、项目结构

```
project/
├── docker-compose.yml       # 一键部署
├── sql/init.sql             # 数据库初始化
├── backend/
│   ├── Dockerfile
│   ├── package.json
│   ├── public/              # 前端界面
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js
│   └── src/
│       ├── index.js         # 入口
│       ├── blockchain/      # 区块链核心 ★
│       │   ├── Block.js
│       │   └── Blockchain.js
│       ├── db/              # 数据库层
│       │   ├── pool.js
│       │   └── repository.js
│       ├── routes/api.js    # API 路由
│       └── services/        # 业务逻辑
│           └── traceService.js
└── README.md                # 本文件
```

---

## License

MIT
