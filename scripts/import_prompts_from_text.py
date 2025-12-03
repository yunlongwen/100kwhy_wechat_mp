#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从文本文件中提取提示词并添加到 prompts.json
支持多种格式的文本输入
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


def extract_prompts_from_text(text: str) -> List[Dict]:
    """
    从文本中提取提示词
    支持多种格式：
    1. 以标题开头，内容在代码块中的格式
    2. 以 # Role、# Goal 等标记的格式
    3. 简单的标题+内容格式
    """
    prompts = []
    
    # 按章节分割（根据常见的章节标记）
    sections = re.split(r'(?:^|\n)(?:#{1,3}\s+|Part\d+[：:]\s*|第[一二三四五六七八九十]+[部分章]|##\s+)', text, flags=re.MULTILINE)
    
    current_title = None
    current_content = []
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # 检查是否是标题行
        lines = section.split('\n')
        first_line = lines[0].strip()
        
        # 如果是明显的标题（短行，不含代码块标记）
        if len(first_line) < 100 and not first_line.startswith('```'):
            # 保存上一个提示词
            if current_title and current_content:
                prompts.append({
                    'title': current_title,
                    'content': '\n'.join(current_content).strip()
                })
            
            current_title = first_line
            current_content = lines[1:] if len(lines) > 1 else []
        else:
            # 继续添加到当前内容
            current_content.extend(lines)
    
    # 添加最后一个提示词
    if current_title and current_content:
        prompts.append({
            'title': current_title,
            'content': '\n'.join(current_content).strip()
        })
    
    return prompts


def create_prompt_entry(title: str, content: str, base_id: int, 
                       category: str = "代码", 
                       tags: Optional[List[str]] = None,
                       url: str = "https://superhuang.feishu.cn/wiki/W1LCwYA8eiTl77kpi81c31yNnJd") -> Dict:
    """创建标准化的提示词条目"""
    
    # 生成标识符
    identifier = re.sub(r'[^\w\s-]', '', title.lower())
    identifier = re.sub(r'[-\s]+', '-', identifier)[:50]
    
    # 生成描述（取内容的前200字符）
    description = content[:200].replace('\n', ' ').strip()
    if len(content) > 200:
        description += '...'
    
    return {
        "name": title,
        "description": description,
        "category": category,
        "tags": tags or [],
        "author": "",
        "url": url,
        "content": content,
        "view_count": 0,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "is_featured": False,
        "id": base_id,
        "identifier": identifier
    }


def import_prompts_to_json(text_file: Path, prompts_json: Path, 
                          start_id: Optional[int] = None):
    """
    从文本文件导入提示词到JSON文件
    """
    # 读取现有提示词
    if prompts_json.exists():
        with prompts_json.open('r', encoding='utf-8') as f:
            existing_prompts = json.load(f)
        max_id = max((p.get('id', 0) for p in existing_prompts), default=0)
        next_id = max_id + 1
    else:
        existing_prompts = []
        next_id = start_id or 1
    
    # 读取文本文件
    with text_file.open('r', encoding='utf-8') as f:
        text_content = f.read()
    
    # 提取提示词
    extracted = extract_prompts_from_text(text_content)
    
    print(f"从文本中提取了 {len(extracted)} 个提示词片段")
    
    # 转换为标准格式
    new_prompts = []
    for idx, item in enumerate(extracted):
        prompt_entry = create_prompt_entry(
            title=item['title'],
            content=item['content'],
            base_id=next_id + idx
        )
        new_prompts.append(prompt_entry)
        print(f"  - {prompt_entry['name']} (ID: {prompt_entry['id']})")
    
    # 合并到现有提示词
    all_prompts = existing_prompts + new_prompts
    
    # 保存
    with prompts_json.open('w', encoding='utf-8') as f:
        json.dump(all_prompts, f, ensure_ascii=False, indent=2)
    
    print(f"\n成功添加 {len(new_prompts)} 个提示词到 {prompts_json}")
    print(f"总提示词数: {len(all_prompts)}")


def manual_add_prompts():
    """手动添加提示词的辅助函数"""
    prompts_data = [
        {
            "title": "06 必备的Windsurf技巧",
            "description": "Windsurf IDE 使用技巧和最佳实践",
            "category": "代码",
            "tags": ["Windsurf", "IDE", "技巧"],
        },
        {
            "title": "使用AI IDE进行创作",
            "description": "如何利用AI IDE进行内容创作",
            "category": "代码",
            "tags": ["AI IDE", "创作"],
        },
        {
            "title": "改写提示词",
            "description": "提示词改写技巧和方法",
            "category": "代码",
            "tags": ["提示词", "改写"],
        },
        {
            "title": "使用提示词生成精美图片",
            "description": "使用AI提示词生成图片的方法",
            "category": "代码",
            "tags": ["提示词", "图片生成"],
        },
        {
            "title": "图片字幕生成器",
            "description": "开发图片字幕生成器的提示词和规则",
            "category": "代码",
            "tags": ["图片", "字幕", "生成器"],
        },
    ]
    
    return prompts_data


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python import_prompts_from_text.py <文本文件路径>")
        print("\n或者直接运行脚本查看手动添加提示词的示例")
        sys.exit(1)
    
    text_file = Path(sys.argv[1])
    prompts_json = Path(__file__).parent.parent / "data" / "prompts.json"
    
    if not text_file.exists():
        print(f"错误: 文件 {text_file} 不存在")
        sys.exit(1)
    
    import_prompts_to_json(text_file, prompts_json)

