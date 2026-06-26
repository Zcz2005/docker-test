import { Block } from './Block.js';

/**
 * 区块链：由多个区块按顺序链接组成的不可篡改账本
 */
export class Blockchain {
  constructor(difficulty = 2) {
    this.chain = [this.createGenesisBlock()];
    this.difficulty = difficulty;
    this.pendingTransactions = [];
  }

  createGenesisBlock() {
    return new Block(0, { message: '绿链溯源创世区块 GreenChain Genesis' }, '0');
  }

  getLatestBlock() {
    return this.chain[this.chain.length - 1];
  }

  /**
   * 添加新的溯源记录（打包成区块并挖矿）
   */
  addBlock(data) {
    const newBlock = new Block(
      this.chain.length,
      data,
      this.getLatestBlock().hash
    );
    newBlock.mineBlock(this.difficulty);
    this.chain.push(newBlock);
    return newBlock;
  }

  /**
   * 验证整条链的完整性
   */
  isChainValid() {
    for (let i = 1; i < this.chain.length; i++) {
      const current = this.chain[i];
      const previous = this.chain[i - 1];

      if (current.hash !== current.calculateHash()) {
        return { valid: false, reason: `区块 #${i} 哈希被篡改` };
      }
      if (current.previousHash !== previous.hash) {
        return { valid: false, reason: `区块 #${i} 链接断裂` };
      }
      const target = '0'.repeat(this.difficulty);
      if (!current.hash.startsWith(target)) {
        return { valid: false, reason: `区块 #${i} 工作量证明无效` };
      }
    }
    return { valid: true, reason: '链完整性验证通过' };
  }

  /**
   * 按批次 ID 查询溯源记录
   */
  getTracesByBatchId(batchId) {
    return this.chain
      .filter((block) => block.data?.batchId === batchId)
      .map((block) => ({
        blockIndex: block.index,
        hash: block.hash,
        timestamp: block.timestamp,
        ...block.data,
      }));
  }

  getChain() {
    return this.chain.map((b) => (b.toJSON ? b.toJSON() : b));
  }

  /**
   * 从数据库加载的区块数据恢复链
   */
  loadChain(blocks) {
    if (!blocks.length) {
      this.chain = [this.createGenesisBlock()];
      return;
    }
    this.chain = blocks.map((b) => {
      const block = new Block(b.block_index, b.data, b.previous_hash);
      block.timestamp = Number(b.timestamp);
      block.nonce = b.nonce;
      block.hash = b.hash;
      return block;
    });
  }
}
