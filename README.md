# 🏆 通宝奖励查询系统

> 腾讯文档在线表格数据自动同步 + 手机号查询系统
> 高颜值 Web 界面，支持自动同步、实时查询

---

## 📋 功能特性

- ✅ **自动同步** — 定时从腾讯文档在线表格拉取数据
- ✅ **手机号查询** — 用户输入手机号即可查询通宝奖励
- ✅ **数据汇总** — 累计通宝、记录天数、日均通宝一目了然
- ✅ **高颜值界面** — 玻璃态设计 + 渐变动画，适配手机/电脑
- ✅ **数据安全** — 本地 SQLite 存储，手机号脱敏显示
- ✅ **手动同步** — 支持后台一键手动触发同步

---

## 🚀 快速开始（小白教程）

### 第一步：申请腾讯文档 API 密钥（5分钟）

1. 打开 [腾讯文档开放平台](https://docs.qq.com/open/)
2. 用微信扫码登录
3. 点击「创建应用」
4. 填写：
   - 应用名称：`通宝查询系统`
   - 应用描述：`通宝奖励数据查询`
5. 创建后你会得到三个值：
   - **AppID**
   - **AppKey**
   - **AppSecret**

⚠️ **重要**：把这三个值记下来，后面要用！

### 第二步：获取文档ID

1. 打开你的腾讯文档在线表格
2. 看浏览器地址栏，URL类似：
   ```
   https://docs.qq.com/sheet/DXXXXXXXXXXXX
   ```
3. `DXXXXXXXXXXXX` 这部分就是**文档ID**

### 第三步：确认表格格式

你的在线表格必须是这个格式：

| 手机号 | 通宝奖励 |
|--------|----------|
| 13800138000 | 100 |
| 13900139000 | 200 |
| 15012345678 | 150 |

- 第1列：手机号（11位数字）
- 第2列：通宝奖励（数字）
- 第1行是表头，数据从第2行开始

### 第四步：配置系统

1. 把项目文件夹放到你的电脑/服务器上
2. 找到 `.env.example` 文件，**复制一份**，改名为 `.env`
3. 用记事本打开 `.env`，填入你的配置：

```
TENCENT_DOC_APP_ID=你的AppID
TENCENT_DOC_APP_KEY=你的AppKey
TENCENT_DOC_APP_SECRET=你的AppSecret
DOC_ID=你的文档ID
SHEET_ID=Sheet1
SYNC_INTERVAL=3600
FLASK_PORT=5000
```

### 第五步：启动系统

**Mac / Linux 用户：**
```bash
cd tongbao-query
chmod +x start.sh
./start.sh
```

**Windows 用户：**
```bash
cd tongbao-query
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

看到以下信息说明启动成功：
```
🚀 启动服务...
   访问地址: http://localhost:5000
```

### 第六步：打开查询页面

浏览器访问：`http://localhost:5000`

输入手机号就能查询了！🎉

---

## 📱 给用户分享

如果你想让其他人也能查询：

### 方案A：局域网访问（同一WiFi下）
- 把 `http://你的电脑IP:5000` 发给用户

### 方案B：公网访问（推荐）
- 部署到云服务器（阿里云/腾讯云）
- 或用 ngrok 内网穿透：
  ```bash
  ngrok http 5000
  ```
  会生成一个公网链接，发给用户即可

---

## 🔧 常见问题

**Q: 同步失败怎么办？**
- 检查 `.env` 里的 API 密钥是否正确
- 检查文档ID是否正确
- 确认表格已设置为「所有人可查看」

**Q: 如何修改同步频率？**
- 修改 `.env` 里的 `SYNC_INTERVAL`
- 单位是秒，比如 `1800` = 30分钟

**Q: 表格列名不是"手机号"和"通宝奖励"怎么办？**
- 没关系！系统按列的位置读取，不按列名
- 只要第1列是手机号，第2列是奖励值就行

**Q: 怎么重启服务？**
- 按 `Ctrl+C` 停止，再运行 `./start.sh`

---

## 📁 项目结构

```
tongbao-query/
├── app.py              # Flask 后端主程序
├── config.py           # 配置文件
├── database.py         # 数据库操作
├── sync.py             # 腾讯文档同步
├── requirements.txt    # Python 依赖
├── start.sh            # 启动脚本
├── .env.example        # 配置模板
├── .env                # 你的配置（需自己创建）
├── data/               # 数据库文件（自动创建）
├── templates/
│   └── index.html      # 前端页面
└── static/
    ├── style.css       # 样式
    └── script.js       # 前端脚本
```

---

## 🔒 安全说明

- 手机号在页面上会脱敏显示（138****8000）
- 数据存储在本地 SQLite 数据库，不会上传到第三方
- API 密钥只存在你的 `.env` 文件中

---

**Made with ❤️ by 通宝奖励查询系统**
