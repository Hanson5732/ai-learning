from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, JSON, DateTime
from sqlalchemy.sql import func
from app.db.database import Base
import enum

# 定义枚举类型
class DifficultyEnum(enum.Enum):
    intro = "intro"
    mid = "mid"
    adv = "adv"

class SourceEnum(enum.Enum):
    manual = "manual"
    ppt = "ppt"

class ActionEnum(enum.Enum):
    generate = "generate"
    regenerate = "regenerate"
    upload_ppt = "upload_ppt"
    answer = "answer"

# 1. 用户表
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)

# 2. 会话表
class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    token = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)

# 3. 知识点表
class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    difficulty = Column(Enum(DifficultyEnum))
    content_text = Column(Text)
    source = Column(Enum(SourceEnum))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

# 4. 题目表
class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge_entries.id"))
    prompt = Column(Text)
    options = Column(JSON)
    correct_answer = Column(String(255))
    explanation = Column(Text)
    difficulty = Column(Enum(DifficultyEnum))
    created_at = Column(DateTime, server_default=func.now())

# 5. 用户答题记录表
class UserAttempt(Base):
    __tablename__ = "user_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_answer = Column(String(255))
    is_correct = Column(Boolean)
    attempt_time = Column(DateTime, server_default=func.now())
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)

# 6. 错题本/合集表
class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100))
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

# 7. 收藏表
class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

# 8. 历史记录表
class HistoryLog(Base):
    __tablename__ = "history_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    knowledge_id = Column(Integer, ForeignKey("knowledge_entries.id"), nullable=True)
    action = Column(Enum(ActionEnum))
    meta_data = Column(JSON) # 避免和 Python 关键字 meta 冲突
    timestamp = Column(DateTime, server_default=func.now())

# 9. PPT 上传记录表
class PptUpload(Base):
    __tablename__ = "ppt_uploads"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(255))
    s3_path = Column(String(255))
    extracted_points = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(String(50))