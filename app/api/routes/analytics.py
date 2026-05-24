# ============================================
# FILE:
# app/api/routes/analytics.py
# ============================================

from fastapi import APIRouter, Depends, Query

from app.auth.admin_auth import verify_admin
from app.services.usage_service import UsageTracker

router = APIRouter()

# ============================================
# USAGE SUMMARY
# ============================================

@router.get("/summary")
async def usage_summary(
    admin=Depends(verify_admin),
):
    return UsageTracker.get_summary()

# ============================================
# RECENT LOGS
# ============================================

@router.get("/recent")
async def recent_usage(
    limit: int = Query(
        default=50, ge=1, le=200
    ),
    admin=Depends(verify_admin),
):
    return UsageTracker.get_recent(limit)

# ============================================
# DAILY STATS
# ============================================

@router.get("/daily")
async def daily_stats(
    days: int = Query(
        default=30, ge=1, le=365
    ),
    admin=Depends(verify_admin),
):
    return UsageTracker.get_daily_stats(days)
