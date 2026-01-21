# Portfolio Backend API Specification

Base URL: `https://api.yourdomain.com/v1`

---

## Authentication

管理員操作（新增、修改、刪除）需要 JWT Token 驗證。

```
Authorization: Bearer <jwt_token>
```

公開 API（GET 請求）不需要驗證。

---

## 1. LabNotes API（技術文章系統）

### Data Model

```typescript
interface LabNote {
  id: string                    // UUID
  title: string                 // 文章標題
  slug: string                  // URL-friendly 識別碼 (e.g., "building-rag-system")
  excerpt: string               // 摘要（用於列表顯示）
  content: string               // 完整內容（Markdown 格式）
  tags: string[]                // 標籤陣列
  readTime: string              // 閱讀時間 (e.g., "5 min read")
  date: string                  // 發布日期 ISO 8601 (e.g., "2024-12-15")
  published: boolean            // 是否發布
  createdAt: string             // 建立時間 ISO 8601
  updatedAt: string             // 更新時間 ISO 8601
}
```

### Endpoints

#### GET /lab-notes
取得所有已發布的文章列表（不含完整內容）

**Query Parameters:**
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| tag       | string | No       | 依標籤篩選 |
| limit     | number | No       | 回傳數量（預設 10）|
| offset    | number | No       | 分頁偏移量（預設 0）|

**Response 200:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Building a Production RAG System",
      "slug": "building-production-rag-system",
      "excerpt": "Learn how to build a scalable RAG system...",
      "tags": ["RAG", "LlamaIndex", "Python"],
      "readTime": "8 min read",
      "date": "2024-12-15",
      "createdAt": "2024-12-15T10:30:00Z",
      "updatedAt": "2024-12-16T08:00:00Z"
    }
  ],
  "pagination": {
    "total": 25,
    "limit": 10,
    "offset": 0,
    "hasMore": true
  }
}
```

---

#### GET /lab-notes/:slug
取得單篇文章完整內容

**Response 200:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Building a Production RAG System",
    "slug": "building-production-rag-system",
    "excerpt": "Learn how to build a scalable RAG system...",
    "content": "# Building a Production RAG System\n\n## Introduction\n\nRAG (Retrieval-Augmented Generation) is...",
    "tags": ["RAG", "LlamaIndex", "Python"],
    "readTime": "8 min read",
    "date": "2024-12-15",
    "published": true,
    "createdAt": "2024-12-15T10:30:00Z",
    "updatedAt": "2024-12-16T08:00:00Z"
  }
}
```

**Response 404:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Lab note not found"
  }
}
```

---

#### POST /lab-notes 🔒
新增文章（需要認證）

**Request Body:**
```json
{
  "title": "Building a Production RAG System",
  "slug": "building-production-rag-system",
  "excerpt": "Learn how to build a scalable RAG system...",
  "content": "# Building a Production RAG System\n\n...",
  "tags": ["RAG", "LlamaIndex", "Python"],
  "readTime": "8 min read",
  "date": "2024-12-15",
  "published": false
}
```

**Response 201:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Building a Production RAG System",
    "slug": "building-production-rag-system",
    "excerpt": "Learn how to build a scalable RAG system...",
    "content": "# Building a Production RAG System\n\n...",
    "tags": ["RAG", "LlamaIndex", "Python"],
    "readTime": "8 min read",
    "date": "2024-12-15",
    "published": false,
    "createdAt": "2024-12-15T10:30:00Z",
    "updatedAt": "2024-12-15T10:30:00Z"
  }
}
```

**Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      { "field": "title", "message": "Title is required" },
      { "field": "slug", "message": "Slug already exists" }
    ]
  }
}
```

---

#### PUT /lab-notes/:id 🔒
更新文章（需要認證）

**Request Body:**（部分更新，只傳需要修改的欄位）
```json
{
  "title": "Updated Title",
  "content": "Updated content...",
  "published": true
}
```

**Response 200:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Updated Title",
    "slug": "building-production-rag-system",
    "excerpt": "Learn how to build a scalable RAG system...",
    "content": "Updated content...",
    "tags": ["RAG", "LlamaIndex", "Python"],
    "readTime": "8 min read",
    "date": "2024-12-15",
    "published": true,
    "createdAt": "2024-12-15T10:30:00Z",
    "updatedAt": "2024-12-17T14:20:00Z"
  }
}
```

