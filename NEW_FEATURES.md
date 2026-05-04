# AI Platform - 新增功能说明

## 概述
本次更新为 AI Platform 添加了 API 文档模块和导出功能模块。

## 后端更新

### 1. API 文档模块

#### 新增文件
- `backend/app/api/routes/export_import.py` - 导出导入功能实现

#### 更新文件
- `backend/app/api/routes/conversations.py` - 添加完整的 API 文档注释
- `backend/app/api/routes/workflow.py` - 添加完整的 API 文档注释
- `backend/app/api/routes/knowledge.py` - 添加完整的 API 文档注释
- `backend/app/main.py` - 注册新的导出导入路由
- `backend/app/api/routes/__init__.py` - 导出新路由模块

#### 新增 API 端点

**对话导出**
- `GET /api/conversations/{id}/export` - 导出对话为 Markdown、JSON、PDF、HTML 格式

**工作流分享与导入导出**
- `GET /api/workflows/{id}/share` - 生成分享链接
- `GET /api/workflows/{id}/export` - 导出工作流配置为 JSON
- `POST /api/workflows/import` - 从 JSON 导入工作流

**知识库备份与导入**
- `GET /api/knowledge/{id}/export` - 导出知识库为 Markdown、JSON、HTML 格式
- `POST /api/knowledge/{id}/import` - 批量导入文档

**Postman Collection**
- `GET /api/docs/postman-collection` - 下载 Postman Collection JSON

#### API 文档改进
- 所有端点添加了详细的 docstring
- 添加了 summary 和 description
- 添加了 response examples
- 完善了参数说明

## 前端更新

### 1. 新增页面

#### API 文档页面 (`/api-docs`)
- 完整的 API 端点文档展示
- 支持搜索过滤
- 分类展示不同模块的接口
- 请求示例和响应示例
- cURL 命令复制功能
- Postman Collection 下载按钮

### 2. 更新页面

#### 聊天页面 (`/chat`)
- 新增导出按钮
- 导出对话框支持 Markdown、JSON、HTML、PDF 格式

#### 工作流编辑页面 (`/workflows/[id]/edit`)
- 新增分享按钮
- 新增导入按钮
- 分享对话框支持生成分享链接
- 导出/导入 JSON 配置文件

#### 知识库详情页面 (`/knowledge/[id]`)
- 新增导入按钮
- 新增导出按钮
- 导出对话框支持 JSON、Markdown、HTML 格式
- 导入对话框支持批量添加文档

### 3. 新增组件

#### 导出对话框组件 (`components/export-dialog.tsx`)
- `ExportConversationDialog` - 对话导出对话框
- `ExportWorkflowDialog` - 工作流分享导出对话框
- `ImportWorkflowDialog` - 工作流导入对话框
- `ExportKnowledgeDialog` - 知识库导出对话框
- `ImportKnowledgeDialog` - 知识库导入对话框

#### Radio Group 组件 (`components/ui/radio-group.tsx`)
- 基于 Radix UI 的单选框组件

### 4. 更新组件

#### 侧边栏 (`components/sidebar.tsx`)
- 新增 "API Docs" 导航入口

## 文件清单

### 后端新增文件
- `backend/app/api/routes/export_import.py`

### 后端更新文件
- `backend/app/main.py`
- `backend/app/api/routes/__init__.py`
- `backend/app/api/routes/conversations.py`
- `backend/app/api/routes/workflow.py`
- `backend/app/api/routes/knowledge.py`

### 前端新增文件
- `frontend/app/api-docs/page.tsx`
- `frontend/components/export-dialog.tsx`
- `frontend/components/ui/radio-group.tsx`

### 前端更新文件
- `frontend/components/sidebar.tsx`
- `frontend/app/chat/page.tsx`
- `frontend/app/workflows/[id]/edit/page.tsx`
- `frontend/app/knowledge/[id]/page.tsx`

## 使用方式

### 导出对话
1. 进入对话页面
2. 点击标题栏右侧的下载图标
3. 选择导出格式（Markdown、JSON、HTML、PDF）
4. 点击导出按钮

### 分享工作流
1. 进入工作流编辑页面
2. 点击 "Share" 按钮
3. 选择 "Generate Share Link" 生成分享链接
4. 链接会自动复制到剪贴板

### 导出工作流
1. 进入工作流编辑页面
2. 点击 "Share" 按钮
3. 点击 "Export as JSON Configuration"
4. 下载 JSON 文件

### 导入工作流
1. 点击工作流编辑页面的上传图标
2. 上传 JSON 文件或粘贴配置
3. 点击 Import 导入

### 导出知识库
1. 进入知识库详情页面
2. 点击 "Export" 按钮
3. 选择导出格式（JSON、Markdown、HTML）
4. 点击导出按钮

### 导入文档到知识库
1. 进入知识库详情页面
2. 点击 "Import" 按钮
3. 上传文件或手动添加文档
4. 点击 Import 导入

## API 文档

访问 `/api-docs` 查看完整的 API 文档。

Swagger UI: `/docs`
ReDoc: `/redoc`
Postman Collection: `/api/docs/postman-collection`
