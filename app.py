"""
通宝奖励查询系统 - Flask 后端
"""
import csv
import io
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, SYNC_INTERVAL, SYSTEM_NAME
from database import init_db, get_rewards_by_phone, get_total_reward_by_phone, get_stats, log_sync, upsert_reward, get_dashboard_data
from scraper import fetch_now

app = Flask(__name__)


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


@app.route("/dashboard")
def dashboard():
    """数据看板"""
    return render_template("dashboard.html", system_name=SYSTEM_NAME)


# ========== API 路由 ==========
@app.route("/api/query", methods=["GET"])
def api_query():
    """查询接口 - 根据手机号查询"""
    phone = request.args.get("phone", "").strip()

    if not phone:
        return jsonify({"code": 400, "msg": "请输入手机号", "data": None})

    if not phone.isdigit() or len(phone) != 11:
        return jsonify({"code": 400, "msg": "手机号格式不正确", "data": None})

    # 查询明细
    records = get_rewards_by_phone(phone)
    # 查询汇总
    summary = get_total_reward_by_phone(phone)

    if not records:
        return jsonify({
            "code": 404,
            "msg": "未找到该手机号的记录",
            "data": {
                "phone": phone,
                "records": [],
                "summary": {"total": 0, "days": 0}
            }
        })

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "phone": phone,
            "records": records,
            "summary": summary
        }
    })


@app.route("/api/sync", methods=["POST"])
def api_sync():
    """手动同步接口"""
    try:
        count = fetch_now()
        return jsonify({
            "code": 200,
            "msg": f"同步成功，共同步{count}条记录",
            "data": {"count": count}
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
                "count": record_count,
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
