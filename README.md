# 绿链溯源 GreenChain v2

基于区块链的农产品全链路溯源平台 — **超详细**技术案例网站。

## 规模概览

| 指标 | 数量 |
|------|------|
| 网站章节 | **17+** 章 |
| 数据库表 | **18** 张 |
| API 接口 | **45+** 个 |
| 微服务 | **7** 个 |
| Docker 服务 | **16** 个 |
| 时序图 | **6** 个 |
| 存储引擎 | **5** 种 |

## 完整章节

1. 案例概述 — 背景、8 大角色
2. 痛点分析 — 传统 vs 区块链
3. 解决方案 — 6 大功能模块
4. 技术架构 — 分层架构、联盟链拓扑
5. **微服务架构** — 7 服务拆分、gRPC、通信方式
6. **批次状态机** — 10 状态、18 种转换规则
7. **数据库设计** — 18 表 DDL、ER 图、视图、触发器、示例数据、业务 SQL、Flyway 迁移
8. **API 接口** — 45+ 接口、Webhook、管理后台、分页规范
9. **数据流程** — 6 个时序图、RabbitMQ 事件、一致性保障
10. 业务流程 — 6 环节详解
11. 智能合约 — Go Chaincode
12. **安全设计** — 5 层防护、RBAC 矩阵、双重认证
13. **测试方案** — 单元/集成/合约/E2E
14. **性能指标** — 压测数据、优化策略
15. 部署运维 — docker-compose.yml、K8s、CI/CD
16. **交互演示** — 四面板（IPFS + DB + 链 + MQ）
17. 效益分析 + FAQ

## 项目文件

```
├── index.html                  # 主页面
├── public/content/             # 扩展章节（动态加载）
│   ├── microservices.html
│   ├── database-extra.html
│   ├── dataflow-extra.html
│   └── advanced-sections.html
├── sql/schema.sql              # PostgreSQL DDL
├── docker-compose.yml          # 16 服务完整配置
├── docs/api-extended.md        # API 扩展文档
├── css/style.css
└── js/main.js
```

## 快速开始

```bash
npm install
npm run dev      # http://localhost:5173
npm run build
```

## License

MIT
