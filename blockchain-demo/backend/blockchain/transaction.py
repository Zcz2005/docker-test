import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class TransactionType(str, Enum):
    GENESIS = "genesis"
    EVIDENCE_SUBMIT = "evidence_submit"
    EVIDENCE_VERIFY = "evidence_verify"
    CUSTODY_TRANSFER = "custody_transfer"
    NOTARY_SEAL = "notary_seal"


@dataclass
class EvidenceTransaction:
    """Single evidence-related transaction stored in a block."""

    tx_id: str
    tx_type: TransactionType
    evidence_hash: str
    case_num: str
    task_id: str
    submitter: str
    platform: str
    file_name: str
    file_size: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    signature: str = ""

    def __post_init__(self) -> None:
        if not self.tx_id:
            self.tx_id = str(uuid.uuid4())
        if isinstance(self.tx_type, str):
            self.tx_type = TransactionType(self.tx_type)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tx_type"] = self.tx_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceTransaction":
        payload = dict(data)
        payload["tx_type"] = TransactionType(payload["tx_type"])
        return cls(**payload)

    def calculate_hash(self) -> str:
        """Deterministic hash of transaction content (tamper detection)."""
        canonical = {
            "tx_id": self.tx_id,
            "tx_type": self.tx_type.value,
            "evidence_hash": self.evidence_hash,
            "case_num": self.case_num,
            "task_id": self.task_id,
            "submitter": self.submitter,
            "platform": self.platform,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }
        encoded = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def sign(self, secret: str = "southnotary-demo-key") -> None:
        payload = f"{self.calculate_hash()}:{secret}"
        self.signature = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def verify_signature(self, secret: str = "southnotary-demo-key") -> bool:
        expected = hashlib.sha256(
            f"{self.calculate_hash()}:{secret}".encode("utf-8")
        ).hexdigest()
        return self.signature == expected
