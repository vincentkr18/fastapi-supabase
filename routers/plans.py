"""
SaaS plan endpoints.
Public endpoints - no authentication required.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from models import Plan
from schemas import PlanResponse

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("", response_model=List[PlanResponse])
async def list_plans(
    db: Session = Depends(get_db),
    active_only: bool = True
):
    """
    List all available SaaS plans.
    
    Public endpoint - no authentication required.
    By default, only returns active plans.
    """
    query = db.query(Plan)
    
    if active_only:
        query = query.filter(Plan.active == True)
    
    plans = query.order_by(Plan.price_monthly).all()
    return plans


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific plan.
    
    Public endpoint - no authentication required.
    """
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    return plan
