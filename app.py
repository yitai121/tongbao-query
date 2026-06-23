"""
通宝奖励查询系统 - Flask 后端
"""
import math
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, SYNC_INTERVAL, SYSTEM_NAME, SECRET_KEY
from database import (
    init_db, get_rewards_by_phone, get_total_reward_by_phone, get_stats,
    log_sync, get_dashboard_data, get_config, set_config,
    get_all_configs, get_sync_logs, get_sync_log_count
)
from scraper import fetch_now
from auth import check_credentials, is_logged_in, login_required, api_login_required

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=8)  # Session 8小时后过期
app.config["SESSION_COOKIE_HTTPONLY"] = True   # 防止 JavaScript 读取 cookie
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # 防止 CSRF 攻击

# 模块级初始化：确保任何部署方式（包括 serverless）都会建表
try:
    init_db()
    print(f"[{datetime.now()}] 数据库初始化完成")
except Exception as e:
    print(f"[{datetime.now()}] 数据库初始化失败: {e}")


# ========== 自动同步线程 ==========
def auto_sync_loop():
    """后台自动同步线程"""
    while True:
        try:
            fetch_now()
        except Exception as e:
            print(f"[{datetime.now()}] 自动同步异常: {e}")
        time.sleep(SYNC_INTERVAL)


# ========== 页面路由 ==========
@app.route("/")
def index():
    """主页"""
    return render_template("index.html", system_name=SYSTEM_NAME)


@app.route("/admin/login")
def admin_login():
    """管理员登录页"""
    if is_logged_in():
        return render_template("admin/index.html", system_name=SYSTEM_NAME)
    return render_template("admin/login.html")


@app.route("/admin")
@login_required
def admin_panel():
    """管理员面板"""
    return render_template("admin/index.html", system_name=SYSTEM_NAME)


# ========== 管理员认证 API ==========
@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    """管理员登录API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "msg": "请求数据无效", "data": None})

        username = data.get("username", "")
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"code": 400, "msg": "请输入用户名和密码", "data": None})

        if check_credentials(username, password):
            session["admin_logged_in"] = True
            session.permanent = True
            return jsonify({"code": 200, "msg": "登录成功", "data": None})
        else:
            return jsonify({"code": 401, "msg": "用户名或密码错误", "data": None})
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[{datetime.now()}] 登录错误: {error_detail}")
        return jsonify({"code": 500, "msg": f"服务器错误: {str(e)}", "data": None}), 500


@app.route("/api/admin/logout", methods=["POST"])
def api_admin_logout():
    """管理员登出API"""
    session.clear()
    return jsonify({"code": 200, "msg": "已退出登录", "data": None})


# ========== 管理员配置 API ==========
@app.route("/api/admin/config", methods=["GET"])
@api_login_required
def api_get_config():
    """获取系统配置"""
    configs = get_all_configs()
    return jsonify({"code": 200, "msg": "success", "data": configs})


@app.route("/api/admin/config", methods=["POST"])
@api_login_required
def api_set_config():
    """更新系统配置"""
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "msg": "请求数据无效", "data": None})

    descriptions = {
        "system_name": "系统名称",
        "doc_id": "文档ID",
        "sheet_id": "工作表名称",
        "phone_column": "手机号列号",
        "reward_column": "奖励列号",
        "sync_interval": "自动同步间隔（秒）",
        "page_size": "每页记录数"
    }

    for key, value in data.items():
        if key in descriptions:
            set_config(key, str(value), descriptions[key])

    return jsonify({"code": 200, "msg": "配置保存成功", "data": None})


@app.route("/api/admin/sync/logs", methods=["GET"])
@api_login_required
def api_sync_logs():
    """获取同步日志（分页）"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    logs = get_sync_logs(page, per_page)
    total = get_sync_log_count()

    return jsonify({
        "code": 200,
        "msg": "success",
        "data": {
            "logs": logs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total / per_page) if per_page > 0 else 0
        }
    })


# ========== 公共 API 路由 ==========
@app.route("/api/query", methods=["GET"])
def api_query():
    """查询接口 - 根据手机号查询（支持分页）"""
    phone = request.args.get("phone", "").strip()

    if not phone:
        return jsonify({"code": 400, "msg": "请输入手机号", "data": None})

    if not phone.isdigit() or len(phone) != 11:
        return jsonify({"code": 400, "msg": "手机号格式不正确", "data": None})

    # 分页参数
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 0, type=int)

    # 如果未指定 per_page，从配置读取
    if per_page <= 0:
        per_page = int(get_config("page_size", "20"))

    # 判断是否为管理员（管理员可查看完整数据，普通用户仅查看最近7天）
    is_admin = session.get("admin_logged_in", False)
    days_limit = None if is_admin else 7

    # 查询明细（数据库层面限制7天）
    all_records = get_rewards_by_phone(phone, days_limit=days_limit)

    # 生成完整日期范围
    end_date = datetime.now()
    if days_limit:
        # 普通用户：最近7天
        start_date = end_date - timedelta(days=days_limit - 1)
    else:
        # 管理员：从2026-06-03开始
        start_date = datetime(2026, 6, 3)

    # 创建日期到记录的映射
    record_map = {r["record_date"]: r for r in all_records}

    # 生成完整日期列表，填充未同步的日期
    full_records = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str in record_map:
            full_records.append({
                "record_date": date_str,
                "reward": record_map[date_str]["reward"],
                "synced": True
            })
        else:
            full_records.append({
                "record_date": date_str,
                "reward": None,
                "synced": False
            })
        current_date += timedelta(days=1)

    # 按日期倒序排列（最新的在前）
    full_records.reverse()

    total = len(full_records)

    # 分页
    if per_page > 0:
        start = (page - 1) * per_page
        end = start + per_page
        records = full_records[start:end]
    else:
        records = full_records

    # 查询汇总（只统计已同步的记录）
    summary = get_total_reward_by_phone(phone, days_limit=days_limit)

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "phone": phone,
            "records": records,
            "summary": summary,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": math.ceil(total / per_page) if per_page > 0 else 1
            }
        }
    })


@app.route("/api/sync", methods=["POST"])
@api_login_required
def api_sync():
    """手动同步接口"""
    try:
        count = fetch_now()
        return jsonify({
            "code": 200,
            "msg": f"同步成功，共同步{count}条记录",
            "data": {"record_count": count}
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"同步失败: {str(e)}",
            "data": None
        })


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """系统统计接口"""
    stats = get_stats()
    return jsonify({
        "code": 200,
        "msg": "success",
        "data": stats
    })


@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """数据看板接口"""
    data = get_dashboard_data()
    return jsonify({
        "code": 200,
        "msg": "success",
        "data": data
    })


# ========== 启动 ==========
if __name__ == "__main__":
    # 启动自动同步线程
    sync_thread = threading.Thread(target=auto_sync_loop, daemon=True)
    sync_thread.start()
    print(f"[{datetime.now()}] 自动同步线程已启动，间隔{SYNC_INTERVAL}秒")

    # 首次同步
    try:
        fetch_now()
    except Exception as e:
        print(f"[{datetime.now()}] 首次同步失败（可能是API未配置）: {e}")
        log_sync("failed", 0, f"首次同步失败: {e}")

    # 启动Flask
    print(f"[{datetime.now()}] 服务启动: http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
