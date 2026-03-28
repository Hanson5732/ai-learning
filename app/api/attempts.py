from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.core import User, Question, UserAttempt

router = APIRouter()

class AnswerItem(BaseModel):
    question_id: int
    selected_answer: str

class BatchEvaluateRequest(BaseModel):
    knowledge_id: int
    answers: List[AnswerItem]

@router.post("/batch-evaluate")
def evaluate_answers(
    req: BatchEvaluateRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 把这组题全都查出来
    questions = db.query(Question).filter(Question.knowledge_id == req.knowledge_id).all()
    q_map = {q.id: q for q in questions}

    correct_count = 0
    results = []

    for ans in req.answers:
        q = q_map.get(ans.question_id)
        if not q: continue

        # 判断对错
        is_correct = (ans.selected_answer == q.correct_answer)
        if is_correct:
            correct_count += 1

        # 记录用户答题历史
        attempt = UserAttempt(
            user_id=current_user.id,
            question_id=q.id,
            selected_answer=ans.selected_answer,
            is_correct=is_correct
        )
        db.add(attempt)

        # 组装返回给前端的解析
        results.append({
            "question_id": q.id,
            "is_correct": is_correct,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation
        })

    db.commit()

    total_count = len(req.answers)
    correct_rate = correct_count / total_count if total_count > 0 else 0
    # 正确率小于 40% (即 5 题对不到 2 题) 触发重做
    need_regenerate = correct_rate < 0.4 

    return {
        "correct_count": correct_count,
        "total_count": total_count,
        "correct_rate": correct_rate,
        "need_regenerate": need_regenerate,
        "results": results
    }