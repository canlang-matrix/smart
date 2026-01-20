from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import time
import os
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, SensorData, ControlCommand, ChatMessage, db
from app.services.prediction import predict_next_30_minutes
from app.services.ai_service import get_planting_advice, chat_response, chat_with_ai, search_knowledge, \
    add_knowledge_document, get_current_weather
from app.services.ai_service import get_kb_info
from app.services.ai_service import get_llm_status

main_bp = Blueprint('main', __name__)


# =========================================================
# 1. 页面路由 (Pages)
# =========================================================

# 门户首页 (任何人都可以看)
@main_bp.route('/')
def home():
    return render_template('home.html')


# 监控仪表盘 (必须登录才能看)
@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    return render_template('dashboard.html',
                           username=session.get('username'),
                           role=session.get('role'))


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            # 登录成功跳转到仪表盘
            return redirect(url_for('main.dashboard'))
        else:
            return render_template('login.html', error="用户名或密码错误")
    return render_template('login.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        # 默认注册为普通用户，管理员需手动修改数据库
        role = 'user'

        if not username or not password:
            return render_template('register.html', error='用户名和密码为必填项')

        if password != confirm:
            return render_template('register.html', error='两次输入的密码不一致')

        if len(password) < 6:
            return render_template('register.html', error='密码长度至少 6 位')

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='用户名已存在')

        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed, role=role)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('main.login'))
    return render_template('register.html')


@main_bp.route('/logout')
def logout():
    session.clear()
    # 👇 修改这里：退出后跳回首页 (home)，而不是登录页
    return redirect(url_for('main.home'))


# =========================================================
# 2. 数据与控制 API (Core APIs)
# =========================================================

@main_bp.route('/api/data')
def api_data():
    # 获取实时数据
    latest = SensorData.query.order_by(SensorData.id.desc()).first()
    # 获取预测数据
    pred_temp = predict_next_30_minutes('temperature')
    pred_hum = predict_next_30_minutes('humidity')
    pred_light = predict_next_30_minutes('light')
    # 获取历史数据(图表用)
    history = SensorData.query.order_by(SensorData.id.desc()).limit(20).all()
    history.reverse()

    # 返回兼容前端的字段
    history_time = [d.timestamp.strftime('%H:%M:%S') for d in history]
    history_temp = [d.temperature for d in history]
    history_hum = [d.humidity for d in history]
    history_light = [d.light for d in history]

    # 天气获取
    weather = get_current_weather()
    if not weather and latest:
        light = latest.light or 0
        hum_v = latest.humidity or 0
        if hum_v > 85:
            category = '雨天'
            emoji = '🌧️'
        else:
            if light >= 800:
                category = '晴天'
                emoji = '☀️'
            elif light >= 400:
                category = '多云'
                emoji = '⛅'
            else:
                category = '阴天'
                emoji = '☁️'

        weather = {
            'temp': latest.temperature,
            'humidity': latest.humidity,
            'desc': category,
            'category': category,
            'emoji': emoji,
            'icon': None,
            'wind': None
        }

    return jsonify({
        'current': {
            'temp': latest.temperature if latest else 0,
            'hum': latest.humidity if latest else 0,
            'light': latest.light if latest else 0
        },
        'weather': weather or {},
        'prediction': {
            'temp': pred_temp,
            'hum': pred_hum,
            'light': pred_light
        },
        'history_time': history_time,
        'history_temp': history_temp,
        'history_hum': history_hum,
        'history_light': history_light
    })


@main_bp.route('/api/control', methods=['POST'])
def api_control():
    # 👇👇👇 【修改点】删除了权限检查，允许所有用户操作 👇👇👇
    if session.get('role') != 'admin':
         return jsonify({"status": "error", "msg": "权限不足：仅管理员可操作设备！"}), 403

    data = request.json
    device = data.get('device', 'unknown')
    command = str(data.get('command', ''))
    user_id = session.get('user_id')

    # 记录指令
    cmd = ControlCommand(device=device, command=command, user_id=user_id)
    db.session.add(cmd)
    db.session.commit()

    return jsonify({"status": "success", "msg": f"{device} 指令已发送"})


@main_bp.route('/api/advice')
def api_advice():
    latest = SensorData.query.order_by(SensorData.id.desc()).first()
    if latest:
        advice = get_planting_advice(latest.temperature, latest.humidity)
        return jsonify({"advice": advice})
    return jsonify({"advice": "数据不足"})


# =========================================================
# 3. AI 与知识库 API (AI Service)
# =========================================================

