import json
import os
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from .block import Block, merkle_root
from .transaction import EvidenceTransaction, TransactionType


class Blockchain:
    """Permissioned evidence notarization blockchain with PoW and JSON persistence."""

    def __init__(
        self,
        data_file: Optional[str] = None,
        difficulty: int = 4,
        mining_reward_tx: bool = True,
    ) -> None:
        self.difficulty = difficulty
        self.mining_reward_tx = mining_reward_tx
        self.pending_transactions: List[EvidenceTransaction] = []
        self.chain: List[Block] = []
        self._lock = Lock()
        self.data_file = Path(data_file or "data/chain.json")
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        if self.data_file.exists():
            self._load()
        else:
            self._create_genesis_block()
            self._save()

    def _create_genesis_block(self) -> None:
        genesis_tx = EvidenceTransaction(
            tx_id="genesis-0000",
            tx_type=TransactionType.GENESIS,
            evidence_hash="0" * 64,
            case_num="GENESIS",
            task_id="GENESIS",
            submitter="Southnotary Chain",
            platform="System",
            file_name="genesis.block",
            file_size=0,
            metadata={
                "message": "南方公证电子证据区块链创世区块",
                "version": "1.0.0",
                "purpose": "电子证据存证与溯源",
            },
        )
        genesis_tx.sign()

        genesis = Block(
            index=0,
            timestamp=time.time(),
            transactions=[genesis_tx],
            previous_hash="0" * 64,
            difficulty=self.difficulty,
            miner="genesis",
        )
        genesis.mine("genesis-miner")
        self.chain.append(genesis)

    def _save(self) -> None:
        payload = {
            "difficulty": self.difficulty,
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "chain": [block.to_dict() for block in self.chain],
        }
        with open(self.data_file, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        with open(self.data_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.difficulty = payload.get("difficulty", self.difficulty)
        self.chain = [Block.from_dict(item) for item in payload.get("chain", [])]
        self.pending_transactions = [
            EvidenceTransaction.from_dict(item)
            for item in payload.get("pending_transactions", [])
        ]

        if not self.chain:
            self._create_genesis_block()

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, transaction: EvidenceTransaction) -> str:
        if not transaction.signature:
            transaction.sign()

        if not transaction.verify_signature():
            raise ValueError("交易签名验证失败")

        if transaction.tx_type != TransactionType.GENESIS:
            if len(transaction.evidence_hash) != 64:
                raise ValueError("证据哈希必须为 64 位 SHA-256 十六进制字符串")

        with self._lock:
            self.pending_transactions.append(transaction)
            self._save()
        return transaction.tx_id

    def mine_pending_transactions(self, miner: str = "demo-miner") -> Dict[str, Any]:
        with self._lock:
            if not self.pending_transactions:
                raise ValueError("没有待打包的交易")

            block = Block(
                index=len(self.chain),
                timestamp=time.time(),
                transactions=self.pending_transactions.copy(),
                previous_hash=self.last_block.hash,
                difficulty=self.difficulty,
            )
            mining_stats = block.mine(miner)
            self.chain.append(block)
            self.pending_transactions.clear()
            self._save()

        return {
            "block": block.to_dict(),
            "mining": mining_stats,
        }

    def is_chain_valid(self) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        if not self.chain:
            errors.append("链为空")
            return False, errors

        for index in range(1, len(self.chain)):
            current = self.chain[index]
            previous = self.chain[index - 1]

            if current.previous_hash != previous.hash:
                errors.append(f"区块 #{current.index} 的 previous_hash 不匹配")

            recalculated = current.calculate_hash()
            if current.hash != recalculated:
                errors.append(f"区块 #{current.index} 的哈希被篡改")

            if not current.hash.startswith("0" * current.difficulty):
                errors.append(f"区块 #{current.index} 不满足 PoW 难度要求")

            tx_hashes = [tx.calculate_hash() for tx in current.transactions]
            expected_merkle = merkle_root(tx_hashes)
            if current.merkle_root != expected_merkle:
                errors.append(f"区块 #{current.index} 的 Merkle Root 不匹配")

            for tx in current.transactions:
                if tx.tx_type != TransactionType.GENESIS and not tx.verify_signature():
                    errors.append(f"区块 #{current.index} 交易 {tx.tx_id} 签名无效")

        return len(errors) == 0, errors

    def find_evidence(self, evidence_hash: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.evidence_hash == evidence_hash:
                    results.append(
                        {
                            "transaction": tx.to_dict(),
                            "block_index": block.index,
                            "block_hash": block.hash,
                            "block_timestamp": block.timestamp,
                            "merkle_root": block.merkle_root,
                        }
                    )
        return results

    def get_chain_summary(self) -> Dict[str, Any]:
        valid, errors = self.is_chain_valid()
        evidence_count = sum(
            1
            for block in self.chain
            for tx in block.transactions
            if tx.tx_type == TransactionType.EVIDENCE_SUBMIT
        )
        return {
            "block_height": len(self.chain),
            "pending_transactions": len(self.pending_transactions),
            "difficulty": self.difficulty,
            "is_valid": valid,
            "validation_errors": errors,
            "latest_block_hash": self.last_block.hash,
            "evidence_count": evidence_count,
            "genesis_timestamp": self.chain[0].timestamp if self.chain else None,
        }

    def get_block(self, index: int) -> Optional[Dict[str, Any]]:
        if index < 0 or index >= len(self.chain):
            return None
        return self.chain[index].to_dict()

    def get_all_blocks(self) -> List[Dict[str, Any]]:
        return [block.to_dict() for block in self.chain]

    def get_custody_timeline(self, case_num: str) -> List[Dict[str, Any]]:
        timeline: List[Dict[str, Any]] = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.case_num == case_num:
                    timeline.append(
                        {
                            "tx_id": tx.tx_id,
                            "tx_type": tx.tx_type.value,
                            "evidence_hash": tx.evidence_hash,
                            "task_id": tx.task_id,
                            "submitter": tx.submitter,
                            "platform": tx.platform,
                            "timestamp": tx.timestamp,
                            "block_index": block.index,
                            "block_hash": block.hash,
                            "metadata": tx.metadata,
                        }
                    )
        timeline.sort(key=lambda item: item["timestamp"])
        return timeline
