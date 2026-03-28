from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.core.config import settings
from app.models.core import User
from app.crud import crud_user

# 这里的 tokenUrl 必须和咱们 auth.py 里登录接口的路径一模一样
# 这样 FastAPI 自动生成的 Swagger UI 才知道去哪里拿 Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    解析 JWT Token 并返回当前登录的数据库用户对象。
    如果 Token 无效或过期，直接拦截请求并报错。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证您的凭据，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 尝试解密 token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
    except jwt.ExpiredSignatureError:
        # 专门捕获 Token 过期的异常，给前端友好的提示
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="登录已过期，请重新登录"
        )
    except jwt.InvalidTokenError:
        # 其他解析错误（比如伪造的 token）
        raise credentials_exception
    
    # 根据解密出来的用户名去数据库查人
    user = crud_user.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
        
    return user