---

#### DELETE /lab-notes/:id 🔒
刪除文章（需要認證）

**Response 204:** No Content

**Response 404:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Lab note not found"
  }
}
```

---

## 2. Contact API（聯絡表單）

### Data Model

```typescript
interface ContactMessage {
  id: string              // UUID
  name: string            // 寄件者姓名
  email: string           // 寄件者 Email
  subject: string         // 主旨
  message: string         // 訊息內容
  read: boolean           // 是否已讀
  replied: boolean        // 是否已回覆
  createdAt: string       // 建立時間 ISO 8601
}
```

### Endpoints

#### POST /contact
提交聯絡訊息（公開，不需認證）

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Collaboration Opportunity",
  "message": "Hi, I'm interested in discussing a potential collaboration..."
}
```

**Validation Rules:**
- `name`: 必填，2-100 字元
- `email`: 必填，有效 Email 格式
- `subject`: 必填，5-200 字元
- `message`: 必填，10-5000 字元

**Response 201:**
```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "message": "Thank you for your message. I'll get back to you soon!"
  }
}
```

**Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      { "field": "email", "message": "Invalid email format" },
      { "field": "message", "message": "Message must be at least 10 characters" }
    ]
  }
}
```

**Response 429:**（Rate Limiting）
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retryAfter": 60
  }
}
```

---

#### GET /contact 🔒
取得所有聯絡訊息（需要認證）

**Query Parameters:**
| Parameter | Type    | Required | Description |
|-----------|---------|----------|-------------|
| read      | boolean | No       | 篩選已讀/未讀 |
| limit     | number  | No       | 回傳數量（預設 20）|
| offset    | number  | No       | 分頁偏移量（預設 0）|

**Response 200:**
```json
{
  "data": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "John Doe",
      "email": "john@example.com",
      "subject": "Collaboration Opportunity",
      "message": "Hi, I'm interested in discussing...",
      "read": false,
      "replied": false,
      "createdAt": "2024-12-20T15:30:00Z"
    }
  ],
  "pagination": {
    "total": 45,
    "limit": 20,
    "offset": 0,
    "hasMore": true
  }
}
```

---

#### PATCH /contact/:id 🔒
更新訊息狀態（需要認證）

**Request Body:**
```json
{
  "read": true,
  "replied": true
}
```

**Response 200:**
```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "John Doe",
    "email": "john@example.com",
    "subject": "Collaboration Opportunity",
    "message": "Hi, I'm interested in discussing...",
    "read": true,
    "replied": true,
    "createdAt": "2024-12-20T15:30:00Z"
  }
}
```

---

#### DELETE /contact/:id 🔒
刪除訊息（需要認證）

**Response 204:** No Content

---

## 3. Projects API（專案管理）

### Data Model

```typescript
interface Project {
  id: string                              // UUID
  slug: string                            // URL-friendly 識別碼
  title: string                           // 專案標題
  description: string                     // 專案描述
  tags: string[]                          // 技術標籤
  category: 'engineering' | 'ml'          // 分類
  year: string                            // 年份 (e.g., "2024" 或 "2024-2025")
  link?: string                           // 專案連結（可選）
  github?: string                         // GitHub 連結（可選）
  metrics?: string                        // 成效指標（可選）
  formula?: string                        // 技術公式/數據（可選）
  featured: boolean                       // 是否為精選專案
  order: number                           // 排序順序
  published: boolean                      // 是否發布
  createdAt: string                       // 建立時間 ISO 8601
  updatedAt: string                       // 更新時間 ISO 8601
}
```

### Endpoints

#### GET /projects
取得所有已發布的專案

