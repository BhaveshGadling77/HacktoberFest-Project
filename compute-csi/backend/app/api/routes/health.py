from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "compute-csi-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
    }
