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


def extract_identifier(title: str) -> str:
    """从标题生成标识符"""
    # 移除特殊字符，转为小写，用连字符连接
    identifier = re.sub(r'[^\w\s-]', '', title.lower())
    identifier = re.sub(r'[-\s]+', '-', identifier)
    return identifier[:50] if len(identifier) > 50 else identifier


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
    project_root = Path(__file__).parent.parent
    resources_json = project_root / "data" / "resources.json"
    
    # 抓取资源
    resources = crawl_devmaster_resources()
    
    if resources:
        # 添加到JSON文件
        add_resources_to_json(resources, resources_json)
        print(f"\n✓ 完成！共添加 {len(resources)} 个资源")
    else:
        print("\n✗ 未抓取到任何资源")

