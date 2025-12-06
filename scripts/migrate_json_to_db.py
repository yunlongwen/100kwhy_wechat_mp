"""将JSON数据迁移到数据库的脚本"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import select
from loguru import logger

# 添加项目根目录到路径
import sys
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.db.database import init_db, AsyncSessionLocal
from app.infrastructure.db.models import Article, Tool, Prompt, Rule, Resource


# 数据目录路径
DATA_DIR = project_root / "data"
ARTICLES_DIR = DATA_DIR / "articles"
TOOLS_DIR = DATA_DIR / "tools"
PROMPTS_DIR = DATA_DIR / "prompts"


def load_json_file(file_path: Path) -> List[Dict]:
    """加载JSON文件"""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
        return []
    except Exception as e:
        logger.error(f"加载文件失败 {file_path}: {e}")
        return []


async def migrate_articles():
    """迁移文章数据"""
    logger.info("[数据迁移] 开始迁移文章数据...")
    
    # 获取所有文章文件（排除候选池和文章池）
    article_files = [
        f for f in ARTICLES_DIR.glob("*.json")
        if f.name not in ["ai_candidates.json", "ai_articles.json"]
    ]
    
    total_count = 0
    for article_file in article_files:
        async with AsyncSessionLocal() as session:
            logger.info(f"[数据迁移] 处理文件: {article_file.name}")
            articles = load_json_file(article_file)
            
            for article_data in articles:
                # 检查是否已存在（基于URL）
                url = article_data.get("url", "").strip()
                if not url:
                    continue
                
                result = await session.execute(
                    select(Article).where(Article.url == url)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # 更新现有记录
                    for key, value in article_data.items():
                        if hasattr(existing, key) and key != "id":  # 不更新ID
                            setattr(existing, key, value)
                    existing.updated_at_db = datetime.now()
                    logger.debug(f"更新文章: {url[:60]}...")
                else:
                    # 创建新记录（不设置id，让数据库自动生成）
                    article = Article(
                        title=article_data.get("title", ""),
                        url=url,
                        summary=article_data.get("summary"),
                        source=article_data.get("source"),
                        category=article_data.get("category") or article_file.stem,
                        published_time=article_data.get("published_time"),
                        created_at=article_data.get("created_at"),
                        archived_at=article_data.get("archived_at"),
                        view_count=article_data.get("view_count", 0),
                        score=article_data.get("score", 0),
                        tags=article_data.get("tags"),
                        tool_tags=article_data.get("tool_tags"),
                        extra_data={k: v for k, v in article_data.items() 
                                   if k not in ["id", "title", "url", "summary", "source", 
                                               "category", "published_time", "created_at", 
                                               "archived_at", "view_count", "score", "tags", "tool_tags"]}
                    )
                    session.add(article)
                    logger.debug(f"添加文章: {url[:60]}...")
                
                total_count += 1
            
            # 每个文件处理完后立即提交
            await session.commit()
            logger.info(f"[数据迁移] 文件 {article_file.name} 处理完成，已提交")
    
    logger.info(f"[数据迁移] 文章数据迁移完成，共处理 {total_count} 条记录")


async def migrate_tools():
    """迁移工具数据"""
    logger.info("[数据迁移] 开始迁移工具数据...")
    
    tool_files = list(TOOLS_DIR.glob("*.json"))
    total_count = 0
    
    for tool_file in tool_files:
        async with AsyncSessionLocal() as session:
            logger.info(f"[数据迁移] 处理文件: {tool_file.name}")
            tools = load_json_file(tool_file)
            
            for tool_data in tools:
                # 检查是否已存在（基于URL或identifier）
                url = tool_data.get("url", "").strip()
                identifier = tool_data.get("identifier")
                
                if not url and not identifier:
                    continue
                
                # 优先使用identifier查找
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
                    for key, value in tool_data.items():
                        if hasattr(existing, key) and key != "id":  # 不更新ID
                            setattr(existing, key, value)
                    existing.updated_at_db = datetime.now()
                    logger.debug(f"更新工具: {tool_data.get('name', '')[:60]}...")
                else:
                    # 创建新记录（不设置id，让数据库自动生成）
                    tool = Tool(
                        identifier=tool_data.get("identifier"),
                        name=tool_data.get("name", ""),
                        url=url,
                        description=tool_data.get("description"),
                        category=tool_data.get("category") or tool_file.stem,
                        is_featured=tool_data.get("is_featured", False) or tool_file.name == "featured.json",
                        view_count=tool_data.get("view_count", 0),
                        score=tool_data.get("score", 0),
                        created_at=tool_data.get("created_at"),
                        extra_data={k: v for k, v in tool_data.items() 
                                   if k not in ["id", "identifier", "name", "url", "description", 
                                               "category", "is_featured", "view_count", "score", "created_at"]}
                    )
                    session.add(tool)
                    logger.debug(f"添加工具: {tool_data.get('name', '')[:60]}...")
                
                total_count += 1
            
            # 每个文件处理完后立即提交
            await session.commit()
            logger.info(f"[数据迁移] 文件 {tool_file.name} 处理完成，已提交")
    
    logger.info(f"[数据迁移] 工具数据迁移完成，共处理 {total_count} 条记录")


async def migrate_prompts():
    """迁移提示词数据"""
    logger.info("[数据迁移] 开始迁移提示词数据...")
    
    prompts_file = PROMPTS_DIR / "prompts.json"
    prompts = load_json_file(prompts_file)
    
    async with AsyncSessionLocal() as session:
        total_count = 0
        for prompt_data in prompts:
            identifier = prompt_data.get("identifier")
            if not identifier:
                continue
            
            result = await session.execute(
                select(Prompt).where(Prompt.identifier == identifier)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新现有记录
                for key, value in prompt_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at_db = datetime.now()
            else:
                # 创建新记录
                prompt = Prompt(
                    identifier=identifier,
                    name=prompt_data.get("name", ""),
                    description=prompt_data.get("description"),
                    content=prompt_data.get("content", ""),
                    category=prompt_data.get("category"),
                    extra_data={k: v for k, v in prompt_data.items() 
                               if k not in ["identifier", "name", "description", "content", "category"]}
                )
                session.add(prompt)
            
            total_count += 1
        
        await session.commit()
        logger.info(f"[数据迁移] 提示词数据迁移完成，共处理 {total_count} 条记录")


async def migrate_rules():
    """迁移规则数据"""
    logger.info("[数据迁移] 开始迁移规则数据...")
    
    rules_file = DATA_DIR / "rules.json"
    rules = load_json_file(rules_file)
    
    async with AsyncSessionLocal() as session:
        total_count = 0
        for rule_data in rules:
            name = rule_data.get("name", "").strip()
            if not name:
                continue
            
            # 基于name查找（可能重复，但先这样处理）
            result = await session.execute(
                select(Rule).where(Rule.name == name)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新现有记录
                for key, value in rule_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at_db = datetime.now()
            else:
                # 创建新记录
                rule = Rule(
                    name=name,
                    description=rule_data.get("description"),
                    content=rule_data.get("content", ""),
                    category=rule_data.get("category"),
                    extra_data={k: v for k, v in rule_data.items() 
                               if k not in ["name", "description", "content", "category"]}
                )
                session.add(rule)
            
            total_count += 1
        
        await session.commit()
        logger.info(f"[数据迁移] 规则数据迁移完成，共处理 {total_count} 条记录")


async def migrate_resources():
    """迁移社区资源数据"""
    logger.info("[数据迁移] 开始迁移社区资源数据...")
    
    resources_file = DATA_DIR / "resources.json"
    resources = load_json_file(resources_file)
    
    async with AsyncSessionLocal() as session:
        total_count = 0
        for resource_data in resources:
            title = resource_data.get("title", "").strip()
            if not title:
                continue
            
            # 基于title和url查找
            url = resource_data.get("url", "").strip()
            result = await session.execute(
                select(Resource).where(Resource.title == title)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新现有记录
                for key, value in resource_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at_db = datetime.now()
            else:
                # 创建新记录
                resource = Resource(
                    title=title,
                    url=url,
                    description=resource_data.get("description"),
                    type=resource_data.get("type"),
                    category=resource_data.get("category"),
                    subcategory=resource_data.get("subcategory"),
                    created_at=resource_data.get("created_at"),
                    extra_data={k: v for k, v in resource_data.items() 
                               if k not in ["title", "url", "description", "type", "category", "subcategory", "created_at"]}
                )
                session.add(resource)
            
            total_count += 1
        
        await session.commit()
        logger.info(f"[数据迁移] 社区资源数据迁移完成，共处理 {total_count} 条记录")


async def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("开始数据迁移：JSON -> 数据库")
    logger.info("=" * 80)
    
    # 初始化数据库
    await init_db()
    
    # 迁移各类数据
    await migrate_articles()
    await migrate_tools()
    await migrate_prompts()
    await migrate_rules()
    await migrate_resources()
    
    logger.info("=" * 80)
    logger.info("数据迁移完成！")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

