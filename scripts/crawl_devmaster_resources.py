#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 devmaster.cn 抓取社区资源并添加到 resources.json
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from playwright.sync_api import sync_playwright


def extract_identifier(title: str) -> str:
    """从标题生成标识符"""
    # 移除特殊字符，转为小写，用连字符连接
    identifier = re.sub(r'[^\w\s-]', '', title.lower())
    identifier = re.sub(r'[-\s]+', '-', identifier)
    return identifier[:50] if len(identifier) > 50 else identifier


def classify_claude_code_resource(title: str, description: str, url: str) -> str:
    """
    根据资源标题、描述和URL，将其分类到四个子类之一：
    - 插件市场
    - 模型服务
    - Skill
    - 其他
    """
    title_lower = title.lower()
    desc_lower = description.lower()
    url_lower = url.lower()
    combined_text = f"{title_lower} {desc_lower} {url_lower}"
    
    # Skill关键词（优先级最高，先检查）
    skill_keywords = [
        'skill', 'skills', 'agent skill', 'agentskills', 'awesome-claude-skills',
        'awesomeagentskills', '官方skill', '官方指南', 'skill例子', 'awesome-claude-skills'
    ]
    
    # 插件市场关键词
    marketplace_keywords = [
        'marketplace', 'market', '插件市场', 'plugin market', '插件', 'plugins',
        'claudemarketplaces', 'ccplugins'
    ]
    
    # 模型服务关键词（需要排除包含skill的）
    model_service_keywords = [
        'api', 'router', 'mirror', 'proxy', '服务', '模型服务', 'api代理',
        'code router', 'any router', 'aicodemirror'
    ]
    
    # 先检查Skill（优先级最高）
    if any(keyword in combined_text for keyword in skill_keywords):
        return 'Skill'
    
    # 检查插件市场
    if any(keyword in combined_text for keyword in marketplace_keywords):
        return '插件市场'
    
    # 检查模型服务（排除包含skill的）
    if not any(keyword in combined_text for keyword in skill_keywords):
        if any(keyword in combined_text for keyword in model_service_keywords):
            return '模型服务'
    
    # 默认归类为其他
    return '其他'


def crawl_claude_code_resources(url: str = "http://devmaster.cn/resource/tool/claude-code") -> List[Dict]:
    """
    从 devmaster.cn 抓取 Claude Code 资源
    
    返回资源列表，每个资源包含：
    - title: 标题
    - url: 链接
    - category: 分类（Claude Code 资源）
    - description: 描述
    """
    resources = []
    
    try:
        logger.info(f"开始抓取 Claude Code 资源: {url}")
        
        # 使用 Playwright 抓取动态内容
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # 访问页面
            page.goto(url, wait_until="networkidle", timeout=30000)
            # 等待内容加载
            page.wait_for_timeout(2000)
            
            # 获取页面HTML
            html_content = page.content()
            browser.close()
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 查找主内容区域 - 尝试多种选择器
        article = soup.find('article')
        if not article:
            article = soup.find('main')
        if not article:
            # 尝试查找包含"Claude Code"的div
            article = soup.find('div', string=re.compile('Claude Code', re.I))
            if article:
                article = article.find_parent()
        
        if not article:
            # 如果还是找不到，使用整个body
            article = soup.find('body')
        
        if not article:
            logger.error("无法找到内容区域")
            return resources
        
        # 查找所有链接
        all_links = article.find_all('a', href=True)
        
        # 排除的链接文本关键词
        exclude_keywords = ['返回', '首页', '关于', '联系', '登录', '注册', '切换菜单', '热门工具', 
                          '最近收录', '入门工具', '开发IDE', '命令行工具', 'AI测试', 'DevOp', 
                          'IDE插件', '代码审查', '文档相关', '设计工具', 'UI生成', 'CodeAgent', 
                          'MCP工具', '其他工具', '相关资源', '每日资讯', '资讯分类', '资讯周报', 
                          '编程资源', '关于我们', '返回顶部', 'AICoding基地']
        
        for link in all_links:
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            # 跳过空标题、导航链接或太短的标题
            if not title or len(title) < 2:
                continue
            
            # 跳过明显的导航链接
            if any(keyword in title for keyword in exclude_keywords):
                continue
            
            # 跳过内部导航链接
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # 跳过相对路径的导航链接（通常是内部导航）
            if href and not href.startswith('http') and not href.startswith('/resource/'):
                # 只保留 /resource/ 开头的链接
                if not href.startswith('/resource/'):
                    continue
            
            # 处理相对链接
            if href and not href.startswith('http'):
                if href.startswith('/'):
                    href = f"http://devmaster.cn{href}"
                else:
                    href = f"{url.rstrip('/')}/{href}"
            
            # 获取描述：尝试从父元素或下一个兄弟元素获取
            description = title
            parent = link.parent
            if parent:
                # 查找描述文本（通常在链接后的文本中）
                next_sibling = link.next_sibling
                if next_sibling:
                    if hasattr(next_sibling, 'get_text'):
                        desc_text = next_sibling.get_text(strip=True)
                    else:
                        desc_text = str(next_sibling).strip()
                    if desc_text and len(desc_text) > 10 and desc_text != title:
                        description = f"{title} - {desc_text[:100]}"
                
                # 如果没找到，尝试从父元素的文本中提取
                if description == title:
                    parent_text = parent.get_text(strip=True)
                    if len(parent_text) > len(title):
                        # 移除标题部分，获取剩余作为描述
                        desc_part = parent_text.replace(title, '', 1).strip()
                        if desc_part and len(desc_part) > 10:
                            description = f"{title} - {desc_part[:100]}"
            
            # 如果还是没有描述，使用默认描述
            if description == title:
                description = f"{title} - Claude Code 相关的工具、教程和资源"
            
            # 检查是否已存在（避免重复）
            if any(r.get('url') == href for r in resources):
                continue
            
            # 自动分类到子类
            subcategory = classify_claude_code_resource(title, description, href)
            
            resources.append({
                'title': title,
                'url': href,
                'category': 'Claude Code 资源',
                'subcategory': subcategory,
                'description': description,
                'type': '资源',
                'tags': ['Claude Code', 'AI编程', '工具'],
                'author': 'devmaster.cn',
                'source_url': url
            })
        
        logger.info(f"成功抓取 {len(resources)} 个 Claude Code 资源")
        
    except Exception as e:
        logger.error(f"抓取 Claude Code 资源失败: {e}", exc_info=True)
    
    return resources


