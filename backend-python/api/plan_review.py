"""施工方案评审 — 文档解析、RAG增强检索、AI审查意见"""

import json
import tempfile

from fastapi import APIRouter, File, Query, UploadFile
from pydantic import BaseModel

router = APIRouter()


class ReviewOpinion(BaseModel):
    clause_ref: str
    severity: str  # 一般 / 严重 / 危急
    comment: str
    suggestion: str


class PlanReviewResult(BaseModel):
    document_id: str
    document_type: str
    opinions: list[ReviewOpinion]
    overall_assessment: str


REVIEW_SYSTEM_PROMPT = """你是电力作业安全方案评审专家，拥有十年以上电力工程安全管理经验。

请根据以下检索到的施工规范和历史案例，对提供的施工方案进行逐条审查。

审查要点：
1. 安全措施是否完备（高空作业、带电作业、机械操作）
2. 是否符合《电力安全工作规程》要求
3. 施工流程是否合理，有无遗漏关键步骤
4. 应急预案是否充分
5. 人员资质与分工是否明确

输出格式为JSON数组，每个元素包含：
- clause_ref: 引用的规范条款编号或名称
- severity: 严重程度（一般/严重/危急）
- comment: 具体审查意见
- suggestion: 修改建议

如果未发现问题，返回空数组 []。
同时请在数组后单独输出一段"总体评价："开头的综合评估。"""


def _extract_text(file_content: bytes, ext: str) -> str:
    if ext == "pdf":
        import fitz

        doc = fitz.open(stream=file_content, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
    elif ext in ("docx", "doc"):
        from docx import Document

        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(file_content)
            tmp.flush()
            text = "\n".join(p.text for p in Document(tmp.name).paragraphs)
    else:
        text = file_content.decode("utf-8", errors="ignore")
    return text


def _build_opinions(parsed: list[dict]) -> list[ReviewOpinion]:
    opinions = []
    for item in parsed:
        opinions.append(
            ReviewOpinion(
                clause_ref=str(item.get("clause_ref", "")),
                severity=str(item.get("severity", "一般")),
                comment=str(item.get("comment", "")),
                suggestion=str(item.get("suggestion", "")),
            )
        )
    return opinions


@router.post("/review", response_model=PlanReviewResult)
async def review_plan(file: UploadFile = File(...)):
    """上传施工方案，AI基于知识库规范进行审查"""
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "unknown"
    content = await file.read()
    doc_text = _extract_text(content, ext)

    if not doc_text.strip():
        return PlanReviewResult(
            document_id=file.filename or "unknown",
            document_type=ext,
            opinions=[],
            overall_assessment="文档内容为空，无法评审",
        )

    # 1. 检索相关规范与案例
    from services.knowledge_service import KnowledgeService

    kb = KnowledgeService()
    standards = await kb.search(query=doc_text[:1000], top_k=5, category="施工规范")
    cases = await kb.search(query=doc_text[:1000], top_k=3, category="历史案例")

    # 2. 构建LLM上下文
    standards_ctx = "\n".join(
        f"[{s['title']}] {s['content_snippet']}" for s in standards
    ) or "暂无匹配的规范条款"
    cases_ctx = "\n".join(
        f"[{c['title']}] {c['content_snippet']}" for c in cases
    ) or "暂无相似历史案例"

    user_prompt = f"""检索到的相关规范:
{standards_ctx}

检索到的历史案例:
{cases_ctx}

待审查施工方案内容:
{doc_text[:6000]}

请逐条审查并返回JSON格式的审查意见列表。"""

    # 3. 调用LLM
    from services.llm_service import call_llm, parse_llm_json

    try:
        response = await call_llm(REVIEW_SYSTEM_PROMPT, user_prompt)
        parsed = parse_llm_json(response)
        opinions = _build_opinions(parsed)
    except Exception:
        opinions = []
        response = ""

    # 4. 提取总体评价
    overall = "施工方案审查完成"
    if "总体评价：" in response:
        overall = response.split("总体评价：")[-1].strip().split("\n")[0]
    elif opinions:
        overall = f"共发现{len(opinions)}条审查意见，请及时修改完善。"

    return PlanReviewResult(
        document_id=file.filename or "unknown",
        document_type=ext,
        opinions=opinions,
        overall_assessment=overall,
    )


@router.get("/standards/search")
async def search_standards(query: str = Query(...), top_k: int = Query(5, ge=1, le=50)):
    """检索施工规范知识库"""
    from services.knowledge_service import KnowledgeService

    kb = KnowledgeService()
    results = await kb.search(query=query, top_k=top_k, category="施工规范")
    return {"query": query, "results": results, "count": len(results)}
