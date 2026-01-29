# 技术设计文档 (TDD)

> 项目名称: 自动化安全检测平台 (AutoSecDet)
> 版本: v1.1
> 创建日期: 2026-01-28
> 最后更新: 2026-01-28 (评审修订)
> 作者: 技术团队
> 参考文档: SRS_v1.1.md

---

## 修订历史

| 版本 | 日期 | 作者 | 描述 |
|------|------|------|------|
| v1.0 | 2026-01-28 | 技术团队 | 初稿 |
| v1.1 | 2026-01-28 | 技术团队 | 根据评审意见修订，增加数据生命周期管理、脚本安全执行、容错恢复机制等 |

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
| 安全优先 | RBAC 权限控制，敏感操作审计，脚本沙箱执行 |
| 用户体验 | 响应式设计，实时状态反馈 |
| 容错设计 | 超时机制、错误隔离、断点续测、日志追踪 |

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
│  │  │ Python 执行器│  │ Shell 执行器 │  │ 沙箱隔离器  │                 │   │
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
| 脚本执行引擎 | 多类型脚本执行、沙箱隔离、超时控制、日志采集 | Python subprocess |
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
│  │  ┌─────────────┐                                        │   │
│  │  │ Celery Beat │  (定时任务: 日志清理、数据归档)          │   │
│  │  └─────────────┘                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│  数据卷: /data/postgres  /data/scripts  /data/logs  /data/reports│
└─────────────────────────────────────────────────────────────────┘
```

**部署要求**:
- 操作系统: Ubuntu 22.04 LTS / CentOS 8+
- CPU: 4 核+，内存: 8GB+，磁盘: 100GB+ SSD
- 网络: 与待测设备同一局域网

### 2.4 可用性保障设计

#### 2.4.1 数据库备份策略

| 备份类型 | 频率 | 保留时间 | 说明 |
|---------|------|---------|------|
| 全量备份 | 每日 02:00 | 7 天 | pg_dump 全库备份 |
| WAL 归档 | 实时 | 3 天 | 支持时间点恢复 |

```bash
# 备份脚本示例
pg_dump -h localhost -U postgres autosecdet > /data/backup/autosecdet_$(date +%Y%m%d).sql
```

#### 2.4.2 服务健康检查

| 服务 | 检查方式 | 检查间隔 | 超时时间 |
|------|---------|---------|---------|
| Backend API | HTTP GET /health | 30s | 10s |
| PostgreSQL | pg_isready | 30s | 5s |
| Redis | redis-cli ping | 30s | 5s |
| Celery Worker | celery inspect ping | 60s | 10s |

```yaml
# Docker healthcheck 配置
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

#### 2.4.3 故障恢复流程

```
1. 故障检测 (健康检查失败)
       │
       ▼
2. 自动重启容器 (Docker restart policy: on-failure)
       │
       ▼
3. 重启失败? ──是──> 告警通知运维人员
       │
       否
       ▼
4. 服务恢复，记录故障日志
```

**RTO 目标**: < 1 小时
- 自动恢复: < 5 分钟
- 人工介入恢复: < 1 小时

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
| `/api/v1/tasks/{task_id}/resume` | POST | 恢复中断的任务（断点续测） |
| `/api/v1/tasks` | GET | 获取历史任务列表 |
| `/ws/tasks/{task_id}` | WebSocket | 实时状态推送 |

#### 3.2.2 用例模块 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/cases` | GET | 获取用例列表 |
| `/api/v1/cases` | POST | 创建用例 |
| `/api/v1/cases/{case_id}` | GET | 获取用例详情 |
| `/api/v1/cases/{case_id}` | PUT | 更新用例 |
| `/api/v1/cases/{case_id}` | DELETE | 软删除用例（设置 is_deleted=true） |
| `/api/v1/cases/{case_id}/toggle` | POST | 启用/禁用用例 |

**分类管理 API 详细定义**:

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/categories` | GET | 获取分类列表 |
| `/api/v1/categories` | POST | 创建分类 |
| `/api/v1/categories/{cat_id}` | GET | 获取分类详情 |
| `/api/v1/categories/{cat_id}` | PUT | 更新分类 |
| `/api/v1/categories/{cat_id}` | DELETE | 删除分类 |

**创建分类请求**:
```json
POST /api/v1/categories
{
  "name": "身份认证",
  "description": "登录、认证相关安全检测",
  "sort_order": 1
}
```

**创建分类响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "身份认证",
    "description": "登录、认证相关安全检测",
    "sort_order": 1,
    "case_count": 0,
    "created_at": "2026-01-28T10:00:00Z"
  }
}
```

