"""模型训练 — 异步训练任务管理与微调"""

import json
from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


# ── 枚举 ───────────────────────────────────────────────────────────

class FineTuneStrategy(str, Enum):
    FULL = "full"
    FREEZE_BACKBONE = "freeze_backbone"
    LORA = "lora"


# ── 全量训练模型 ──────────────────────────────────────────────────

class TrainingJobRequest(BaseModel):
    dataset_path: str
    model_type: str = "yolov8n"
    epochs: int = 100
    batch_size: int = 16
    img_size: int = 640
    gpu_ids: str = "0"


class TrainingJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post("/start", response_model=TrainingJobResponse)
async def start_training(req: TrainingJobRequest):
    import uuid

    from tasks.train_task import start_training_task

    job_id = str(uuid.uuid4())[:8]
    start_training_task.delay(job_id, req.model_dump())
    return TrainingJobResponse(job_id=job_id, status="queued", message=f"训练任务 {job_id} 已加入队列")


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    from config import settings
    import redis

    r = redis.from_url(settings.redis_url)
    status = r.hgetall(f"training:{job_id}")
    return {k.decode(): v.decode() for k, v in status.items()} if status else {"status": "not_found"}


# ── 微调模型 ──────────────────────────────────────────────────────

class FineTuneRequest(BaseModel):
    base_model: str = "yolov8n"
    dataset_path: str
    strategy: FineTuneStrategy = FineTuneStrategy.LORA
    epochs: int = 50
    batch_size: int = 16
    img_size: int = 640
    learning_rate: float = 0.001
    freeze_layers: int = 10
    lora_rank: int = 8
    lora_alpha: float = 16.0
    gpu_ids: str = "0"
    description: str = ""


class FineTuneStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    current_epoch: int = 0
    total_epochs: int = 50
    metrics: dict = {}
    message: str = ""
    output_model_path: str | None = None


@router.post("/fine-tune", response_model=TrainingJobResponse)
async def start_fine_tune(req: FineTuneRequest):
    import uuid

    from tasks.train_task import fine_tune_task

    job_id = str(uuid.uuid4())[:8]
    fine_tune_task.delay(job_id, req.model_dump())
    return TrainingJobResponse(
        job_id=job_id,
        status="queued",
        message=f"微调任务 {job_id} 已加入队列（策略: {req.strategy.value}）",
    )


@router.get("/fine-tune/{job_id}/status", response_model=FineTuneStatusResponse)
async def get_fine_tune_status(job_id: str):
    from config import settings
    import redis

    r = redis.from_url(settings.redis_url)
    data = r.hgetall(f"training:fine-tune:{job_id}")
    if not data:
        return FineTuneStatusResponse(job_id=job_id, status="not_found", message="未找到微调任务")

    decoded = {k.decode(): v.decode() for k, v in data.items()}
    metrics = {}
    if "metrics" in decoded:
        try:
            metrics = json.loads(decoded["metrics"])
        except (json.JSONDecodeError, TypeError):
            pass

    return FineTuneStatusResponse(
        job_id=job_id,
        status=decoded.get("status", "unknown"),
        progress=int(decoded.get("progress", "0")),
        current_epoch=int(decoded.get("current_epoch", "0")),
        total_epochs=int(decoded.get("total_epochs", "50")),
        metrics=metrics,
        message=decoded.get("message", ""),
        output_model_path=decoded.get("output_model_path"),
    )


@router.get("/models")
async def list_base_models():
    """列出可用于微调的基础模型"""
    return {
        "models": [
            {"name": "yolov8n", "size": "nano", "mAP": "37.3", "params_m": 3.2, "speed_ms": 6.9},
            {"name": "yolov8s", "size": "small", "mAP": "44.9", "params_m": 11.2, "speed_ms": 8.1},
            {"name": "yolov8m", "size": "medium", "mAP": "50.2", "params_m": 25.9, "speed_ms": 11.7},
            {"name": "yolov8l", "size": "large", "mAP": "52.9", "params_m": 43.7, "speed_ms": 17.4},
            {"name": "yolov8x", "size": "x-large", "mAP": "53.9", "params_m": 68.2, "speed_ms": 24.6},
        ]
    }
