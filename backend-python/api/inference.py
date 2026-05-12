"""模型推理 — 图片/视频推理，多模型对比，集成融合"""

import json
from enum import Enum

from fastapi import APIRouter, Body, File, Query, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter()


# ── 枚举 ───────────────────────────────────────────────────────────

class FusionStrategy(str, Enum):
    NMS = "nms"
    WBF = "wbf"
    VOTING = "voting"


# ── 基础模型 ──────────────────────────────────────────────────────

class DetectionBox(BaseModel):
    bbox: list[float]
    class_name: str
    confidence: float


class InferenceResult(BaseModel):
    image_id: str
    model_name: str
    detections: list[DetectionBox]
    inference_time_ms: float
    image_width: int
    image_height: int


class ModelCapability(BaseModel):
    name: str
    type: str
    tasks: list[str] = ["detect"]
    loaded: bool = True
    classes: list[str] | None = None
    gpu_memory_mb: int = 0


# ── 集成模型 ──────────────────────────────────────────────────────

class EnsembleRequest(BaseModel):
    models: list[str]
    fusion: FusionStrategy = FusionStrategy.NMS
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45
    weights: list[float] | None = None


class EnsembleResult(BaseModel):
    image_id: str
    detections: list[DetectionBox]
    per_model_results: dict[str, list[DetectionBox]] = {}
    fusion_strategy: str
    inference_time_ms: float
    image_width: int
    image_height: int


# ── 辅助 ──────────────────────────────────────────────────────────

def _run_single(yolo, img, conf: float, iou: float) -> list[DetectionBox]:
    import numpy as np

    detections = []
    preds = yolo(np.array(img), conf=conf, iou=iou, verbose=False)
    for pred in preds:
        for box in pred.boxes:
            x1, y1, x2, y2 = box.xyxyn[0].tolist()
            detections.append(
                DetectionBox(
                    bbox=[round(v, 4) for v in [x1, y1, x2, y2]],
                    class_name=pred.names.get(int(box.cls[0]), "unknown"),
                    confidence=round(float(box.conf[0]), 3),
                )
            )
    return detections


def _dets_to_dicts(dets: list[DetectionBox]) -> list[dict]:
    return [d.model_dump() for d in dets]


# ── 端点 ──────────────────────────────────────────────────────────

@router.post("/detect", response_model=InferenceResult)
async def detect(file: UploadFile = File(...), model: str = "yolov8n", conf: float = 0.25, iou: float = 0.45):
    """单模型推理"""
    import time

    from PIL import Image
    from main import app

    img = Image.open(file.file).convert("RGB")
    w, h = img.size

    t0 = time.time()
    yolo = await app.state.model_manager.get_model(model)
    detections = _run_single(yolo, img, conf, iou) if yolo else []

    return InferenceResult(
        image_id=file.filename or "unknown",
        model_name=model,
        detections=detections,
        inference_time_ms=round((time.time() - t0) * 1000, 1),
        image_width=w,
        image_height=h,
    )


@router.post("/compare", response_model=list[InferenceResult])
async def compare_models(file: UploadFile = File(...), models: str = '["yolov8n"]', conf: float = 0.25):
    """多模型对比推理"""
    import time

    from PIL import Image
    from main import app

    model_names = json.loads(models)
    img = Image.open(file.file).convert("RGB")
    w, h = img.size

    results = []
    for model_name in model_names:
        t0 = time.time()
        yolo = await app.state.model_manager.get_model(model_name)
        detections = _run_single(yolo, img, conf, 0.45) if yolo else []
        results.append(
            InferenceResult(
                image_id=file.filename or "unknown",
                model_name=model_name,
                detections=detections,
                inference_time_ms=round((time.time() - t0) * 1000, 1),
                image_width=w,
                image_height=h,
            )
        )

    return results


@router.post("/ensemble", response_model=EnsembleResult)
async def ensemble_inference(file: UploadFile = File(...), req: EnsembleRequest = Body(...)):
    """多模型集成推理 — NMS/WBF/投票融合"""
    import time

    from PIL import Image
    from main import app
    from services.inference_service import nms_fusion, voting_fusion, wbf_fusion

    img = Image.open(file.file).convert("RGB")
    w, h = img.size
    t0 = time.time()

    per_model: dict[str, list[DetectionBox]] = {}
    all_dets: list[list[dict]] = []

    for name in req.models:
        yolo = await app.state.model_manager.get_model(name)
        dets = _run_single(yolo, img, req.conf_threshold, req.iou_threshold) if yolo else []
        per_model[name] = dets
        all_dets.append(_dets_to_dicts(dets))

    # 融合
    if req.fusion == FusionStrategy.NMS:
        fused_dicts = nms_fusion(all_dets, req.iou_threshold)
    elif req.fusion == FusionStrategy.WBF:
        fused_dicts = wbf_fusion(all_dets, req.weights, req.iou_threshold, req.conf_threshold)
    else:
        fused_dicts = voting_fusion(all_dets, min_votes=max(2, len(req.models) // 2 + 1), iou_threshold=req.iou_threshold)

    fused_dets = [DetectionBox(**d) for d in fused_dicts]

    return EnsembleResult(
        image_id=file.filename or "unknown",
        detections=fused_dets,
        per_model_results={k: [d.model_dump() for d in v] for k, v in per_model.items()},
        fusion_strategy=req.fusion.value,
        inference_time_ms=round((time.time() - t0) * 1000, 1),
        image_width=w,
        image_height=h,
    )


@router.get("/models", response_model=list[ModelCapability])
async def list_models():
    """列出所有已加载模型及其能力"""
    from main import app

    caps = await app.state.model_manager.get_model_capabilities()
    return [ModelCapability(**c) for c in caps]


@router.put("/models/load")
async def load_model(name: str = Body(...), path: str = Body(...), model_type: str = Body("yolo")):
    """动态加载模型"""
    from main import app

    ok = await app.state.model_manager.load_model(name, path, model_type)
    return {"status": "loaded" if ok else "failed", "model": name}


@router.delete("/models/{name}")
async def unload_model(name: str):
    """卸载模型释放GPU内存"""
    from main import app

    ok = await app.state.model_manager.unload_model(name)
    return {"status": "unloaded" if ok else "not_found", "model": name}


@router.websocket("/ws/training-progress")
async def training_progress_ws(websocket: WebSocket):
    """WebSocket — 实时训练进度推送"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
