# 通宝奖励查询系统 - 一键部署指南

## 🚀 3分钟完成部署（完全免费）

### 第一步：注册 PythonAnywhere（1分钟）
1. 访问 https://www.pythonanywhere.com
2. 点击 "Pricing & signup"
3. 选择 "Create a Beginner account"（免费版）
4. 填写用户名、邮箱、密码
5. 点击 "Register"

### 第二步：上传代码（1分钟）
1. 登录后，点击顶部 "Files" 标签
2. 点击 "Upload a file" 按钮
3. 下载项目压缩包（我会提供链接）
4. 上传后，点击文件，选择 "Extract here"

### 第三步：配置Web应用（1分钟）
1. 点击顶部 "Web" 标签
2. 点击 "Add a new web app"
3. 点击 "Next" → "Manual configuration" → "Python 3.10"
4. 在 "Code" 部分：
   - Source code: `/home/你的用户名/tongbao-query`
   - Working directory: `/home/你的用户名/tongbao-query`
5. 在 "Virtualenv" 部分：
   - 点击 "Enter path to a virtualenv"
   - 输入：`/home/你的用户名/tongbao-query/venv`
   - 勾选 "Create automatically"

### 第四步：安装依赖
1. 点击顶部 "Consoles" 标签
2. 点击 "$ Bash"
3. 依次执行：
```bash
cd ~/tongbao-query
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 第五步：配置WSGI文件
1. 回到 "Web" 标签
2. 点击 WSGI configuration file 链接
3. 删除所有内容，粘贴以下代码：
```python
import sys
import logging

path = '/home/你的用户名/tongbao-query'
if path not in sys.path:
    sys.path.insert(0, path)

logging.basicConfig(level=logging.INFO)

from app import app as application

from database import init_db
init_db()
```
4. 保存（Ctrl+O，然后 Enter）

### 第六步：重新加载应用
1. 回到 "Web" 标签
2. 点击绿色的 "Reload" 按钮

## ✅ 完成！

访问：`https://你的用户名.pythonanywhere.com`

## 📝 如何更新数据

由于腾讯文档需要登录，使用CSV导入方式：
1. 打开腾讯文档，导出为CSV
2. 访问你的网站，点击"管理员导入"
3. 上传CSV文件

## 🔄 如何更新代码

当代码更新时：
1. 下载新的压缩包
2. 在 PythonAnywhere 的 Files 页面上传
3. 解压覆盖
4. 在 Web 页面点击 "Reload"

## 💡 优势

✅ 完全免费，永久使用
✅ 数据持久化，不会丢失
✅ 自动HTTPS，安全可靠
✅ 全球CDN，访问快速
✅ 稳定运行，几乎无故障