def crawl_devmaster_resources(url: str = "http://devmaster.cn/resource/AICoding%E7%A4%BE%E5%8C%BA") -> List[Dict]:
    """
    从 devmaster.cn 抓取社区资源
    
    返回资源列表，每个资源包含：
    - title: 标题
    - url: 链接
    - category: 分类（飞书知识库/技术社区）
    - description: 描述
    """
    resources = []
    
    try:
        logger.info(f"开始抓取: {url}")
        
        # 发送HTTP请求
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            html_content = response.text
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 查找主内容区域
        article = soup.find('article')
        if not article:
            logger.warning("未找到 article 标签，尝试其他方法")
            article = soup.find('main')
        
        if not article:
            logger.error("无法找到内容区域")
            return resources
        
        # 查找所有标题和链接
        current_category = None
        current_section = None
        
        # 查找所有 h2 或 h3 标题作为分类
        headings = article.find_all(['h1', 'h2', 'h3'])
        
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            
            # 判断是否为分类标题
            if '飞书知识库' in heading_text:
                current_category = '飞书知识库'
                current_section = '知识库'
                continue
            elif '技术社区' in heading_text:
                current_category = '技术社区'
                current_section = '社区'
                continue
            
            # 如果找到分类，继续查找该分类下的链接
            if current_category:
                # 查找该标题后的列表项
                next_element = heading.find_next_sibling()
                while next_element:
                    if next_element.name == 'ul' or next_element.name == 'ol':
                        # 查找列表中的所有链接
                        links = next_element.find_all('a', href=True)
                        for link in links:
                            title = link.get_text(strip=True)
                            href = link.get('href', '')
                            
                            # 处理相对链接
                            if href and not href.startswith('http'):
                                if href.startswith('/'):
                                    href = f"http://devmaster.cn{href}"
                                else:
                                    href = f"{url.rstrip('/')}/{href}"
                            
                            if title and href:
                                # 生成描述
                                if current_category == '飞书知识库':
                                    description = f"{title} - 飞书知识库中的AI编程相关内容"
                                else:
                                    description = f"{title} - 技术社区中的AI编程相关内容"
                                
                                resources.append({
                                    'title': title,
                                    'url': href,
                                    'category': current_category,
                                    'description': description,
                                    'type': '知识库' if current_category == '飞书知识库' else '社区',
                                    'tags': ['AI编程', current_section] if current_section else ['AI编程'],
                                    'author': 'devmaster.cn',
                                    'source_url': url
                                })
                        break
                    elif next_element.name in ['h1', 'h2', 'h3']:
                        # 遇到下一个标题，停止当前分类
                        break
                    next_element = next_element.find_next_sibling()
        
        # 如果没有通过标题找到，尝试直接查找所有链接
        if not resources:
            logger.info("尝试直接查找所有链接")
            all_links = article.find_all('a', href=True)
            current_category = None
            
            for link in all_links:
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                # 跳过空标题或导航链接
                if not title or len(title) < 2:
                    continue
                
                # 查找链接前面的文本，判断分类
                parent = link.parent
                prev_text = ''
                if parent:
                    prev_sibling = parent.find_previous_sibling()
                    if prev_sibling:
                        prev_text = prev_sibling.get_text(strip=True)
                
                # 根据上下文判断分类
                if '飞书知识库' in prev_text or '知识库' in prev_text:
                    current_category = '飞书知识库'
                elif '技术社区' in prev_text or '社区' in prev_text:
                    current_category = '技术社区'
                
                if title and href and current_category:
                    # 处理相对链接
                    if href and not href.startswith('http'):
                        if href.startswith('/'):
                            href = f"http://devmaster.cn{href}"
                        else:
                            href = f"{url.rstrip('/')}/{href}"
                    
                    description = f"{title} - {current_category}中的AI编程相关内容"
                    resources.append({
                        'title': title,
                        'url': href,
                        'category': current_category,
                        'description': description,
                        'type': '知识库' if current_category == '飞书知识库' else '社区',
                        'tags': ['AI编程', current_category],
                        'author': 'devmaster.cn',
                        'source_url': url
                    })
        
        logger.info(f"成功抓取 {len(resources)} 个资源")
        
    except Exception as e:
        logger.error(f"抓取失败: {e}", exc_info=True)
    
    return resources


