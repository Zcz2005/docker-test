import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { query } from './pool.js';

export { query };

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export async function initDatabase() {
  const sqlPath = path.resolve(__dirname, '../../../sql/init.sql');
  const sql = fs.readFileSync(sqlPath, 'utf8');
  await query(sql);
  console.log('✅ 数据库表初始化完成');
}

export async function saveBlock(block) {
  const json = block.toJSON ? block.toJSON() : block;
  await query(
    `INSERT INTO blocks (block_index, timestamp, data, previous_hash, hash, nonce)
     VALUES ($1, $2, $3, $4, $5, $6)
     ON CONFLICT (block_index) DO NOTHING`,
    [
      json.index,
      json.timestamp,
      JSON.stringify(json.data),
      json.previousHash,
      json.hash,
      json.nonce,
    ]
  );
}

export async function loadBlocks() {
  const result = await query(
    'SELECT block_index, timestamp, data, previous_hash, hash, nonce FROM blocks ORDER BY block_index ASC'
  );
  return result.rows.map((row) => ({
    block_index: row.block_index,
    timestamp: row.timestamp,
    data: typeof row.data === 'string' ? JSON.parse(row.data) : row.data,
    previous_hash: row.previous_hash,
    hash: row.hash,
    nonce: row.nonce,
  }));
}

export async function createBatch(batch) {
  const result = await query(
    `INSERT INTO product_batches (batch_id, product_name, category, quantity, unit, operator, description)
     VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *`,
    [
      batch.batchId,
      batch.productName,
      batch.category || '蔬菜',
      batch.quantity,
      batch.unit || 'kg',
      batch.operator || '系统',
      batch.description || '',
    ]
  );
  return result.rows[0];
}

export async function getBatch(batchId) {
  const result = await query('SELECT * FROM product_batches WHERE batch_id = $1', [batchId]);
  return result.rows[0];
}

export async function listBatches() {
  const result = await query('SELECT * FROM product_batches ORDER BY created_at DESC');
  return result.rows;
}

export async function updateBatchStatus(batchId, status) {
  await query('UPDATE product_batches SET status = $1 WHERE batch_id = $2', [status, batchId]);
}

export async function createTraceRecord(record) {
  const result = await query(
    `INSERT INTO trace_records (record_id, batch_id, stage, action, operator, location)
     VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
    [
      record.recordId,
      record.batchId,
      record.stage,
      record.action,
      record.operator || '系统',
      record.location || '',
    ]
  );
  return result.rows[0];
}

export async function getTraceRecords(batchId) {
  const result = await query(
    'SELECT * FROM trace_records WHERE batch_id = $1 ORDER BY created_at ASC',
    [batchId]
  );
  return result.rows;
}

export async function getStats() {
  const batches = await query('SELECT COUNT(*) FROM product_batches');
  const traces = await query('SELECT COUNT(*) FROM trace_records');
  const blocks = await query('SELECT COUNT(*) FROM blocks');
  return {
    batchCount: Number(batches.rows[0].count),
    traceCount: Number(traces.rows[0].count),
    blockCount: Number(blocks.rows[0].count),
  };
}
