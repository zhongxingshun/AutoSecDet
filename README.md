# AutoSecDet - 自动化安全检测平台

<p align="center">
  <img src="docs/logo.png" alt="AutoSecDet Logo" width="120" />
</p>

<p align="center">
  <strong>一站式自动化安全检测解决方案</strong>
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#技术栈">技术栈</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#项目结构">项目结构</a> •
  <a href="#使用指南">使用指南</a>
</p>

---

## 📖 项目简介

AutoSecDet（Automated Security Detection）是一个面向企业的自动化安全检测平台，支持对目标设备进行批量安全合规检测。平台提供用例管理、任务调度、结果分析和报告导出等完整功能，帮助安全团队高效完成安全评估工作。

## ✨ 功能特性

### 🔐 用户管理
- 基于角色的访问控制（管理员/测试人员）
- JWT Token 认证机制
- 密码使用 bcrypt 加密存储
- 登录失败锁定保护

### 📋 用例管理
- 用例分类管理（身份认证、访问控制、数据安全、网络安全、系统安全）
- 用例 CRUD 操作
- 风险等级标记（高/中/低）
- 用例启用/禁用控制
- 软删除支持数据恢复

### 🚀 任务管理
- 指定目标 IP 创建检测任务
- **分类折叠面板选择用例**（支持按分类批量选择）
- 任务实时进度追踪
- 任务停止/重试功能
- 任务结果统计（通过/失败/错误）

### 📊 报告功能
- 任务详情查看
- 检测结果分析
- 报告导出（JSON/HTML 格式）

### 🎨 现代化 UI
- 响应式设计
- 深色/浅色主题支持
- 实时数据刷新
- 友好的交互体验

## 🛠 技术栈

### 后端
| 技术 | 说明 |
|------|------|
| Python 3.11+ | 编程语言 |
| FastAPI | Web 框架 |
| SQLAlchemy | ORM |
| PostgreSQL | 数据库 |
| Redis | 缓存/消息队列 |
| Celery | 异步任务队列 |
| Alembic | 数据库迁移 |
| Pydantic | 数据验证 |

### 前端
| 技术 | 说明 |
|------|------|
| React 18 | UI 框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| TailwindCSS | 样式框架 |
| React Router v6 | 路由管理 |
| React Query | 数据请求 |
| Zustand | 状态管理 |
| Lucide React | 图标库 |

### 部署
| 技术 | 说明 |
|------|------|
| Docker | 容器化 |
| Docker Compose | 服务编排 |

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- Node.js 18+（前端开发）
- Python 3.11+（后端开发）

### 使用 Docker 启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-username/AutoSecDet.git
cd AutoSecDet

# 2. 启动后端服务
cd docker
docker-compose up -d

# 3. 等待服务启动完成，运行数据库迁移
docker exec autosecdet-backend alembic upgrade head

# 4. 启动前端开发服务器
cd ../frontend
npm install
npm run dev
```

### 访问应用

- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8001
- **API 文档**: http://localhost:8001/docs

### 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

> ⚠️ **安全提示**: 首次登录后请立即修改默认密码！

## 📁 项目结构

```
AutoSecDet/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   └── v1/         # v1 版本接口
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── services/       # 业务逻辑
│   │   └── tasks/          # Celery 任务
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt    # Python 依赖
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # 通用组件
│   │   ├── pages/          # 页面组件
│   │   ├── stores/         # 状态管理
│   │   └── lib/            # 工具函数
│   ├── package.json        # Node 依赖
│   └── vite.config.ts      # Vite 配置
│
├── docker/                 # Docker 配置
│   ├── docker-compose.yml  # 服务编排
│   ├── Dockerfile          # 后端镜像
│   └── init-db.sql         # 数据库初始化
│
└── docs/                   # 文档
    ├── requirements/       # 需求文档
    └── design/             # 设计文档
```

## 📖 使用指南

### 1. 用例管理

1. 登录系统后，点击左侧菜单「用例管理」
2. 点击「新建用例」按钮创建检测用例
3. 填写用例信息：
   - **用例名称**: 描述检测项
   - **分类**: 选择所属分类
   - **风险等级**: 高/中/低
   - **脚本路径**: 检测脚本位置
   - **描述**: 详细说明
   - **修复建议**: 问题修复方案

### 2. 创建检测任务

1. 点击左侧菜单「任务管理」
2. 点击「新建任务」按钮
3. 输入目标设备 IP 地址
4. 选择要执行的用例：
   - 勾选「运行所有启用的用例」执行全部
   - 或取消勾选，按分类选择特定用例
5. 点击「开始检测」启动任务

### 3. 查看检测结果

1. 在任务列表中点击「查看详情」图标
2. 查看任务执行进度和结果统计
3. 查看每个用例的检测状态
4. 可导出 JSON 或 HTML 格式报告

### 4. 用户管理（仅管理员）

1. 点击左侧菜单「用户管理」
2. 可创建新用户、重置密码、启用/禁用账号

## 🔧 开发指南

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn app.main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 🔒 安全说明

- 密码使用 bcrypt 算法加密（cost factor=12）
- JWT Token 有效期 30 分钟，支持刷新
- 登录失败 5 次后账号锁定 15 分钟
- 所有 API 请求需要认证（除登录接口）
- 敏感操作记录审计日志

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

<p align="center">
  Made with ❤️ by AutoSecDet Team
</p>
