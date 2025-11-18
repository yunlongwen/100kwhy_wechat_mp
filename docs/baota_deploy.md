## 宝塔面板部署说明（企业微信每日 AI 编程推荐）

本说明帮助你在宝塔面板中部署 `100kwhy_wechat_mp`，并通过企业微信群机器人每天 14:00 推送 5 篇 AI 编程文章。

> 假设项目路径为：`/www/wwwroot/100kwhy_wechat_mp`

---

### 一、环境变量文件（推荐）

1. 在服务器上创建环境变量文件 `env.sh`：

```bash
cd /www/wwwroot/100kwhy_wechat_mp
cat > env.sh << 'EOF'
#!/usr/bin/env bash

# 企业微信群机器人 Webhook 地址
export WECOM_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=替换成你的key"

# 如果后续接入微信公众号，可在这里一起配置
# export WECHAT_TOKEN="your_wechat_token"
EOF

chmod +x env.sh
```

2. 在宝塔「Python项目」中配置环境变量：

- 选择项目 → 「添加 Python 项目」弹窗中：
  - `环境变量` 选择：**从文件加载**
  - 右侧选择文件：指向 `/www/wwwroot/100kwhy_wechat_mp/env.sh`

---

### 二、在宝塔 Python3.13.7 环境安装依赖（方式 A）

> 你已经验证成功的做法，这里作为正式文档记录。

在服务器上执行（SSH 或宝塔终端）：

```bash
cd /www/wwwroot/100kwhy_wechat_mp

# 使用宝塔的 Python 3.13.7 环境安装依赖
/www/server/pyporject_evn/versions/3.13.7/bin/pip install \
  fastapi "uvicorn[standard]" httpx apscheduler loguru
```

安装完成后，`uvicorn` 在宝塔的 3.13.7 环境中就能正常导入这些模块。

---

### 三、启动方式与启动命令

在宝塔「添加 Python 项目」中按如下填写：

- **项目名称**：`100kwhy_wechat_mp`
- **Python环境**：选择 **Python 3.13.7**（或你安装的其他 Python 3.x，**不要选 2.7**）
- **启动方式**：选择 **命令行启动**
- **项目路径**：`/www/wwwroot/100kwhy_wechat_mp`
- **当前框架**：选择 `fastapi` / `asgi`（不同版本文案略有差异，选 ASGI 类型即可）
- **环境变量**：建议：先选「无」确认能正常启动；确认 OK 后再换成「从文件加载」并选中 `env.sh`
- **启动命令（简化版，使用全局 3.13.7 环境）**：

```bash
cd /www/wwwroot/100kwhy_wechat_mp && \
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如果你想使用虚拟环境（可选），可以改为两步执行（先在终端里创建好）：

```bash
cd /www/wwwroot/100kwhy_wechat_mp
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi "uvicorn[standard]" httpx apscheduler loguru
```

然后在宝塔的启动命令里写：

```bash
cd /www/wwwroot/100kwhy_wechat_mp && \
source venv/bin/activate && \
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**重要说明**：

1. 如果启动失败，请先在终端里用同样的命令手动执行，查看完整错误信息。
2. 确认 `env.sh` 文件存在且 `WECOM_WEBHOOK` 已正确配置后，再在宝塔里启用「从文件加载」环境变量。
3. FastAPI 监听 `8000` 端口，宝塔会自动使用 Nginx 做反向代理。

---

### 四、定时任务参数配置（config/digest_schedule.json）

定时任务由 `app/main.py` 中的 `AsyncIOScheduler` 管理，启动时会从配置文件读取参数：

配置文件路径：`config/digest_schedule.json`

示例内容：

```json
{
  "hour": 14,
  "minute": 0,
  "count": 5
}
```

- `hour`：每日推送小时（0–23，默认 `14`）
- `minute`：每日推送分钟（0–59，默认 `0`）
- `count`：每天推送的文章数量（默认 `5`）

修改方式：

1. 编辑服务器上的 `config/digest_schedule.json`；
2. 在宝塔中重启 Python 项目；
3. 启动日志中会打印类似信息：

```text
Scheduler started. Daily digest will be sent at 14:00 (Asia/Shanghai), with up to 5 articles.
```

如果需要临时调整时间（例如改为当前时间之后几分钟测试），只需修改配置文件并重启项目即可。

---

### 五、手动触发一次企业微信推送（验证链路）

在服务器上执行以下命令，可以立即向企业微信群发送一条推荐消息，验证 `WECOM_WEBHOOK`、文章配置和推送逻辑是否正常：

```bash
cd /www/wwwroot/100kwhy_wechat_mp

python3 - << 'EOF'
import asyncio
from datetime import datetime

from app.notifier.wecom import build_wecom_digest_markdown, send_markdown_to_wecom
from app.sources.ai_articles import pick_daily_ai_articles, todays_theme

now = datetime.now()
articles = pick_daily_ai_articles(k=5)
items = [
    {"title": a.title, "url": a.url, "source": a.source, "summary": a.summary}
    for a in articles
]

content = build_wecom_digest_markdown(
    date_str=now.strftime("%Y-%m-%d"),
    theme=todays_theme(now),
    items=items,
)

asyncio.run(send_markdown_to_wecom(content))
EOF
```

若企业微信群收到消息，则说明手动触发和自动定时任务公用的链路已经通畅；后续只需要依赖定时任务即可。

---

### 六、前端管理页面：预览 & 一键触发

项目内置了一个简单的管理页面，用于：

- 预览当前配置下将要推送的文章列表；
- 手动触发一次企业微信推送；
- 查看当前定时任务时间与篇数配置。

访问方式（假设服务运行在 8000 端口）：

- 在浏览器访问：`http://服务器IP:8000/digest/panel`

页面功能说明：

- 打开页面时，会自动调用 `GET /digest/preview`，展示：
  - 日期、主题
  - 当前定时配置（小时、分钟、篇数）
  - 本次将要推送的文章列表（标题、来源、摘要）
- 点击「手动触发一次推送到企业微信群」按钮时：
  - 会调用 `POST /digest/trigger`
  - 成功后页面会显示「已触发一次推送：YYYY-MM-DD ｜ 主题：...」

> 注意：管理页面不会做登录鉴权，默认只在你自己的内网/服务器环境上使用，如需对外开放建议加一层反向代理或认证。

