import json
from openai import OpenAI
from app.core.config import settings

# 假设这里配置了 API Key，实际项目中请放在 .env 文件里
client = OpenAI(
    api_key=settings.OPENAI_API_KEY, 
    base_url=settings.OPENAI_BASE_URL
)

def generate_knowledge_and_questions(topic: str, difficulty: str):
    """
    调用 LLM 生成知识点和题目，包含合法性校验
    """
    difficulty_map = {"intro": "入门", "mid": "中级", "adv": "高级"}
    level_str = difficulty_map.get(difficulty, "入门")

    # 核心 Prompt 设计
    system_prompt = """
    你是一个专业的 AI 辅导老师。用户会输入一个词语或一句话。
    你的任务是：
    1. 判断用户的输入是否是一个合理的“学术概念”、“知识点”或“学习主题”。
    2. 如果输入无意义、是日常闲聊（如“你好”、“今天吃什么”）、或者是明显恶搞的词汇，请判定为非法知识点。
    3. 如果非法，只返回错误提示。
    4. 如果合法，请根据难度生成通俗易懂的知识点解释，以及 5 道单选题（包含选项、正确答案和解析）。
    
    必须严格以 JSON 格式输出，格式如下：
    {
        "is_valid": true/false,
        "error_message": "如果非法，这里填写委婉的提示，如'这看起来不像是一个知识点哦，请换个词试试'。合法则为 null",
        "title": "规范化后的知识点名称",
        "content": "知识点详细解释，支持 Markdown",
        "questions": [
            {
                "prompt": "题目内容",
                "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                "correct_answer": "正确选项的完整内容(如: A. 选项1)",
                "explanation": "答案解析"
            }
        ]
    }
    """
    
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"知识点：{topic}，难度：{level_str}"}
        ],
        response_format={"type": "json_object"} # 强制输出 JSON
    )
    
    result_str = response.choices[0].message.content
    return json.loads(result_str)


def extract_ppt_topics(text: str):
    """
    接收 PPT 的纯文本内容，调用 LLM 提炼出核心知识点列表
    """
    system_prompt = """
    你是一个资深的教学大纲提取专家。
    用户会输入一份 PPT 课件提取出来的纯文本（可能排版混乱，包含很多噪音）。
    你的任务是：
    1. 仔细阅读文本，理解这份 PPT 主要在讲什么。
    2. 从中提炼出 3 到 8 个最核心的“知识点名称”；如果提取到的文本极少，提炼 1 到 2 个知识点即可。
    3. 知识点名称必须简练、专业（例如：“微积分链式法则”、“冯诺依曼架构”）。
    
    必须严格以 JSON 格式输出，格式如下：
    {
        "topics": ["知识点1", "知识点2", "知识点3"]
    }
    """
    
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"以下是 PPT 内容：\n\n{text}"}
        ],
        response_format={"type": "json_object"}
    )
    
    result_str = response.choices[0].message.content
    return json.loads(result_str)