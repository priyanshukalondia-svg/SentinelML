from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import AuditLog, RecoveryWorkflow
from app.schemas.schemas import AuditLogOut, RecoveryWorkflowOut

router = APIRouter(prefix="/api/v1", tags=["audit"])


@router.get("/audit-log", response_model=List[AuditLogOut])
def get_audit_log(db: Session = Depends(get_db)):
    return db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(300)).scalars().all()


@router.get("/recovery", response_model=List[RecoveryWorkflowOut])
def list_recovery_workflows(db: Session = Depends(get_db)):
    return db.execute(select(RecoveryWorkflow).order_by(RecoveryWorkflow.started_at.desc()).limit(50)).scalars().all()


@router.get("/recovery/{workflow_id}", response_model=RecoveryWorkflowOut)
def get_recovery_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.get(RecoveryWorkflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail={"error": "WORKFLOW_NOT_FOUND", "message": "Recovery workflow not found."})
    return workflow
