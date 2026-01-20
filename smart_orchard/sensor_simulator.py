import time
import random
from datetime import datetime
from app import create_app, db
from app.models import SensorData, ControlCommand


def run_simulator(interval=60):
    app = create_app()

    with app.app_context():
        print(f"传感器模拟器启动，间隔 {interval} 秒。Ctrl+C 停止")
        try:
            while True:
                # 随机生成模拟数据（可按需要替换为串口/脚本输入）
                temp = round(random.uniform(15.0, 35.0), 2)
                hum = round(random.uniform(30.0, 90.0), 2)
                light = round(random.uniform(100.0, 1000.0), 2)

                sd = SensorData(temperature=temp, humidity=hum, light=light)
                db.session.add(sd)
                db.session.commit()

                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 插入数据: temp={temp}, hum={hum}, light={light}")

                # 轮询未执行的控制命令并“执行”它们（模拟串口发送）
                pending = ControlCommand.query.filter_by(status='pending').order_by(ControlCommand.id.asc()).all()
                for cmd in pending:
                    print(f"执行控制命令 id={cmd.id} device={cmd.device} command={cmd.command}")
                    # 在真实场景这里应该发送到串口，或调用设备控制代码
                    cmd.status = 'done'
                    cmd.executed_at = datetime.now()
                    db.session.add(cmd)
                if pending:
                    db.session.commit()

                time.sleep(interval)
        except KeyboardInterrupt:
            print("传感器模拟器已停止")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='智能果园 传感器模拟器')
    parser.add_argument('--interval', type=int, default=60, help='数据发送间隔(秒)')
    args = parser.parse_args()

    run_simulator(interval=args.interval)