**Query Parameters:**
| Parameter | Type    | Required | Description |
|-----------|---------|----------|-------------|
| category  | string  | No       | 依分類篩選（engineering / ml）|
| featured  | boolean | No       | 只取得精選專案 |
| tag       | string  | No       | 依標籤篩選 |
| limit     | number  | No       | 回傳數量（預設 50）|
| offset    | number  | No       | 分頁偏移量（預設 0）|

**Response 200:**
```json
{
  "data": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "slug": "maiagent-platform",
      "title": "The MaiAgent Platform",
      "description": "Led development of a production Generative AI platform...",
      "tags": ["Python", "LlamaIndex", "FastAPI", "PostgreSQL", "Milvus"],
      "category": "engineering",
      "year": "2024-2025",
      "link": null,
      "github": null,
      "metrics": "567% user growth / 120% partner growth / 67% token reduction",
      "formula": null,
      "featured": true,
      "order": 1,
      "createdAt": "2024-01-15T10:00:00Z",
      "updatedAt": "2024-12-01T08:00:00Z"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440003",
      "slug": "agentic-hybrid-rag",
      "title": "Agentic Hybrid RAG",
      "description": "Implemented a query classification agentic AI system...",
      "tags": ["Neo4j", "Cypher", "Milvus", "LangGraph", "Python"],
      "category": "ml",
      "year": "2024",
      "link": "#",
      "github": "https://github.com/yarikama",
      "metrics": null,
      "formula": "MAR@10 = 88.2% on multi-hop datasets",
      "featured": true,
      "order": 2,
      "createdAt": "2024-03-20T14:00:00Z",
      "updatedAt": "2024-11-15T09:30:00Z"
    }
  ],
  "pagination": {
    "total": 10,
    "limit": 50,
    "offset": 0,
    "hasMore": false
  }
}
```

---

#### GET /projects/:slug
取得單一專案詳情

**Response 200:**
```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "slug": "maiagent-platform",
    "title": "The MaiAgent Platform",
    "description": "Led development of a production Generative AI platform...",
    "tags": ["Python", "LlamaIndex", "FastAPI", "PostgreSQL", "Milvus"],
    "category": "engineering",
    "year": "2024-2025",
    "link": null,
    "github": null,
    "metrics": "567% user growth / 120% partner growth / 67% token reduction",
    "formula": null,
    "featured": true,
    "order": 1,
    "published": true,
    "createdAt": "2024-01-15T10:00:00Z",
    "updatedAt": "2024-12-01T08:00:00Z"
  }
}
```

