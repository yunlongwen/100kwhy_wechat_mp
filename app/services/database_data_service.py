"""数据库数据服务 - 从SQLite数据库读取数据

此服务用于从数据库读取所有正式数据：
- 文章（articles表）
- 工具（tools表）
- 提示词（prompts表）
- 规则（rules表）
- 社区资源（resources表）

注意：候选池等临时数据仍使用JSON文件，由DataLoader处理。
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.infrastructure.db.models import Article, Tool, Prompt, Rule, Resource
from app.infrastructure.db.database import AsyncSessionLocal


class DatabaseDataService:
    """数据库数据服务 - 从数据库读取数据"""
    
    @staticmethod
    async def get_tools(
        category: Optional[str] = None,
        featured: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        sort_by: str = "score"
    ) -> Tuple[List[Dict], int]:
        """
        从数据库获取工具列表（支持分页）
        
        Args:
            category: 工具分类
            featured: 是否热门（True/False/None）
            page: 页码（从1开始）
            page_size: 每页数量
            search: 搜索关键词（搜索名称和描述）
            sort_by: 排序字段（score, view_count, created_at）
        
        Returns:
            (工具列表, 总数)
        """
        async with AsyncSessionLocal() as session:
            # 构建查询
            query = select(Tool)
            
            # 筛选分类
            if category:
                query = query.where(Tool.category == category)
            
            # 筛选热门
            if featured is not None:
                query = query.where(Tool.is_featured == featured)
            
            # 搜索
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        Tool.name.like(search_pattern),
                        Tool.description.like(search_pattern)
                    )
                )
            
            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # 排序
            if sort_by == "score":
                query = query.order_by(Tool.score.desc(), Tool.id.desc())
            elif sort_by == "view_count":
                query = query.order_by(Tool.view_count.desc(), Tool.created_at.desc())
            elif sort_by == "created_at":
                query = query.order_by(Tool.created_at.desc())
            
            # 分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # 执行查询
            result = await session.execute(query)
            tools = result.scalars().all()
            
            # 转换为字典
            tools_list = []
            for tool in tools:
                tool_dict = {
                    "id": tool.id,
                    "identifier": tool.identifier,
                    "name": tool.name,
                    "url": tool.url,
                    "description": tool.description,
                    "category": tool.category,
                    "is_featured": tool.is_featured or False,
                    "view_count": tool.view_count or 0,
                    "score": tool.score or 0,
                    "created_at": tool.created_at,
                }
                # 合并extra_data
                if tool.extra_data:
                    tool_dict.update(tool.extra_data)
                tools_list.append(tool_dict)
            
            return tools_list, total
    
    @staticmethod
    async def get_tool_by_id(
        tool_id: Optional[int] = None,
        tool_identifier: Optional[str] = None
    ) -> Optional[Dict]:
        """
        从数据库获取工具详情
        
        Args:
            tool_id: 工具ID（数字）
            tool_identifier: 工具identifier（字符串，优先使用）
        
        Returns:
            工具详情字典，如果未找到则返回None
        """
        async with AsyncSessionLocal() as session:
            # 优先使用identifier查找
            if tool_identifier:
                result = await session.execute(
                    select(Tool).where(Tool.identifier == tool_identifier)
                )
                tool = result.scalar_one_or_none()
            elif tool_id is not None:
                result = await session.execute(
                    select(Tool).where(Tool.id == tool_id)
                )
                tool = result.scalar_one_or_none()
            else:
                return None
            
            if not tool:
                return None
            
            tool_dict = {
                "id": tool.id,
                "identifier": tool.identifier,
                "name": tool.name,
                "url": tool.url,
                "description": tool.description,
                "category": tool.category,
                "is_featured": tool.is_featured or False,
                "view_count": tool.view_count or 0,
                "score": tool.score or 0,
                "created_at": tool.created_at,
            }
            # 合并extra_data
            if tool.extra_data:
                tool_dict.update(tool.extra_data)
            
            return tool_dict
    
    @staticmethod
    async def get_articles(
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        sort_by: str = "published_time"
    ) -> Tuple[List[Dict], int]:
        """
        从数据库获取文章列表（支持分页）
        
        Args:
            category: 文章分类（programming, ai_news等）
            page: 页码（从1开始）
            page_size: 每页数量
            search: 搜索关键词
            sort_by: 排序字段（archived_at归档时间默认, published_time, score热度, created_at）
        
        Returns:
            (文章列表, 总数)
        """
        async with AsyncSessionLocal() as session:
            # 构建查询
            query = select(Article)
            
            # 筛选分类
            if category:
                query = query.where(Article.category == category)
            
            # 搜索
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        Article.title.like(search_pattern),
                        Article.summary.like(search_pattern)
                    )
                )
            
            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # 排序
            if sort_by == "archived_at":
                query = query.order_by(Article.archived_at.desc(), Article.id.desc())
            elif sort_by == "published_time":
                query = query.order_by(Article.published_time.desc(), Article.id.desc())
            elif sort_by == "score":
                query = query.order_by(Article.view_count.desc(), Article.archived_at.desc())
            elif sort_by == "created_at":
                query = query.order_by(Article.created_at.desc(), Article.id.desc())
            
            # 分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # 执行查询
            result = await session.execute(query)
            articles = result.scalars().all()
            
            # 转换为字典
            articles_list = []
            for article in articles:
                article_dict = {
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "summary": article.summary,
                    "source": article.source,
                    "category": article.category,
                    "published_time": article.published_time,
                    "created_at": article.created_at,
                    "archived_at": article.archived_at,
                    "view_count": article.view_count or 0,
                    "score": article.score or 0,
                    "tags": article.tags or [],
                    "tool_tags": article.tool_tags or [],
                }
                # 合并extra_data
                if article.extra_data:
                    article_dict.update(article.extra_data)
                articles_list.append(article_dict)
            
            return articles_list, total
    
    @staticmethod
    async def get_articles_by_tool(
        tool_name: str = None,
        tool_id: int = None,
        tool_identifier: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        从数据库获取与工具相关的文章
        
        Args:
            tool_name: 工具名称（可选）
            tool_id: 工具ID（可选）
            tool_identifier: 工具标识符（可选，用于匹配文章的tool_tags）
            page: 页码
            page_size: 每页数量
        
        Returns:
            (文章列表, 总数)
        """
        async with AsyncSessionLocal() as session:
            # 如果提供了tool_identifier，优先使用它
            if tool_identifier:
                tool_result = await session.execute(
                    select(Tool).where(Tool.identifier == tool_identifier)
                )
                tool = tool_result.scalar_one_or_none()
                if tool:
                    tool_name = tool.name
            elif tool_id:
                tool_result = await session.execute(
                    select(Tool).where(Tool.id == tool_id)
                )
                tool = tool_result.scalar_one_or_none()
                if tool:
                    tool_name = tool.name
                    tool_identifier = tool.identifier
            
            # 构建查询 - 先获取所有文章
            query = select(Article)
            
            # 执行查询获取所有文章
            result = await session.execute(query)
            all_articles = result.scalars().all()
            
            # 在Python中筛选包含该工具标签的文章
            filtered_articles = []
            for article in all_articles:
                matched = False
                tool_tags = article.tool_tags or []
                
                # 优先使用identifier匹配（精确匹配）
                if tool_identifier and tool_identifier in tool_tags:
                    matched = True
                
                # 如果没有identifier或identifier未匹配，使用工具名称匹配（模糊匹配）
                if not matched and tool_name:
                    tool_name_lower = tool_name.lower()
                    for tag in tool_tags:
                        if tool_name_lower in str(tag).lower() or str(tag).lower() in tool_name_lower:
                            matched = True
                            break
                
                if matched:
                    filtered_articles.append(article)
            
            # 按发布时间排序
            filtered_articles.sort(
                key=lambda x: (x.published_time or x.created_at or ""),
                reverse=True
            )
            
            # 分页
            total = len(filtered_articles)
            offset = (page - 1) * page_size
            paginated_articles = filtered_articles[offset:offset + page_size]
            
            # 转换为字典
            articles_list = []
            for article in paginated_articles:
                article_dict = {
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "summary": article.summary,
                    "source": article.source,
                    "category": article.category,
                    "published_time": article.published_time,
                    "created_at": article.created_at,
                    "archived_at": article.archived_at,
                    "view_count": article.view_count or 0,
                    "score": article.score or 0,
                    "tags": article.tags or [],
                    "tool_tags": article.tool_tags or [],
                }
                # 合并extra_data
                if article.extra_data:
                    article_dict.update(article.extra_data)
                articles_list.append(article_dict)
            
            return articles_list, total
    
    @staticmethod
    async def get_recent_items(
        type_filter: str = "all",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        从数据库获取最近收录的内容
        
        Args:
            type_filter: 类型筛选（all, articles, tools）
            page: 页码
            page_size: 每页数量
        
        Returns:
            (内容列表, 总数)
        """
        async with AsyncSessionLocal() as session:
            all_items = []
            
            if type_filter in ["all", "articles"]:
                # 获取文章
                query = select(Article).order_by(Article.archived_at.desc(), Article.id.desc())
                result = await session.execute(query)
                articles = result.scalars().all()
                for article in articles:
                    article_dict = {
                        "id": article.id,
                        "title": article.title,
                        "url": article.url,
                        "summary": article.summary,
                        "category": article.category,
                        "archived_at": article.archived_at,
                        "view_count": article.view_count or 0,
                        "item_type": "article",
                    }
                    if article.extra_data:
                        article_dict.update(article.extra_data)
                    all_items.append(article_dict)
            
            if type_filter in ["all", "tools"]:
                # 获取工具
                query = select(Tool).order_by(Tool.created_at_db.desc(), Tool.id.desc())
                result = await session.execute(query)
                tools = result.scalars().all()
                for tool in tools:
                    tool_dict = {
                        "id": tool.id,
                        "name": tool.name,
                        "url": tool.url,
                        "description": tool.description,
                        "category": tool.category,
                        "created_at": tool.created_at,
                        "archived_at": tool.created_at,  # 使用created_at作为archived_at
                        "view_count": tool.view_count or 0,
                        "item_type": "tool",
                    }
                    if tool.extra_data:
                        tool_dict.update(tool.extra_data)
                    all_items.append(tool_dict)
            
            # 按归档时间排序
            all_items.sort(
                key=lambda x: x.get("archived_at", "") or x.get("created_at", ""),
                reverse=True
            )
            
            # 分页
            total = len(all_items)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_items = all_items[start:end]
            
            return paginated_items, total
    
    @staticmethod
    async def get_prompts(
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """从数据库获取提示词列表（支持分页和筛选）"""
        async with AsyncSessionLocal() as session:
            query = select(Prompt)
            
            if category:
                query = query.where(Prompt.category == category)
            
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        Prompt.name.like(search_pattern),
                        Prompt.description.like(search_pattern)
                    )
                )
            
            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            result = await session.execute(query)
            prompts = result.scalars().all()
            
            prompts_list = []
            for prompt in prompts:
                prompt_dict = {
                    "identifier": prompt.identifier,
                    "name": prompt.name,
                    "description": prompt.description,
                    "content": prompt.content,
                    "category": prompt.category,
                }
                if prompt.extra_data:
                    prompt_dict.update(prompt.extra_data)
                prompts_list.append(prompt_dict)
            
            return prompts_list, total
    
    @staticmethod
    async def get_prompt_content(identifier: str) -> Optional[str]:
        """从数据库获取提示词内容"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Prompt).where(Prompt.identifier == identifier)
            )
            prompt = result.scalar_one_or_none()
            if prompt:
                return prompt.content
            return None
    
    @staticmethod
    async def get_rules(
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """从数据库获取规则列表（支持分页和筛选）"""
        async with AsyncSessionLocal() as session:
            query = select(Rule)
            
            if category:
                query = query.where(Rule.category == category)
            
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        Rule.name.like(search_pattern),
                        Rule.description.like(search_pattern),
                        Rule.content.like(search_pattern)
                    )
                )
            
            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            result = await session.execute(query)
            rules = result.scalars().all()
            
            rules_list = []
            for rule in rules:
                rule_dict = {
                    "name": rule.name,
                    "description": rule.description,
                    "content": rule.content,
                    "category": rule.category,
                }
                if rule.extra_data:
                    rule_dict.update(rule.extra_data)
                rules_list.append(rule_dict)
            
            return rules_list, total
    
    @staticmethod
    async def get_resources(
        type: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """从数据库获取社区资源列表（支持分页和筛选）"""
        async with AsyncSessionLocal() as session:
            query = select(Resource)
            
            if type:
                query = query.where(Resource.type == type)
            
            if category:
                query = query.where(Resource.category == category)
            
            if subcategory:
                query = query.where(Resource.subcategory == subcategory)
            
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        Resource.title.like(search_pattern),
                        Resource.description.like(search_pattern)
                    )
                )
            
            # 排序
            query = query.order_by(Resource.created_at.desc(), Resource.id.desc())
            
            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            result = await session.execute(query)
            resources = result.scalars().all()
            
            resources_list = []
            for resource in resources:
                resource_dict = {
                    "title": resource.title,
                    "url": resource.url,
                    "description": resource.description,
                    "type": resource.type,
                    "category": resource.category,
                    "subcategory": resource.subcategory,
                    "created_at": resource.created_at,
                }
                if resource.extra_data:
                    resource_dict.update(resource.extra_data)
                resources_list.append(resource_dict)
            
            return resources_list, total
    
    @staticmethod
    async def increment_article_view_count(url: str) -> bool:
        """增加文章的点击次数（热度）"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Article).where(Article.url == url)
            )
            article = result.scalar_one_or_none()
            if article:
                article.view_count = (article.view_count or 0) + 1
                await session.commit()
                return True
            return False
    
    @staticmethod
    async def increment_tool_view_count(
        tool_id: Optional[int] = None,
        tool_identifier: Optional[str] = None
    ) -> bool:
        """增加工具的点击次数（热度）"""
        async with AsyncSessionLocal() as session:
            if tool_identifier:
                result = await session.execute(
                    select(Tool).where(Tool.identifier == tool_identifier)
                )
            elif tool_id is not None:
                result = await session.execute(
                    select(Tool).where(Tool.id == tool_id)
                )
            else:
                return False
            
            tool = result.scalar_one_or_none()
            if tool:
                tool.view_count = (tool.view_count or 0) + 1
                await session.commit()
                return True
            return False
    
    @staticmethod
    async def is_article_archived(url: str) -> bool:
        """检查文章是否已归档"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Article).where(Article.url == url)
            )
            article = result.scalar_one_or_none()
            return article is not None

