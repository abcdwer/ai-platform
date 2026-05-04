# AI Platform 设计文档

## 项目定位
个人 AI 工作台，可扩展为团队/对外产品。一站式管理对话、Agent、工作流、知识库、模型训练等 AI 能力。

## 技术栈

### 前端
- **React 18 + Next.js 14**（App Router）
- **Tailwind CSS** + **shadcn/ui**（组件库）
- **Zustand**（状态管理）
- **React Flow**（工作流可视化编辑）
- **Monaco Editor**（代码编辑）

选 React 而不是 Vue 的理由：
- AI 领域生态更好（Vercel AI SDK、LangChain.js 等都是 React 优先）
- 工作流编辑器 React Flow 是 React 生态
- Next.js 的 SSR/API Routes 可以简化部署

### 后端
- **Python 3.11+ + FastAPI**
- **SQLAlchemy**（ORM）
- **Celery + Redis**（异步任务队列，用于训练/微调等长任务）
- **LangChain / LangGraph**（Agent 编排）

选 Python 而不是 Node 的理由：
- AI/ML 生态绝对主力（PyTorch、transformers、peft 等）
- 模型训练、LoRA、微调只能用 Python
- FastAPI 性能足够，异步支持好

### 数据存储
- **PostgreSQL**（结构化数据：用户、对话、Agent 配置等）
- **Redis**（缓存、会话、任务队列）
- **ChromaDB**（向量数据库，知识库 RAG）
- **MinIO**（对象存储，模型文件、数据集等）

### 模型层
- **Ollama**（本地模型推理）
- **OpenAI API / 其他 API**（云端模型）
- **vLLM**（自部署模型高性能推理）
- 混合架构：本地 + API 统一调度

---

## 模块架构

```
┌─────────────────────────────────────────────────┐
│                   前端 (Next.js)                  │
├────────┬────────┬────────┬────────┬─────────────┤
│  对话   │ 工作流  │ 知识库  │ 模型管理 │  MCP 管理  │
├────────┴────────┴────────┴────────┴─────────────┤
│                  API Gateway (FastAPI)            │
├──────────┬──────────┬──────────┬────────────────┤
│ Agent引擎 │ 工作流引擎 │ RAG引擎  │  训练引擎      │
├──────────┴──────────┴──────────┴────────────────┤
│  模型调度层（Ollama / vLLM / API 统一接口）        │
├─────────────────────────────────────────────────┤
│  数据层（PostgreSQL / Redis / ChromaDB / MinIO）  │
└─────────────────────────────────────────────────┘
```

---

## 分期计划

### Phase 1：基础对话 + Agent（预计 1-2 周）
- 项目脚手架搭建（前后端）
- 对话界面（支持多模型切换）
- 流式输出
- 基础 Agent 能力（工具调用、代码执行）
- Agent 创建/管理界面
- 对话历史管理

### Phase 2：知识库（预计 1 周）
- 文档上传与解析（PDF、Word、网页、TXT）
- 向量化与存储（ChromaDB）
- RAG 对话（知识库检索增强）
- 知识库管理界面
- *现有 kb-app 的经验可以复用*

### Phase 3：工作流（预计 2 周）
- 可视化工作流编辑器（React Flow）
- 节点类型：LLM、条件分支、工具、代码、HTTP请求等
- 工作流执行引擎
- 工作流版本管理

### Phase 4：多智能体（预计 1 周）
- 多 Agent 编排（基于 LangGraph）
- Agent 角色定义与协作模式
- Agent 间通信与任务分配
- 可视化监控

### Phase 5：模型管理 + LoRA 微调（预计 2 周）
- 模型列表与状态监控（Ollama/API）
- 数据集管理
- LoRA 训练配置与启动（基于 peft + transformers）
- 训练任务队列（Celery）
- 训练进度监控
- 模型评估与对比

### Phase 6：MCP 接口（预计 1 周）
- MCP Server 创建与管理
- 接口配置（工具定义、权限）
- MCP Client 对接
- 接口测试与调试

---

## 目录结构（初期）

```
ai-platform/
├── frontend/                # Next.js 前端
│   ├── app/                 # App Router 页面
│   │   ├── chat/            # 对话页
│   │   ├── agents/          # Agent 管理
│   │   ├── knowledge/       # 知识库
│   │   ├── workflows/       # 工作流
│   │   ├── models/          # 模型管理
│   │   ├── training/        # 训练/微调
│   │   └── mcp/             # MCP 接口
│   ├── components/          # 公共组件
│   ├── lib/                 # 工具函数
│   └── stores/              # 状态管理
│
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── core/            # 核心配置
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   ├── agents/          # Agent 引擎
│   │   ├── rag/             # RAG 引擎
│   │   ├── workflow/        # 工作流引擎
│   │   ├── training/        # 训练引擎
│   │   └── mcp/             # MCP 管理
│   ├── alembic/             # 数据库迁移
│   └── tests/               # 测试
│
├── docker-compose.yml       # 一键部署
└── DESIGN.md                # 本文档
```

---

## 部署方案
- **开发**：本地 docker-compose（PostgreSQL + Redis + ChromaDB + Ollama）
- **生产**：同上，可加 Nginx 反代
- 模型训练需要 GPU 机器，可远程调度

---

## 与现有项目的关系
- **知识库应用（kb-app）**：独立保留，Phase 2 的知识库功能是新实现，但会参考 kb-app 的经验
- 两个项目暂不合并，未来可以 API 对接
