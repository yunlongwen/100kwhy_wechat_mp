"""数据备份服务 - 从数据库导出JSON并推送到GitHub（手动触发）"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Any

from sqlalchemy import select
from loguru import logger

from app.infrastructure.db.database import AsyncSessionLocal
from app.infrastructure.db.models import Article, Tool, Prompt, Rule, Resource


class WeeklyBackupService:
    """每周数据备份服务"""
    
    def __init__(self):
        """初始化备份服务"""
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.articles_dir = self.data_dir / "articles"
        self.tools_dir = self.data_dir / "tools"
        self.prompts_dir = self.data_dir / "prompts"
    
    def _run_git_command(self, cmd: list, env: dict = None) -> Tuple[str, str, int]:
        """
        执行 Git 命令
        
        Args:
            cmd: Git命令列表
            env: 环境变量字典
            
        Returns:
            (stdout, stderr, returncode)
        """
        try:
        
            cmd_env = os.environ.copy()
            if env:
                cmd_env.update(env)
            # 禁用交互式提示
            cmd_env['GIT_TERMINAL_PROMPT'] = '0'
            
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300,  # 5分钟超时
                env=cmd_env
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            logger.error("[每周备份] Git 命令执行超时")
            return "", "Timeout", -1
        except Exception as e:
            logger.error(f"[每周备份] Git 命令执行失败: {e}")
            return "", str(e), -1
    
    async def _export_articles_to_json(self) -> Dict[str, List[Dict]]:
        """从数据库导出文章数据到JSON格式"""
        logger.info("[每周备份] 开始导出文章数据...")
        
        async with AsyncSessionLocal() as session:
            # 获取所有文章
            result = await session.execute(select(Article))
            articles = result.scalars().all()
            
            # 按分类分组
            articles_by_category: Dict[str, List[Dict]] = {}
            
            for article in articles:
                # 转换为字典
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
                
                # 按分类分组
                category = article.category or "uncategorized"
                if category not in articles_by_category:
                    articles_by_category[category] = []
                articles_by_category[category].append(article_dict)
            
            logger.info(f"[每周备份] 导出文章数据完成，共 {len(articles)} 条，分类数: {len(articles_by_category)}")
            return articles_by_category
    
    async def _export_tools_to_json(self) -> Dict[str, List[Dict]]:
        """从数据库导出工具数据到JSON格式"""
        logger.info("[每周备份] 开始导出工具数据...")
        
        async with AsyncSessionLocal() as session:
            # 获取所有工具
            result = await session.execute(select(Tool))
            tools = result.scalars().all()
            
            # 按分类分组
            tools_by_category: Dict[str, List[Dict]] = {}
            
            for tool in tools:
                # 转换为字典
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
                
                # 按分类分组
                category = tool.category or "other"
                if category not in tools_by_category:
                    tools_by_category[category] = []
                tools_by_category[category].append(tool_dict)
            
            logger.info(f"[每周备份] 导出工具数据完成，共 {len(tools)} 条，分类数: {len(tools_by_category)}")
            return tools_by_category
    
    async def _export_prompts_to_json(self) -> List[Dict]:
        """从数据库导出提示词数据到JSON格式"""
        logger.info("[每周备份] 开始导出提示词数据...")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Prompt))
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
                
                # 合并extra_data
                if prompt.extra_data:
                    prompt_dict.update(prompt.extra_data)
                
                prompts_list.append(prompt_dict)
            
            logger.info(f"[每周备份] 导出提示词数据完成，共 {len(prompts_list)} 条")
            return prompts_list
    
    async def _export_rules_to_json(self) -> List[Dict]:
        """从数据库导出规则数据到JSON格式"""
        logger.info("[每周备份] 开始导出规则数据...")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Rule))
            rules = result.scalars().all()
            
            rules_list = []
            for rule in rules:
                rule_dict = {
                    "name": rule.name,
                    "description": rule.description,
                    "content": rule.content,
                    "category": rule.category,
                }
                
                # 合并extra_data
                if rule.extra_data:
                    rule_dict.update(rule.extra_data)
                
                rules_list.append(rule_dict)
            
            logger.info(f"[每周备份] 导出规则数据完成，共 {len(rules_list)} 条")
            return rules_list
    
    async def _export_resources_to_json(self) -> List[Dict]:
        """从数据库导出社区资源数据到JSON格式"""
        logger.info("[每周备份] 开始导出社区资源数据...")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Resource))
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
                
                # 合并extra_data
                if resource.extra_data:
                    resource_dict.update(resource.extra_data)
                
                resources_list.append(resource_dict)
            
            logger.info(f"[每周备份] 导出社区资源数据完成，共 {len(resources_list)} 条")
            return resources_list
    
    def _save_json_file(self, file_path: Path, data: Any) -> bool:
        """保存JSON文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"[每周备份] 保存文件失败 {file_path}: {e}")
            return False
    
    async def export_data_to_json(self) -> bool:
        """
        从数据库导出所有数据到JSON文件
        
        Returns:
            是否成功
        """
        try:
            logger.info("[每周备份] 开始从数据库导出数据到JSON文件...")
            
            # 导出文章数据
            articles_by_category = await self._export_articles_to_json()
            for category, articles in articles_by_category.items():
                # 排除候选池和文章池文件
                if category in ["ai_candidates", "ai_articles"]:
                    continue
                file_path = self.articles_dir / f"{category}.json"
                self._save_json_file(file_path, articles)
                logger.info(f"[每周备份] 保存文章文件: {file_path.name} ({len(articles)} 条)")
            
            # 导出工具数据
            tools_by_category = await self._export_tools_to_json()
            for category, tools in tools_by_category.items():
                # 处理featured工具
                if category == "featured" or any(t.get("is_featured") for t in tools):
                    file_path = self.tools_dir / "featured.json"
                    featured_tools = [t for t in tools if t.get("is_featured")]
                    if featured_tools:
                        self._save_json_file(file_path, featured_tools)
                        logger.info(f"[每周备份] 保存工具文件: featured.json ({len(featured_tools)} 条)")
                
                # 保存其他分类
                if category != "featured":
                    file_path = self.tools_dir / f"{category}.json"
                    category_tools = [t for t in tools if not t.get("is_featured")]
                    if category_tools:
                        self._save_json_file(file_path, category_tools)
                        logger.info(f"[每周备份] 保存工具文件: {category}.json ({len(category_tools)} 条)")
            
            # 导出提示词数据
            prompts = await self._export_prompts_to_json()
            prompts_file = self.prompts_dir / "prompts.json"
            self._save_json_file(prompts_file, prompts)
            logger.info(f"[每周备份] 保存提示词文件: prompts.json ({len(prompts)} 条)")
            
            # 导出规则数据
            rules = await self._export_rules_to_json()
            rules_file = self.data_dir / "rules.json"
            self._save_json_file(rules_file, rules)
            logger.info(f"[每周备份] 保存规则文件: rules.json ({len(rules)} 条)")
            
            # 导出社区资源数据
            resources = await self._export_resources_to_json()
            resources_file = self.data_dir / "resources.json"
            self._save_json_file(resources_file, resources)
            logger.info(f"[每周备份] 保存社区资源文件: resources.json ({len(resources)} 条)")
            
            logger.info("[每周备份] 数据导出完成")
            return True
            
        except Exception as e:
            logger.error(f"[每周备份] 数据导出失败: {e}", exc_info=True)
            return False
    
    async def backup_to_github(self) -> None:
        """
        手动备份任务：从数据库导出JSON并推送到GitHub
        由管理员在管理面板手动触发
        """
        try:
            now = datetime.now()
            logger.info(
                f"[每周备份] 开始执行每周数据备份任务，时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # 检查是否是 Git 仓库
            git_dir = self.project_root / ".git"
            if not git_dir.exists():
                logger.warning("[每周备份] 当前目录不是 Git 仓库，跳过备份")
                return
            
            # 1. 从数据库导出数据到JSON文件
            success = await self.export_data_to_json()
            if not success:
                logger.error("[每周备份] 数据导出失败，终止备份")
                return
            
            # 2. 检查是否有变更
            stdout, stderr, code = await asyncio.to_thread(
                self._run_git_command,
                ["git", "status", "--porcelain", "data/"]
            )
            
            if code != 0:
                logger.error(f"[每周备份] 检查 Git 状态失败: {stderr}")
                return
            
            if not stdout.strip():
                logger.info("[每周备份] data/ 目录没有变更，跳过提交")
                return
            
            # 3. 添加变更的文件
            logger.info("[每周备份] 添加变更的文件...")
            stdout, stderr, code = await asyncio.to_thread(
                self._run_git_command,
                ["git", "add", "data/"]
            )
            
            if code != 0:
                logger.error(f"[每周备份] 添加文件失败: {stderr}")
                return
            
            # 4. 提交变更
            week_num = now.isocalendar()[1]  # 获取周数
            commit_message = f"chore: weekly backup from database - {now.strftime('%Y-%m-%d')} (Week {week_num})"
            logger.info(f"[每周备份] 提交变更: {commit_message}")
            stdout, stderr, code = await asyncio.to_thread(
                self._run_git_command,
                ["git", "commit", "-m", commit_message]
            )
            
            if code != 0:
                if "nothing to commit" in stderr.lower() or "nothing to commit" in stdout.lower():
                    logger.info("[每周备份] 没有需要提交的变更")
                    return
                logger.error(f"[每周备份] 提交失败: {stderr}")
                return
            
            logger.info(f"[每周备份] 提交成功: {stdout.strip()}")
            
            # 5. 推送到远程仓库
            logger.info("[每周备份] 推送到远程仓库...")
            stdout, stderr, code = await asyncio.to_thread(
                self._run_git_command,
                ["git", "push", "origin", "master"]
            )
            
            if code != 0:
                # 检查是否是 SSH host key 验证错误
                if "Host key verification failed" in stderr or "host key" in stderr.lower():
                    logger.error(f"[每周备份] 推送失败: SSH host key 验证失败")
                    logger.error(f"[每周备份] 错误详情: {stderr}")
                    logger.warning("[每周备份] 提示: 请确保 SSH 密钥已添加到 GitHub")
                else:
                    logger.error(f"[每周备份] 推送失败: {stderr}")
                
                # 如果推送失败，尝试拉取最新代码后再推送
                logger.info("[每周备份] 尝试拉取最新代码...")
                stdout, stderr, code = await asyncio.to_thread(
                    self._run_git_command,
                    ["git", "pull", "origin", "master", "--rebase"]
                )
                if code == 0:
                    logger.info("[每周备份] 拉取成功，重新推送...")
                    stdout, stderr, code = await asyncio.to_thread(
                        self._run_git_command,
                        ["git", "push", "origin", "master"]
                    )
                    if code == 0:
                        logger.info("[每周备份] 推送成功")
                    else:
                        logger.error(f"[每周备份] 重新推送失败: {stderr}")
                else:
                    logger.error(f"[每周备份] 拉取失败: {stderr}")
                return
            
            logger.info(f"[每周备份] 推送成功: {stdout.strip()}")
            logger.info("[每周备份] 每周数据备份任务执行成功")
            
        except Exception as e:
            logger.error(f"[每周备份] 每周数据备份任务执行失败: {e}", exc_info=True)

