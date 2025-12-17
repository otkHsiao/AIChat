# AI Chat API 规范文档

## 基础信息

- **Base URL**: `https://app-ai-chat-be.azurewebsites.net/api`
- **版本**: v1
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

### 错误码列表

| 错误码 | HTTP 状态码 | 描述 |
|--------|------------|------|
| UNAUTHORIZED | 401 | 未认证或 Token 无效 |
| FORBIDDEN | 403 | 无权限访问 |
| NOT_FOUND | 404 | 资源不存在 |
| VALIDATION_ERROR | 422 | 请求参数验证失败 |
| RATE_LIMIT_EXCEEDED | 429 | 请求过于频繁 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

---

## 认证 API

### 用户注册

**POST** `/auth/register`

注册新用户账户。

**请求体**:

```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| email | string | 是 | 有效邮箱格式 |
| username | string | 是 | 3-50 字符，字母数字下划线 |
| password | string | 是 | 最少 8 字符，包含大小写和数字 |

**成功响应** (201):

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-xxx",
      "email": "user@example.com",
      "username": "johndoe",
      "createdAt": "2024-12-17T08:00:00Z"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 86400
  }
}
```

**错误响应**:

- `422` - 邮箱或用户名已存在

---

### 用户登录

**POST** `/auth/login`

使用邮箱和密码登录。

**请求体**:

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-xxx",
      "email": "user@example.com",
      "username": "johndoe"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 86400
  }
}
```

**错误响应**:

- `401` - 邮箱或密码错误

---

### 刷新 Token

**POST** `/auth/refresh`

使用 Refresh Token 获取新的 Access Token。

**请求体**:

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 86400
  }
}
```

---

### 获取当前用户

**GET** `/auth/me`

获取当前登录用户信息。

**请求头**:

```
Authorization: Bearer <accessToken>
```

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "id": "uuid-xxx",
    "email": "user@example.com",
    "username": "johndoe",
    "createdAt": "2024-12-17T08:00:00Z",
    "settings": {
      "defaultModel": "gpt-4o",
      "theme": "light"
    }
  }
}
```

---

## 会话 API

### 获取会话列表

**GET** `/conversations`

获取当前用户的所有会话。

**请求头**:

```
Authorization: Bearer <accessToken>
```

**查询参数**:

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| limit | number | 20 | 返回数量限制 |
| offset | number | 0 | 偏移量 |
| sort | string | updatedAt | 排序字段 |
| order | string | desc | 排序方向 |

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": "conv-uuid-xxx",
        "title": "Python 编程问题",
        "systemPrompt": "你是一个专业的 Python 开发者...",
        "model": "gpt-4o",
        "messageCount": 15,
        "createdAt": "2024-12-17T08:00:00Z",
        "updatedAt": "2024-12-17T10:30:00Z"
      }
    ],
    "total": 25,
    "limit": 20,
    "offset": 0
  }
}
```

---

### 创建新会话

**POST** `/conversations`

创建一个新的聊天会话。

**请求头**:

```
Authorization: Bearer <accessToken>
```

**请求体**:

```json
{
  "title": "新对话",
  "systemPrompt": "你是一个有帮助的 AI 助手。",
  "model": "gpt-4o"
}
```

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| title | string | 否 | "新对话" | 会话标题 |
| systemPrompt | string | 否 | 默认提示 | 系统提示词 |
| model | string | 否 | "gpt-4o" | 使用的模型 |

**成功响应** (201):

```json
{
  "success": true,
  "data": {
    "id": "conv-uuid-xxx",
    "title": "新对话",
    "systemPrompt": "你是一个有帮助的 AI 助手。",
    "model": "gpt-4o",
    "messageCount": 0,
    "createdAt": "2024-12-17T08:00:00Z",
    "updatedAt": "2024-12-17T08:00:00Z"
  }
}
```

---

### 获取会话详情

**GET** `/conversations/{conversationId}`

获取指定会话的详细信息。

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| conversationId | string | 会话 ID |

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "id": "conv-uuid-xxx",
    "title": "Python 编程问题",
    "systemPrompt": "你是一个专业的 Python 开发者...",
    "model": "gpt-4o",
    "messageCount": 15,
    "createdAt": "2024-12-17T08:00:00Z",
    "updatedAt": "2024-12-17T10:30:00Z"
  }
}
```

---

### 更新会话

**PUT** `/conversations/{conversationId}`

更新会话信息（标题、系统提示等）。

**请求体**:

```json
{
  "title": "更新后的标题",
  "systemPrompt": "更新后的系统提示"
}
```

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "id": "conv-uuid-xxx",
    "title": "更新后的标题",
    "systemPrompt": "更新后的系统提示",
    "updatedAt": "2024-12-17T11:00:00Z"
  }
}
```

---

### 删除会话

**DELETE** `/conversations/{conversationId}`

删除指定会话及其所有消息。

**成功响应** (200):

```json
{
  "success": true,
  "message": "会话已删除"
}
```

---

## 聊天 API

### 获取消息历史

**GET** `/conversations/{conversationId}/messages`

获取指定会话的消息历史。

