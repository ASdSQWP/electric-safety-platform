"""标注数据模型 — 参考 X-AnyLabeling schema 设计"""

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ShapeType(str, Enum):
    RECTANGLE = "rectangle"
    ROTATION = "rotation"  # 旋转框 OBB
    POLYGON = "polygon"
    POINT = "point"
    LINE = "line"
    CIRCLE = "circle"
    LINESTRIP = "linestrip"
    CUBOID = "cuboid"  # 3D框


class AnnotationShape(BaseModel):
    label: str
    shape_type: ShapeType
    points: list[list[float]]  # [[x1,y1], [x2,y2], ...] 绝对像素坐标
    group_id: int | None = None
    score: float | None = None  # AI 置信度
    difficult: bool = False
    description: str = ""
    flags: dict[str, Any] = {}
    attributes: dict[str, str] = {}

    @property
    def bbox_xyxy(self) -> tuple[float, float, float, float]:
        """转为 (x1, y1, x2, y2) 格式"""
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return min(xs), min(ys), max(xs), max(ys)


class AnnotationImage(BaseModel):
    """单张图片的标注数据"""
    image_path: str
    image_width: int
    image_height: int
    shapes: list[AnnotationShape] = []
    flags: dict[str, Any] = {}


class AnnotationDataset(BaseModel):
    """数据集标注清单"""
    version: str = "1.0"
    images: list[AnnotationImage] = []


# ---- 支持的类别配置 ----
POWER_GRID_CLASSES = {
    "绝缘子": {"color": "#FF0000", "supercategory": "电气设备"},
    "导线": {"color": "#00FF00", "supercategory": "电气设备"},
    "塔材": {"color": "#0000FF", "supercategory": "结构"},
    "防振锤": {"color": "#FFFF00", "supercategory": "金具"},
    "间隔棒": {"color": "#FF00FF", "supercategory": "金具"},
    "均压环": {"color": "#00FFFF", "supercategory": "金具"},
    "线夹": {"color": "#FFA500", "supercategory": "金具"},
    "接地线": {"color": "#800080", "supercategory": "安全设施"},
    "标示牌": {"color": "#008080", "supercategory": "安全设施"},
    "安全带": {"color": "#FF4500", "supercategory": "个人防护"},
    "安全帽": {"color": "#1E90FF", "supercategory": "个人防护"},
    "施工机械": {"color": "#808080", "supercategory": "机械设备"},
    "孔洞": {"color": "#A52A2A", "supercategory": "隐患"},
    "人员": {"color": "#008000", "supercategory": "人员"},
}
