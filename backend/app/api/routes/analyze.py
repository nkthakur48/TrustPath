import logging
import time

from fastapi import APIRouter

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services import analyzer

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    # sync def: FastAPI runs it in a threadpool, so the blocking LLM call is fine.
    started = time.perf_counter()
    result = analyzer.analyze(req)
    # Never log posting text, recruiter email, or the API key.
    log.info("analyze verdict=%s engine=%s latency_ms=%d", result.verdict, result.engine,
             (time.perf_counter() - started) * 1000)
    return result