@main_bp.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json or {}
    msg = data.get('message', '')
    if not msg:
        return jsonify({'error': 'empty message'}), 400

    # 保存用户消息
    user_id = session.get('user_id') if session else None
    cm = ChatMessage(user_id=user_id, role='user', content=msg)
    db.session.add(cm)
    db.session.commit()

    # 取上下文
    recent = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.timestamp.asc()).limit(40).all()
    history = [{'role': r.role, 'content': r.content} for r in recent]

    use_kb = bool(data.get('use_kb'))
    if use_kb:
        kb_results = search_knowledge(msg, topk=3)
        kb_texts = [f"[{it['title']}] {it['snippet']}" for it in kb_results]
        if kb_texts:
            history.insert(0, {'role': 'system', 'content': '参考资料：\n' + '\n---\n'.join(kb_texts)})

    use_web = bool(data.get('use_web'))

    # AI 调用逻辑
    import os
    if os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('OPENAI_API_KEY'):
        try:
            reply = chat_with_ai(msg)
        except Exception:
            reply = chat_response(msg, history=history, use_web=use_web)
    else:
        reply = chat_response(msg, history=history, use_web=use_web)

    # 保存 AI 回复
    cm2 = ChatMessage(user_id=user_id, role='assistant', content=reply)
    db.session.add(cm2)
    db.session.commit()

    return jsonify({'reply': reply})


@main_bp.route('/api/knowledge/search', methods=['POST'])
def api_kb_search():
    data = request.json or {}
    q = data.get('q', '')
    if not q:
        return jsonify({'results': []})
    res = search_knowledge(q, topk=5)
    info = get_kb_info()
    return jsonify({'results': res, 'kb_info': info})


@main_bp.route('/api/knowledge/add', methods=['POST'])
def api_kb_add():
    data = request.json or {}
    title = data.get('title') or f'doc_{int(time.time())}.txt'
    content = data.get('content', '')
    if not content:
        return jsonify({'error': 'empty content'}), 400
    path = add_knowledge_document(title, content)
    return jsonify({'path': path})


@main_bp.route('/api/llm_status')
def api_llm_status():
    try:
        status = get_llm_status()
    except Exception:
        status = {'available': False, 'model': None}
    return jsonify(status)


# =========================================================
# 4. 后台管理 (Admin Panel)
# =========================================================

@main_bp.route('/admin/users')
def admin_users():
    # 🔒 权限检查
    if session.get('role') != 'admin':
        return "<h1>403 Forbidden - 仅管理员可见</h1>", 403

    # 获取所有用户列表
    users = User.query.all()
    return render_template('admin_users.html', users=users, username=session.get('username'))


@main_bp.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    # 🔒 1. 权限检查
    if session.get('role') != 'admin':
        return "权限不足", 403

    # 不能删除自己
    if user_id == session.get('user_id'):
        return "无法删除当前登录的管理员账号", 400

    user = User.query.get(user_id)
    if user:
        try:
            # 🔒 2. 重点修改：级联删除 (斩草除根)
            # 必须先删除该用户的所有聊天记录和控制记录，否则会报外键错误
            ChatMessage.query.filter_by(user_id=user_id).delete()
            ControlCommand.query.filter_by(user_id=user_id).delete()

            # 最后删除用户
            db.session.delete(user)
            db.session.commit()
            print(f"✅ 用户 {user.username} 已成功删除")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 删除失败: {e}")
            return f"删除失败，数据库错误: {e}", 500

    return redirect(url_for('main.admin_users'))


@main_bp.route('/admin/edit_user', methods=['POST'])
def edit_user():
    # 🔒 权限检查
    if session.get('role') != 'admin':
        return "权限不足", 403

    user_id = request.form.get('user_id')
    new_username = request.form.get('username')
    new_password = request.form.get('password')  # 如果为空则不修改
    new_role = request.form.get('role')  # 可选：修改角色

    user = User.query.get(user_id)
    if not user:
        return "用户不存在", 404

    # 1. 修改用户名 (需要检查是否重复)
    if new_username and new_username != user.username:
        if User.query.filter_by(username=new_username).first():
            # 这里简单返回错误，实际可优化为 flash 消息
            return "<h1>修改失败：该用户名已存在</h1><a href='/admin/users'>返回</a>"
        user.username = new_username

    # 2. 修改密码 (只有输入了新密码才修改)
    if new_password and new_password.strip():
        user.password = generate_password_hash(new_password)

    # 3. 修改角色
    if new_role:
        user.role = new_role

    db.session.commit()

    return redirect(url_for('main.admin_users'))