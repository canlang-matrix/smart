"""
简易测试脚本：向本地 `/api/chat` 发送问题并打印回复。
确保 Flask 服务正在运行且 `OPENAI_API_KEY` 已在系统环境中设置（可选）。
"""
import os
import requests

def test_chat(question):
    url = 'http://127.0.0.1:5000/api/chat'
    try:
        r = requests.post(url, json={'message': question}, timeout=10)
        r.raise_for_status()
        j = r.json()
        print('Reply:', j.get('reply') or j.get('error'))
    except Exception as e:
        print('请求失败：', e)

if __name__ == '__main__':
    q = os.environ.get('TEST_QUESTION', '当前温度较高，我该如何处理？')
    test_chat(q)
