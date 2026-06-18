# 通宝奖励查询系统 - PythonAnywhere 部署配置

import sys
import logging

# 添加项目路径
path = '/home/你的用户名/tongbao-query'
if path not in sys.path:
    sys.path.insert(0, path)

# 设置日志
logging.basicConfig(level=logging.INFO)

# 导入Flask应用
from app import app as application

# 初始化数据库
from database import init_db
init_db()
