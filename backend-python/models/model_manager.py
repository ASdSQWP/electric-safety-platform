"""模型管理器 — 负责模型加载、推理调度、GPU资源管理"""

import threading
from dataclasses import dataclass, field
from typing import Any

import torch


@dataclass
class ModelInfo:
    name: str
    type: str  # yolo / trex / llm
    path: str
    loaded: bool = False
    gpu_memory_mb: int = 0
    tasks: list[str] = field(default_factory=lambda: ["detect"])


class ModelManager:
    """统一模型管理，支持多模型注册与懒加载"""

    def __init__(self):
        self._models: dict[str, Any] = {}
        self._infos: dict[str, ModelInfo] = {}
        self._lock = threading.Lock()

    async def load_defaults(self):
        try:
            from ultralytics import YOLO

            yolo = YOLO("yolov8n.pt")
            self._models["yolov8n"] = yolo
            self._infos["yolov8n"] = ModelInfo(
                name="yolov8n",
                type="yolo",
                path="yolov8n.pt",
                loaded=True,
                gpu_memory_mb=int(torch.cuda.memory_allocated(0) / 1024**2) if torch.cuda.is_available() else 0,
            )
            print("[ModelManager] YOLOv8n loaded")
        except Exception as e:
            print(f"[ModelManager] YOLOv8n load failed: {e}")

    async def get_model(self, name: str) -> Any:
        with self._lock:
            return self._models.get(name)

    async def list_models(self) -> list[ModelInfo]:
        return list(self._infos.values())

    async def load_model(self, name: str, path: str, model_type: str) -> bool:
        with self._lock:
            if name in self._models:
                return True
            try:
                if model_type == "yolo":
                    from ultralytics import YOLO

                    self._models[name] = YOLO(path)
                self._infos[name] = ModelInfo(name=name, type=model_type, path=path, loaded=True)
                return True
            except Exception:
                return False

    async def unload_model(self, name: str) -> bool:
        with self._lock:
            if name in self._models:
                del self._models[name]
                if name in self._infos:
                    self._infos[name].loaded = False
                return True
            return False

    async def register_fine_tuned_model(self, name: str, path: str):
        with self._lock:
            self._infos[name] = ModelInfo(name=name, type="yolo", path=path, loaded=False, tasks=["detect"])

    async def get_model_capabilities(self) -> list[dict]:
        result = []
        for name, info in self._infos.items():
            model = self._models.get(name)
            tasks = ["detect"]
            classes = None
            if model is not None and hasattr(model, "model"):
                task_map = model.model.task if hasattr(model.model, "task") else "detect"
                tasks = [task_map] if isinstance(task_map, str) else list(task_map)
            if model is not None and hasattr(model, "names"):
                classes = list(model.names.values()) if isinstance(model.names, dict) else list(model.names)
            result.append({
                "name": info.name,
                "type": info.type,
                "tasks": tasks,
                "loaded": info.loaded,
                "classes": classes,
                "gpu_memory_mb": info.gpu_memory_mb,
            })
        return result

    async def cleanup(self):
        self._models.clear()
        self._infos.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def gpu_available(self) -> bool:
        return torch.cuda.is_available()

    def gpu_count(self) -> int:
        return torch.cuda.device_count() if torch.cuda.is_available() else 0
