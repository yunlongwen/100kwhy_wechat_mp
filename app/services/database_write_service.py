"""数据库写入服务 - 将数据写入SQLite数据库

此服务用于将数据写入数据库：
- 归档文章到数据库
- 归档工具到数据库
- 删除文章（从数据库删除）

所有正式数据都存储在数据库中，不再使用JSON文件存储。
"""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.infrastructure.db.models import Article, Tool
from app.infrastructure.db.database import AsyncSessionLocal


class DatabaseWriteService:
    """数据库写入服务 - 将数据写入数据库"""
    
    @staticmethod
    async def archive_article_to_category(
        article: Dict,
        category: str,
        tool_tags: Optional[List[str]] = None
    ) -> bool:
        """
        将文章归档到数据库的指定分类
        
        Args:
            article: 文章数据字典
            category: 分类名称（如 programming, ai_news）
            tool_tags: 工具标签列表（可选）
        
        Returns:
            是否成功
        """
        try:
            async with AsyncSessionLocal() as session:
                url = article.get("url", "").strip()
                if not url:
                    logger.error("文章URL为空，无法归档")
                    return False
                
                # 检查是否已存在
                result = await session.execute(
                    select(Article).where(Article.url == url)
                )
                existing = result.scalar_one_or_none()
                
                now = datetime.now()
                now_iso = now.isoformat() + "Z"
                
                if existing:
                    # 更新现有记录
                    existing.title = article.get("title", existing.title)
                    existing.summary = article.get("summary", existing.summary)
                    existing.source = article.get("source", existing.source)
                    existing.category = category
                    existing.published_time = article.get("published_time", existing.published_time)
                    existing.created_at = article.get("created_at", existing.created_at) or now_iso
                    existing.archived_at = now_iso
                    existing.view_count = article.get("view_count", existing.view_count) or 0
                    existing.score = article.get("score", existing.score) or 0
                    existing.tags = article.get("tags", existing.tags) or []
                    if tool_tags:
                        existing.tool_tags = tool_tags
                    existing.updated_at_db = now
                    logger.info(f"更新文章: {url[:60]}...")
                else:
                    # 创建新记录
                    new_article = Article(
                        title=article.get("title", ""),
                        url=url,
                        summary=article.get("summary"),
                        source=article.get("source"),
                        category=category,
                        published_time=article.get("published_time"),
                        created_at=article.get("created_at") or now_iso,
                        archived_at=now_iso,
                        view_count=article.get("view_count", 0),
                        score=article.get("score", 0),
                        tags=article.get("tags", []),
                        tool_tags=tool_tags or [],
                        extra_data={k: v for k, v in article.items() 
                                   if k not in ["title", "url", "summary", "source", 
                                               "category", "published_time", "created_at", 
                                               "archived_at", "view_count", "score", "tags", "tool_tags"]}
                    )
                    session.add(new_article)
                    logger.info(f"添加文章: {url[:60]}...")
                
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"归档文章失败: {e}", exc_info=True)
            return False
    
    @staticmethod
    async def archive_tool_to_category(tool: Dict, category: str) -> bool:
        """
        将工具保存到数据库的指定分类
        
        Args:
            tool: 工具数据字典
            category: 工具分类
        
        Returns:
            是否成功
        """
        try:
            async with AsyncSessionLocal() as session:
                url = tool.get("url", "").strip()
                identifier = tool.get("identifier")
                
                if not url and not identifier:
                    logger.error("工具URL和identifier都为空，无法归档")
                    return False
                
                # 检查是否已存在（优先使用identifier）
                if identifier:
                    result = await session.execute(
                        select(Tool).where(Tool.identifier == identifier)
                    )
                    existing = result.scalar_one_or_none()
                else:
                    result = await session.execute(
                        select(Tool).where(Tool.url == url)
                    )
                    existing = result.scalar_one_or_none()
                
                if existing:
                    # 更新现有记录
                    existing.name = tool.get("name", existing.name)
                    existing.url = url or existing.url
                    existing.description = tool.get("description", existing.description)
                    existing.category = category
                    existing.is_featured = tool.get("is_featured", existing.is_featured) or False
                    existing.view_count = tool.get("view_count", existing.view_count) or 0
                    existing.score = tool.get("score", existing.score) or 0
                    existing.created_at = tool.get("created_at", existing.created_at)
                    existing.updated_at_db = datetime.now()
                    logger.info(f"更新工具: {tool.get('name', '')[:60]}...")
                else:
                    # 创建新记录
                    new_tool = Tool(
                        identifier=identifier,
                        name=tool.get("name", ""),
                        url=url,
                        description=tool.get("description"),
                        category=category,
                        is_featured=tool.get("is_featured", False),
                        view_count=tool.get("view_count", 0),
                        score=tool.get("score", 0),
                        created_at=tool.get("created_at"),
                        extra_data={k: v for k, v in tool.items() 
                                   if k not in ["identifier", "name", "url", "description", 
                                               "category", "is_featured", "view_count", "score", "created_at"]}
                    )
                    session.add(new_tool)
                    logger.info(f"添加工具: {tool.get('name', '')[:60]}...")
                
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"归档工具失败: {e}", exc_info=True)
            return False
    
    @staticmethod
    async def delete_article_from_all_categories(url: str) -> Dict[str, bool]:
        """
        从数据库中删除指定URL的文章
        
        Args:
            url: 要删除的文章URL
            
        Returns:
            Dict[str, bool]: 删除结果
        """
        try:
            async with AsyncSessionLocal() as session:
                url_to_delete = url.strip()
                
                result = await session.execute(
                    select(Article).where(Article.url == url_to_delete)
                )
                article = result.scalar_one_or_none()
                
                if article:
                    await session.delete(article)
                    await session.commit()
                    logger.info(f"从数据库删除文章: {url_to_delete[:60]}...")
                    return {"database": True}
                else:
                    logger.warning(f"文章不存在: {url_to_delete[:60]}...")
                    return {"database": False}
                    
        except Exception as e:
            logger.error(f"删除文章失败: {e}", exc_info=True)
            return {"database": False}

