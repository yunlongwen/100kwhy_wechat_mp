#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新现有Claude Code资源的subcategory字段
"""

import json
import sys
from pathlib import Path
from typing import Dict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.crawl_devmaster_resources import classify_claude_code_resource


def update_resources_subcategories():
    """更新resources.json中Claude Code资源的subcategory字段"""
    resources_file = project_root / "data" / "resources.json"
    
    # 读取现有资源
    with resources_file.open('r', encoding='utf-8') as f:
        resources = json.load(f)
    
    updated_count = 0
    for resource in resources:
        if resource.get('category') == 'Claude Code 资源':
            # 如果已经有subcategory，跳过
            if 'subcategory' in resource and resource['subcategory']:
                continue
            
            # 自动分类
            title = resource.get('title', '')
            description = resource.get('description', '')
            url = resource.get('url', '')
            
            subcategory = classify_claude_code_resource(title, description, url)
            resource['subcategory'] = subcategory
            updated_count += 1
            print(f"更新: {title} -> {subcategory}")
    
    # 保存更新后的资源
    with resources_file.open('w', encoding='utf-8') as f:
        json.dump(resources, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 完成！共更新 {updated_count} 个资源的subcategory字段")


if __name__ == "__main__":
    update_resources_subcategories()

