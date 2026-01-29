# 技术设计文档 (TDD)

> 项目名称: 自动化安全检测平台 (AutoSecDet)
> 版本: v1.0
> 创建日期: 2026-01-28
> 作者: 技术团队
> 参考文档: SRS_v1.1.md

---

## 修订历史

| 版本 | 日期 | 作者 | 描述 |
|------|------|------|------|
| v1.0 | 2026-01-28 | 技术团队 | 初稿 |

---

## 1. 概述

### 1.1 设计目标

基于 SRS_v1.1 需求规格，设计一个自动化安全检测平台，实现：

- **高效执行**: 支持 100+ 安全用例的自动化执行，单个脚本超时控制在 5 分钟内
- **易于扩展**: 用例库支持从百级向千级平滑扩展
- **稳定可靠**: 单个用例失败不影响整体任务，支持任务中断与恢复
- **美观易用**: 现代化 UI 设计，操作流程简洁直观

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| 模块化设计 | 前后端分离，各模块职责清晰、低耦合 |
| 可扩展性 | 预留扩展接口，支持多类型脚本执行 |
| 安全优先 | RBAC 权限控制，敏感操作审计 |
| 用户体验 | 响应式设计，实时状态反馈 |
| 容错设计 | 超时机制、错误隔离、日志追踪 |

### 1.3 参考文档

| 文档 | 版本 | 说明 |
|------|------|------|
| 需求规格说明书 (SRS) | v1.1 | 功能需求与非功能需求定义 |
| 原始需求文档 | - | 项目背景与业务目标 |

---

## 2. 系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户层 (User Layer)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Web Browser (Chrome/Firefox/Edge)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │ HTTPS
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            前端层 (Frontend Layer)                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         React + TypeScript                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │ 任务执行  │  │ 用例管理  │  │ 结果报告  │  │ 用户管理  │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │   │
│  │  UI 组件库: TailwindCSS + shadcn/ui + Lucide Icons                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │ REST API / WebSocket
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            后端层 (Backend Layer)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Python + FastAPI                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │ 任务调度  │  │ 用例服务  │  │ 报告服务  │  │ 认证服务  │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │   │
│  │                    脚本执行引擎 (Script Engine)                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │ Python 执行器│  │ Shell 执行器 │  │ 超时控制器  │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             数据层 (Data Layer)                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │    PostgreSQL    │  │      Redis       │  │   File Storage   │         │
│  │   (主数据库)      │  │  (缓存/会话)     │  │  (脚本/日志/报告) │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 组件说明

| 组件 | 职责 | 技术栈 |
|------|------|--------|
| Web 前端 | 用户交互界面，实时状态展示 | React 18 + TypeScript + TailwindCSS |
| API 网关 | 请求路由、认证鉴权、限流 | FastAPI + JWT |
| 任务调度服务 | 检测任务的创建、执行、状态管理 | Python + Celery |
| 用例服务 | 用例 CRUD、分类管理 | Python + SQLAlchemy |
| 报告服务 | 结果统计、报告生成导出 | Python + WeasyPrint |
| 认证服务 | 用户认证、权限控制、会话管理 | Python + JWT + bcrypt |
| 脚本执行引擎 | 多类型脚本执行、超时控制、日志采集 | Python subprocess |
| PostgreSQL | 持久化存储（用例、任务、用户等） | PostgreSQL 15 |
| Redis | 会话缓存、任务队列、实时状态 | Redis 7 |
| 文件存储 | 脚本文件、执行日志、报告文件 | 本地文件系统 |

