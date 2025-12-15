"""DevMaster 资讯抓取服务"""
from typing import Dict, List
from loguru import logger

from ..infrastructure.crawlers.devmaster_news import fetch_today_devmaster_news
from .database_write_service import DatabaseWriteService


class DevMasterNewsService:
    """DevMaster 资讯抓取服务"""
    
    @staticmethod
    async def crawl_and_archive_today_news() -> int:
        """
        抓取今天的 DevMaster 资讯并归档到数据库
        
        Returns:
            成功归档的资讯数量
        """
        try:
            logger.info("[DevMaster资讯] 开始抓取今日资讯...")
            
            # 抓取资讯
            all_news = await fetch_today_devmaster_news()
            
            if not all_news or all(len(v) == 0 for v in all_news.values()):
                logger.warning("[DevMaster资讯] 未抓取到任何资讯")
                return 0
            
            # 归档到数据库
            success_count = 0
            failed_count = 0
            
            for category, news_list in all_news.items():
                for news in news_list:
                    try:
                        # 提取标签
                        tags = news.get("tags", [])
                        
                        # 归档到数据库
                        success = await DatabaseWriteService.archive_article_to_category(
                            article=news,
                            category=category,
                            tool_tags=tags
                        )
                        
                        if success:
                            logger.info(f"[DevMaster资讯] 归档成功: {news['title'][:50]}...")
                            success_count += 1
                        else:
                            logger.warning(f"[DevMaster资讯] 归档失败（可能已存在）: {news['title'][:50]}...")
                            failed_count += 1
                            
                    except Exception as e:
                        logger.error(f"[DevMaster资讯] 归档失败: {e}", exc_info=True)
                        failed_count += 1
            
            logger.info(f"[DevMaster资讯] 抓取完成！成功: {success_count}, 失败: {failed_count}")
            return success_count
            
        except Exception as e:
            logger.error(f"[DevMaster资讯] 抓取失败: {e}", exc_info=True)
            return 0

