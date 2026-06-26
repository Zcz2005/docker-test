-- GreenChain 区块链溯源项目 - 数据库初始化

CREATE TABLE IF NOT EXISTS product_batches (
    id              SERIAL PRIMARY KEY,
    batch_id        VARCHAR(64)  NOT NULL UNIQUE,
    product_name    VARCHAR(128) NOT NULL,
    category        VARCHAR(64)  NOT NULL DEFAULT '蔬菜',
    quantity        DECIMAL(12,2) NOT NULL,
    unit            VARCHAR(16)  NOT NULL DEFAULT 'kg',
    status          VARCHAR(32)  NOT NULL DEFAULT 'CREATED',
    operator        VARCHAR(64),
    description     TEXT,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trace_records (
    id              SERIAL PRIMARY KEY,
    record_id       VARCHAR(64)  NOT NULL UNIQUE,
    batch_id        VARCHAR(64)  NOT NULL REFERENCES product_batches(batch_id),
    stage           VARCHAR(32)  NOT NULL,
    action          TEXT         NOT NULL,
    operator        VARCHAR(64),
    location        VARCHAR(256),
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- 区块链区块持久化表（链下镜像 + 快速查询）
CREATE TABLE IF NOT EXISTS blocks (
    id              SERIAL PRIMARY KEY,
    block_index     INT          NOT NULL UNIQUE,
    timestamp       BIGINT       NOT NULL,
    data            JSONB        NOT NULL,
    previous_hash   VARCHAR(64)  NOT NULL,
    hash            VARCHAR(64)  NOT NULL UNIQUE,
    nonce           INT          NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(64)  NOT NULL UNIQUE,
    password_hash   VARCHAR(256) NOT NULL,
    role            VARCHAR(32)  NOT NULL DEFAULT 'operator',
    org_name        VARCHAR(128),
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trace_batch ON trace_records(batch_id);
CREATE INDEX IF NOT EXISTS idx_blocks_hash ON blocks(hash);
CREATE INDEX IF NOT EXISTS idx_batch_status ON product_batches(status);

-- 示例数据
INSERT INTO product_batches (batch_id, product_name, category, quantity, unit, status, operator, description)
VALUES ('GC-DEMO-001', '有机番茄', '蔬菜', 100, 'kg', 'CREATED', '张农户', '学习用示例批次')
ON CONFLICT (batch_id) DO NOTHING;
