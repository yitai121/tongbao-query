"""
通宝奖励查询系统 - 配置文件
"""
import os

# ========== 腾讯文档 API 配置 ==========
# 申请地址: https://docs.qq.com/open/
TENCENT_DOC_APP_ID = os.getenv("TENCENT_DOC_APP_ID", "你的APP_ID")
TENCENT_DOC_APP_KEY = os.getenv("TENCENT_DOC_APP_KEY", "你的APP_KEY")
TENCENT_DOC_APP_SECRET = os.getenv("TENCENT_DOC_APP_SECRET", "你的APP_SECRET")

# ========== 文档配置 ==========
# 在线表格的文档ID（从表格URL中获取）
# 例如: https://docs.qq.com/sheet/DXXXXXXXXXXXX
# 其中 DXXXXXXXXXXXX 就是文档ID
DOC_ID = os.getenv("DOC_ID", "你的文档ID")
SHEET_ID = os.getenv("SHEET_ID", "Sheet1")  # 工作表名称，默认Sheet1

# ========== 数据列配置 ==========
# 手机号在第几列（从1开始）
PHONE_COLUMN = 1
# 通宝奖励在第几列（从1开始）
REWARD_COLUMN = 2

# ========== 数据库配置 ==========
# 默认路径：本地开发用 data/tongbao.db
# Vercel 环境：Lambda 只允许写 /tmp，自动切换
_default_db_path = "data/tongbao.db"
if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    _default_db_path = "/tmp/tongbao.db"
DB_PATH = os.getenv("DB_PATH", _default_db_path)

# ========== 同步配置 ==========
# 自动同步间隔（秒），默认1小时
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "3600"))

# ========== Flask 配置 ==========
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# ========== 系统配置 ==========
SYSTEM_NAME = "通宝奖励查询系统"
SYSTEM_VERSION = "1.0.0"

# ========== 管理员认证配置 ==========
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "etheric")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "etheric123123")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
