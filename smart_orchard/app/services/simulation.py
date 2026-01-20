import threading
import time
import random
from app import db
from app.models import SensorData


def start_simulation(app):
    """启动后台线程模拟传感器数据"""
    thread = threading.Thread(target=_simulate_loop, args=(app,), daemon=True)
    thread.start()


def _simulate_loop(app):
    with app.app_context():
        while True:
            # 模拟生成数据
            temp = round(25 + random.uniform(-3, 3), 2)
            hum = round(60 + random.uniform(-10, 10), 2)
            light = round(1000 + random.uniform(-200, 200), 2)

            new_data = SensorData(temperature=temp, humidity=hum, light=light)
            db.session.add(new_data)
            db.session.commit()

            # print(f"[模拟] 数据存入: T={temp}")
            time.sleep(5)  # 5秒生成一次