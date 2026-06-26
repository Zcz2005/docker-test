import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .transaction import EvidenceTransaction


def merkle_root(hashes: List[str]) -> str:
    """Build a Merkle root from transaction hashes."""
    if not hashes:
        return hashlib.sha256(b"").hexdigest()

    layer = hashes[:]
    while len(layer) > 1:
        next_layer: List[str] = []
        for index in range(0, len(layer), 2):
            left = layer[index]
            right = layer[index + 1] if index + 1 < len(layer) else left
            combined = hashlib.sha256(f"{left}{right}".encode("utf-8")).hexdigest()
            next_layer.append(combined)
        layer = next_layer
    return layer[0]


@dataclass
class Block:
    index: int
    timestamp: float
    transactions: List[EvidenceTransaction]
    previous_hash: str
    nonce: int = 0
    difficulty: int = 4
    miner: str = "system"
    hash: str = field(default="", init=False)
    merkle_root: str = field(default="", init=False)

    def __post_init__(self) -> None:
        tx_hashes = [tx.calculate_hash() for tx in self.transactions]
        self.merkle_root = merkle_root(tx_hashes)
        if not self.hash:
            self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_header = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "miner": self.miner,
            "tx_count": len(self.transactions),
        }
        encoded = json.dumps(block_header, sort_keys=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def mine(self, miner: str = "demo-miner") -> Dict[str, Any]:
        """Proof of Work: find nonce where hash starts with `difficulty` zeros."""
        self.miner = miner
        target = "0" * self.difficulty
        start = time.time()

        while True:
            self.hash = self.calculate_hash()
            if self.hash.startswith(target):
                elapsed = time.time() - start
                return {
                    "hash": self.hash,
                    "nonce": self.nonce,
                    "attempts": self.nonce + 1,
                    "elapsed_seconds": round(elapsed, 4),
                }
            self.nonce += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "miner": self.miner,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        transactions = [
            EvidenceTransaction.from_dict(item) for item in data.get("transactions", [])
        ]
        block = cls(
            index=data["index"],
            timestamp=data["timestamp"],
            transactions=transactions,
            previous_hash=data["previous_hash"],
            nonce=data.get("nonce", 0),
            difficulty=data.get("difficulty", 4),
            miner=data.get("miner", "system"),
        )
        block.merkle_root = data.get("merkle_root", block.merkle_root)
        block.hash = data.get("hash", block.calculate_hash())
        return block
