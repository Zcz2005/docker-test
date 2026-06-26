# 绿链溯源 GreenChain

基于区块链的农产品全链路溯源平台 — 完整技术案例网站（含数据库、API、数据流、部署）。

## 案例简介

以「有机番茄从田间到餐桌」为例，展示联盟链 + 多存储引擎的完整溯源系统设计与实现。

## 网站章节（13 章）

| # | 章节 | 内容 |
|---|------|------|
| 01 | 案例概述 | 背景、目标、参与角色 |
| 02 | 痛点分析 | 传统 vs 区块链对比 |
| 03 | 解决方案 | 6 大功能模块 |
| 04 | 技术架构 | 分层架构、联盟链拓扑 |
| 05 | **数据库设计** | 13 张表 DDL、ER 图、Redis Key、存储决策矩阵 |
| 06 | **API 接口** | 28+ RESTful 接口、请求/响应示例、错误码 |
| 07 | **数据流程** | 时序图、消息队列、端到端数据管道 |
| 08 | 业务流程 | 6 环节全链路操作 |
| 09 | 智能合约 | Go Chaincode 完整代码 |
| 10 | **部署运维** | Docker Compose、K8s、CI/CD、备份监控 |
| 11 | 交互演示 | 区块链 + 数据库双写模拟器 |
| 12 | 效益分析 | ROI、实施路线、成本估算 |
| 13 | FAQ | 常见问题 |

## 数据存储架构

| 引擎 | 用途 |
|------|------|
| PostgreSQL 15 | 核心业务库（13 张表） |
| TimescaleDB | IoT 温湿度/GPS 时序数据 |
| Redis 7 | 查询缓存、Session、分布式锁 |
| IPFS + MinIO | 图片、视频、质检报告 |
| Hyperledger Fabric | 链上存证（批次、溯源哈希） |

## 快速开始

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # 生产构建
```

## 项目结构

```
├── index.html           # 主页面（13 章节）
├── css/style.css        # 样式
├── js/main.js           # 交互逻辑
├── sql/schema.sql       # PostgreSQL DDL 参考
├── package.json
└── vite.config.js
```

## License

MIT
