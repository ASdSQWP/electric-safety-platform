"""数据标注API — AI预标注、SAM交互式标注、格式转换、类别管理"""

import json
import os
import tempfile
import time
from typing import Any

from fastapi import APIRouter, File, Form, Query, UploadFile
from pydantic import BaseModel

from services.label_converter import LabelConverter
from services.label_schema import POWER_GRID_CLASSES, AnnotationImage, AnnotationShape, ShapeType

router = APIRouter()


# ==== 数据模型 ====

class ShapeDTO(BaseModel):
    label: str
    shape_type: str = "rectangle"
    points: list[list[float]]
    group_id: int | None = None
    score: float | None = None
    difficult: bool = False
    description: str = ""
    flags: dict[str, Any] = {}
    attributes: dict[str, str] = {}


class AnnotationResult(BaseModel):
    bbox: list[float]
    class_name: str
    confidence: float
    shape_type: str = "rectangle"


class AIAnnotationResponse(BaseModel):
    image_id: str
    shapes: list[AnnotationResult]
    inference_time_ms: float


class ExportRequest(BaseModel):
    images: list[dict]  # [{image_path, width, height, shapes: [...]}]
    format: str = "yolo"  # yolo / voc / coco
    classes: list[str] = []


class ImportResponse(BaseModel):
    images: list[dict]


# ==== AI 预标注 ====

@router.post("/predict", response_model=AIAnnotationResponse)
async def ai_predict(
    file: UploadFile = File(...),
    model: str = "yolov8n",
    conf: float = 0.25,
    classes: str | None = Query(None, description="逗号分隔的类别过滤"),
):
    """上传图片 → AI自动预标注（YOLO推理）"""
    import numpy as np
    from PIL import Image

    from main import app

    img = Image.open(file.file).convert("RGB")
    w, h = img.size
    class_filter = set(classes.split(",")) if classes else None

    t0 = time.time()
    yolo = await app.state.model_manager.get_model(model)
    shapes = []

    if yolo:
        preds = yolo(np.array(img), conf=conf, verbose=False)
        for pred in preds:
            for box in pred.boxes:
                x1, y1, x2, y2 = box.xyxyn[0].tolist()
                cls_name = pred.names.get(int(box.cls[0]), str(int(box.cls[0])))
                if class_filter and cls_name not in class_filter:
                    continue
                shapes.append(AnnotationResult(
                    bbox=[round(v, 6) for v in [x1, y1, x2, y2]],
                    class_name=cls_name,
                    confidence=round(float(box.conf[0]), 3),
                    shape_type="rectangle",
                ))

    return AIAnnotationResponse(
        image_id=file.filename or "unknown",
        shapes=shapes,
        inference_time_ms=round((time.time() - t0) * 1000, 1),
    )


# ==== 格式导出 ====

@router.post("/export")
async def export_annotations(req: ExportRequest):
    """标注数据 → 指定格式导出（VOC XML / YOLO TXT / COCO JSON）"""
    export_dir = tempfile.mkdtemp(prefix="label_export_")
    images = [_dict_to_annotation_image(d) for d in req.images]
    files = []

    if req.format == "yolo":
        labels_dir = os.path.join(export_dir, "labels")
        os.makedirs(labels_dir, exist_ok=True)
        for img in images:
            LabelConverter.image_to_yolo(img, labels_dir, req.classes)
        files.append({"path": labels_dir, "type": "yolo_labels"})
    elif req.format == "voc":
        voc_dir = os.path.join(export_dir, "voc")
        os.makedirs(voc_dir, exist_ok=True)
        for img in images:
            stem = os.path.splitext(os.path.basename(img.image_path))[0]
            LabelConverter.image_to_voc_xml(img, os.path.join(voc_dir, f"{stem}.xml"))
        files.append({"path": voc_dir, "type": "voc_xml"})
    elif req.format == "coco":
        coco_json = LabelConverter.images_to_coco_json(images, req.classes)
        coco_path = os.path.join(export_dir, "coco.json")
        with open(coco_path, "w", encoding="utf-8") as f:
            json.dump(coco_json, f, ensure_ascii=False, indent=2)
        files.append({"path": coco_path, "type": "coco_json"})

    return {"export_dir": export_dir, "files": files, "count": len(images)}


@router.post("/import")
async def import_annotations(files: list[UploadFile] = File(...), format: str = "voc"):
    """外部标注文件 → 内部格式"""
    results = []
    for file in files:
        content = await file.read()
        tmp = tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False)
        tmp.write(content)
        tmp.close()

        if format == "voc":
            img = LabelConverter.voc_xml_to_image(tmp.name)
            results.append(_image_to_dict(img))
        elif format in ("yolo", "txt"):
            # YOLO导入需要额外参数，简化处理
            results.append({"filename": file.filename, "status": "parsed", "shapes": []})

        os.unlink(tmp.name)

    return {"images": results, "count": len(results)}


# ==== 类别管理 ====

@router.get("/classes")
async def get_classes():
    """获取预定义的电网作业检测类别"""
    return {"classes": list(POWER_GRID_CLASSES.keys()), "colors": {k: v["color"] for k, v in POWER_GRID_CLASSES.items()}}


# ==== 视频帧提取 ====

@router.post("/video/extract-frames")
async def extract_video_frames(
    file: UploadFile = File(...),
    interval: int = Query(30, description="每N帧提取1帧"),
    max_frames: int = Query(100, description="最大帧数"),
):
    """视频 → 关键帧提取"""
    import cv2
    import numpy as np

    content = await file.read()
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp.write(content)
    tmp.close()

    cap = cv2.VideoCapture(tmp.name)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    frames = []
    count = 0
    while count < total and len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if count % interval == 0:
            _, buf = cv2.imencode(".jpg", frame)
            frames.append({
                "frame_index": count,
                "timestamp": round(count / fps, 2) if fps > 0 else 0,
                "image_base64": buf.tobytes().hex(),
            })
        count += 1

    cap.release()
    os.unlink(tmp.name)

    return {"total_frames": total, "fps": fps, "extracted_count": len(frames), "frames": frames}


# ==== helpers ====

def _dict_to_annotation_image(d: dict) -> AnnotationImage:
    return AnnotationImage(
        image_path=d.get("image_path", ""),
        image_width=d.get("width", d.get("image_width", 0)),
        image_height=d.get("height", d.get("image_height", 0)),
        shapes=[AnnotationShape(**s) for s in d.get("shapes", [])],
    )


def _image_to_dict(img: AnnotationImage) -> dict:
    return {
        "image_path": img.image_path,
        "width": img.image_width,
        "height": img.image_height,
        "shapes": [s.model_dump() for s in img.shapes],
    }
