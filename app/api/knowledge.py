from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.api.deps import get_db, get_current_user
from app.models.core import User, KnowledgeEntry, Question, DifficultyEnum, SourceEnum, Favorite, UserAttempt
from app.services.llm_service import generate_knowledge_and_questions

router = APIRouter()

class GenerateRequest(BaseModel):
    topic: str
    difficulty: str

@router.post("/generate")
def generate_knowledge(
    req: GenerateRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. 调用大模型
    try:
        llm_result = generate_knowledge_and_questions(req.topic, req.difficulty)
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI 大脑暂时短路了，请稍后再试")

    # 2. 拦截非知识点输入
    if not llm_result.get("is_valid"):
        # 直接返回 400 错误，让前端提示用户
        raise HTTPException(status_code=400, detail=llm_result.get("error_message", "这好像不是一个知识点哦。"))

    # 3. 存入数据库
    # 保存知识点
    db_knowledge = KnowledgeEntry(
        user_id=current_user.id,
        title=llm_result["title"],
        difficulty=DifficultyEnum[req.difficulty],
        content_text=llm_result["content"],
        source=SourceEnum.manual
    )
    db.add(db_knowledge)
    db.commit()
    db.refresh(db_knowledge)

    # 保存题目并获取对应的数据库 ID
    saved_questions = []
    for q_data in llm_result["questions"]:
        db_question = Question(
            knowledge_id=db_knowledge.id,
            prompt=q_data["prompt"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
            explanation=q_data["explanation"],
            difficulty=DifficultyEnum[req.difficulty]
        )
        db.add(db_question)
        db.commit()  # 提交单道题的事务
        db.refresh(db_question)  # 刷新以获取自动生成的自增 ID
        
        # 把大模型的原始数据加上数据库 ID，准备返回给前端
        q_data["id"] = db_question.id 
        saved_questions.append(q_data)

    return {
        "knowledge_id": db_knowledge.id,
        "title": db_knowledge.title,
        "content": db_knowledge.content_text,
        "questions": saved_questions # 返回带 ID 的题目列表
    }


@router.get("/history")
def get_knowledge_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = db.query(KnowledgeEntry).filter(
        KnowledgeEntry.user_id == current_user.id
    ).order_by(KnowledgeEntry.id.desc()).all()
    
    results = []
    for item in history:
        # 把这个知识点名下的 5 道题也一起查出来
        questions = db.query(Question).filter(Question.knowledge_id == item.id).all()
        q_list = [{
            "prompt": q.prompt,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation
        } for q in questions]

        results.append({
            "id": item.id,
            "title": item.title,
            "difficulty": item.difficulty.value if hasattr(item.difficulty, 'value') else item.difficulty,
            "content": item.content_text,
            "source": item.source.value if hasattr(item.source, 'value') else item.source,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else "未知时间",
            "questions": q_list  # 把题目数组塞进返回结果里
        })
    return results


@router.delete("/history/{knowledge_id}")
def delete_knowledge_history(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. 查找父亲：主记录（知识点）
    record = db.query(KnowledgeEntry).filter(
        KnowledgeEntry.id == knowledge_id,
        KnowledgeEntry.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在或无权删除")
    
    # 2. 查找儿子：关联的所有题目 ID
    questions = db.query(Question).filter(Question.knowledge_id == knowledge_id).all()
    question_ids = [q.id for q in questions]
    
    # 3. 按顺序清理后代（如果存在题目）
    if question_ids:
        # 杀孙子：删除错题本中的收藏记录
        db.query(Favorite).filter(Favorite.question_id.in_(question_ids)).delete(synchronize_session=False)
        # 杀孙子：删除用户的答题历史记录
        db.query(UserAttempt).filter(UserAttempt.question_id.in_(question_ids)).delete(synchronize_session=False)
        # 杀儿子：删除题目本身
        db.query(Question).filter(Question.knowledge_id == knowledge_id).delete(synchronize_session=False)
    
    # 4. 最后删除父亲：知识点主记录
    db.delete(record)
    db.commit()
    
    return {"message": "删除成功"}