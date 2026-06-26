import hashlib
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from blockchain.transaction import EvidenceTransaction, TransactionType
from services import (
    CustodyTransferRequest,
    EvidenceSubmitRequest,
    HashFileMeta,
    MineRequest,
    NotarySealRequest,
    blockchain,
    seed_demo_data,
)

app = FastAPI(
    title="电子证据区块链存证平台",
    description="南方公证 · 区块链电子证据存证与溯源演示系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.on_event("startup")
def on_startup() -> None:
    seed_demo_data()


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "evidence-blockchain"}


@app.get("/api/chain/summary")
def chain_summary() -> Dict[str, Any]:
    return blockchain.get_chain_summary()


@app.get("/api/chain/validate")
def validate_chain() -> Dict[str, Any]:
    valid, errors = blockchain.is_chain_valid()
    return {"is_valid": valid, "errors": errors}


@app.get("/api/chain/blocks")
def list_blocks() -> Dict[str, Any]:
    return {"blocks": blockchain.get_all_blocks(), "count": len(blockchain.chain)}


@app.get("/api/chain/blocks/{index}")
def get_block(index: int) -> Dict[str, Any]:
    block = blockchain.get_block(index)
    if not block:
        raise HTTPException(status_code=404, detail="区块不存在")
    return block


@app.get("/api/chain/pending")
def pending_transactions() -> Dict[str, Any]:
    return {
        "pending": [tx.to_dict() for tx in blockchain.pending_transactions],
        "count": len(blockchain.pending_transactions),
    }


@app.post("/api/chain/mine")
def mine_block(request: MineRequest) -> Dict[str, Any]:
    try:
        return blockchain.mine_pending_transactions(request.miner)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/evidence/submit")
def submit_evidence(request: EvidenceSubmitRequest) -> Dict[str, Any]:
    tx = EvidenceTransaction(
        tx_type=TransactionType.EVIDENCE_SUBMIT,
        tx_id="",
        evidence_hash=request.evidence_hash,
        case_num=request.case_num,
        task_id=request.task_id,
        submitter=request.submitter,
        platform=request.platform,
        file_name=request.file_name,
        file_size=request.file_size,
        metadata={
            "screen_start_time": request.screen_start_time,
            "screen_end_time": request.screen_end_time,
            "room_id": request.room_id,
            "title": request.title,
        },
    )
    tx.sign()
    tx_id = blockchain.add_transaction(tx)
    return {
        "message": "证据交易已加入待打包池",
        "tx_id": tx_id,
        "evidence_hash": request.evidence_hash,
        "pending_count": len(blockchain.pending_transactions),
    }


@app.post("/api/evidence/custody")
def custody_transfer(request: CustodyTransferRequest) -> Dict[str, Any]:
    tx = EvidenceTransaction(
        tx_type=TransactionType.CUSTODY_TRANSFER,
        tx_id="",
        evidence_hash=request.evidence_hash.strip().lower(),
        case_num=request.case_num,
        task_id=request.task_id,
        submitter=request.from_party,
        platform="Custody",
        file_name="custody-record",
        file_size=0,
        metadata={
            "from_party": request.from_party,
            "to_party": request.to_party,
            "reason": request.reason,
        },
    )
    tx.sign()
    tx_id = blockchain.add_transaction(tx)
    return {"message": "保管转移记录已创建", "tx_id": tx_id}


@app.post("/api/evidence/notary")
def notary_seal(request: NotarySealRequest) -> Dict[str, Any]:
    tx = EvidenceTransaction(
        tx_type=TransactionType.NOTARY_SEAL,
        tx_id="",
        evidence_hash=request.evidence_hash.strip().lower(),
        case_num=request.case_num,
        task_id=request.task_id,
        submitter=request.notary_office,
        platform="Notary",
        file_name="notary-certificate",
        file_size=0,
        metadata={
            "notary_office": request.notary_office,
            "certificate_no": request.certificate_no or f"NF-GZ-{request.case_num}",
            "legal_effect": "电子数据保管证明",
        },
    )
    tx.sign()
    tx_id = blockchain.add_transaction(tx)
    return {"message": "公证封印记录已创建", "tx_id": tx_id}


@app.get("/api/evidence/verify/{evidence_hash}")
def verify_evidence(evidence_hash: str) -> Dict[str, Any]:
    normalized = evidence_hash.strip().lower()
    records = blockchain.find_evidence(normalized)
    if not records:
        return {
            "found": False,
            "evidence_hash": normalized,
            "message": "链上未找到该证据哈希，可能尚未上链或哈希不匹配",
        }

    submit_records = [
        r for r in records if r["transaction"]["tx_type"] == "evidence_submit"
    ]
    return {
        "found": True,
        "evidence_hash": normalized,
        "on_chain_count": len(records),
        "first_seen": submit_records[0] if submit_records else records[0],
        "all_records": records,
        "chain_valid": blockchain.is_chain_valid()[0],
    }


@app.get("/api/case/{case_num}/timeline")
def case_timeline(case_num: str) -> Dict[str, Any]:
    timeline = blockchain.get_custody_timeline(case_num)
    return {"case_num": case_num, "events": timeline, "count": len(timeline)}


@app.post("/api/tools/hash")
def compute_hash(meta: HashFileMeta) -> Dict[str, str]:
    content = meta.simulated_content or f"demo-file:{meta.file_name}:{meta.file_name.encode()}"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return {
        "file_name": meta.file_name,
        "sha256": digest,
        "algorithm": "SHA-256",
    }


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
