"""
通宝奖励查询系统 - 认证模块
"""
import hmac
from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from config import ADMIN_USERNAME, ADMIN_PASSWORD


def check_credentials(username, password):
    """验证用户名密码"""
    # 使用 hmac.compare_digest 防止时序攻击
    username_match = hmac.compare_digest(username, ADMIN_USERNAME)
    password_match = hmac.compare_digest(password, ADMIN_PASSWORD)
    return username_match and password_match


def is_logged_in():
    """检查是否已登录"""
    return session.get("admin_logged_in", False)


def login_required(f):
    """页面路由认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """API路由认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return jsonify({"code": 401, "msg": "未登录", "data": None}), 401
        return f(*args, **kwargs)
    return decorated_function
