import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from blockchain.chain import Blockchain
from blockchain.transaction import EvidenceTransaction, TransactionType

blockchain = Blockchain(data_file="data/chain.json", difficulty=4)


class EvidenceSubmitRequest(BaseModel):
    evidence_hash: str = Field(..., description="SHA-256 文件哈希")
    case_num: str = Field(..., min_length=1, max_length=128)
    task_id: str = Field(..., min_length=1, max_length=128)
    submitter: str = Field(default="公证处操作员")
    platform: str = Field(default="Douyin")
    file_name: str = Field(default="evidence.mp4")
    file_size: int = Field(default=0, ge=0)
    screen_start_time: Optional[str] = None
    screen_end_time: Optional[str] = None
    room_id: Optional[str] = None
    title: Optional[str] = None

    @field_validator("evidence_hash")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) != 64 or not all(c in "0123456789abcdef" for c in normalized):
            raise ValueError("证据哈希必须为 64 位十六进制 SHA-256")
        return normalized


class CustodyTransferRequest(BaseModel):
    evidence_hash: str
    case_num: str
    task_id: str
    from_party: str
    to_party: str
    reason: str = "证据保管权转移"


class NotarySealRequest(BaseModel):
    evidence_hash: str
    case_num: str
    task_id: str
    notary_office: str = "广东省广州市南方公证处"
    certificate_no: Optional[str] = None


class MineRequest(BaseModel):
    miner: str = "demo-miner"


class HashFileMeta(BaseModel):
    file_name: str
    simulated_content: str = ""


def seed_demo_data() -> None:
    """Populate chain with realistic demo evidence if only genesis exists."""
    if len(blockchain.chain) > 1:
        return

    samples = [
        {
            "case_num": "GZ2025-EV-00128",
            "task_id": "TASK-8f3a21bc",
            "platform": "Douyin",
            "file_name": "live_record_20250620_143022.mp4",
            "file_size": 524288000,
            "title": "直播间售假化妆品取证",
            "room_id": "88776655",
        },
        {
            "case_num": "GZ2025-EV-00129",
            "task_id": "TASK-91de44af",
            "platform": "Kuaishou",
            "file_name": "ks_evidence_20250621.mp4",
            "file_size": 318767104,
            "title": "虚假宣传保健品直播",
            "room_id": "22334455",
        },
        {
            "case_num": "GZ2025-EV-00130",
            "task_id": "TASK-c7bb90e1",
            "platform": "Xiaohongshu",
            "file_name": "xhs_note_video.mp4",
            "file_size": 89128960,
            "title": "笔记视频侵权取证",
            "room_id": "note-99881",
        },
    ]

    for sample in samples:
        seed = f"{sample['task_id']}:{sample['file_name']}:{sample['case_num']}"
        evidence_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        tx = EvidenceTransaction(
            tx_id=str(uuid.uuid4()),
            tx_type=TransactionType.EVIDENCE_SUBMIT,
            evidence_hash=evidence_hash,
            case_num=sample["case_num"],
            task_id=sample["task_id"],
            submitter="自动化取证系统",
            platform=sample["platform"],
            file_name=sample["file_name"],
            file_size=sample["file_size"],
            metadata={
                "title": sample["title"],
                "room_id": sample["room_id"],
                "screen_start_time": "2025-06-20 14:30:22",
                "screen_end_time": "2025-06-20 15:12:08",
                "storage_path": f"evidenceProd/Casefile/File/2025-06-20/{int(time.time())}/{sample['file_name']}",
                "source": "southnotary automated forensics",
            },
        )
        tx.sign()
        blockchain.add_transaction(tx)

    blockchain.mine_pending_transactions("southnotary-seed-miner")

    # Add custody + notary for first case
    first_hash = hashlib.sha256(
        f"TASK-8f3a21bc:live_record_20250620_143022.mp4:GZ2025-EV-00128".encode()
    ).hexdigest()

    custody_tx = EvidenceTransaction(
        tx_id=str(uuid.uuid4()),
        tx_type=TransactionType.CUSTODY_TRANSFER,
        evidence_hash=first_hash,
        case_num="GZ2025-EV-00128",
        task_id="TASK-8f3a21bc",
        submitter="公证处证据管理员",
        platform="Douyin",
        file_name="live_record_20250620_143022.mp4",
        file_size=524288000,
        metadata={
            "from_party": "自动化取证系统",
            "to_party": "广东省广州市南方公证处",
            "reason": "证据入库保管",
        },
    )
    custody_tx.sign()
    blockchain.add_transaction(custody_tx)

    notary_tx = EvidenceTransaction(
        tx_id=str(uuid.uuid4()),
        tx_type=TransactionType.NOTARY_SEAL,
        evidence_hash=first_hash,
        case_num="GZ2025-EV-00128",
        task_id="TASK-8f3a21bc",
        submitter="南方公证处",
        platform="Douyin",
        file_name="live_record_20250620_143022.mp4",
        file_size=524288000,
        metadata={
            "notary_office": "广东省广州市南方公证处",
            "certificate_no": "NF-GZ-2025-0620-8891",
            "legal_effect": "具备电子数据保管证明效力",
        },
    )
    notary_tx.sign()
    blockchain.add_transaction(notary_tx)
    blockchain.mine_pending_transactions("notary-seal-miner")
