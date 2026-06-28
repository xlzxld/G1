from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/process-flows", tags=["process-flows"])

@router.get("", response_model=List[schemas.ProcessFlowResponse])
def get_process_flows(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    flows = db.query(models.ProcessFlow).filter(models.ProcessFlow.is_template == 1).offset(skip).limit(limit).all()
    return flows

@router.post("", response_model=schemas.ProcessFlowResponse)
def create_process_flow(flow: schemas.ProcessFlowCreate, db: Session = Depends(get_db)):
    if not flow.name or not flow.name.strip():
        raise HTTPException(status_code=400, detail="工艺模板名称不能为空")
    db_flow = models.ProcessFlow(**flow.model_dump(), is_template=1)
    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    return db_flow

@router.get("/{flow_id}", response_model=schemas.ProcessFlowResponse)
def get_process_flow(flow_id: int, db: Session = Depends(get_db)):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if flow is None:
        raise HTTPException(status_code=404, detail="Process Flow not found")
    return flow

@router.put("/{flow_id}", response_model=schemas.ProcessFlowResponse)
def update_process_flow(flow_id: int, flow_update: schemas.ProcessFlowCreate, db: Session = Depends(get_db)):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Process Flow not found")
    if not flow_update.name or not flow_update.name.strip():
        raise HTTPException(status_code=400, detail="工艺模板名称不能为空")
        
    flow.name = flow_update.name
    flow.description = flow_update.description
    db.commit()
    db.refresh(flow)
    return flow

@router.delete("/{flow_id}")
def delete_process_flow(flow_id: int, db: Session = Depends(get_db)):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Process Flow not found")
    db.delete(flow)
    db.commit()
    return {"ok": True}

from pydantic import BaseModel
class StepsUpdate(BaseModel):
    steps: List[dict]

@router.put("/{flow_id}/steps")
def update_process_steps(flow_id: int, payload: StepsUpdate, db: Session = Depends(get_db)):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Process Flow not found")
    
    # Delete old steps
    db.query(models.ProcessStep).filter(models.ProcessStep.flow_id == flow_id).delete()
    
    # Insert new steps
    for s in payload.steps:
        if not s.get("name") or not s.get("name").strip():
            raise HTTPException(status_code=400, detail="工序名称不能为空")
        if not s.get("assignee") or not s.get("assignee").strip():
            raise HTTPException(status_code=400, detail="负责人不能为空")
            
        new_step = models.ProcessStep(
            flow_id=flow_id,
            name=s.get("name", ""),
            seq=s.get("seq", 0),
            required=1 if s.get("required") else 0,
            completion_condition=s.get("completion_condition", "manual"),
            assignee=s.get("assignee", "")
        )
        db.add(new_step)
    
    db.commit()
    return {"ok": True}
