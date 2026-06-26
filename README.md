# Southnotary Evidence Upload Service

自动化取证任务同步与视频上传服务，面向 [www.southnotary.cn](https://www.southnotary.cn) 平台。

## 功能概述

本服务包含两个后台定时任务：

1. **取证数据同步** — 定期调用 `getAutomatedForensics` 接口，将新取证任务写入 MySQL `tasktest` 表
2. **视频上传** — 查询 `complete=1 AND upload=0` 的任务，将本地视频上传至天翼云 ZOS 对象存储，并回调 `uploadAutomatedForensicsFile` 接口

```
┌─────────────────┐     轮询取证 API      ┌──────────────┐
│  Evidence API   │ ────────────────────► │    MySQL     │
│ southnotary.cn  │                       │  tasktest    │
└─────────────────┘                       └──────┬───────┘
                                                   │
                     查询已完成未上传任务            │
                                                   ▼
┌─────────────────┐     PUT Object        ┌──────────────┐
│  CTyun ZOS/OOS  │ ◄──────────────────── │   Uploader   │
└─────────────────┘                       └──────┬───────┘
                                                   │
                     回调上传结果                   ▼
┌─────────────────┐ ◄──────────────────── ┌──────────────┐
│  Evidence API   │                       │   Uploader   │
└─────────────────┘                       └──────────────┘
```

## 项目结构

```
.
├── run.py                  # 启动入口
├── src/
│   ├── main.py             # 主程序，启动两个定时线程
│   ├── config.py           # 环境变量配置
│   ├── db_utils.py         # MySQL 连接封装
│   ├── evidence_api.py     # 取证平台 API 客户端
│   ├── oos_client.py       # ZOS/OOS 上传客户端
│   ├── oos_patch.py        # zos endpoint 区域解析补丁
│   ├── scheduler.py        # 定时线程
│   ├── logging_config.py   # 日志配置
│   └── workers/
│       ├── evidence_worker.py   # 取证数据入库
│       └── upload_worker.py     # 视频上传与回调
├── sql/schema.sql          # 数据库建表脚本
├── sdk/                    # 天翼云 OOS SDK（需手动下载）
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 安装天翼云 OOS SDK

参见 [sdk/README.md](sdk/README.md)，将官方 SDK 解压到 `sdk/` 目录后离线安装。

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入数据库、API 凭证、OOS 密钥等
```

### 4. 初始化数据库

```bash
mysql -u root -p < sql/schema.sql
```

### 5. 启动服务

```bash
python run.py
# 或
python -m src.main
```

## Docker 部署

```bash
cp .env.example .env
# 编辑 .env

docker compose up -d
```

## 配置说明

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `DOMAIN_ID` | 域名标识，用于区分多站点 | `southnotary` |
| `BASE_URL` | 取证 API 基础地址 | `https://www.southnotary.cn/api` |
| `EVIDENCE_APPID` | 取证平台 appid | — |
| `EVIDENCE_RANDKEY` | 取证平台 randkey | — |
| `EVIDENCE_HASHVAL` | 取证平台 hashval | — |
| `OOS_ACCESS_KEY` | ZOS Access Key | — |
| `OOS_SECRET_KEY` | ZOS Secret Key | — |
| `OOS_ENDPOINT` | ZOS Endpoint | `https://huanan2.zos.ctyun.cn` |
| `OOS_BUCKET` | 存储桶名称 | — |
| `MYSQL_HOST` | MySQL 主机 | `127.0.0.1` |
| `MYSQL_DATABASE` | 数据库名 | `evidence_db` |
| `EVIDENCE_POLL_INTERVAL` | 取证轮询间隔（秒） | `10` |
| `UPLOAD_POLL_INTERVAL` | 上传轮询间隔（秒） | `10` |

## 数据流说明

### 取证入库

- 调用 `GET /fh-evidence/openApi/v1/getAutomatedForensics?type=1`
- 按 `taskid + domain` 去重后插入 `tasktest` 表
- 支持 Xiuse 平台 `roomId=0` 时从 URL 末尾提取房间号

### 视频上传

- 查询条件：`complete = 1 AND upload = 0 AND domain = 'southnotary'`
- 上传路径格式：`evidenceProd/Casefile/File/{日期}/{时间戳}/{文件名}`
- 上传成功后调用 `POST /api/fh-evidence/openApi/v1/uploadAutomatedForensicsFile`
- 回调成功或返回「取证任务已结束/不存在」时，将 `upload` 置为 `1`

## 日志

日志输出至 `logs/oos_uploader_southnotary.log`，按天轮转，保留 7 天。

## 注意事项

- 敏感凭证请通过 `.env` 配置，勿提交到版本库
- OOS SDK 需 Python 3.4–3.11，不支持 3.12+
- 视频文件路径 `videopath` 需由录制服务在任务完成后写入数据库
