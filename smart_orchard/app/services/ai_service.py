import os
import requests
from datetime import datetime  # 关键导入：用于获取时间
from app.models import SensorData


# ---------------------------------------------------------
# 1. 核心 AI 对话服务 (包含 DeepSeek 接入 + 时间修正)
# ---------------------------------------------------------

def chat_with_ai(user_question: str):
    """
    使用 DeepSeek / OpenAI 兼容接口进行对话，自动注入最新传感器数据 + 当前时间作为上下文。
    """
    import os
    try:
        from openai import OpenAI
    except Exception:
        try:
            import openai
        except Exception:
            OpenAI = None

    # 优先 DeepSeek 专用变量
    api_key = os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('OPENAI_API_KEY')
    base_url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    model_name = os.environ.get('DEEPSEEK_MODEL', os.environ.get('OPENAI_MODEL', 'deepseek-chat'))

    # --- 1. 获取实时传感器数据 ---
    try:
        latest = SensorData.query.order_by(SensorData.id.desc()).first()
    except Exception:
        latest = None

    env_info = "暂无数据"
    if latest:
        env_info = f"温度: {latest.temperature}°C, 湿度: {latest.humidity}%, 光照: {latest.light}Lx"

    # --- 2. 获取当前系统时间 (关键修改) ---
    # 格式示例：2026年01月06日 15:30 星期二
    week_days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    now = datetime.now()
    current_time_str = now.strftime('%Y年%m月%d日 %H:%M') + " " + week_days[now.weekday()]

    # --- 3. 构建提示词 (System Prompt) ---
    system_prompt = f"""
    你是一个智慧果园的高级农业专家助手。

    【当前时间】：{current_time_str}
    【果园环境】：[{env_info}]

    请根据上述环境数据和时间，回答用户的问题。
    回答要求：
    1. 结合当前季节和时间给出建议。
    2. 如果环境数据异常（如高温、低湿），优先发出预警。
    3. 语气专业、亲切。
    """

    # 如果没有配置 Key，进入简单的规则回复
    if not api_key:
        return chat_response(user_question)

    # --- 4. 调用 AI 接口 ---
    try:
        if OpenAI is not None:
            # 使用官方 SDK (OpenAI / DeepSeek)
            client = OpenAI(api_key=api_key, base_url=base_url)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                temperature=0.7,
                stream=False
            )
            return resp.choices[0].message.content
        else:
            # 使用 requests 直连 (备用方案)
            url = f"{base_url}/v1/chat/completions"
            headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
            payload = {
                'model': model_name,
                'messages': [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                'temperature': 0.7
            }
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            r.raise_for_status()
            j = r.json()
            return j['choices'][0]['message']['content']

    except Exception as e:
        print(f"AI 调用失败: {e}")
        return f"🤖 抱歉，AI 连接出现问题：{str(e)}"


# ---------------------------------------------------------
# 2. 辅助功能 (旧版规则回复/工具函数)
# ---------------------------------------------------------

def get_planting_advice(temp, hum):
    """(旧接口) 根据环境数据返回建议"""
    if temp > 32:
        return "⚠️ 高温预警：当前温度过高，建议开启遮阳网并增加灌溉频率，防止果实灼伤。"
    elif hum > 80:
        return "⚠️ 湿度过高：病虫害风险增加，建议暂停喷灌，开启通风设备。"
    elif hum < 40:
        return "⚠️ 湿度过低：建议立即进行根部滴灌，保持土壤水分。"
    else:
        return "✅ 环境优良：当前气候适宜果树生长，适合进行正常的修剪维护。"


def chat_response(message, history=None, use_web=False):
    """
    (回退接口) 当没有配置 API Key 时使用的简单规则回复
    """
    msg = message.lower()

    # 简单的关键词匹配规则
    if '时间' in msg or '几点' in msg:
        return f"系统当前时间是：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    if '温度' in msg or '高温' in msg:
        return "建议：\n1) 临时遮阳：在白天高温时段拉遮阳网。\n2) 分次灌溉：早晚各一次，避免中午灌溉。"

    if '湿度' in msg or '潮湿' in msg:
        return "建议：\n1) 减少喷灌并开启通风。\n2) 检查叶面是否有病斑。"

    if '卖' in msg or '销售' in msg:
        return "建议：\n1) 按成熟度分批采摘。\n2) 同时使用本地线上平台和批发渠道。"

    return "（未配置 DeepSeek Key，使用规则回复）抱歉，我无法理解您的问题。请配置 API Key 以启用智能对话。"


def get_llm_status():
    """返回本机是否配置了 API Key"""
    api_key = os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('OPENAI_API_KEY')
    model = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
    return {'available': bool(api_key), 'model': model}


# ---------------------------------------------------------
# 3. 知识库 & 搜索桩代码 (防止 routes.py 报错)
# ---------------------------------------------------------
# 以下函数保留为空或简单实现，防止 import error

def search_knowledge(query, topk=3):
    return []


def add_knowledge_document(title, content):
    return "mock_path"


def get_kb_info():
    return {'count': 0}


def get_current_weather():
    return None