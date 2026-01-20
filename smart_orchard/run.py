import os
from app import create_app
from app.services.simulation import start_simulation

# =======================================================
os.environ['DEEPSEEK_API_KEY'] = "sk-3382fa93cbf44299839914a4a57a2561"
os.environ['DEEPSEEK_BASE_URL'] = "https://api.deepseek.com"
os.environ['DEEPSEEK_MODEL'] = "deepseek-chat"
# =======================================================

app = create_app()

if __name__ == '__main__':
    # 启动数据模拟线程 (模拟温度、湿度数据写入数据库)
    start_simulation(app)

    print("✅ 系统已启动")
    print(f"📡 AI 模型配置: {os.environ['DEEPSEEK_MODEL']}")
    if os.environ['DEEPSEEK_API_KEY'] == "sk-这里换成你的Key":
        print("⚠️ 警告: 你还没有填写真实的 DeepSeek API Key，AI 功能将无法使用！")

    # 启动 Web 服务
    # 生产/测试时关闭 debug 重新加载，避免多进程导致端口冲突
    app.run(host='127.0.0.1', port=5000, debug=False)