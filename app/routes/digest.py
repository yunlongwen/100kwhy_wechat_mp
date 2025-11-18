from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from loguru import logger

from ..config_loader import load_digest_schedule
from ..notifier.wecom import build_wecom_digest_markdown, send_markdown_to_wecom
from ..sources.ai_articles import pick_daily_ai_articles, todays_theme

router = APIRouter()


def _build_digest():
    now = datetime.now()
    schedule = load_digest_schedule()
    articles = pick_daily_ai_articles(k=schedule.count)

    items = [
        {
            "title": a.title,
            "url": a.url,
            "source": a.source,
            "summary": a.summary,
        }
        for a in articles
    ]

    digest = {
        "date": now.strftime("%Y-%m-%d"),
        "theme": todays_theme(now),
        "schedule": {
            "hour": schedule.hour,
            "minute": schedule.minute,
            "count": schedule.count,
        },
        "articles": items,
    }
    return digest


@router.get("/preview")
async def preview_digest():
    """
    返回当前配置下将要推送的日报内容（不真正发送）。
    """
    digest = _build_digest()
    return digest


@router.post("/trigger")
async def trigger_digest():
    """
    手动触发一次企业微信推送，并返回本次发送的内容。
    """
    digest = _build_digest()
    content = build_wecom_digest_markdown(
        date_str=digest["date"],
        theme=digest["theme"],
        items=digest["articles"],
    )
    logger.info("Manual trigger: sending digest to WeCom group...")
    await send_markdown_to_wecom(content)
    return {"ok": True, **digest}


@router.get("/panel", response_class=HTMLResponse)
async def digest_panel():
    """
    简单的前端页面：展示预览内容 + 一键触发按钮。
    """
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8" />
      <title>AI 编程日报面板</title>
      <style>
        body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; background: #f5f5f7; color: #111827; }
        h1 { font-size: 24px; margin-bottom: 8px; }
        .meta { margin-bottom: 16px; color: #6b7280; }
        button { padding: 8px 16px; border-radius: 999px; border: none; cursor: pointer; background: #2563eb; color: #fff; font-size: 14px; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .articles { margin-top: 16px; }
        .article { background: #ffffff; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
        .article-title { font-weight: 600; margin-bottom: 4px; }
        .article-meta { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
        .article-summary { font-size: 13px; color: #374151; }
        .status { margin-top: 12px; font-size: 13px; }
        a { color: #2563eb; text-decoration: none; }
        a:hover { text-decoration: underline; }
      </style>
    </head>
    <body>
      <h1>AI 编程 & 团队管理日报 · 面板</h1>
      <div class="meta" id="meta">加载中...</div>
      <button id="trigger-btn">手动触发一次推送到企业微信群</button>
      <div class="status" id="status"></div>

      <div class="articles" id="articles"></div>

      <script>
        async function loadPreview() {
          const metaEl = document.getElementById("meta");
          const listEl = document.getElementById("articles");
          const statusEl = document.getElementById("status");
          statusEl.textContent = "";
          listEl.innerHTML = "";
          metaEl.textContent = "加载中...";

          try {
            const res = await fetch("./preview");
            const data = await res.json();
            metaEl.textContent = `日期：${data.date} ｜ 主题：${data.theme} ｜ 定时：${String(data.schedule.hour).padStart(2,'0')}:${String(data.schedule.minute).padStart(2,'0')} ｜ 篇数：${data.schedule.count}`;

            if (!data.articles || data.articles.length === 0) {
              listEl.innerHTML = "<p>当前配置下没有可用文章，请在服务器的 config/ai_articles.json 中添加。</p>";
              return;
            }

            data.articles.forEach((item, idx) => {
              const div = document.createElement("div");
              div.className = "article";
              div.innerHTML = `
                <div class="article-title">${idx + 1}. <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title}</a></div>
                <div class="article-meta">来源：${item.source}</div>
                <div class="article-summary">${item.summary || ""}</div>
              `;
              listEl.appendChild(div);
            });
          } catch (err) {
            console.error(err);
            metaEl.textContent = "加载失败，请检查服务是否正常运行。";
          }
        }

        async function triggerOnce() {
          const btn = document.getElementById("trigger-btn");
          const statusEl = document.getElementById("status");
          btn.disabled = true;
          statusEl.textContent = "正在触发推送，请稍候...";
          try {
            const res = await fetch("./trigger", { method: "POST" });
            const data = await res.json();
            if (data.ok) {
              statusEl.textContent = `✅ 已触发一次推送：${data.date} ｜ 主题：${data.theme}`;
            } else {
              statusEl.textContent = "❌ 推送失败，请查看服务器日志。";
            }
          } catch (err) {
            console.error(err);
            statusEl.textContent = "❌ 请求失败，请查看浏览器控制台或服务器日志。";
          } finally {
            btn.disabled = false;
            // 触发后重新加载预览，保证展示的内容与最近一次一致
            loadPreview();
          }
        }

        document.getElementById("trigger-btn").addEventListener("click", triggerOnce);
        loadPreview();
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


