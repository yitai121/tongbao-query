"""
通宝奖励查询系统 - Flask 后端
"""
import csv
import io
import math
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, SYNC_INTERVAL, SYSTEM_NAME, SECRET_KEY
from database import (
    init_db, get_rewards_by_phone, get_total_reward_by_phone, get_stats,
    log_sync, upsert_reward, get_dashboard_data, get_config, set_config,
    get_all_configs, get_sync_logs, get_sync_log_count
)
from scraper import fetch_now
from auth import check_credentials, is_logged_in, login_required, api_login_required

app = Flask(__name__)
app.secret_key = SECRET_KEY


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

    # 查询明细
    all_records = get_rewards_by_phone(phone)
    total = len(all_records)

    # 分页
    if per_page > 0:
        start = (page - 1) * per_page
        end = start + per_page
        records = all_records[start:end]
    else:
        records = all_records

    # 查询汇总
    summary = get_total_reward_by_phone(phone)

    if not all_records:
        return jsonify({
            "code": 404,
            "msg": "未找到该手机号的记录",
            "data": {
                "phone": phone,
                "records": [],
                "summary": {"total": 0, "days": 0},
                "pagination": {"page": 1, "per_page": per_page, "total": 0, "total_pages": 0}
            }
        })

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


@app.route("/api/import", methods=["POST"])
@api_login_required
def api_import():
    """CSV文件导入接口"""
    if "file" not in request.files:
        return jsonify({"code": 400, "msg": "请选择文件", "data": None})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"code": 400, "msg": "请选择文件", "data": None})

    # 检查文件类型
    if not file.filename.endswith((".csv", ".txt")):
        return jsonify({"code": 400, "msg": "只支持CSV或TXT文件", "data": None})

    try:
        # 读取文件内容
        content = file.read().decode("utf-8-sig")
        reader = csv.reader(io.StringIO(content))

        rows = list(reader)
        if len(rows) < 2:
            return jsonify({"code": 400, "msg": "文件为空或只有表头", "data": None})

        # 获取今天的日期
        today = datetime.now().strftime("%Y-%m-%d")
        record_count = 0
        errors = []

        # 跳过表头，从第二行开始
        for i, row in enumerate(rows[1:], start=2):
            if len(row) < 2:
                errors.append(f"第{i}行数据不完整")
                continue

            phone = str(row[0]).strip()
            reward_raw = str(row[1]).strip()

            # 验证手机号
            if not phone or not phone.isdigit() or len(phone) != 11:
                errors.append(f"第{i}行手机号无效: {phone}")
                continue

            # 解析奖励值
            try:
                reward = float(reward_raw) if reward_raw else 0
            except (ValueError, TypeError):
                errors.append(f"第{i}行奖励值无效: {reward_raw}")
                continue

            upsert_reward(phone, reward, today)
            record_count += 1

        msg = f"导入成功，共同步{record_count}条记录"
        if errors:
            msg += f"，{len(errors)}条跳过"

        log_sync("success", record_count, msg)

        return jsonify({
            "code": 200,
            "msg": msg,
            "data": {
                "imported": record_count,
                "errors": errors[:10]  # 最多返回10条错误
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"导入失败: {str(e)}",
            "data": None
        })


# ========== 启动 ==========
if __name__ == "__main__":
    # 初始化数据库
    init_db()
    print(f"[{datetime.now()}] 数据库初始化完成")

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
