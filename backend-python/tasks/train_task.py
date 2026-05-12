"""Celery异步训练任务 — 全量训练 + 微调"""

import json
import os

from celery import Celery

from config import settings

celery_app = Celery("training", broker=settings.redis_url, backend=settings.redis_url)


def _redis():
    import redis

    return redis.from_url(settings.redis_url)


# ── 全量训练 ──────────────────────────────────────────────────────

@celery_app.task(bind=True)
def start_training_task(self, job_id: str, params: dict):
    """异步执行YOLO全量训练"""
    r = _redis()

    def update_status(status: str, progress: int = 0, msg: str = ""):
        r.hset(
            f"training:{job_id}",
            mapping={"status": status, "progress": str(progress), "message": msg, "params": json.dumps(params)},
        )

    try:
        update_status("running", 0, "正在加载模型...")
        from ultralytics import YOLO

        model = YOLO(f"{params['model_type']}.pt")
        update_status("running", 20, "开始训练...")

        results = model.train(
            data=params["dataset_path"],
            epochs=params.get("epochs", 100),
            batch=params.get("batch_size", 16),
            imgsz=params.get("img_size", 640),
            device=params.get("gpu_ids", "0"),
            verbose=False,
        )

        metrics = {
            "mAP50": round(float(results.results_dict.get("metrics/mAP50(B)", 0)), 4),
            "mAP50-95": round(float(results.results_dict.get("metrics/mAP50-95(B)", 0)), 4),
        }

        update_status("completed", 100, f"训练完成 mAP50={metrics['mAP50']}")
        r.hset(f"training:{job_id}", "metrics", json.dumps(metrics))

    except Exception as e:
        update_status("failed", 0, str(e))


# ── 微调 ──────────────────────────────────────────────────────────

@celery_app.task(bind=True)
def fine_tune_task(self, job_id: str, params: dict):
    """异步执行YOLO微调（full / freeze_backbone / lora）"""
    r = _redis()
    key = f"training:fine-tune:{job_id}"

    def update(progress: int, msg: str, **extra):
        mapping = {"status": "running", "progress": str(progress), "message": msg}
        mapping.update({k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in extra.items()})
        r.hset(key, mapping=mapping)

    try:
        base_model = params.get("base_model", "yolov8n")
        strategy = params.get("strategy", "lora")
        epochs = params.get("epochs", 50)
        batch = params.get("batch_size", 16)
        img_size = params.get("img_size", 640)
        lr = params.get("learning_rate", 0.001)
        dataset = params["dataset_path"]
        device = params.get("gpu_ids", "0")

        update(0, f"加载基础模型 {base_model}...", strategy=strategy)

        from ultralytics import YOLO

        model_path = f"{base_model}.pt"
        if not os.path.exists(model_path):
            model_dir = getattr(settings, "model_dir", "./models/weights")
            model_path = os.path.join(model_dir, model_path) if os.path.exists(os.path.join(model_dir, f"{base_model}.pt")) else f"{base_model}.pt"

        model = YOLO(model_path)
        update(10, f"模型加载完成，策略={strategy}")

        # 训练参数
        train_kwargs = {
            "data": dataset,
            "epochs": epochs,
            "batch": batch,
            "imgsz": img_size,
            "device": device,
            "lr0": lr,
            "verbose": False,
        }

        if strategy == "freeze_backbone":
            freeze_layers = params.get("freeze_layers", 10)
            update(15, f"冻结前{freeze_layers}层，开始微调...")
            train_kwargs["freeze"] = freeze_layers
        elif strategy == "lora":
            update(15, "使用LoRA微调...")
            train_kwargs["lora"] = True
            train_kwargs["lora_rank"] = params.get("lora_rank", 8)
        else:
            update(15, "全参数微调...")

        results = model.train(**train_kwargs)

        metrics = {
            "mAP50": round(float(results.results_dict.get("metrics/mAP50(B)", 0)), 4),
            "mAP50-95": round(float(results.results_dict.get("metrics/mAP50-95(B)", 0)), 4),
            "precision": round(float(results.results_dict.get("metrics/precision(B)", 0)), 4),
            "recall": round(float(results.results_dict.get("metrics/recall(B)", 0)), 4),
        }

        # 保存微调后模型
        output_dir = os.path.join(getattr(settings, "model_dir", "./models/weights"), "fine-tuned", job_id, "weights")
        os.makedirs(output_dir, exist_ok=True)
        model.save(os.path.join(output_dir, "best.pt"))

        r.hset(key, mapping={
            "status": "completed",
            "progress": "100",
            "message": f"微调完成 mAP50={metrics['mAP50']}",
            "strategy": strategy,
            "metrics": json.dumps(metrics),
            "output_model_path": os.path.join(output_dir, "best.pt"),
        })

    except Exception as e:
        r.hset(key, mapping={"status": "failed", "progress": "0", "message": str(e)})
