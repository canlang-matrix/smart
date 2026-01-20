import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from app.models import SensorData


def _series_to_supervised(y, window=5):
    X, Y = [], []
    for i in range(window, len(y)):
        X.append(y[i - window:i])
        Y.append(y[i])
    return np.array(X), np.array(Y)


def predict_next_30_minutes(data_type='temperature'):
    """使用基于滑动窗口的梯度提升回归进行多步递归预测，较线性回归更真实。"""
    recent_data = SensorData.query.order_by(SensorData.id.desc()).limit(100).all()
    if len(recent_data) < 8:
        return []

    recent_data.reverse()

    if data_type == 'temperature':
        y_values = [d.temperature for d in recent_data]
    elif data_type == 'humidity':
        y_values = [d.humidity for d in recent_data]
    elif data_type == 'light':
        y_values = [d.light for d in recent_data]
    else:
        return []

    y = np.array(y_values)

    # 窗口大小根据数据长度自适应
    window = min(12, max(3, len(y) // 4))

    # 如果数据太少，退回线性回归
    if len(y) < window + 5:
        X_time = np.array(range(len(y))).reshape(-1, 1)
        model = LinearRegression()
        model.fit(X_time, y)
        future_X = np.array(range(len(y), len(y) + 30)).reshape(-1, 1)
        predicted = model.predict(future_X)
        return [round(float(val), 2) for val in predicted]

    # 构造监督学习样本
    X, Y = _series_to_supervised(y, window=window)

    model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
    model.fit(X, Y)

    # 递归预测未来30个点
    preds = []
    last_window = y[-window:].tolist()
    for _ in range(30):
        x_in = np.array(last_window[-window:]).reshape(1, -1)
        p = model.predict(x_in)[0]
        preds.append(round(float(p), 2))
        last_window.append(p)

    return preds