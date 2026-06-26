import { Blockchain } from '../blockchain/Blockchain.js';
import * as db from '../db/repository.js';

const STAGE_STATUS = {
  PLANTING: 'PLANTED',
  HARVESTING: 'HARVESTED',
  PROCESSING: 'PROCESSING',
  INSPECTION: 'INSPECTED',
  LOGISTICS: 'IN_TRANSIT',
  RETAIL: 'ON_SHELF',
};

let blockchain = new Blockchain(Number(process.env.MINING_DIFFICULTY || 2));

export async function initBlockchain() {
  const blocks = await db.loadBlocks();
  blockchain.loadChain(blocks);
  if (blocks.length === 0) {
    const genesis = blockchain.getLatestBlock();
    await db.saveBlock(genesis);
  }
  console.log(`⛓️  区块链已加载，当前 ${blockchain.chain.length} 个区块`);
  return blockchain;
}

export function getBlockchain() {
  return blockchain;
}

function generateId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
}

export async function createProductBatch(input) {
  const batchId = input.batchId || generateId('GC');
  const batch = await db.createBatch({ ...input, batchId });

  const blockData = {
    type: 'CREATE_BATCH',
    batchId: batch.batch_id,
    productName: batch.product_name,
    quantity: batch.quantity,
    operator: batch.operator,
    timestamp: new Date().toISOString(),
  };

  const block = blockchain.addBlock(blockData);
  await db.saveBlock(block);

  return { batch, block: block.toJSON() };
}

export async function addTraceRecord(input) {
  const batch = await db.getBatch(input.batchId);
  if (!batch) throw new Error(`批次 ${input.batchId} 不存在`);

  const recordId = generateId('TR');
  const record = await db.createTraceRecord({ ...input, recordId });

  const blockData = {
    type: 'ADD_TRACE',
    recordId,
    batchId: input.batchId,
    stage: input.stage,
    action: input.action,
    operator: input.operator,
    location: input.location,
    timestamp: new Date().toISOString(),
  };

  const block = blockchain.addBlock(blockData);
  await db.saveBlock(block);

  if (STAGE_STATUS[input.stage]) {
    await db.updateBatchStatus(input.batchId, STAGE_STATUS[input.stage]);
  }

  return { record, block: block.toJSON() };
}

export async function getFullTrace(batchId) {
  const batch = await db.getBatch(batchId);
  if (!batch) return null;

  const dbRecords = await db.getTraceRecords(batchId);
  const chainRecords = blockchain.getTracesByBatchId(batchId);
  const validation = blockchain.isChainValid();

  return {
    batch,
    dbRecords,
    chainRecords,
    blockCount: blockchain.chain.length,
    chainValid: validation.valid,
    validationMessage: validation.reason,
  };
}

export async function verifyChain() {
  return blockchain.isChainValid();
}

export function getChain() {
  return blockchain.getChain();
}
