# app/api/routers/analytics.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.schemas.analytics import DashboardOverview, AiOperationalSummary
from app.services.analytics_service import DashboardAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/workspaces/{workspace_id}/overview",
    response_model=DashboardOverview,
)
def get_dashboard_overview(
    workspace_id: UUID,
    db: Session = Depends(get_db),
):
    service = DashboardAnalyticsService(db)
    return service.get_overview(workspace_id)


@router.get(
    "/workspaces/{workspace_id}/ai-operational-summary",
    response_model=AiOperationalSummary,
)
async def get_ai_operational_summary(
    workspace_id: UUID,
    db: Session = Depends(get_db),
):
    service = DashboardAnalyticsService(db)
    return await service.get_ai_operational_summary(workspace_id)