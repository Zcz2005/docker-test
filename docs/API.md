# API 接口说明

本文档描述 `southnotary_uploader` 使用的南方公证处开放接口。

基础地址（默认）：

```
https://www.southnotary.cn/api
```

认证方式：除获取 Token 外，其余接口均需在 Header 中携带：

```
gdazh-Access-Authorization: <token>
```

---

## 1. 获取通用授权 Token

### 请求

```
GET /fh-evidence/openApi/v1/getCommAuthors
```

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| appid | string | 是 | 应用 ID |
| randkey | string | 是 | 随机 key |
| hashval | string | 是 | 签名哈希值 |

### 响应示例

```json
{
  "code": "200",
  "token": "eyJhbGciOi...",
  "expireAt": "2026-06-26 12:00:00",
  "message": "success"
}
```

### 代码位置

- `southnotary_uploader/api.py` → `EvidenceApiClient.get_token()`

### 注意事项

- 响应 `code` 可能是字符串 `"200"` 或数字 `200`，代码使用 `is_success_code()` 统一判断。
- Token 有效期由 `expireAt` 返回；当前实现每个工作周期会重新获取 Token。

---

## 2. 获取自动取证任务列表

### 请求

```
GET /fh-evidence/openApi/v1/getAutomatedForensics?type=1
```

Header：

```
gdazh-Access-Authorization: <token>
```

### 响应字段（data 数组元素）

| 字段 | 类型 | 说明 |
|------|------|------|
| taskId | string | 取证任务 ID（入库主键逻辑） |
| anchorId | string | 主播 ID |
| caseNum | string | 案号 |
| forensicType | string | 取证类型 |
| platform | string | 平台编号，见 `constants.PLATFORM_MAP` |
| roomId | string | 直播间 ID |
| title | string | 直播间标题 |
| url | string | 直播间地址 |

### 代码位置

- `EvidenceApiClient.get_automated_forensics()`
- `EvidenceTaskService.evidence_api_worker()`

---

## 3. 上传自动取证文件回调

### 请求

```
POST /fh-evidence/openApi/v1/uploadAutomatedForensicsFile
Content-Type: application/json; charset=utf-8
```

Body：

```json
{
  "obsPath": "evidenceProd/Casefile/File/2026-06-26/1719360000/video.mp4",
  "caseNum": "CASE-001",
  "taskId": "TASK-001",
  "screenStartTime": "2026-06-26 01:00:00",
  "screenEndTime": "2026-06-26 02:00:00",
  "hash": "sha256hex..."
}
```

| 字段 | 说明 |
|------|------|
| obsPath | OOS 对象 Key（非完整 URL） |
| caseNum | 案号 |
| taskId | 任务 ID |
| screenStartTime | 录屏开始时间 |
| screenEndTime | 录屏结束时间 |
| hash | 视频文件 SHA-256 |

### 成功响应

HTTP 200 且 JSON `code` 为 200。

### 特殊终态响应

HTTP 200，业务 `code=500`，`message` 为：

- `取证任务已结束！`
- `取证任务不存在！`

服务会将此类响应视为可结束重试，并更新 `upload=1`。

### 代码位置

- `EvidenceApiClient.upload_automated_forensics_file()`
- `EvidenceTaskService._upload_one_completed_task()`

---

## 4. 平台编号映射

| platform | appname |
|----------|---------|
| 3 | Douyin |
| 5 | Kuaishou |
| 7 | Ailiao |
| 11 | Huajiao |
| 12 | Yingke |
| 14 | Lespark |
| 17 | Mifeng |
| 18 | Momo |
| 21 | Xiaohongshu |
| 22 | Xiuse |
| 24 | Baobao |
| 27 | Kelakela |
| 33 | Aichang |
| 36 | Lingsheng |
| 43 | Hongguo |

完整定义见 `southnotary_uploader/constants.py`。
