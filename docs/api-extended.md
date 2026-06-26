# GreenChain API 扩展接口文档

## Webhook 回调

| 事件 | 回调 URL | Payload |
|------|----------|---------|
| batch.created | POST {org_webhook_url} | `{event, batchId, status, timestamp}` |
| chain.tx.committed | POST {org_webhook_url} | `{event, txId, blockNumber, refId}` |
| iot.alert | POST {org_webhook_url} | `{event, batchId, alertType, value}` |
| recall.initiated | POST {org_webhook_url} | `{event, batchId, reason, affectedCount}` |

## 分页规范

```json
GET /api/v1/batches?page=1&size=20&status=ON_SHELF&sort=created_at,desc

{
  "code": 0,
  "data": {
    "content": [...],
    "page": 1,
    "size": 20,
    "totalElements": 156,
    "totalPages": 8
  }
}
```

## 管理后台接口（额外 12 个）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/admin/organizations | 组织列表 |
| POST | /api/v1/admin/organizations | 创建组织 |
| GET | /api/v1/admin/users | 用户列表 |
| POST | /api/v1/admin/users | 创建用户 |
| PUT | /api/v1/admin/users/{id}/cert | 更新 Fabric 证书 |
| GET | /api/v1/admin/dashboard/stats | 仪表盘统计 |
| GET | /api/v1/admin/dashboard/trend | 溯源趋势图数据 |
| GET | /api/v1/admin/chain/status | 区块链网络状态 |
| GET | /api/v1/admin/chain/pending-tx | 待确认交易 |
| POST | /api/v1/admin/chain/retry/{txId} | 重试失败交易 |
| GET | /api/v1/admin/audit/logs | 审计日志 |
| GET | /api/v1/admin/system/health | 系统健康检查 |

## 文件上传接口

```
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: (binary)
refTable: trace_records
refId: TR-2026-00421-001

Response:
{
  "cid": "QmX7yK9p3mNw8Rt2xVb",
  "fileName": "harvest_photo.jpg",
  "fileSize": 245760,
  "mimeType": "image/jpeg"
}
```