**Response 404:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Project not found"
  }
}
```

---

#### POST /projects 🔒
新增專案（需要認證）

**Request Body:**
```json
{
  "slug": "new-project",
  "title": "New Project Title",
  "description": "Project description...",
  "tags": ["Python", "FastAPI"],
  "category": "engineering",
  "year": "2025",
  "link": "https://example.com",
  "github": "https://github.com/yarikama/new-project",
  "metrics": "Some metrics",
  "formula": null,
  "featured": false,
  "order": 11,
  "published": true
}
```

**Response 201:**
```json
{
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440004",
    "slug": "new-project",
    "title": "New Project Title",
    "description": "Project description...",
    "tags": ["Python", "FastAPI"],
    "category": "engineering",
    "year": "2025",
    "link": "https://example.com",
    "github": "https://github.com/yarikama/new-project",
    "metrics": "Some metrics",
    "formula": null,
    "featured": false,
    "order": 11,
    "published": true,
    "createdAt": "2025-01-20T10:00:00Z",
    "updatedAt": "2025-01-20T10:00:00Z"
  }
}
```

---

#### PUT /projects/:id 🔒
更新專案（需要認證）

**Request Body:**（部分更新）
```json
{
  "title": "Updated Project Title",
  "featured": true,
  "order": 1
}
```

**Response 200:**
```json
{
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440004",
    "slug": "new-project",
    "title": "Updated Project Title",
    "description": "Project description...",
    "tags": ["Python", "FastAPI"],
    "category": "engineering",
    "year": "2025",
    "link": "https://example.com",
    "github": "https://github.com/yarikama/new-project",
    "metrics": "Some metrics",
    "formula": null,
    "featured": true,
    "order": 1,
    "published": true,
    "createdAt": "2025-01-20T10:00:00Z",
    "updatedAt": "2025-01-20T12:30:00Z"
  }
}
```

---

#### DELETE /projects/:id 🔒
刪除專案（需要認證）

**Response 204:** No Content

---

#### PATCH /projects/reorder 🔒
重新排序專案（需要認證）

**Request Body:**
```json
{
  "orders": [
    { "id": "770e8400-e29b-41d4-a716-446655440002", "order": 1 },
    { "id": "770e8400-e29b-41d4-a716-446655440003", "order": 2 },
    { "id": "880e8400-e29b-41d4-a716-446655440004", "order": 3 }
  ]
}
```

**Response 200:**
```json
{
  "data": {
    "message": "Projects reordered successfully",
    "updated": 3
  }
}
```

---

## 4. Categories API（分類管理）

### GET /projects/categories
取得所有專案分類及數量

**Response 200:**
```json
{
  "data": [
    { "id": "all", "label": "All", "count": 10 },
    { "id": "engineering", "label": "Engineering", "count": 6 },
    { "id": "ml", "label": "ML/AI", "count": 4 }
  ]
}
```

---

### GET /lab-notes/tags
取得所有文章標籤及數量

**Response 200:**
```json
{
  "data": [
    { "tag": "RAG", "count": 5 },
    { "tag": "LlamaIndex", "count": 3 },
    { "tag": "Python", "count": 8 },
    { "tag": "System Design", "count": 2 }
  ]
}
```

---

## Common Error Responses

### 401 Unauthorized
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

### 403 Forbidden
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You don't have permission to perform this action"
  }
}
```

### 500 Internal Server Error
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

---

## Rate Limiting

| Endpoint | Rate Limit |
|----------|------------|
| POST /contact | 5 requests per minute per IP |
| GET /* | 100 requests per minute per IP |
| POST/PUT/DELETE /* | 30 requests per minute per token |

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703123456
```

---

## CORS Configuration

允許的 Origins:
- `https://yourdomain.com`
- `http://localhost:5173`（開發環境）

允許的 Methods:
- GET, POST, PUT, PATCH, DELETE, OPTIONS

允許的 Headers:
- Content-Type
- Authorization

---

## Database Schema Suggestion (PostgreSQL)

```sql
-- Lab Notes
CREATE TABLE lab_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    excerpt TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    read_time VARCHAR(50),
    date DATE NOT NULL,
    published BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lab_notes_slug ON lab_notes(slug);
CREATE INDEX idx_lab_notes_published ON lab_notes(published);
CREATE INDEX idx_lab_notes_tags ON lab_notes USING GIN(tags);

-- Contact Messages
CREATE TABLE contact_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT false,
    replied BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contact_messages_read ON contact_messages(read);
CREATE INDEX idx_contact_messages_created_at ON contact_messages(created_at DESC);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    category VARCHAR(50) NOT NULL CHECK (category IN ('engineering', 'ml')),
    year VARCHAR(20) NOT NULL,
    link VARCHAR(500),
    github VARCHAR(500),
    metrics TEXT,
    formula TEXT,
    featured BOOLEAN DEFAULT false,
    "order" INTEGER DEFAULT 0,
    published BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_projects_slug ON projects(slug);
CREATE INDEX idx_projects_category ON projects(category);
CREATE INDEX idx_projects_featured ON projects(featured);
CREATE INDEX idx_projects_order ON projects("order");
```

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/portfolio

# JWT
JWT_SECRET=your-super-secret-key
JWT_EXPIRES_IN=7d

# Email (for contact form notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
NOTIFICATION_EMAIL=your-email@gmail.com

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,http://localhost:5173

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
```