def add_resources_to_json(resources: List[Dict], resources_json_path: Path):
    """将抓取的资源添加到 resources.json"""
    
    # 读取现有资源
    if resources_json_path.exists():
        with resources_json_path.open('r', encoding='utf-8') as f:
            existing_resources = json.load(f)
        max_id = max((r.get('id', 0) for r in existing_resources), default=0)
        next_id = max_id + 1
    else:
        existing_resources = []
        next_id = 1
    
    # 准备新资源
    new_resources = []
    for resource in resources:
        # 检查是否已存在（根据URL）
        if any(r.get('url') == resource['url'] for r in existing_resources):
            logger.info(f"资源已存在，跳过: {resource['title']}")
            continue
        
        # 创建完整的资源条目
        resource_entry = {
            'title': resource['title'],
            'description': resource.get('description', resource['title']),
            'type': resource.get('type', '资源'),
            'category': resource.get('category', '其他'),
            'tags': resource.get('tags', ['AI编程']),
            'url': resource['url'],
            'author': resource.get('author', ''),
            'view_count': 0,
            'created_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'is_featured': False,
            'id': next_id,
            'identifier': extract_identifier(resource['title'])
        }
        
        # 如果是Claude Code资源，添加subcategory字段
        if resource.get('category') == 'Claude Code 资源' and 'subcategory' in resource:
            resource_entry['subcategory'] = resource['subcategory']
        
        new_resources.append(resource_entry)
        next_id += 1
    
    if not new_resources:
        logger.info("没有新资源需要添加")
        return
    
    # 合并资源
    all_resources = existing_resources + new_resources
    
    # 保存
    with resources_json_path.open('w', encoding='utf-8') as f:
        json.dump(all_resources, f, ensure_ascii=False, indent=2)
    
    logger.info(f"成功添加 {len(new_resources)} 个新资源")
    logger.info(f"总资源数: {len(all_resources)}")
    
    # 打印新添加的资源
    for resource in new_resources:
        print(f"  - [{resource['id']}] {resource['title']} ({resource['category']})")


if __name__ == "__main__":
    import sys
    
    project_root = Path(__file__).parent.parent
    resources_json = project_root / "data" / "resources.json"
    
    # 根据命令行参数决定抓取哪个资源
    if len(sys.argv) > 1 and sys.argv[1] == "claude-code":
        # 抓取 Claude Code 资源
        resources = crawl_claude_code_resources()
    else:
        # 默认抓取社区资源
        resources = crawl_devmaster_resources()
    
    if resources:
        # 添加到JSON文件
        add_resources_to_json(resources, resources_json)
        print(f"\n✓ 完成！共添加 {len(resources)} 个资源")
    else:
        print("\n✗ 未抓取到任何资源")

