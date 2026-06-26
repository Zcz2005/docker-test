# Southnotary OOS Uploader

南方公证处取证任务同步与天翼云 OOS/ZOS 视频上传服务。

该项目由原始单文件脚本重构而来，保留以下业务流程：

- 定时调用 `www.southnotary.cn` 开放接口获取自动取证任务。
- 将新任务写入 MySQL `tasktest` 表，按 `domain = southnotary` 去重。
- 查询已完成且未上传的任务视频，计算 SHA-256。
- 上传视频到天翼云 OOS/ZOS。
- 回调上传结果，成功后将 `tasktest.upload` 更新为 `1`。
- 兼容 `huanan2.zos.ctyun.cn` 这类 ZOS endpoint 的 CTYun SDK region 解析。

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

天翼云 OOS SDK 需要从天翼云文档/控制台下载源码包安装。安装完成后，Python 环境中应能成功导入：

```python
import oos
import ooscore
```

## 配置

复制环境变量模板并填入真实值：

```bash
cp .env.example .env
```

本项目不自动读取 `.env` 文件。可以使用 shell 导出环境变量：

```bash
set -a
source .env
set +a
```

必须配置：

- `SOUTHNOTARY_APPID`
- `SOUTHNOTARY_RANDKEY`
- `SOUTHNOTARY_HASHVAL`
- `OOS_ACCESS_KEY`
- `OOS_SECRET_KEY`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

默认值已覆盖当前业务域名：

- `SOUTHNOTARY_DOMAIN_ID=southnotary`
- `SOUTHNOTARY_BASE_URL=https://www.southnotary.cn/api`
- `SOUTHNOTARY_API_HOST=www.southnotary.cn`
- `OOS_ENDPOINT=https://huanan2.zos.ctyun.cn`
- `OOS_BUCKET=bucket-azy-southnotary`

## 运行

持续运行两个定时线程：

```bash
python -m southnotary_uploader
```

或：

```bash
python main.py
```

单次运行：

```bash
python -m southnotary_uploader --once fetch
python -m southnotary_uploader --once upload
python -m southnotary_uploader --once both
```

## 数据库表

服务默认使用 `tasktest` 表，代码会读取/写入以下字段：

- `id`
- `appname`
- `task_args`
- `title`
- `roomid`
- `casenum`
- `taskid`
- `forensic_type`
- `domain`
- `complete`
- `upload`
- `videopath`
- `start_time`
- `end_time`

## 日志

默认写入项目根目录下 `logs/oos_uploader_southnotary.log`，按天轮转并保留 7 天。可通过 `LOG_DIR` 和 `LOG_LEVEL` 调整。
