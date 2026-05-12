"""标注格式转换服务 — 参考 X-AnyLabeling label_converter.py

支持的格式: XLABEL JSON (内部) ↔ VOC XML / YOLO TXT / COCO JSON
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

from services.label_schema import AnnotationImage, AnnotationShape, ShapeType


class LabelConverter:
    """标注格式双向转换器"""

    # ==== 内部 XLABEL JSON → 各格式 ====

    @staticmethod
    def image_to_voc_xml(img: AnnotationImage, xml_path: str) -> None:
        """单张图片标注 → Pascal VOC XML"""
        root = ET.Element("annotation")
        ET.SubElement(root, "folder").text = os.path.dirname(img.image_path) or "."
        ET.SubElement(root, "filename").text = os.path.basename(img.image_path)
        size = ET.SubElement(root, "size")
        ET.SubElement(size, "width").text = str(img.image_width)
        ET.SubElement(size, "height").text = str(img.image_height)
        ET.SubElement(size, "depth").text = "3"

        for shape in img.shapes:
            obj = ET.SubElement(root, "object")
            ET.SubElement(obj, "name").text = shape.label
            if shape.difficult:
                ET.SubElement(obj, "difficult").text = "1"
            bnd = ET.SubElement(obj, "bndbox")
            x1, y1, x2, y2 = shape.bbox_xyxy
            ET.SubElement(bnd, "xmin").text = str(int(x1))
            ET.SubElement(bnd, "ymin").text = str(int(y1))
            ET.SubElement(bnd, "xmax").text = str(int(x2))
            ET.SubElement(bnd, "ymax").text = str(int(y2))

        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def image_to_yolo(img: AnnotationImage, labels_dir: str, classes: list[str]) -> None:
        """单张图片标注 → YOLO TXT（归一化坐标）"""
        stem = Path(img.image_path).stem
        txt_path = os.path.join(labels_dir, f"{stem}.txt")
        w, h = img.image_width, img.image_height

        lines = []
        for shape in img.shapes:
            cls_id = classes.index(shape.label) if shape.label in classes else -1
            if cls_id < 0:
                continue

            if shape.shape_type in (ShapeType.RECTANGLE, ShapeType.ROTATION):
                x1, y1, x2, y2 = shape.bbox_xyxy
                cx = ((x1 + x2) / 2) / w
                cy = ((y1 + y2) / 2) / h
                bw = (x2 - x1) / w
                bh = (y2 - y1) / h
                lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

            elif shape.shape_type == ShapeType.POLYGON:
                # 多边形归一化
                pts = [f"{p[0]/w:.6f} {p[1]/h:.6f}" for p in shape.points]
                lines.append(f"{cls_id} " + " ".join(pts))

        with open(txt_path, "w") as f:
            f.write("\n".join(lines))

    @staticmethod
    def images_to_coco_json(images: list[AnnotationImage], classes: list[str]) -> dict:
        """多张图片 → COCO JSON"""
        coco = {
            "images": [],
            "annotations": [],
            "categories": [{"id": i + 1, "name": c, "supercategory": ""} for i, c in enumerate(classes)],
        }
        ann_id = 0
        for img_id, img in enumerate(images, 1):
            coco["images"].append({
                "id": img_id,
                "file_name": os.path.basename(img.image_path),
                "width": img.image_width,
                "height": img.image_height,
            })
            for shape in img.shapes:
                cls_id = classes.index(shape.label) + 1 if shape.label in classes else 1
                coco["annotations"].append({
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": cls_id,
                    "bbox": list(shape.bbox_xyxy) + [
                        shape.bbox_xyxy[2] - shape.bbox_xyxy[0],
                        shape.bbox_xyxy[3] - shape.bbox_xyxy[1],
                    ],
                    "area": (shape.bbox_xyxy[2] - shape.bbox_xyxy[0]) * (shape.bbox_xyxy[3] - shape.bbox_xyxy[1]),
                    "iscrowd": 0,
                })
                ann_id += 1
        return coco

    # ==== 各格式 → 内部 XLABEL ====

    @staticmethod
    def voc_xml_to_image(xml_path: str) -> AnnotationImage:
        """Pascal VOC XML → 内部格式"""
        tree = ET.parse(xml_path)
        root = tree.getroot()

        filename = root.findtext("filename", "")
        size = root.find("size")
        w = int(size.findtext("width", "0"))
        h = int(size.findtext("height", "0"))

        shapes = []
        for obj in root.findall("object"):
            name = obj.findtext("name", "")
            bnd = obj.find("bndbox")
            if bnd is not None:
                x1 = float(bnd.findtext("xmin", "0"))
                y1 = float(bnd.findtext("ymin", "0"))
                x2 = float(bnd.findtext("xmax", "0"))
                y2 = float(bnd.findtext("ymax", "0"))
                shapes.append(AnnotationShape(
                    label=name, shape_type=ShapeType.RECTANGLE,
                    points=[[x1, y1], [x2, y2]],
                ))

        return AnnotationImage(image_path=filename, image_width=w, image_height=h, shapes=shapes)

    @staticmethod
    def yolo_txt_to_image(txt_path: str, img_w: int, img_h: int, classes: list[str]) -> AnnotationImage:
        """YOLO TXT → 内部格式"""
        shapes = []
        if os.path.exists(txt_path):
            with open(txt_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 5:
                        continue
                    cls_id = int(parts[0])
                    if len(parts) == 5:
                        # 检测格式: cls cx cy w h
                        cx, cy, bw, bh = map(float, parts[1:5])
                        x1 = (cx - bw / 2) * img_w
                        y1 = (cy - bh / 2) * img_h
                        x2 = (cx + bw / 2) * img_w
                        y2 = (cy + bh / 2) * img_h
                        shapes.append(AnnotationShape(
                            label=classes[cls_id] if cls_id < len(classes) else str(cls_id),
                            shape_type=ShapeType.RECTANGLE,
                            points=[[x1, y1], [x2, y2]],
                        ))
                    elif len(parts) > 5:
                        # 分割格式: cls x1 y1 x2 y2 ...
                        pts = [(float(parts[i]) * img_w, float(parts[i + 1]) * img_h) for i in range(1, len(parts), 2)]
                        shapes.append(AnnotationShape(
                            label=classes[cls_id] if cls_id < len(classes) else str(cls_id),
                            shape_type=ShapeType.POLYGON,
                            points=pts,
                        ))

        stem = Path(txt_path).stem
        return AnnotationImage(image_path=f"{stem}.jpg", image_width=img_w, image_height=img_h, shapes=shapes)
