-- GreenChain 绿链溯源 - PostgreSQL 核心表结构
-- 运行: psql -U greenchain -d greenchain -f sql/schema.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 组织
CREATE TABLE organizations (
    id              BIGSERIAL PRIMARY KEY,
    org_code        VARCHAR(32)  NOT NULL UNIQUE,
    name            VARCHAR(128) NOT NULL,
    org_type        VARCHAR(32)  NOT NULL,
    msp_id          VARCHAR(64)  NOT NULL UNIQUE,
    status          SMALLINT     DEFAULT 1,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- 用户
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    org_id          BIGINT       NOT NULL REFERENCES organizations(id),
    username        VARCHAR(64)  NOT NULL UNIQUE,
    password_hash   VARCHAR(256) NOT NULL,
    role            VARCHAR(32)  NOT NULL,
    did             VARCHAR(128),
    status          SMALLINT     DEFAULT 1,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- 产品批次（核心主表）
CREATE TABLE product_batches (
    id              BIGSERIAL PRIMARY KEY,
    batch_id        VARCHAR(64)  NOT NULL UNIQUE,
    product_name    VARCHAR(128) NOT NULL,
    category        VARCHAR(64)  NOT NULL,
    quantity        DECIMAL(12,2) NOT NULL,
    unit            VARCHAR(16)  NOT NULL DEFAULT 'kg',
    status          VARCHAR(32)  NOT NULL DEFAULT 'CREATED',
    parent_batch_id VARCHAR(64)  REFERENCES product_batches(batch_id),
    org_id          BIGINT       NOT NULL REFERENCES organizations(id),
    created_by      BIGINT       NOT NULL REFERENCES users(id),
    metadata_hash   VARCHAR(128),
    chain_tx_id     VARCHAR(128),
    chain_status    VARCHAR(16)  DEFAULT 'PENDING',
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_batch_status ON product_batches(status);
CREATE INDEX idx_batch_org ON product_batches(org_id);

-- 溯源记录
CREATE TABLE trace_records (
    id              BIGSERIAL PRIMARY KEY,
    record_id       VARCHAR(64)  NOT NULL UNIQUE,
    batch_id        VARCHAR(64)  NOT NULL REFERENCES product_batches(batch_id),
    stage           VARCHAR(32)  NOT NULL,
    action          VARCHAR(256) NOT NULL,
    operator_id     BIGINT       NOT NULL REFERENCES users(id),
    org_id          BIGINT       NOT NULL REFERENCES organizations(id),
    data_hash       VARCHAR(128) NOT NULL,
    chain_tx_id     VARCHAR(128),
    operated_at     TIMESTAMPTZ  NOT NULL,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_trace_batch ON trace_records(batch_id);

-- 区块链交易同步
CREATE TABLE blockchain_transactions (
    id              BIGSERIAL PRIMARY KEY,
    tx_id           VARCHAR(128) NOT NULL UNIQUE,
    chaincode       VARCHAR(64)  NOT NULL,
    function_name   VARCHAR(64)  NOT NULL,
    status          VARCHAR(16)  NOT NULL DEFAULT 'SUBMITTED',
    ref_table       VARCHAR(64),
    ref_id          VARCHAR(64),
    submitted_at    TIMESTAMPTZ  DEFAULT NOW(),
    committed_at    TIMESTAMPTZ
);

CREATE INDEX idx_bctx_ref ON blockchain_transactions(ref_table, ref_id);
