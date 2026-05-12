"""多模型推断服务 — 集成融合策略"""

import numpy as np


def _iou(box1, box2):
    """计算两个归一化边界框的IoU [x1,y1,x2,y2]"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    return inter / (area1 + area2 - inter + 1e-6)


def nms_fusion(all_boxes: list[list[dict]], iou_threshold: float = 0.45) -> list[dict]:
    """NMS融合：合并所有模型检测结果后执行非极大值抑制"""
    all_dets = []
    for boxes in all_boxes:
        all_dets.extend(boxes)

    if not all_dets:
        return []

    all_dets.sort(key=lambda x: x["confidence"], reverse=True)
    kept = []

    while all_dets:
        best = all_dets.pop(0)
        kept.append(best)
        filtered = []
        for box in all_dets:
            if box["class_name"] != best["class_name"]:
                filtered.append(box)
            elif _iou(best["bbox"], box["bbox"]) < iou_threshold:
                filtered.append(box)
        all_dets = filtered

    return kept


def wbf_fusion(
    all_boxes: list[list[dict]], weights: list[float] | None = None, iou_threshold: float = 0.55, conf_threshold: float = 0.25
) -> list[dict]:
    """加权框融合：对每个类别独立进行加权平均合并"""
    if weights is None:
        weights = [1.0] * len(all_boxes)

    # 按类别分组
    class_boxes: dict[str, list[tuple[int, dict]]] = {}
    for model_idx, boxes in enumerate(all_boxes):
        for box in boxes:
            cls = box["class_name"]
            if cls not in class_boxes:
                class_boxes[cls] = []
            class_boxes[cls].append((model_idx, box))

    fused = []
    for cls_name, entries in class_boxes.items():
        entries.sort(key=lambda x: x[1]["confidence"] * weights[x[0]], reverse=True)
        clusters = []

        for model_idx, box in entries:
            merged = False
            for cluster in clusters:
                cluster_iou = max(_iou(box["bbox"], b) for _, b in cluster)
                if cluster_iou >= iou_threshold:
                    cluster.append((model_idx, box))
                    merged = True
                    break
            if not merged:
                clusters.append([(model_idx, box)])

        for cluster in clusters:
            conf_sum = 0.0
            bx_sum = np.zeros(4)
            for model_idx, box in cluster:
                w = weights[model_idx] * box["confidence"]
                conf_sum += w
                bx_sum += np.array(box["bbox"]) * w

            avg_bbox = (bx_sum / conf_sum).tolist()
            avg_conf = conf_sum / sum(weights[:len(cluster)])

            if avg_conf >= conf_threshold:
                fused.append({
                    "bbox": [round(v, 4) for v in avg_bbox],
                    "class_name": cls_name,
                    "confidence": round(min(avg_conf, 1.0), 3),
                })

    return fused


def voting_fusion(all_boxes: list[list[dict]], min_votes: int = 2, iou_threshold: float = 0.45) -> list[dict]:
    """投票融合：至少min_votes个模型都检测到的框才保留"""
    model_count = len(all_boxes)
    if model_count < min_votes:
        min_votes = model_count

    fused = []
    for cls_name in _collect_classes(all_boxes):
        class_entries = []
        for model_idx, boxes in enumerate(all_boxes):
            for box in boxes:
                if box["class_name"] == cls_name:
                    class_entries.append((model_idx, box))

        class_entries.sort(key=lambda x: x[1]["confidence"], reverse=True)
        used = set()

        for i, (mi, box_a) in enumerate(class_entries):
            if i in used:
                continue
            cluster = [(mi, box_a)]
            used.add(i)
            for j, (mj, box_b) in enumerate(class_entries):
                if j in used:
                    continue
                if _iou(box_a["bbox"], box_b["bbox"]) >= iou_threshold:
                    cluster.append((mj, box_b))
                    used.add(j)

            voters = len(set(m for m, _ in cluster))
            if voters >= min_votes:
                avg_conf = np.mean([b[1]["confidence"] for b in cluster])
                fused_box = {
                    "bbox": box_a["bbox"].copy(),
                    "class_name": cls_name,
                    "confidence": round(float(avg_conf), 3),
                }
                fused.append(fused_box)

    return fused


def _collect_classes(all_boxes: list[list[dict]]) -> set[str]:
    classes: set[str] = set()
    for boxes in all_boxes:
        for b in boxes:
            classes.add(b["class_name"])
    return classes
