from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.models.core import User, Collection, Favorite, Question

router = APIRouter()

# --- Pydantic 模型 ---
class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None

class FavoriteCreate(BaseModel):
    question_id: int
    collection_id: Optional[int] = None

# --- 错题集 (Collection) 接口 ---
@router.get("/collections")
def get_collections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Collection).filter(Collection.user_id == current_user.id).all()

@router.post("/collections")
def create_collection(req: CollectionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_col = Collection(user_id=current_user.id, name=req.name, description=req.description)
    db.add(new_col)
    db.commit()
    db.refresh(new_col)
    return new_col

# --- 收藏 (Favorite) 接口 ---
@router.post("/favorites")
def add_favorite(req: FavoriteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 检查是否已经收藏过
    exist = db.query(Favorite).filter(
        Favorite.user_id == current_user.id, 
        Favorite.question_id == req.question_id
    ).first()
    if exist:
        # 如果传了新的 collection_id，就更新它
        exist.collection_id = req.collection_id
        db.commit()
        return {"message": "已更新收藏夹", "id": exist.id}
        
    new_fav = Favorite(user_id=current_user.id, question_id=req.question_id, collection_id=req.collection_id)
    db.add(new_fav)
    db.commit()
    db.refresh(new_fav)
    return {"message": "收藏成功", "id": new_fav.id}

@router.delete("/favorites/{question_id}")
def remove_favorite(question_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id, 
        Favorite.question_id == question_id
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
    return {"message": "已取消收藏"}

@router.get("/favorites")
def get_favorites(collection_id: Optional[int] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 连表查询，把题目内容一起带出来
    query = db.query(Favorite, Question).join(Question, Favorite.question_id == Question.id).filter(Favorite.user_id == current_user.id)
    if collection_id is not None:
        query = query.filter(Favorite.collection_id == collection_id)
    
    results = query.all()
    # 组装返回给前端的数据
    return [
        {
            "favorite_id": fav.id,
            "collection_id": fav.collection_id,
            "question": {
                "id": q.id,
                "prompt": q.prompt,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation
            }
        }
        for fav, q in results
    ]