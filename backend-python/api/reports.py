"""报告生成API — 统一报告生成、下载、删除"""

import os
from enum import Enum

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter()


class ReportType(str, Enum):
    DRAWING_REVIEW = "drawing_review"
    PLAN_REVIEW = "plan_review"
    TRAINING = "training"
    INFERENCE = "inference"


class SectionData(BaseModel):
    title: str = ""
    content: str | dict | list = ""
    severity: str = ""
    category: str = ""
    description: str = ""
    position: str = ""
    clause_ref: str = ""
    comment: str = ""
    suggestion: str = ""
    class_name: str = ""
    confidence: float = 0.0
    bbox: list[float] = []


class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    title: str
    sections: list[dict] = []
    metadata: dict = {}


class ReportResponse(BaseModel):
    report_id: str
    status: str
    download_url: str = ""
    message: str = ""


@router.post("/generate", response_model=ReportResponse)
async def generate_report(req: ReportGenerateRequest):
    """统一报告生成入口"""
    from services.report_service import ReportService, ReportType as SvcReportType

    svc = ReportService()
    type_map = {
        ReportType.DRAWING_REVIEW: SvcReportType.DRAWING_REVIEW,
        ReportType.PLAN_REVIEW: SvcReportType.PLAN_REVIEW,
        ReportType.TRAINING: SvcReportType.TRAINING,
        ReportType.INFERENCE: SvcReportType.INFERENCE,
    }

    try:
        filepath = svc.generate(type_map[req.report_type], req.title, req.sections, req.metadata)
        report_id = os.path.splitext(os.path.basename(filepath))[0]
        return ReportResponse(
            report_id=report_id,
            status="completed",
            download_url=f"/api/reports/{report_id}",
            message="报告生成成功",
        )
    except Exception as e:
        return ReportResponse(report_id="", status="failed", message=str(e))


@router.get("/{report_id}")
async def download_report(report_id: str):
    """下载生成的报告文件"""
    from config import settings

    report_dir = getattr(settings, "report_dir", "./reports")
    filepath = os.path.join(report_dir, f"{report_id}.docx")
    if not os.path.exists(filepath):
        return {"error": "报告不存在"}

    return FileResponse(filepath, filename=f"{report_id}.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.get("/{report_id}/status")
async def report_status(report_id: str):
    """查询报告状态"""
    from config import settings

    report_dir = getattr(settings, "report_dir", "./reports")
    filepath = os.path.join(report_dir, f"{report_id}.docx")
    exists = os.path.exists(filepath)
    return {"report_id": report_id, "status": "ready" if exists else "not_found", "download_url": f"/api/reports/{report_id}" if exists else ""}


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """删除报告文件"""
    from config import settings

    report_dir = getattr(settings, "report_dir", "./reports")
    filepath = os.path.join(report_dir, f"{report_id}.docx")
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"report_id": report_id, "status": "deleted"}
    return {"report_id": report_id, "status": "not_found"}