**查询参数**:

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| limit | number | 50 | 返回数量限制 |
| before | string | - | 获取此 ID 之前的消息 |

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "msg-uuid-xxx",
        "role": "user",
        "content": "请帮我解释一下 Python 的装饰器",
        "attachments": [],
        "createdAt": "2024-12-17T08:00:00Z"
      },
      {
        "id": "msg-uuid-yyy",
        "role": "assistant",
        "content": "Python 装饰器是一种设计模式...",
        "tokens": {
          "input": 150,
          "output": 500
        },
        "createdAt": "2024-12-17T08:00:05Z"
      }
    ],
    "hasMore": true
  }
}
```

---

### 发送消息（非流式）

**POST** `/conversations/{conversationId}/messages`

发送消息并等待完整响应。

**请求体**:

```json
{
  "content": "请帮我解释一下 Python 的装饰器",
  "attachments": [
    {
      "id": "file-uuid-xxx",
      "type": "image"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| content | string | 是 | 消息内容 |
| attachments | array | 否 | 附件列表 |

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "userMessage": {
      "id": "msg-uuid-xxx",
      "role": "user",
      "content": "请帮我解释一下 Python 的装饰器",
      "createdAt": "2024-12-17T08:00:00Z"
    },
    "assistantMessage": {
      "id": "msg-uuid-yyy",
      "role": "assistant",
      "content": "Python 装饰器是一种设计模式...",
      "tokens": {
        "input": 150,
        "output": 500
      },
      "createdAt": "2024-12-17T08:00:05Z"
    }
  }
}
```

---

### 发送消息（流式）

**POST** `/conversations/{conversationId}/messages/stream`

发送消息并获取流式响应 (Server-Sent Events)。

**请求体**:

```json
{
  "content": "请帮我解释一下 Python 的装饰器",
  "attachments": []
}
```

**响应类型**: `text/event-stream`

**SSE 事件格式**:

```
event: message_start
data: {"messageId": "msg-uuid-yyy"}

event: content_delta
data: {"delta": "Python "}

event: content_delta
data: {"delta": "装饰器是"}

event: content_delta
data: {"delta": "一种设计模式..."}

event: message_end
data: {"tokens": {"input": 150, "output": 500}}
```

**事件类型**:

| 事件 | 描述 |
|------|------|
| message_start | 消息开始，包含消息 ID |
| content_delta | 内容片段 |
| message_end | 消息结束，包含 Token 统计 |
| error | 错误发生 |

---

## 文件 API

### 上传文件

**POST** `/files/upload`

上传图片或文件。

**请求头**:

```
Content-Type: multipart/form-data
Authorization: Bearer <accessToken>
```

**表单字段**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| file | File | 是 | 要上传的文件 |
| type | string | 否 | 文件类型: image/file |

**文件限制**:

- 图片: jpg, png, gif, webp (最大 10MB)
- 文件: pdf, txt, md, doc, docx (最大 20MB)

**成功响应** (201):

```json
{
  "success": true,
  "data": {
    "id": "file-uuid-xxx",
    "fileName": "screenshot.png",
    "type": "image",
    "mimeType": "image/png",
    "size": 1048576,
    "url": "https://stgaichat.blob.core.windows.net/uploads/xxx.png?sv=...",
    "createdAt": "2024-12-17T08:00:00Z"
  }
}
```

---

### 获取文件信息

**GET** `/files/{fileId}`

获取已上传文件的信息和访问 URL。

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "id": "file-uuid-xxx",
    "fileName": "screenshot.png",
    "type": "image",
    "mimeType": "image/png",
    "size": 1048576,
    "url": "https://stgaichat.blob.core.windows.net/uploads/xxx.png?sv=...",
    "createdAt": "2024-12-17T08:00:00Z"
  }
}
```

---

### 删除文件

**DELETE** `/files/{fileId}`

删除已上传的文件。

**成功响应** (200):

```json
{
  "success": true,
  "message": "文件已删除"
}
```

---

## 用户设置 API

### 更新用户设置

**PUT** `/users/settings`

更新当前用户的偏好设置。

**请求体**:

```json
{
  "defaultModel": "gpt-4o-mini",
  "theme": "dark"
}
```

**成功响应** (200):

```json
{
  "success": true,
  "data": {
    "defaultModel": "gpt-4o-mini",
    "theme": "dark"
  }
}
```

---

### 修改密码

**PUT** `/users/password`

修改当前用户的密码。

**请求体**:

```json
{
  "currentPassword": "OldPass123!",
  "newPassword": "NewPass456!"
}
```

**成功响应** (200):

```json
{
  "success": true,
  "message": "密码已更新"
}
```

**错误响应**:

- `401` - 当前密码错误

---

## WebSocket 支持 (可选)

如果需要更好的实时体验，可以使用 WebSocket：

**连接**: `wss://app-ai-chat-be.azurewebsites.net/ws`

**认证**: 在连接时通过查询参数传递 Token

```
wss://app-ai-chat-be.azurewebsites.net/ws?token=<accessToken>
```

**消息格式**:

```json
{
  "type": "send_message",
  "data": {
    "conversationId": "conv-uuid-xxx",
    "content": "你好"
  }
}
```

---

## 速率限制

| 端点 | 限制 |
|------|------|
| 认证相关 | 10 次/分钟 |
| 聊天消息 | 20 次/分钟 |
| 文件上传 | 10 次/分钟 |
| 其他 API | 60 次/分钟 |

超过限制时返回 `429 Too Many Requests`。

---

*文档版本：1.0*
*创建时间：2024-12-17*