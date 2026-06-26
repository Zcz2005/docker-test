# GreenChain 绿链溯源

本仓库包含两部分：

## 1. 可部署的区块链学习项目（推荐从这里开始）

**目录**：[`project/`](project/)

一个完整的、带 PostgreSQL 数据库的区块链农产品溯源项目，适合学习和部署。

```bash
cd project
docker compose up --build
# 访问 http://localhost:3000
```

详细说明见 [project/README.md](project/README.md)，包含：
- 区块链作用介绍
- 架构说明
- API 文档
- 学习路径

## 2. 技术案例展示网站

**目录**：根目录（`index.html`）

详细的区块链使用案例文档网站（17+ 章节），含数据库设计、API、时序图等。

```bash
npm install
npm run dev
# 访问 http://localhost:5173
```

---

**新手建议**：先部署 `project/` 动手操作，再阅读根目录案例网站深入理解。