### 2.3 部署架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      部署服务器 (Linux)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Docker Compose                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │   Nginx     │  │  Frontend   │  │   Backend   │     │   │
│  │  │  (反向代理)  │  │  (静态资源)  │  │  (API服务)   │     │   │
│  │  │   :80/443   │  │    :3000    │  │    :8000    │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │ PostgreSQL  │  │    Redis    │  │   Celery    │     │   │
│  │  │    :5432    │  │    :6379    │  │  (Worker)   │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│  数据卷: /data/postgres  /data/scripts  /data/logs  /data/reports│
└─────────────────────────────────────────────────────────────────┘
```

**部署要求**:
- 操作系统: Ubuntu 22.04 LTS / CentOS 8+
- CPU: 4 核+，内存: 8GB+，磁盘: 100GB+ SSD
- 网络: 与待测设备同一局域网

---

## 3. 模块设计

### 3.1 模块划分

| 模块 | 前端组件 | 后端服务 | 说明 |
|------|---------|---------|------|
| 任务执行 | TaskExec | task_service | 任务创建、执行控制、状态展示 |
| 用例管理 | CaseMgmt | case_service | 用例 CRUD、分类管理 |
| 结果报告 | Report | report_service | 结果展示、报告导出、历史查询 |
| 系统管理 | System | user_service | 用户认证、账号管理 |

### 3.2 模块接口定义

#### 3.2.1 任务模块 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/tasks` | POST | 创建检测任务 |
| `/api/v1/tasks/{task_id}` | GET | 获取任务详情 |
| `/api/v1/tasks/{task_id}/start` | POST | 启动任务 |
| `/api/v1/tasks/{task_id}/stop` | POST | 停止任务 |
| `/api/v1/tasks` | GET | 获取历史任务列表 |
| `/ws/tasks/{task_id}` | WebSocket | 实时状态推送 |

#### 3.2.2 用例模块 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/cases` | GET | 获取用例列表 |
| `/api/v1/cases` | POST | 创建用例 |
| `/api/v1/cases/{case_id}` | PUT | 更新用例 |
| `/api/v1/cases/{case_id}` | DELETE | 删除用例 |
| `/api/v1/cases/{case_id}/toggle` | POST | 启用/禁用用例 |
| `/api/v1/categories` | GET/POST/PUT/DELETE | 分类管理 |

#### 3.2.3 报告模块 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/tasks/{task_id}/results` | GET | 获取任务结果详情 |
| `/api/v1/tasks/{task_id}/results/{id}/log` | GET | 获取执行日志 |
| `/api/v1/tasks/{task_id}/export/pdf` | GET | 导出 PDF 报告 |
| `/api/v1/tasks/{task_id}/export/html` | GET | 导出 HTML 报告 |

#### 3.2.4 用户模块 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/logout` | POST | 用户登出 |
| `/api/v1/users` | GET/POST | 用户列表/创建 |
| `/api/v1/users/{user_id}` | PUT | 更新用户 |
| `/api/v1/users/{user_id}/reset-password` | POST | 重置密码 |

### 3.3 检测任务执行流程

```
用户 ──> 输入IP+选择用例 ──> POST /tasks ──> 返回task_id
                                │
用户 ──> 点击启动 ──> POST /tasks/{id}/start ──> Celery异步执行
                                │
                    WebSocket实时推送状态 <── 脚本执行 ──> 目标设备
                                │
用户 <── 实时显示进度 <── 任务完成 ──> 保存结果
```

**中断处理**: 点击停止 → 终止当前脚本 → 已完成结果保存 → 当前用例标记 Error(中断)

---

## 4. 数据设计

### 4.1 数据模型

```
users (用户表)                    categories (分类表)
├── id (PK)                       ├── id (PK)
├── username                      ├── name
├── password_hash                 ├── description
├── role (tester/admin)           └── sort_order
├── is_active                            │
├── login_attempts                       │ 1:N
└── locked_until                         ▼
        │                         cases (用例表)
        │ 1:N                     ├── id (PK)
        ▼                         ├── name
tasks (任务表)                    ├── category_id (FK)
├── id (PK)                       ├── risk_level (high/medium/low)
├── target_ip                     ├── description
├── user_id (FK)                  ├── fix_suggestion
├── status                        ├── script_path
├── total_cases                   └── is_enabled
├── completed_cases                      │
├── passed/failed/error_count            │ N:1
├── start_time                           ▼
└── end_time                      task_results (任务结果表)
        │                         ├── id (PK)
        │ 1:N                     ├── task_id (FK)
        └─────────────────────────├── case_id (FK)
                                  ├── status (pending/running/pass/fail/error)
                                  ├── start_time / end_time
                                  ├── log_path
                                  └── error_message

audit_logs (审计日志表)
├── id (PK)
├── user_id (FK)
├── action (login/create/update/delete)
├── resource_type / resource_id
├── details (JSONB)
└── ip_address
```

