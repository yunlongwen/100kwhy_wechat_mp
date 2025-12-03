#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量添加飞书文档中的提示词到 prompts.json
使用方法：
1. 从飞书文档复制所有提示词内容到一个文本文件
2. 运行此脚本：python scripts/add_feishu_prompts.py <文本文件路径>
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


def extract_prompt_sections(text: str) -> List[Dict[str, str]]:
    """
    从文本中提取提示词章节
    支持多种格式的文档结构
    """
    prompts = []
    
    # 方法1: 按标题分割（支持 #、##、### 或 Part1: 等格式）
    title_pattern = r'(?:^|\n)(?:#{1,3}\s+|Part\d+[：:]\s*|第[一二三四五六七八九十]+[部分章节]|##\s+|###\s+)(.+?)(?:\n|$)'
    matches = list(re.finditer(title_pattern, text, re.MULTILINE))
    
    if matches:
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start_pos:end_pos].strip()
            
            if content:
                prompts.append({
                    'title': title,
                    'content': content
                })
    
    # 方法2: 如果没有找到标题，尝试按代码块分割
    if not prompts:
        code_block_pattern = r'```(?:shell|bash|text|markdown)?\n(.*?)\n```'
        code_blocks = re.findall(code_block_pattern, text, re.DOTALL)
        
        for i, block in enumerate(code_blocks):
            prompts.append({
                'title': f'提示词 {i + 1}',
                'content': block.strip()
            })
    
    # 方法3: 如果都没有，尝试按空行分割大段落
    if not prompts:
        paragraphs = re.split(r'\n\s*\n+', text)
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if len(para) > 50:  # 只保留较长的段落
                lines = para.split('\n')
                title = lines[0][:50] if lines else f'提示词 {i + 1}'
                content = para
                prompts.append({
                    'title': title,
                    'content': content
                })
    
    return prompts


def create_prompt_entry(
    title: str,
    content: str,
    base_id: int,
    source_url: str = "https://superhuang.feishu.cn/wiki/W1LCwYA8eiTl77kpi81c31yNnJd",
    category: str = "代码"
) -> Dict:
    """创建标准化的提示词条目"""
    
    # 清理标题
    clean_title = title.strip().replace('\n', ' ').strip()
    
    # 生成标识符
    identifier = re.sub(r'[^\w\s-]', '', clean_title.lower())
    identifier = re.sub(r'[-\s]+', '-', identifier)
    identifier = identifier[:50] if len(identifier) > 50 else identifier
    
    # 生成描述
    # 移除代码块标记和特殊字符
    clean_content = re.sub(r'```[a-z]*\n', '', content)
    clean_content = re.sub(r'```', '', clean_content)
    description = clean_content.replace('\n', ' ').strip()[:200]
    if len(clean_content.replace('\n', ' ')) > 200:
        description += '...'
    
    # 提取标签（从标题和内容中）
    tags = []
    tag_keywords = {
        'Windsurf': ['windsurf', 'ide'],
        'AI IDE': ['ai ide', 'ide'],
        '提示词': ['提示词', 'prompt'],
        '图片': ['图片', 'image'],
        '网页': ['网页', 'web', '网站'],
        'DeepSeek': ['deepseek'],
        '浏览器插件': ['浏览器', '插件', 'extension'],
        '抖音': ['抖音', 'douyin'],
        '播客': ['播客', 'podcast'],
        '多维表格': ['多维表格', '飞书'],
    }
    
    title_lower = clean_title.lower()
    content_lower = content.lower()
    for tag, keywords in tag_keywords.items():
        if any(kw in title_lower or kw in content_lower for kw in keywords):
            tags.append(tag)
    
    if not tags:
        tags = ['AI编程']
    
    return {
        "name": clean_title,
        "description": description,
        "category": category,
        "tags": tags,
        "author": "",
        "url": source_url,
        "content": content.strip(),
        "view_count": 0,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "is_featured": False,
        "id": base_id,
        "identifier": identifier
    }


def add_prompts_from_file(text_file_path: Path, prompts_json_path: Path):
    """从文本文件读取并添加提示词"""
    
    # 读取文本文件
    try:
        with text_file_path.open('r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        print(f"错误: 无法读取文件 {text_file_path}: {e}")
        return
    
    # 提取提示词
    prompt_sections = extract_prompt_sections(text_content)
    
    if not prompt_sections:
        print("警告: 未能从文本中提取到提示词内容")
        print("\n提示: 请确保文本文件中包含:")
        print("  1. 以 #、##、Part1: 等开头的标题")
        print("  2. 或者包含代码块 (```...```)")
        print("  3. 或者包含用空行分隔的段落")
        return
    
    print(f"✓ 从文本中提取了 {len(prompt_sections)} 个提示词片段\n")
    
    # 读取现有提示词
    if prompts_json_path.exists():
        with prompts_json_path.open('r', encoding='utf-8') as f:
            existing_prompts = json.load(f)
        max_id = max((p.get('id', 0) for p in existing_prompts), default=0)
        next_id = max_id + 1
    else:
        existing_prompts = []
        next_id = 1
    
    # 创建新提示词条目
    new_prompts = []
    for idx, section in enumerate(prompt_sections):
        prompt_entry = create_prompt_entry(
            title=section['title'],
            content=section['content'],
            base_id=next_id + idx
        )
        new_prompts.append(prompt_entry)
        print(f"  [{prompt_entry['id']}] {prompt_entry['name']}")
        print(f"      标签: {', '.join(prompt_entry['tags'])}")
        print()
    
    # 合并提示词
    all_prompts = existing_prompts + new_prompts
    
    # 保存
    try:
        with prompts_json_path.open('w', encoding='utf-8') as f:
            json.dump(all_prompts, f, ensure_ascii=False, indent=2)
        print(f"✓ 成功添加 {len(new_prompts)} 个提示词到 {prompts_json_path}")
        print(f"✓ 总提示词数: {len(all_prompts)}")
    except Exception as e:
        print(f"错误: 无法保存到文件: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python scripts/add_feishu_prompts.py <文本文件路径>")
        print("\n说明:")
        print("  1. 从飞书文档复制所有提示词内容到文本文件")
        print("  2. 保存为 .txt 或 .md 文件")
        print("  3. 运行此脚本导入提示词")
        print("\n示例:")
        print("  python scripts/add_feishu_prompts.py prompts_from_feishu.txt")
        sys.exit(1)
    
    text_file = Path(sys.argv[1])
    project_root = Path(__file__).parent.parent
    prompts_json = project_root / "data" / "prompts.json"
    
    if not text_file.exists():
        print(f"错误: 文件不存在: {text_file}")
        print("\n请先创建文本文件，从飞书文档复制提示词内容到文件中")
        sys.exit(1)
    
    print(f"正在从 {text_file} 导入提示词...\n")
    add_prompts_from_file(text_file, prompts_json)

