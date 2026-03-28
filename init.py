from app.db.database import engine, Base
# 这里必须导入所有的 model，这样 SQLAlchemy 才能识别到它们
from app.models import core 

print("正在往 MySQL 里建表...")
# 这行代码会自动检测并创建所有还没建的表
Base.metadata.create_all(bind=engine)
print("搞定！表建完了。")