### 4.2 核心表结构

#### users 表
```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'tester',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    login_attempts  INTEGER NOT NULL DEFAULT 0,
    locked_until    TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### cases 表
```sql
CREATE TABLE cases (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    risk_level      VARCHAR(10) NOT NULL,  -- 'high' | 'medium' | 'low'
    description     TEXT,
    fix_suggestion  TEXT,
    script_path     VARCHAR(500) NOT NULL,
    is_enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, category_id)
);
CREATE INDEX idx_cases_category_id ON cases(category_id);
CREATE INDEX idx_cases_is_enabled ON cases(is_enabled);
```

#### tasks 表
```sql
CREATE TABLE tasks (
    id              SERIAL PRIMARY KEY,
    target_ip       VARCHAR(15) NOT NULL,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_cases     INTEGER NOT NULL DEFAULT 0,
    completed_cases INTEGER NOT NULL DEFAULT 0,
    passed_count    INTEGER NOT NULL DEFAULT 0,
    failed_count    INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0,
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_target_ip ON tasks(target_ip);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
```

#### task_results 表
```sql
CREATE TABLE task_results (
    id              SERIAL PRIMARY KEY,
    task_id         INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    case_id         INTEGER NOT NULL REFERENCES cases(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    log_path        VARCHAR(500),
    error_message   TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_task_results_task_id ON task_results(task_id);
```

---

## 5. 接口设计

### 5.1 API 规范

- **Base URL**: `/api/v1`
- **认证方式**: Bearer Token (JWT)
- **数据格式**: JSON

**通用响应格式**:
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**错误码**:
| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 40001 | 参数校验失败 |
| 40101 | 未认证 |
| 40301 | 无权限 |
| 40401 | 资源不存在 |
| 50001 | 服务器内部错误 |

### 5.2 核心 API 示例

**创建检测任务**:
```
POST /api/v1/tasks
Request: { "target_ip": "192.168.1.100", "case_ids": [1, 2, 3] }
Response: { "code": 0, "data": { "task_id": 12345, "status": "pending" } }
```

**WebSocket 状态推送**:
```
WS /ws/tasks/{task_id}
Message: {
  "type": "progress",
  "data": {
    "current_case": { "id": 3, "name": "SSH弱密码检测", "status": "running" },
    "progress": { "completed": 2, "total": 5, "percentage": 40 }
  }
}
```

---

## 6. 安全设计

### 6.1 认证授权

- **认证方式**: JWT (Access Token 30分钟, Refresh Token 7天)
- **密码存储**: bcrypt 哈希 (cost factor = 12)
- **登录保护**: 5次错误锁定30分钟

### 6.2 权限控制 (RBAC)

| 资源 | 操作 | tester | admin |
|------|------|--------|-------|
| 任务 | 创建/执行/查看 | ✓ | ✓ |
| 用例 | 查看 | ✓ | ✓ |
| 用例 | 创建/编辑/删除 | ✗ | ✓ |
| 分类 | 管理 | ✗ | ✓ |
| 用户 | 管理 | ✗ | ✓ |

### 6.3 安全措施

| 措施 | 说明 |
|------|------|
| 传输加密 | HTTPS (TLS 1.2+) |
| SQL 注入防护 | 参数化查询 (SQLAlchemy ORM) |
| XSS 防护 | React 自动转义 + CSP 头 |
| 审计日志 | 记录登录、用例修改等敏感操作 |

---

## 7. 性能设计

### 7.1 性能目标

| 指标 | 目标值 |
|------|--------|
| 页面加载时间 | < 2s |
| 用例列表加载 | < 1s (1000条) |
| 报告生成时间 | < 10s |
| 并发用户数 | 10+ |
| WebSocket 延迟 | < 500ms |

### 7.2 优化策略

**前端**: 代码分割、资源压缩、虚拟列表
**后端**: 数据库索引、连接池、Celery 异步执行
**缓存**: Redis 缓存会话、用例列表、任务状态

---

## 8. 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 脚本执行超时 | 高 | 5分钟超时自动终止 |
| WebSocket 不稳定 | 中 | 心跳检测 + 自动重连 |
| 大量用例加载慢 | 中 | 分页 + 虚拟列表 + 缓存 |
| 脚本影响目标设备 | 高 | 脚本审核 + 非破坏性测试 |

---

## 9. 技术选型

| 类别 | 选型 | 版本 | 原因 |
|------|------|------|------|
| 前端框架 | React | 18.x | 生态成熟，组件化开发 |
| 前端语言 | TypeScript | 5.x | 类型安全 |
| UI 框架 | TailwindCSS + shadcn/ui | 3.x | 快速开发美观界面 |
| 后端框架 | FastAPI | 0.100+ | 高性能，自动文档 |
| 后端语言 | Python | 3.11+ | 脚本执行便捷 |
| ORM | SQLAlchemy | 2.x | 功能强大 |
| 任务队列 | Celery | 5.x | 成熟稳定 |
| 数据库 | PostgreSQL | 15.x | 功能强大，性能优秀 |
| 缓存 | Redis | 7.x | 高性能 |
| PDF 生成 | WeasyPrint | 60.x | 支持 CSS 样式 |
| 容器化 | Docker | 24.x | 环境一致性 |

---

## 10. 目录结构

```
AutoSecDet/
├── docs/                           # 文档
│   ├── requirements/               # 需求文档
│   └── design/                     # 设计文档
├── frontend/                       # 前端项目
│   ├── src/
│   │   ├── components/             # 组件
│   │   ├── pages/                  # 页面
│   │   ├── hooks/                  # 自定义 Hooks
│   │   ├── stores/                 # 状态管理
│   │   ├── services/               # API 服务
│   │   └── types/                  # 类型定义
│   └── package.json
├── backend/                        # 后端项目
│   ├── app/
│   │   ├── api/v1/                 # API 路由
│   │   ├── core/                   # 核心配置
│   │   ├── models/                 # 数据模型
│   │   ├── schemas/                # Pydantic 模式
│   │   ├── services/               # 业务逻辑
│   │   ├── engine/                 # 脚本执行引擎
│   │   └── main.py
│   └── requirements.txt
├── scripts/                        # 检测脚本目录
├── docker/                         # Docker 配置
└── README.md
```

---

## 11. 脚本执行引擎

### 11.1 架构

```
Executor (执行调度器)
    │
    ├── 接收执行请求
    ├── 根据脚本类型选择执行器
    ├── 管理超时控制 (5分钟)
    └── 收集执行结果
            │
            ▼
    ┌───────────────┐
    │ PythonRunner  │  .py 脚本执行
    │ ShellRunner   │  .sh 脚本执行
    └───────────────┘
            │
            ▼
    执行结果: status(pass/fail/error) + stdout + stderr + exit_code
```

### 11.2 脚本规范

**输入**: 通过环境变量传递 `TARGET_IP`
**输出**: 
- 退出码 0 = Pass, 非0 = Fail
- stdout 输出检测详情
- stderr 输出错误信息

**示例脚本**:
```python
#!/usr/bin/env python3
import os
import sys

target_ip = os.environ.get('TARGET_IP')
# 执行检测逻辑...
if check_passed:
    print("检测通过: ...")
    sys.exit(0)
else:
    print("检测失败: ...")
    sys.exit(1)
```

---

## 12. 设计评审检查清单

- [x] 架构设计满足非功能需求
- [x] 模块职责清晰、边界明确
- [x] 接口设计规范、易于理解
- [x] 数据模型设计合理
- [x] 安全设计完善
- [x] 性能设计可达成目标
- [x] 技术风险已识别并有缓解措施
- [x] 技术选型有充分理由

---

## 签字确认

| 角色 | 姓名 | 签字 | 日期 |
|------|------|------|------|
| 技术负责人 | | | |
| 架构师 | | | |
| 开发负责人 | | | |
| 测试负责人 | | | |
