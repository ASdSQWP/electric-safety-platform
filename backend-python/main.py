"""电力作业AI安全监管平台 — Python AI服务入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import annotation, drawing, inference, knowledge, plan_review, reports, training
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时加载模型
    from models.model_manager import ModelManager

    app.state.model_manager = ModelManager()
    await app.state.model_manager.load_defaults()
    yield
    # 关闭时释放资源
    await app.state.model_manager.cleanup()


app = FastAPI(title="电力作业AI安全监管平台 - AI服务", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(annotation.router, prefix="/api/annotation", tags=["AI辅助标注"])
app.include_router(inference.router, prefix="/api/inference", tags=["模型推理"])
app.include_router(training.router, prefix="/api/training", tags=["模型训练"])
app.include_router(drawing.router, prefix="/api/drawing", tags=["图纸评审"])
app.include_router(plan_review.router, prefix="/api/plan-review", tags=["方案评审"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])
app.include_router(reports.router, prefix="/api/reports", tags=["报告生成"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-backend"}
