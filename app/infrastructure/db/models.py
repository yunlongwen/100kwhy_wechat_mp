"""数据库模型定义"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Article(Base):
    """文章模型"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=True)
    source = Column(String(200), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    published_time = Column(String(100), nullable=True)
    created_at = Column(String(100), nullable=True)
    archived_at = Column(String(100), nullable=True, index=True)
    view_count = Column(Integer, default=0, index=True)
    score = Column(Integer, default=0)
    tags = Column(JSON, nullable=True)
    tool_tags = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)  # 存储其他额外字段
    created_at_db = Column(DateTime, default=datetime.now)
    updated_at_db = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_article_category_archived', 'category', 'archived_at'),
        Index('idx_article_view_count', 'view_count'),
    )


class Tool(Base):
    """工具模型"""
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(200), nullable=True, unique=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    view_count = Column(Integer, default=0, index=True)
    score = Column(Integer, default=0)
    created_at = Column(String(100), nullable=True)
    extra_data = Column(JSON, nullable=True)  # 存储其他额外字段
    created_at_db = Column(DateTime, default=datetime.now)
    updated_at_db = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_tool_category_featured', 'category', 'is_featured'),
        Index('idx_tool_view_count', 'view_count'),
    )


class Prompt(Base):
    """提示词模型"""
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(200), nullable=True, unique=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    extra_data = Column(JSON, nullable=True)  # 存储其他额外字段
    created_at_db = Column(DateTime, default=datetime.now)
    updated_at_db = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Rule(Base):
    """规则模型"""
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    extra_data = Column(JSON, nullable=True)  # 存储其他额外字段
    created_at_db = Column(DateTime, default=datetime.now)
    updated_at_db = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Resource(Base):
    """社区资源模型"""
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)
    type = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True, index=True)
    created_at = Column(String(100), nullable=True)
    extra_data = Column(JSON, nullable=True)  # 存储其他额外字段
    created_at_db = Column(DateTime, default=datetime.now)
    updated_at_db = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_resource_type_category', 'type', 'category'),
    )

