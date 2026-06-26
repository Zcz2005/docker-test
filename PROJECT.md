# 南方公证处 OOS 上传服务

由原始单文件脚本 `oos_uploader_southnotary.py` 重新生成的完整项目。

## 一分钟启动

```bash
pip install -r requirements.txt
# 另需安装天翼云 OOS SDK（oos / ooscore）

cp .env.example .env
# 编辑 .env，填入 API 凭证、OOS AK/SK、MySQL 配置

mysql -h ... -u ... -p ... < sql/tasktest.sql

python oos_uploader_southnotary.py
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `oos_uploader_southnotary.py` | **主程序**（双线程：拉任务 + 上传） |
| `db_utils.py` | MySQL 连接，`MySQLConnector()` 无参即用 |
| `.env.example` | 配置模板 |
| `sql/tasktest.sql` | 数据库建表 |
| `southnotary_uploader/` | 模块化增强版（可选） |
| `scrcpy_manager/` | Android 录屏服务（可选） |

## 业务流程

```
线程1 (10s): 公证处API拉任务 → INSERT tasktest (complete=0)
线程2 (10s): 查 complete=1 → SHA256 → 上传OOS → 回调API → upload=1
```

## 环境变量

```bash
SOUTHNOTARY_APPID=
SOUTHNOTARY_RANDKEY=
SOUTHNOTARY_HASHVAL=
OOS_ACCESS_KEY=
OOS_SECRET_KEY=
OOS_ENDPOINT=https://huanan2.zos.ctyun.cn
OOS_BUCKET=bucket-azy-southnotary
MYSQL_HOST=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=
```

详细文档见 `docs/` 目录。
