from fastapi import FastAPI
from app.api import auth, knowledge, notebook, ppt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI-Learning Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有来源，方便调试
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法 (GET, POST 等)
    allow_headers=["*"],  # 允许所有请求头
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(notebook.router, prefix="/api/notebook", tags=["Notebook"])
app.include_router(ppt.router, prefix="/api/ppt", tags=["PPT"])

@app.get("/")
def read_root():
    return {"Hello": "World"}