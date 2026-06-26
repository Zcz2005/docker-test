# 故障排查手册

## 1. 启动失败

### 症状：`Missing required environment variable`

**原因**：必填环境变量未设置。

**处理**：

```bash
python3 scripts/check_env.py
```

根据输出补齐 `.env` 或 systemd `EnvironmentFile`。

---

### 症状：`CTYun OOS SDK is not installed`

**原因**：未安装天翼云 OOS Python SDK。

**处理**：

```bash
python3 -c "import oos, ooscore"
```

若失败，按 `docs/DEPLOYMENT.md` 安装 SDK。

---

## 2. Token 获取失败

### 症状：`Failed to get token`

**可能原因**：

- `SOUTHNOTARY_APPID` / `SOUTHNOTARY_RANDKEY` / `SOUTHNOTARY_HASHVAL` 错误
- 服务器时间偏差过大
- 网络无法访问 `www.southnotary.cn`

**排查**：

```bash
python3 -m southnotary_uploader doctor
curl -I https://www.southnotary.cn/api/fh-evidence/openApi/v1/getCommAuthors
```

---

## 3. 任务拉取正常但无法入库

### 症状：日志显示 `taskid已存在`

**原因**：`uk_taskid_domain` 唯一约束或业务去重逻辑生效，属正常行为。

### 症状：`处理失败（查询/插入异常）`

**可能原因**：

- MySQL 连接失败
- 表结构缺失字段
- 字符集问题

**排查**：

```bash
mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p -e "DESC tasktest;"
```

对照 `docs/DATABASE.md` 与 `sql/tasktest.sql`。

---

## 4. 视频无法上传

### 症状：`videopath为空，跳过上传`

**原因**：录制程序未将 `videopath` 写回数据库。

**处理**：检查录制侧是否在 `complete=1` 时更新 `videopath`。

---

### 症状：`文件不存在，跳过上传`

**原因**：路径错误或上传服务无权读取文件。

**处理**：

```bash
ls -l <videopath>
```

确认运行用户（`southnotary` / 容器 `appuser`）有读权限。

---

### 症状：OOS `Invalid Endpoint!`

**原因**：CTYun SDK 无法从 endpoint 解析 region。

**处理**：

- 确认 `OOS_ENDPOINT` 为 `https://huanan2.zos.ctyun.cn` 这类 ZOS 地址
- 确认 `ctyun_patch.py` 已在客户端初始化前执行（服务默认会自动 patch）

---

### 症状：OOS `AccessDenied` / 签名错误

**可能原因**：

- AccessKey / SecretKey 错误
- Bucket 名称错误
- 账号无 `PutObject` 权限

**排查**：在 OOS 控制台核对桶名、AK/SK、策略。

---

## 5. 上传成功但回调失败

### 症状：HTTP 非 200

**处理**：查看日志中完整响应体，联系公证处平台确认任务状态。

### 症状：业务 code 非 200（非终态 500）

常见原因：

- `taskId` 与公证处不一致
- `hash` 与实际上传文件不一致
- `screenStartTime` / `screenEndTime` 格式错误（应为 `YYYY-MM-DD HH:MM:SS`）

### 症状：`取证任务已结束！` / `取证任务不存在！`

**说明**：服务会仍将 `upload=1`，避免无限重试。若业务上不应结束，需与公证处确认任务生命周期。

---

## 6. 日志位置

| 场景 | 路径 |
|------|------|
| 默认文件日志 | `logs/oos_uploader_<domain>.log` |
| systemd | `journalctl -u southnotary-uploader` |
| Docker | `docker compose logs -f` |

提高日志级别：

```bash
export LOG_LEVEL=DEBUG
```

---

## 7. 常用诊断命令

```bash
# 环境变量
python3 scripts/check_env.py

# 全链路诊断
python3 -m southnotary_uploader doctor

# 仅拉取一次任务
python3 -m southnotary_uploader --once fetch

# 仅上传一次
python3 -m southnotary_uploader --once upload

# 数据库待上传数量
mysql -e "SELECT COUNT(*) FROM tasktest WHERE domain='southnotary' AND complete=1 AND upload=0;"
```

---

## 8. 性能与并发说明

- 当前实现为 **单进程双线程**，每个周期顺序处理任务列表。
- 大文件 SHA-256 与 OOS 上传会阻塞当前上传周期。
- 若任务量大，可考虑：
  - 增大 `UPLOAD_INTERVAL_SECONDS`
  - 拆分多实例并按 `domain` 分片（需业务层支持）
  - 将上传改为队列 + 多 worker 架构（需二次开发）
