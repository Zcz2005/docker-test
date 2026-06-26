# 部署指南

本文档覆盖裸机部署、systemd 服务、Docker 部署三种方式。

---

## 1. 环境要求

| 组件 | 版本建议 |
|------|----------|
| Python | 3.9+（推荐 3.11） |
| MySQL | 5.7+ / 8.0+ |
| 操作系统 | Linux（生产推荐） |

### Python 依赖

```bash
pip install -r requirements.txt
```

### 天翼云 OOS SDK

SDK 不通过 PyPI 发布，需从天翼云控制台下载 `oos-python-sdk-*.zip`，解压后安装：

```bash
cd oos-python-sdk-6.5.0
python3 -m pip install .
python3 -c "import oos, ooscore; print('OOS SDK OK')"
```

---

## 2. 配置

### 2.1 复制环境变量模板

```bash
cp .env.example .env
```

编辑 `.env`，填入真实凭证。服务启动时会自动尝试加载项目根目录或当前工作目录下的 `.env`（可用 `DOTENV_PATH` 指定路径）。

### 2.2 导出环境变量（可选）

```bash
set -a
source .env
set +a
```

### 2.3 配置自检

```bash
python3 scripts/check_env.py
python3 -m southnotary_uploader doctor
```

---

## 3. 初始化数据库

```bash
mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < sql/tasktest.sql
```

---

## 4. 裸机部署

### 4.1 安装到 /opt

```bash
sudo mkdir -p /opt/southnotary-uploader
sudo rsync -av --exclude .venv --exclude logs ./ /opt/southnotary-uploader/
cd /opt/southnotary-uploader
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 安装 OOS SDK ...
```

### 4.2 创建运行用户

```bash
sudo useradd --system --home /opt/southnotary-uploader --shell /usr/sbin/nologin southnotary || true
sudo chown -R southnotary:southnotary /opt/southnotary-uploader
```

### 4.3 环境文件

```bash
sudo mkdir -p /etc/southnotary-uploader
sudo cp .env /etc/southnotary-uploader/env
sudo chmod 600 /etc/southnotary-uploader/env
sudo chown root:southnotary /etc/southnotary-uploader/env
```

### 4.4 启动脚本

```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

---

## 5. systemd 部署

```bash
sudo cp deploy/southnotary-uploader.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable southnotary-uploader
sudo systemctl start southnotary-uploader
sudo systemctl status southnotary-uploader
```

查看日志：

```bash
journalctl -u southnotary-uploader -f
```

---

## 6. Docker 部署

### 6.1 构建镜像

```bash
docker compose build
```

> 注意：需在 Dockerfile 中补充 CTYun OOS SDK 安装步骤，或基于已内置 SDK 的基础镜像构建。

### 6.2 启动

```bash
cp .env.example .env
# 编辑 .env
docker compose up -d
docker compose logs -f southnotary-uploader
```

### 6.3 挂载录制目录

确保 `.env` 中 `videopath` 指向的路径在容器内可访问。`docker-compose.yml` 默认示例：

```yaml
volumes:
  - /data/recordings:/data/recordings:ro
```

---

## 7. 运行模式

### 7.1 常驻双线程（默认）

```bash
python3 -m southnotary_uploader
```

### 7.2 单次执行

```bash
python3 -m southnotary_uploader --once fetch
python3 -m southnotary_uploader --once upload
python3 -m southnotary_uploader --once both
```

### 7.3 健康检查 / 诊断

```bash
python3 -m southnotary_uploader doctor
python3 -m southnotary_uploader doctor --json
```

---

## 8. 上线检查清单

- [ ] `.env` / systemd `EnvironmentFile` 已配置且权限正确
- [ ] MySQL 可连接，`tasktest` 表已创建
- [ ] OOS SDK 可 `import oos`
- [ ] `scripts/check_env.py` 全部通过
- [ ] `doctor` 命令 API Token 获取成功
- [ ] 录制目录对运行用户可读
- [ ] 日志目录可写（默认 `logs/`）
- [ ] 防火墙允许访问 `www.southnotary.cn` 与 OOS endpoint

---

## 9. 升级与回滚

### 升级

```bash
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart southnotary-uploader
```

### 回滚

```bash
git checkout <previous-tag-or-commit>
sudo systemctl restart southnotary-uploader
```

服务无状态，回滚不影响已写入数据库的任务记录。
