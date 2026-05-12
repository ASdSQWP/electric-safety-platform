# 电力作业 AI 安全监管平台

面向电力作业场景的 **数据标注、模型训练与推理、图纸与施工方案评审、知识库与报告** 的一体化 Web 平台。适合 **个人先行落地使用**，后续可扩展为小团队多用户协作。

## 技术架构

| 组件 | 说明 |
|------|------|
| **前端** | Vue 3 + Vite + Element Plus + Pinia，画布标注（Konva）、图表（ECharts） |
| **网关** | Nginx：静态站点、`/api/` → Java、`/ai/` → Python（含 WebSocket 反代） |
| **业务后端** | Spring Boot 3（Java 17）+ PostgreSQL + Redis + MinIO，预留 JWT / MyBatis-Plus |
| **AI 后端** | FastAPI：YOLO（Ultralytics）、训练任务（Celery + Redis）、知识库（Chroma / LLM 等） |
| **基础设施** | PostgreSQL（pgvector）、Redis（redis-stack）、MinIO |

## 仓库结构

```
electric-safety-platform/
├── frontend/           # 前端工程（npm run build → dist）
├── backend-java/       # Spring Boot 业务与认证（持续完善中）
├── backend-python/     # FastAPI AI 服务
├── nginx.conf          # 反向代理与路由
├── docker-compose.yml  # 一键编排（含 GPU 可选配置）
└── README.md
```

## 环境要求

- **Docker** 与 **Docker Compose**（推荐用于整体运行）
- 或本地开发：**Node.js 18+**、**JDK 17**、**Maven**、**Python 3.11+**
- **训练 / YOLO 推理**：有 NVIDIA GPU 时可在 `docker-compose.yml` 中保留 `deploy.resources`；纯 CPU 环境请去掉 GPU 段，避免编排失败

## 使用 Docker Compose 运行

### 1. 构建前端静态资源

Nginx 挂载的是本机目录 `frontend/dist`，需先构建：

```bash
cd frontend
npm ci
npm run build
cd ..
```

### 2. 构建 Java 镜像（需本地先有 JAR）

`backend-java/Dockerfile` 从 `target/*.jar` 复制制品，请先打包：

```bash
cd backend-java
mvn -q package -DskipTests
cd ..
```

### 3. 启动全部服务

```bash
docker compose up -d --build
```

浏览器访问：**http://localhost**（默认 80 端口）。

### 4. 常用端口

| 服务 | 端口 |
|------|------|
| 站点（Nginx） | 80 |
| Java API | 8080 |
| Python AI | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| MinIO API / 控制台 | 9000 / 9001 |
| RedisInsight（redis-stack） | 8002（映射容器 8001） |

> **默认账号口令** 仅用于本地开发，上线前务必在 `docker-compose.yml` 与环境变量中全部替换。

### 5. 训练任务（Celery）

训练相关接口使用 Celery 异步执行。当前 Compose **仅启动 uvicorn**，若需真实训练消费队列，请在本机或单独容器中启动 Worker，例如：

```bash
cd backend-python
celery -A tasks.train_task worker -l info
```

（需在能与 Redis 互通的环境中运行，与 `docker-compose` 中网络、环境变量一致。）

## 本地开发（不依赖完整 Compose）

- **前端**：`cd frontend && npm run dev`（默认 Vite 开发服务器，需在 `vite.config.js` 中配置代理到后端，或自行对接网关）
- **Python AI**：`cd backend-python`，配置 `.env`（可参考 `config.py` 中的变量名），安装依赖后 `uvicorn main:app --reload --port 8000`
- **Java**：`cd backend-java && mvn spring-boot:run`（需本地 PostgreSQL / Redis / MinIO 与 `application.yml` 一致）

Python 可选环境变量（示例）见 `backend-python/config.py`，敏感项请放在 **`.env`** 且勿提交仓库（已在根目录 `.gitignore` 中忽略）。

## 与远程仓库同步

```bash
git add .
git commit -m "描述你的修改"
git push origin main
```

若远程先有 README 等提交，首次合并可使用：

```bash
git pull origin main --allow-unrelated-histories
```

## 当前状态说明（给维护者）

- **前端**：主要页面与路由已具备；登录等为演示逻辑时，需按产品规划对接真实认证。
- **Java**：安全与数据源等已配置，业务接口与领域模型可按迭代补充。
- **Python**：标注、推理、训练、图纸/方案评审、知识库、报告等路由已挂载，具体能力以各模块实现为准。

## 许可证

若用于商业或对外分发，请自行补充许可证文件（如 `LICENSE`）并确认依赖组件的许可条款。
