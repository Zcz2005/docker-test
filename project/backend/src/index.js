import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import apiRouter from './routes/api.js';
import { initDatabase } from './db/repository.js';
import { initBlockchain } from './services/traceService.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

app.use('/api', apiRouter);

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

async function start() {
  const maxRetries = 10;
  for (let i = 0; i < maxRetries; i++) {
    try {
      await initDatabase();
      await initBlockchain();
      break;
    } catch (err) {
      console.log(`等待数据库就绪... (${i + 1}/${maxRetries})`);
      if (i === maxRetries - 1) throw err;
      await new Promise((r) => setTimeout(r, 3000));
    }
  }

  app.listen(PORT, () => {
    console.log(`\n🚀 GreenChain 区块链溯源服务已启动`);
    console.log(`   前端界面: http://localhost:${PORT}`);
    console.log(`   API 文档: http://localhost:${PORT}/api/health\n`);
  });
}

start().catch((err) => {
  console.error('启动失败:', err);
  process.exit(1);
});
