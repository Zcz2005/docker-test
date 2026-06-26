import crypto from 'crypto';

/**
 * 区块：区块链的基本组成单元
 * 每个区块包含业务数据、时间戳、前一区块哈希和本区块哈希
 */
export class Block {
  constructor(index, data, previousHash = '0') {
    this.index = index;
    this.timestamp = Date.now();
    this.data = data;
    this.previousHash = previousHash;
    this.nonce = 0;
    this.hash = this.calculateHash();
  }

  calculateHash() {
    return crypto
      .createHash('sha256')
      .update(
        this.index +
          this.previousHash +
          this.timestamp +
          JSON.stringify(this.data) +
          this.nonce
      )
      .digest('hex');
  }

  /**
   * 简单工作量证明（学习用，难度较低）
   * 找到使哈希前 difficulty 位为 0 的 nonce
   */
  mineBlock(difficulty) {
    const target = '0'.repeat(difficulty);
    while (!this.hash.startsWith(target)) {
      this.nonce++;
      this.hash = this.calculateHash();
    }
  }

  toJSON() {
    return {
      index: this.index,
      timestamp: this.timestamp,
      data: this.data,
      previousHash: this.previousHash,
      hash: this.hash,
      nonce: this.nonce,
    };
  }
}
