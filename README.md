# Designflow · AI Product Concept Workflow Agent

面向消费品公司的 **AI 设计前期工作流助手 MVP**。  
自动完成市场研究、用户洞察、概念方向与 Design Brief 草案；**最终方向由人决定**。

## 核心闭环

```
输入需求 → Requirement Agent → Market Research Agent → User Insight Agent
        → Concept Generation Agent → 人工选择/评分/合并
        → Design Brief Generator → 人工编辑并确认
```

## 系统架构

```
┌──────────────────────────────┐
│  React + TypeScript Frontend │
│  Dashboard / Research /      │
│  Concepts / Brief / History  │
└──────────────┬───────────────┘
               │ REST
┌──────────────▼───────────────┐
│  FastAPI Orchestrator        │
│  Sequential Agent Pipeline   │
└──────────────┬───────────────┘
               │
     ┌─────────┼─────────┐
     ▼         ▼         ▼
 Requirement Research Insight
     ▼
  Concept → (Human Decision) → Brief
               │
               ▼
            SQLite
```

### Agents

| Agent | 职责 | 结构化输出 |
|-------|------|------------|
| Requirement Understanding | 解析模糊需求 | product_category, target_users, … |
| Market Research | 趋势/竞品/痛点/机会 | market_trends, competitors, … |
| User Insight | 用户画像 | persona JSON |
| Concept Generation | 3 个可选方向 | concepts[] |
| Concept Sketch | 初步方案草图 + 参考图 | sketch_svg / sketch_image_url |
| Design Brief | 选中方向 → brief | design_goal, CMF, avoid, … |

Human Decision Layer：收藏、评分、改关键词、合并方向、选择并确认最终 brief。AI **不会**自动 finalize。

## 技术栈

- Frontend: React + TypeScript + Vite
- Backend: Python FastAPI
- AI: OpenAI / Anthropic（无 Key 时自动 **mock mode**，可完整演示）
- DB: SQLite
- Workflow: 轻量 Agent Orchestration（`backend/agents/orchestrator.py`）

## 快速启动

### 正式入口：纯 HTML（推荐）

```bash
py -m pip install -r backend/requirements.txt
copy .env.example .env
py -m uvicorn backend.main:app --reload --port 8000
```

打开：**http://127.0.0.1:8000/app**

> React 前端（`frontend/`）仍可作开发对照，但以 `static/index.html` 为正式 UI。

### 可选：React 前端

```bash
cd frontend
npm install
npm run dev
```

打开：http://127.0.0.1:5173

API 文档：http://127.0.0.1:8000/docs  
健康检查：http://127.0.0.1:8000/api/health

### 环境变量

见 `.env.example`：

- `LLM_PROVIDER=openai|anthropic|mock`
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`
- `LLM_MODEL=gpt-4o-mini`（或 Claude 模型名）

未配置 Key 时 `mock_mode=true`，使用内置消费品领域示例数据，保证闭环可演示。

## 页面

1. **Project Dashboard** — 项目列表与需求输入  
2. **AI Research Board** — 需求/市场/竞品/用户洞察 + Agent 进度  
3. **Concept Board** — 概念卡片与人工决策  
4. **Brief Editor** — 编辑 brief 并人工 finalize  
5. **Decision History** — AI 与人工操作轨迹  

## 项目结构

```
ai-design-workflow/
├── backend/
│   ├── agents/
│   ├── database/
│   ├── routers/
│   └── main.py
├── static/
│   └── index.html     # 纯 HTML 完整界面（推荐）
├── frontend/          # React 版本（可选）
├── database/          # SQLite 文件目录
├── .env.example
└── README.md
```

## License

MIT