**删除分类错误响应**（分类下有用例时）:
```json
{
  "code": 40901,
  "message": "该分类下存在用例，请先移除或迁移用例",
  "data": null
}
```

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

**中断处理**: 点击停止 → 终止当前脚本 → 已完成结果保存 → 当前用例标记 Error(中断) → 任务状态设为 stopped

### 3.4 容错与恢复机制

#### 3.4.1 断点续测

当任务因中断（用户停止、网络异常、系统故障）而未完成时，支持从断点继续执行：

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  任务中断    │────>│  保存断点    │────>│  恢复执行    │
│  (stopped)   │     │  (记录进度)  │     │  (resume)    │
└──────────────┘     └──────────────┘     └──────────────┘
```

**恢复接口**:
```
POST /api/v1/tasks/{task_id}/resume
```

**恢复逻辑**:
1. 检查任务状态是否为 `stopped`
2. 获取已完成的用例列表
3. 从未执行的用例继续执行
4. 更新任务状态为 `running`

#### 3.4.2 单用例重试策略

| 场景 | 重试次数 | 重试间隔 | 说明 |
|------|---------|---------|------|
| 网络超时 | 2 | 5s | 目标设备网络不稳定 |
| 连接拒绝 | 1 | 10s | 目标服务未就绪 |
| 脚本执行超时 | 0 | - | 不重试，直接标记 Error |
| 脚本执行失败 | 0 | - | 不重试，标记 Fail |

**重试流程**:
```python
def execute_case_with_retry(case, target_ip, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            result = execute_script(case.script_path, target_ip)
            return result
        except NetworkTimeoutError:
            if attempt < max_retries:
                time.sleep(5)
                continue
            raise
```

#### 3.4.3 任务状态机

```
                    ┌─────────┐
                    │ pending │
                    └────┬────┘
                         │ start
                         ▼
                    ┌─────────┐
         ┌─────────│ running │─────────┐
         │         └────┬────┘         │
         │ stop         │ complete     │ error
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ stopped │   │completed│   │  error  │
    └────┬────┘   └─────────┘   └─────────┘
         │ resume
         ▼
    ┌─────────┐
    │ running │
    └─────────┘
```

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
├── total_cases                   ├── is_enabled
├── completed_cases               ├── is_deleted        ← 新增
├── passed/failed/error_count     └── deleted_at        ← 新增
├── start_time                           │
└── end_time                             │ N:1
        │                                ▼
        │ 1:N                     task_results (任务结果表)
        └─────────────────────────├── id (PK)
                                  ├── task_id (FK)
                                  ├── case_id (FK)
                                  ├── status
                                  ├── retry_count       ← 新增
                                  ├── start_time / end_time
                                  ├── log_path
                                  └── error_message

audit_logs (审计日志表)
├── id (PK)
├── user_id (FK)
├── action
├── resource_type / resource_id
├── details (JSONB)
├── ip_address
└── created_at
```

### 4.2 核心表结构

#### 4.2.1 users 表
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
CREATE INDEX idx_users_username ON users(username);
```

#### 4.2.2 categories 表
```sql
CREATE TABLE categories (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    description     TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_categories_sort_order ON categories(sort_order);
```

#### 4.2.3 cases 表
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
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,  -- 软删除标志
    deleted_at      TIMESTAMP,                        -- 删除时间
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, category_id)
);
CREATE INDEX idx_cases_category_id ON cases(category_id);
CREATE INDEX idx_cases_is_enabled ON cases(is_enabled);
CREATE INDEX idx_cases_is_deleted ON cases(is_deleted);
```

#### 4.2.4 tasks 表
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
CREATE INDEX idx_tasks_status ON tasks(status);
```

#### 4.2.5 task_results 表
```sql
CREATE TABLE task_results (
    id              SERIAL PRIMARY KEY,
    task_id         INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    case_id         INTEGER NOT NULL REFERENCES cases(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    retry_count     INTEGER NOT NULL DEFAULT 0,  -- 重试次数
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    log_path        VARCHAR(500),
    error_message   TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_task_results_task_id ON task_results(task_id);
CREATE INDEX idx_task_results_status ON task_results(status);
```

#### 4.2.6 audit_logs 表
```sql
CREATE TABLE audit_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id),
    username        VARCHAR(50),                    -- 冗余存储，便于查询
    action          VARCHAR(50) NOT NULL,           -- 'login' | 'logout' | 'login_failed' | 'create' | 'update' | 'delete'
    resource_type   VARCHAR(50),                    -- 'case' | 'category' | 'user' | 'task'
    resource_id     INTEGER,
    details         JSONB,                          -- 操作详情
    ip_address      VARCHAR(45),                    -- 支持 IPv6
    user_agent      VARCHAR(500),                   -- 浏览器信息
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- 审计日志分区（按月分区，便于清理）
-- 可选：生产环境可考虑使用分区表
```

**审计日志示例**:
```json
{
  "id": 1,
  "user_id": 1,
  "username": "admin",
  "action": "create",
  "resource_type": "case",
  "resource_id": 101,
  "details": {
    "case_name": "SSH弱密码检测",
    "category_id": 1,
    "risk_level": "high"
  },
  "ip_address": "192.168.1.50",
  "user_agent": "Mozilla/5.0 ...",
  "created_at": "2026-01-28T10:00:00Z"
}
```

### 4.3 数据生命周期管理

#### 4.3.1 数据保留策略

| 数据类型 | 保留时间 | 清理方式 | 说明 |
|---------|---------|---------|------|
| 执行日志文件 | 30 天 | 定时删除 | SRS F-007 要求 |
| 历史任务记录 | 90 天 | 定时归档/删除 | SRS F-011 要求 |
| 审计日志 | 180 天 | 定时归档 | 安全合规要求 |
| 报告文件 | 90 天 | 定时删除 | 与历史任务同步 |

#### 4.3.2 定时清理任务 (Celery Beat)

```python
# celery_config.py
from celery.schedules import crontab

beat_schedule = {
    # 每日凌晨 3:00 清理过期日志
    'cleanup-expired-logs': {
        'task': 'tasks.cleanup_expired_logs',
        'schedule': crontab(hour=3, minute=0),
    },
    # 每日凌晨 4:00 清理过期历史记录
    'cleanup-expired-tasks': {
        'task': 'tasks.cleanup_expired_tasks',
        'schedule': crontab(hour=4, minute=0),
    },
    # 每周日凌晨 5:00 归档审计日志
    'archive-audit-logs': {
        'task': 'tasks.archive_audit_logs',
        'schedule': crontab(hour=5, minute=0, day_of_week=0),
    },
}
```

#### 4.3.3 清理任务实现

```python
# tasks/cleanup.py
from datetime import datetime, timedelta

@celery_app.task
def cleanup_expired_logs():
    """清理超过 30 天的执行日志文件"""
    cutoff_date = datetime.now() - timedelta(days=30)
    log_dir = Path('/data/logs')
    
    for log_file in log_dir.glob('**/*.log'):
        if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
            log_file.unlink()
            logger.info(f"Deleted expired log: {log_file}")

@celery_app.task
def cleanup_expired_tasks():
    """清理超过 90 天的历史任务记录"""
    cutoff_date = datetime.now() - timedelta(days=90)
    
    # 删除任务结果
    db.execute("""
        DELETE FROM task_results 
        WHERE task_id IN (
            SELECT id FROM tasks WHERE created_at < %s
        )
    """, [cutoff_date])
    
    # 删除任务
    db.execute("DELETE FROM tasks WHERE created_at < %s", [cutoff_date])
    
    # 删除对应的报告文件
    # ...
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
| 40901 | 资源冲突 |
| 50001 | 服务器内部错误 |

**WebSocket 认证方式**:

WebSocket 连接通过 query parameter 传递 JWT Token：
```
ws://host/ws/tasks/{task_id}?token={jwt_token}
```

服务端验证流程：
1. 解析 URL 中的 token 参数
2. 验证 JWT 有效性
3. 验证用户是否有权限访问该任务
4. 验证通过后建立 WebSocket 连接

### 5.2 核心 API 示例

**创建检测任务**:
```
POST /api/v1/tasks
Request: { "target_ip": "192.168.1.100", "case_ids": [1, 2, 3] }
Response: { "code": 0, "data": { "task_id": 12345, "status": "pending" } }
```

**恢复中断任务**:
```
POST /api/v1/tasks/{task_id}/resume
Response: { 
  "code": 0, 
  "data": { 
    "task_id": 12345, 
    "status": "running",
    "resumed_from_case": 5,
    "remaining_cases": 10
  } 
}
```

**WebSocket 状态推送**:
```
WS /ws/tasks/{task_id}?token={jwt_token}
Message: {
  "type": "progress",
  "data": {
    "current_case": { "id": 3, "name": "SSH弱密码检测", "status": "running", "retry_count": 0 },
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

**后端**: 
- 数据库索引优化
- 连接池配置：`min_size=5, max_size=20`
- Celery 异步执行

**数据库连接池配置**:
```python
# database.py
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=5,          # 最小连接数
    max_overflow=15,      # 最大溢出连接数 (总最大 = 5 + 15 = 20)
    pool_timeout=30,      # 获取连接超时时间
    pool_recycle=1800,    # 连接回收时间 (30分钟)
)
```

**缓存**: Redis 缓存会话、用例列表、任务状态

---

## 8. 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 脚本执行超时 | 高 | 5分钟超时自动终止 |
| WebSocket 不稳定 | 中 | 心跳检测 + 自动重连 |
| 大量用例加载慢 | 中 | 分页 + 虚拟列表 + 缓存 |
| 脚本影响目标设备 | 高 | 沙箱隔离 + 资源限制 + 脚本白名单 |
| 网络不稳定 | 中 | 断点续测 + 重试机制 |
| 数据增长导致性能下降 | 中 | 定时清理 + 数据归档 |

---

## 9. 技术选型

| 类别 | 选型 | 版本 | 原因 |
|------|------|------|------|
| 前端框架 | React | 18.x | 生态成熟，组件化开发 |
| 前端语言 | TypeScript | 5.x | 类型安全 |
| UI 框架 | TailwindCSS + shadcn/ui | 3.x | 快速开发美观界面 |
| 状态管理 | Zustand | 4.x | 轻量级，API 简洁 |
| 后端框架 | FastAPI | 0.100+ | 高性能，自动文档 |
| 后端语言 | Python | 3.11+ | 脚本执行便捷 |
| ORM | SQLAlchemy | 2.x | 功能强大 |
| 任务队列 | Celery | 5.x | 成熟稳定 |
| 定时任务 | Celery Beat | 5.x | 与 Celery 集成 |
| 数据库 | PostgreSQL | 15.x | 功能强大，性能优秀 |
| 缓存 | Redis | 7.x | 高性能 |
| PDF 生成 | WeasyPrint | 60.x | 支持 CSS 样式 |
| 容器化 | Docker | 24.x | 环境一致性 |

---

## 10. 目录结构

### 10.1 项目整体结构

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
│   │   ├── stores/                 # Zustand 状态管理
│   │   ├── services/               # API 服务
│   │   ├── utils/                  # 工具函数
│   │   │   └── errorHandler.ts     # 全局错误处理
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
│   │   ├── tasks/                  # Celery 任务
│   │   │   ├── executor.py         # 任务执行
│   │   │   └── cleanup.py          # 定时清理
│   │   └── main.py
│   └── requirements.txt
├── scripts/                        # 检测脚本目录
├── docker/                         # Docker 配置
└── README.md
```

### 10.2 前端错误处理方案

**全局错误处理架构**:

```typescript
// utils/errorHandler.ts
export class ErrorHandler {
  // API 错误处理
  static handleApiError(error: AxiosError) {
    const code = error.response?.data?.code;
    switch (code) {
      case 40101:
        // 未认证，跳转登录
        router.push('/login');
        break;
      case 40301:
        toast.error('无权限执行此操作');
        break;
      default:
        toast.error(error.response?.data?.message || '请求失败');
    }
  }

  // WebSocket 错误处理
  static handleWsError(event: Event) {
    console.error('WebSocket error:', event);
    // 自动重连逻辑
    this.scheduleReconnect();
  }

  // 全局未捕获错误
  static handleUncaughtError(error: Error) {
    console.error('Uncaught error:', error);
    toast.error('系统异常，请刷新页面重试');
  }
}

// 注册全局错误处理
window.addEventListener('unhandledrejection', (event) => {
  ErrorHandler.handleUncaughtError(event.reason);
});
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
    ├── 管理重试逻辑
    └── 收集执行结果
            │
            ▼
    ┌───────────────┐
    │ PythonRunner  │  .py 脚本执行
    │ ShellRunner   │  .sh 脚本执行
    └───────────────┘
            │
            ▼
    ┌───────────────┐
    │ SandboxRunner │  沙箱隔离执行
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

### 11.3 脚本安全执行机制

#### 11.3.1 执行用户隔离

脚本以专用低权限用户 `script_runner` 执行，限制系统访问权限：

```bash
# 创建专用用户
useradd -r -s /bin/false script_runner

# 脚本目录权限
chown -R script_runner:script_runner /data/scripts
chmod 750 /data/scripts
```

```python
# executor.py
import subprocess
import pwd

def execute_script(script_path, target_ip):
    # 获取 script_runner 用户信息
    pw_record = pwd.getpwnam('script_runner')
    
    process = subprocess.Popen(
        [script_path],
        env={'TARGET_IP': target_ip},
        user=pw_record.pw_uid,
        group=pw_record.pw_gid,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
```

#### 11.3.2 资源限制

使用 `resource` 模块和 cgroups 限制脚本资源使用：

| 资源 | 限制值 | 说明 |
|------|--------|------|
| CPU 时间 | 300s | 单个脚本最大执行时间 |
| 内存 | 512MB | 防止内存泄漏 |
| 文件描述符 | 100 | 限制文件打开数 |
| 进程数 | 10 | 限制子进程数量 |

```python
import resource

def set_resource_limits():
    # CPU 时间限制 (5分钟)
    resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
    # 内存限制 (512MB)
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    # 文件描述符限制
    resource.setrlimit(resource.RLIMIT_NOFILE, (100, 100))
    # 进程数限制
    resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))

process = subprocess.Popen(
    [script_path],
    preexec_fn=set_resource_limits,
    # ...
)
```

#### 11.3.3 脚本白名单校验

仅允许执行已注册的脚本，防止任意代码执行：

```python
def validate_script(script_path):
    """验证脚本是否在白名单中"""
    # 1. 检查脚本是否在允许的目录下
    allowed_dirs = ['/data/scripts']
    script_abs = os.path.abspath(script_path)
    if not any(script_abs.startswith(d) for d in allowed_dirs):
        raise SecurityError("脚本路径不在允许范围内")
    
    # 2. 检查脚本是否在数据库中注册
    case = db.query(Case).filter(Case.script_path == script_path).first()
    if not case:
        raise SecurityError("脚本未注册")
    
    # 3. 检查脚本文件完整性 (可选: 校验哈希)
    # ...
    
    return True
```

### 11.4 并发控制配置

#### 11.4.1 Celery Worker 配置

```python
# celery_config.py
worker_concurrency = 4          # 并发 worker 数量
worker_prefetch_multiplier = 1  # 每次预取任务数
task_acks_late = True           # 任务完成后确认
task_reject_on_worker_lost = True
```

#### 11.4.2 任务并发限制

```python
# 同一目标 IP 同时只能执行一个任务
@celery_app.task(
    bind=True,
    max_retries=0,
    rate_limit='1/m',  # 每分钟最多 1 个任务
)
def execute_task(self, task_id):
    # 检查是否有正在执行的任务
    running_task = db.query(Task).filter(
        Task.target_ip == task.target_ip,
        Task.status == 'running',
        Task.id != task_id
    ).first()
    
    if running_task:
        raise TaskConflictError("该目标 IP 已有任务在执行中")
    
    # 执行任务...
```

---

## 12. 设计评审检查清单

- [x] 架构设计满足非功能需求
- [x] 模块职责清晰、边界明确
- [x] 接口设计规范、易于理解
- [x] 数据模型设计合理
- [x] 安全设计完善（含脚本安全执行）
- [x] 性能设计可达成目标
- [x] 技术风险已识别并有缓解措施
- [x] 技术选型有充分理由
- [x] 数据生命周期管理完善
- [x] 容错与恢复机制完善

---

## 签字确认

| 角色 | 姓名 | 签字 | 日期 |
|------|------|------|------|
| 技术负责人 | | | |
| 架构师 | | | |
| 开发负责人 | | | |
| 测试负责人 | | | |
