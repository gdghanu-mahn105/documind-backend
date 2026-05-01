from fastapi import APIRouter, Depends, HTTPException, Body, status, BackgroundTasks
from sqlalchemy.orm import Session, selectinload
from app.database import get_db
from app.api.auth import get_current_user
from app.models import models
from app.core.rag import generate_mindmap_from_rag
import json
from app.schemas import mindmap_schemas as schemas
from app.schemas.common_schemas import GenerateRequest
from sqlalchemy import desc
from app.database import SessionLocal


router = APIRouter(
    prefix="/mindmaps",
    tags=["Mindmaps"]
)

@router.get("/list-by-documents")
def get_mindmaps_grouped_by_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    documents = db.query(models.UserDocument).options(
        selectinload(models.UserDocument.mindmaps)
    ).filter(models.UserDocument.user_id == current_user.user_id
            ,models.UserDocument.is_deleted == False
             ).order_by( desc(models.UserDocument.created_at)
              ).all()

    result = []
    for doc in documents:
        if doc.is_deleted:
            continue
        result.append({
            "document_id": doc.document_id,
            "file_name": doc.file_name,
            "created_at": doc.created_at,
            "mindmap_count": len(doc.mindmaps),
            "mindmaps": [
                {
                    "mindmap_id": m.mindmap_id,
                    "title": m.title,
                    "created_at": m.created_at,
                    "status": m.status
                } for m in doc.mindmaps if not m.is_deleted
            ]
        })    
    return result

@router.post("/{document_id}/mindmap")
async def create_mindmap_api(
    document_id: int, 
    request_data: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_mindmap = models.Mindmap(
        document_id=document_id,
        title="Đang khởi tạo...",
        user_hint=request_data.user_hint,
        status="PENDING",
        structure_json="{}"
    )
    db.add(new_mindmap)
    db.commit()
    db.refresh(new_mindmap)

    background_tasks.add_task(generate_mindmap_task, new_mindmap.mindmap_id, document_id,request_data.user_hint)
    
    return {
        "message": "AI is processing to generate mindmap!",
        "mindmap_id": new_mindmap.mindmap_id,
        "status": "PENDING"
    }

@router.get("/{mindmap_id}/status")
def get_mindmap_status(
    mindmap_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    mindmap = db.query(models.Mindmap).filter(models.Mindmap.mindmap_id == mindmap_id, models.Mindmap.is_deleted == False).first()
    
    if not mindmap:
        raise HTTPException(status_code=404, detail="Không thấy sơ đồ này")
    
    return {
        "mindmap_id": mindmap.mindmap_id,
        "status": mindmap.status,
        "title": mindmap.title,
        "structure_json": json.loads(mindmap.structure_json) if mindmap.status == "COMPLETED" else None
    }

@router.get("/{mindmap_id}", response_model=schemas.MindmapDetail)
def get_mindmap_detail(
    mindmap_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    mindmap = db.query(models.Mindmap).filter(models.Mindmap.mindmap_id == mindmap_id, models.Mindmap.is_deleted == False).first()
    
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mindmap not found")
    
    return {
        "mindmap_id": mindmap.mindmap_id,
        "status": mindmap.status,
        "document_id": mindmap.document_id,
        "title": mindmap.title,
        "created_at": mindmap.created_at,
        "structure_json": json.loads(mindmap.structure_json)
    }


@router.put("/{mindmap_id}", response_model=schemas.MindmapDetail)
def update_mindmap(
    mindmap_id: int,
    update_data: schemas.MindmapUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    mindmap = db.query(models.Mindmap).join(models.UserDocument).filter(
        models.Mindmap.mindmap_id == mindmap_id,
        models.UserDocument.user_id == current_user.user_id,
        models.Mindmap.is_deleted == False
    ).first()
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mindmap not found or access denied")

    if update_data.title:
        mindmap.title = update_data.title
    

    mindmap.structure_json = json.dumps(update_data.structure_json, ensure_ascii=False)

    db.commit()
    db.refresh(mindmap)

    return {
        "mindmap_id": mindmap.mindmap_id,
        "status": mindmap.status,
        "title": mindmap.title,
        "document_id": mindmap.document_id,
        "created_at": mindmap.created_at,
        "structure_json": update_data.structure_json 
    }


@router.delete("/{mindmap_id}", status_code=status.HTTP_200_OK, summary="Soft-delete a mindmap")
def delete_mindmap(
    mindmap_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
   
    mindmap = db.query(models.Mindmap).join(models.UserDocument).filter(
        models.Mindmap.mindmap_id == mindmap_id,
        models.UserDocument.user_id == current_user.user_id,
        models.Mindmap.is_deleted == False

    ).first()

    if not mindmap:
        raise HTTPException(
            status_code=404, 
            detail="Mindmap not found or not have permission to delete!"
        )

    try:
        mindmap.is_deleted = True
        db.commit()
        
        return {
            "message": f"Delete mindmap successfully: '{mindmap.title}'!",
            "mindmap_id": mindmap_id
        }
    except Exception as e:
        db.rollback()
        print(f"[DELETE ERROR]: {e}")
        raise HTTPException(status_code=500, detail="Error when deleting mindmap.")
    
async def generate_mindmap_task(mindmap_id: int, document_id: int, user_hint: str):
    db = SessionLocal()
    try:
        mindmap = db.query(models.Mindmap).filter(models.Mindmap.mindmap_id == mindmap_id, models.Mindmap.is_deleted == False).first()
        if mindmap:
            mindmap.status = "PROCESSING"
            db.commit()

        mindmap_data = await generate_mindmap_from_rag(document_id, user_hint)

        if mindmap_data:
            mindmap.status = "COMPLETED"
            mindmap.title = mindmap_data.get("name", mindmap.title)
            mindmap.structure_json = json.dumps(mindmap_data)
        else:
            mindmap.status = "FAILED"
        
        db.commit()
    except Exception as e:
        print(f"Error in background task: {e}")
        mindmap = db.query(models.Mindmap).filter(models.Mindmap.mindmap_id == mindmap_id, models.Mindmap.is_deleted == False).first()
        if mindmap:
            mindmap.status = "FAILED"
            db.commit()
    finally:
        db.close()