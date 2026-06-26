# docker-test

Monorepo containing:

- **blockchain-demo/** — 电子证据区块链存证演示平台（网站 + API + 区块链引擎）
- See [blockchain-demo/README.md](blockchain-demo/README.md) for details.

## Quick Start (Blockchain Demo)

```bash
cd blockchain-demo
pip install -r requirements.txt
cd backend && python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000
