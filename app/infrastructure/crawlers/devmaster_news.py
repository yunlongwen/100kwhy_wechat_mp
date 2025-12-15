"""DevMaster.cn 资讯爬虫"""
import asyncio
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from loguru import logger


async def fetch_devmaster_news_by_category(category_url: str, category_name: str) -> List[Dict]:
    """
    从 DevMaster.cn 抓取指定分类的今日资讯
    
    Args:
        category_url: 分类页面 URL
        category_name: 分类名称（用于日志）
        
    Returns:
        资讯列表
    """
    news_list = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        async with async_playwright() as p:
            logger.info(f"[DevMaster爬虫] 开始抓取 {category_name} 的资讯...")
            
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # 访问页面
            await page.goto(category_url, wait_until="networkidle", timeout=30000)
            
            # 等待内容加载
            await page.wait_for_timeout(3000)
            
            # 提取今天的资讯
            # 查找所有文章元素
            articles = await page.query_selector_all("article")
            
            for article in articles:
                try:
                    # 提取日期
                    date_elem = await article.query_selector("[class*='date'], [class*='time']")
                    if date_elem:
                        date_text = await date_elem.inner_text()
                        # 如果不是今天的，跳过
                        if today not in date_text and datetime.now().strftime("%m-%d") not in date_text:
                            continue
                    
                    # 提取标题和链接
                    title_elem = await article.query_selector("a[href], h1, h2, h3")
                    if not title_elem:
                        continue
                    
                    title = await title_elem.inner_text()
                    title = title.strip()
                    
                    # 提取链接
                    link_elem = await article.query_selector("a[href]")
                    url = ""
                    if link_elem:
                        url = await link_elem.get_attribute("href")
                        if url and not url.startswith("http"):
                            url = f"https://devmaster.cn{url}"
                    
                    # 如果没有链接，使用分类页面URL
                    if not url:
                        url = category_url
                    
                    # 提取摘要
                    summary_elem = await article.query_selector("p, [class*='summary'], [class*='desc']")
                    summary = ""
                    if summary_elem:
                        summary = await summary_elem.inner_text()
                        summary = summary.strip()[:200]  # 限制长度
                    
                    if title and len(title) > 5:  # 确保标题有效
                        news_list.append({
                            "title": title,
                            "url": url,
                            "summary": summary,
                            "source": "DevMaster",
                            "published_time": datetime.now().isoformat() + "Z",
                        })
                        logger.info(f"[DevMaster爬虫] 发现资讯: {title[:50]}...")
                    
                except Exception as e:
                    logger.debug(f"[DevMaster爬虫] 解析文章元素失败: {e}")
                    continue
            
            await browser.close()
            
    except PlaywrightTimeoutError:
        logger.error(f"[DevMaster爬虫] 访问 {category_url} 超时")
    except Exception as e:
        logger.error(f"[DevMaster爬虫] 抓取失败: {e}", exc_info=True)
    
    logger.info(f"[DevMaster爬虫] {category_name} 抓取到 {len(news_list)} 条资讯")
    return news_list


async def fetch_today_devmaster_news() -> Dict[str, List[Dict]]:
    """
    抓取今天的 DevMaster 资讯
    
    Returns:
        按分类分组的资讯字典
    """
    categories = [
        {
            "url": "https://devmaster.cn/news?category=%E7%BC%96%E7%A8%8B%E6%A8%A1%E5%9E%8B",
            "name": "编程模型",
            "db_category": "programming"  # 映射到数据库的分类
        },
        {
            "url": "https://devmaster.cn/news?category=%E7%BC%96%E7%A8%8B%E5%AE%9E%E8%B7%B5",
            "name": "编程实践",
            "db_category": "programming"  # 映射到数据库的分类
        }
    ]
    
    all_news = {
        "ai_news": [],
        "programming": []
    }
    
    # 并行抓取所有分类
    tasks = [
        fetch_devmaster_news_by_category(cat["url"], cat["name"])
        for cat in categories
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 整理结果
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"[DevMaster爬虫] 抓取分类 {categories[i]['name']} 失败: {result}")
            continue
        
        if result:
            # 添加分类信息
            for news in result:
                news["category"] = categories[i]["db_category"]
                all_news[categories[i]["db_category"]].append(news)
    
    total = sum(len(v) for v in all_news.values())
    logger.info(f"[DevMaster爬虫] 总共抓取到 {total} 条今日资讯")
    
    return all_news

