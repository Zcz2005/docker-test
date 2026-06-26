import { Router } from 'express';
import * as traceService from '../services/traceService.js';
import * as db from '../db/repository.js';

const router = Router();

// 健康检查
router.get('/health', async (req, res) => {
  try {
    await db.query('SELECT 1');
    res.json({ status: 'ok', database: 'connected', timestamp: new Date().toISOString() });
  } catch (err) {
    res.status(503).json({ status: 'error', database: 'disconnected', message: err.message });
  }
});

// 系统统计
router.get('/stats', async (req, res) => {
  const stats = await db.getStats();
  const chain = traceService.getChain();
  const validation = await traceService.verifyChain();
  res.json({ ...stats, chainLength: chain.length, chainValid: validation.valid });
});

// 创建产品批次（写入数据库 + 上链）
router.post('/batches', async (req, res) => {
  try {
    const result = await traceService.createProductBatch(req.body);
    res.status(201).json({ code: 0, message: '批次创建成功并已上链', data: result });
  } catch (err) {
    res.status(400).json({ code: 40001, message: err.message });
  }
});

// 批次列表
router.get('/batches', async (req, res) => {
  const batches = await db.listBatches();
  res.json({ code: 0, data: batches });
});

// 批次详情
router.get('/batches/:batchId', async (req, res) => {
  const batch = await db.getBatch(req.params.batchId);
  if (!batch) return res.status(404).json({ code: 404, message: '批次不存在' });
  res.json({ code: 0, data: batch });
});

// 添加溯源记录（写入数据库 + 上链）
router.post('/traces', async (req, res) => {
  try {
    const result = await traceService.addTraceRecord(req.body);
    res.status(201).json({ code: 0, message: '溯源记录已添加并上链', data: result });
  } catch (err) {
    res.status(400).json({ code: 40002, message: err.message });
  }
});

// 完整溯源查询（数据库 + 区块链双重验证）
router.get('/trace/:batchId', async (req, res) => {
  const trace = await traceService.getFullTrace(req.params.batchId);
  if (!trace) return res.status(404).json({ code: 404, message: '批次不存在' });
  res.json({ code: 0, data: trace });
});

// 获取完整区块链
router.get('/chain', (req, res) => {
  res.json({ code: 0, data: traceService.getChain() });
});

// 验证区块链完整性
router.get('/chain/verify', async (req, res) => {
  const result = await traceService.verifyChain();
  res.json({ code: 0, data: result });
});

export default router;
