from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.crud import crud_user
from app.core.security import verify_password, create_access_token
from app.api.deps import get_current_user
from app.models.core import User

router = APIRouter()

# 获取数据库会话的依赖函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # 查查邮箱或用户名是不是被占用了
    if crud_user.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="邮箱已经注册过啦")
    if crud_user.get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="用户名太抢手，换一个吧")
    
    return crud_user.create_user(db=db, user=user)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm 默认接收 username 和 password 字段
    # 这里咱们允许用户用 username 登录
    user = crud_user.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不对哦",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 签发 Token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    通过 Token 获取当前登录的用户信息
    """
    return current_user