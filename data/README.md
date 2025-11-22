# 数据目录说明

本目录用于存储工具和资讯的元数据（不存储实际内容，只存储链接和元信息）。

## 目录结构

```
data/
├── tools/          # 工具数据
│   ├── featured.json    # 热门工具
│   ├── cli.json         # 命令行工具
│   ├── ide.json         # 开发IDE
│   └── ...              # 其他分类
└── articles/       # 资讯数据
    ├── programming.json  # 编程资讯
    ├── ai.json          # AI资讯
    └── ...              # 其他分类
```

## 数据格式

### 工具数据格式 (tools/*.json)

```json
{
  "id": 1,
  "name": "工具名称",
  "url": "https://tool-url.com",
  "description": "工具描述",
  "category": "cli",
  "tags": ["SaaS", "AI", "终端"],
  "icon": "</>",
  "score": 9.5,
  "view_count": 1250,
  "like_count": 89,
  "is_featured": true,
  "created_at": "2025-01-08T10:00:00Z"
}
```

**字段说明：**
- `id`: 唯一标识符
- `name`: 工具名称
- `url`: 工具官网链接
- `description`: 工具描述
- `category`: 工具分类（cli, ide, ai-test, devops, plugin, review, doc, design, ui, codeagent, mcp, other）
- `tags`: 标签列表
- `icon`: 图标（emoji或字符）
- `score`: 热度分/推荐指数（0-10）
- `view_count`: 访问次数
- `like_count`: 点赞数
- `is_featured`: 是否热门推荐
- `created_at`: 创建时间（ISO 8601格式）

### 资讯数据格式 (articles/*.json)

```json
{
  "id": 1,
  "title": "文章标题",
  "url": "https://article-url.com",
  "source": "来源名称",
  "summary": "文章摘要",
  "category": "programming",
  "tags": ["标签1", "标签2"],
  "published_time": "2025-01-08T10:00:00Z",
  "created_at": "2025-01-08T10:00:00Z",
  "score": 8.5
}
```

**字段说明：**
- `id`: 唯一标识符
- `title`: 文章标题
- `url`: 文章链接
- `source`: 来源（公众号名/网站名）
- `summary`: 文章摘要
- `category`: 文章分类（programming, ai_coding等）
- `tags`: 标签列表
- `published_time`: 发布时间（ISO 8601格式）
- `created_at`: 收录时间（ISO 8601格式）
- `score`: 热度分（0-10）

## 注意事项

1. **不存储实际内容**：本平台只存储链接和元信息，不存储文章或工具的完整内容
2. **数据去重**：系统会自动根据 `id` 字段去重
3. **分页加载**：所有API都支持分页，默认每页20条，最大100条
4. **文件命名**：建议使用分类名称作为文件名（如 `cli.json`, `programming.json`）
5. **数据更新**：可以通过管理面板或直接编辑JSON文件来更新数据

## API使用

### 获取工具列表
```
GET /api/tools?category=cli&page=1&page_size=20
```

### 获取热门工具
```
GET /api/tools/featured?page=1&page_size=20
```

### 获取编程资讯
```
GET /api/news?category=programming&page=1&page_size=20
```

### 获取AI资讯
```
GET /api/ai-news?page=1&page_size=20
```

### 获取最近收录
```
GET /api/recent?type_filter=all&page=1&page_size=20
```

