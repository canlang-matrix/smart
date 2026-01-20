from app import create_app, db
from app.models import User

# 1. 创建应用实例
app = create_app()

# 2. 进入应用上下文 (这是关键！没有这一步会报错)
with app.app_context():
    # 打印提示
    print("正在连接数据库...")

    # 3. 检查是否已经存在管理员，防止重复添加
    existing_user = User.query.filter_by(username='admin').first()

    if existing_user:
        print("❌ 错误：管理员用户 'admin' 已经存在，无需重复创建！")
    else:
        # 4. 创建用户对象
        # 注意：这里密码暂时用明文（为了配合你之前的简单代码）
        admin = User(username='admin', password='123', role='admin')

        # 5. 添加到会话并提交
        db.session.add(admin)
        db.session.commit()
        print("✅ 成功：已创建管理员用户 (账号: admin, 密码: 123)")

    # 如果你想顺便加一个普通用户用于测试
    if not User.query.filter_by(username='farmer').first():
        user = User(username='farmer', password='123', role='user')
        db.session.add(user)
        db.session.commit()
        print("✅ 成功：已创建普通用户 (账号: farmer, 密码: 123)")

print("=== 数据库初始化完成 ===")