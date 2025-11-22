"""测试多资讯源功能"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.crawlers.rss import fetch_rss_articles
from app.crawlers.github_trending import fetch_github_trending
from app.crawlers.hackernews import fetch_hackernews_articles
from app.sources.article_sources import fetch_from_all_sources


async def test_rss():
    """测试 RSS Feed"""
    print("\n" + "="*60)
    print("测试 RSS Feed 抓取")
    print("="*60)
    
    # 使用一些公开的 RSS Feed 进行测试
    test_feeds = [
        "https://rss.cnn.com/rss/edition.rss",  # CNN
        "https://feeds.bbci.co.uk/news/rss.xml",  # BBC News
    ]
    
    for feed_url in test_feeds:
        print(f"\n测试 Feed: {feed_url}")
        articles = await fetch_rss_articles(feed_url, max_items=3)
        print(f"抓取到 {len(articles)} 篇文章")
        for i, article in enumerate(articles, 1):
            print(f"  {i}. {article.get('title', '无标题')[:60]}")
            print(f"     来源: {article.get('source', '未知')}")
            print(f"     链接: {article.get('url', '')[:80]}")


async def test_github_trending():
    """测试 GitHub Trending"""
    print("\n" + "="*60)
    print("测试 GitHub Trending 抓取")
    print("="*60)
    
    languages = ["python", "javascript"]
    
    for lang in languages:
        print(f"\n测试语言: {lang}")
        articles = await fetch_github_trending(lang, max_items=3)
        print(f"抓取到 {len(articles)} 个项目")
        for i, article in enumerate(articles, 1):
            print(f"  {i}. {article.get('title', '无标题')}")
            print(f"     来源: {article.get('source', '未知')}")
            print(f"     摘要: {article.get('summary', '无摘要')[:60]}")


async def test_hackernews():
    """测试 Hacker News"""
    print("\n" + "="*60)
    print("测试 Hacker News 抓取")
    print("="*60)
    
    articles = await fetch_hackernews_articles(min_points=50, max_items=5)
    print(f"抓取到 {len(articles)} 篇高分文章")
    for i, article in enumerate(articles, 1):
        print(f"  {i}. {article.get('title', '无标题')[:60]}")
        print(f"     分数: {article.get('points', 0)} points")
        print(f"     链接: {article.get('url', '')[:80]}")


async def test_all_sources():
    """测试统一资讯源管理器"""
    print("\n" + "="*60)
    print("测试统一资讯源管理器")
    print("="*60)
    
    articles = await fetch_from_all_sources(
        keywords=["AI"],  # 搜狗微信搜索关键词
        rss_feeds=[
            "https://rss.cnn.com/rss/edition.rss",
        ],
        github_languages=["python"],
        hackernews_min_points=50,
        max_per_source=3,
    )
    
    print(f"\n总共抓取到 {len(articles)} 篇文章（已按热度分排序）")
    print("\n前 10 篇文章：")
    for i, article in enumerate(articles[:10], 1):
        score = article.get("score", 0)
        print(f"  {i}. [{score:.1f}分] {article.get('title', '无标题')[:60]}")
        print(f"     来源: {article.get('source', '未知')}")


async def main():
    """主函数"""
    print("开始测试多资讯源功能...")
    
    # 测试各个资讯源
    await test_rss()
    await test_github_trending()
    await test_hackernews()
    
    # 测试统一管理器
    await test_all_sources()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

