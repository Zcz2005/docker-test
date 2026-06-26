import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Domain
DOMAIN_ID = os.getenv("DOMAIN_ID", "southnotary")
BASE_URL = os.getenv("BASE_URL", "https://www.southnotary.cn/api")
API_HOST = os.getenv("API_HOST", "www.southnotary.cn")

# Evidence API
EVIDENCE_APPID = os.getenv("EVIDENCE_APPID", "")
EVIDENCE_RANDKEY = os.getenv("EVIDENCE_RANDKEY", "")
EVIDENCE_HASHVAL = os.getenv("EVIDENCE_HASHVAL", "")

# OOS / ZOS
OOS_ACCESS_KEY = os.getenv("OOS_ACCESS_KEY", "")
OOS_SECRET_KEY = os.getenv("OOS_SECRET_KEY", "")
OOS_ENDPOINT = os.getenv("OOS_ENDPOINT", "https://huanan2.zos.ctyun.cn")
OOS_BUCKET = os.getenv("OOS_BUCKET", "bucket-azy-southnotary")

# MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "evidence_db")

# Scheduler
EVIDENCE_POLL_INTERVAL = int(os.getenv("EVIDENCE_POLL_INTERVAL", "10"))
UPLOAD_POLL_INTERVAL = int(os.getenv("UPLOAD_POLL_INTERVAL", "10"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Platform mapping
PLATFORM_MAP = {
    "3": "Douyin",
    "5": "Kuaishou",
    "7": "Ailiao",
    "11": "Huajiao",
    "12": "Yingke",
    "14": "Lespark",
    "17": "Mifeng",
    "18": "Momo",
    "21": "Xiaohongshu",
    "22": "Xiuse",
    "24": "Baobao",
    "27": "Kelakela",
    "33": "Aichang",
    "36": "Lingsheng",
    "43": "Hongguo",
}
