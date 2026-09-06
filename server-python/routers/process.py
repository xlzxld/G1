from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from routers.auth import get_current_user
import models, schemas

# Router 级鉴权（8/6 报告 P0-1）
router = APIRouter(prefix="/process-flows", tags=["process-flows"], dependencies=[Depends(get_current_user)])

@router.get("", response_model=List[schemas.ProcessFlowResponse])
def get_process_flows(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    flows = db.query(models.ProcessFlow).filter(models.ProcessFlow.is_template == 1).offset(skip).limit(limit).all()
    return flows

@router.post("", response_model=schemas.ProcessFlowResponse)
def create_process_flow(flow: schemas.ProcessFlowCreate, db: Session = Depends(get_db)):
    if not flow.name or not flow.name.strip():
        raise HTTPException(status_code=400, detail="工艺模板名称不能为空")
    db_flow = models.ProcessFlow(**flow.model_dump(exclude={'is_template'}), is_template=1)
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
    # CRITICAL 守卫：order_id 非空的是订单实例流程（无 FK 关联，删模板接口曾可
    # 连带级联删除订单全部工序与工序照片）。实例流程只能随订单删除。
    if flow.order_id:
        raise HTTPException(status_code=400, detail="该流程是订单实例，不能从模板管理删除")
    db.delete(flow)
    db.commit()
    return {"ok": True}

from pydantic import BaseModel
class StepsUpdate(BaseModel):
    steps: List[dict]

@router.put("/{flow_id}/steps")
def update_process_steps(flow_id: int, payload: StepsUpdate, db: Session = Depends(get_db)):
    """保存模板步骤——按位置差量 UPDATE 而非全删重建。

    旧实现 delete+reinsert 会静默抹掉 outsourced/vendor_id/cost/status，且
    Document.step_id CASCADE 连带删除工序照片（CRITICAL）。现按序号位置
    逐行更新运行时字段，仅新增行才 INSERT、尾部裁剪才 DELETE。
    仅模板可编辑；订单实例流程在此返回 400。"""
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Process Flow not found")
    if flow.is_template != 1:
        raise HTTPException(status_code=400, detail="订单实例流程不能在此编辑步骤")

    for s in payload.steps:
        if not s.get("name") or not str(s.get("name")).strip():
            raise HTTPException(status_code=400, detail="工序名称不能为空")
        if not s.get("assignee") or not str(s.get("assignee")).strip():
            raise HTTPException(status_code=400, detail="负责人不能为空")

    existing = db.query(models.ProcessStep).filter(
        models.ProcessStep.flow_id == flow_id
    ).order_by(models.ProcessStep.seq).all()

    for idx, s in enumerate(payload.steps):
        fields = dict(
            name=str(s.get("name", "")).strip(),
            seq=s.get("seq", idx + 1),
            required=1 if s.get("required") else 0,
            completion_condition=s.get("completion_condition", "manual"),
            assignee=str(s.get("assignee", "")).strip(),
            # 外协标志可由编辑器设置（此前唯一来源是 seed 数据）
            outsourced=1 if s.get("outsourced") else 0,
        )
        if idx < len(existing):
            # 原位 UPDATE：status/started_at/completed_at/vendor_id/sent_date/
            # return_date/cost 及关联照片全部保留
            for k, v in fields.items():
                setattr(existing[idx], k, v)
        else:
            db.add(models.ProcessStep(flow_id=flow_id, status="pending", **fields))

    # 尾部裁剪：用户明确删除的末尾步骤才删除（其照片随之删除属预期）
    if len(payload.steps) < len(existing):
        for extra in existing[len(payload.steps):]:
            db.delete(extra)

    db.commit()
    return {"ok": True}
