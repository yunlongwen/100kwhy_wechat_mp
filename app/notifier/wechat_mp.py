"""微信公众号发布接口"""
import os
from typing import Dict, Any, Optional

import httpx
from loguru import logger

from ..config_loader import load_env_var


class WeChatMPClient:
    """微信公众号客户端"""
    
    def __init__(self):
        # 优先从 .env 文件读取，如果不存在则从环境变量读取
        self.appid = load_env_var("WECHAT_MP_APPID") or os.getenv("WECHAT_MP_APPID")
        self.secret = load_env_var("WECHAT_MP_SECRET") or os.getenv("WECHAT_MP_SECRET")
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
        # 如果配置了，记录日志（不记录敏感信息）
        if self.appid and self.secret:
            logger.info("微信公众号配置已加载")
        else:
            logger.warning("微信公众号 AppID 或 Secret 未配置，相关功能将不可用")
    
    async def get_access_token(self) -> Optional[str]:
        """获取 access_token"""
        if self.access_token and self.token_expires_at and self.token_expires_at > __import__("time").time():
            return self.access_token
        
        if not self.appid or not self.secret:
            logger.error("微信公众号 AppID 或 Secret 未配置")
            return None
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.secret}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                data = resp.json()
                
                if "access_token" in data:
                    self.access_token = data["access_token"]
                    expires_in = data.get("expires_in", 7200)
                    self.token_expires_at = __import__("time").time() + expires_in - 300  # 提前5分钟刷新
                    return self.access_token
                else:
                    logger.error(f"获取 access_token 失败: {data}")
                    return None
        except Exception as e:
            logger.error(f"获取 access_token 异常: {e}")
            return None
    
    async def upload_media(self, media_type: str, media_path: str) -> Optional[str]:
        """上传素材"""
        token = await self.get_access_token()
        if not token:
            return None
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/media/upload?access_token={token}&type={media_type}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(media_path, "rb") as f:
                    files = {"media": f}
                    resp = await client.post(url, files=files)
                    data = resp.json()
                    
                    if "media_id" in data:
                        return data["media_id"]
                    else:
                        logger.error(f"上传素材失败: {data}")
                        return None
        except Exception as e:
            logger.error(f"上传素材异常: {e}")
            return None
    
    async def create_draft(self, articles: list) -> Optional[str]:
        """创建草稿"""
        token = await self.get_access_token()
        if not token:
            return None
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"articles": articles})
                data = resp.json()
                
                if "media_id" in data:
                    return data["media_id"]
                else:
                    logger.error(f"创建草稿失败: {data}")
                    return None
        except Exception as e:
            logger.error(f"创建草稿异常: {e}")
            return None
    
    async def publish(self, media_id: str) -> bool:
        """发布草稿"""
        token = await self.get_access_token()
        if not token:
            return False
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"media_id": media_id})
                data = resp.json()
                
                if data.get("errcode") == 0:
                    return True
                else:
                    logger.error(f"发布失败: {data}")
                    return False
        except Exception as e:
            logger.error(f"发布异常: {e}")
            return False
    
    async def get_draft_list(self, offset: int = 0, count: int = 20) -> Optional[Dict[str, Any]]:
        """获取草稿箱列表"""
        token = await self.get_access_token()
        if not token:
            return None
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={
                    "offset": offset,
                    "count": count,
                    "no_content": 0  # 返回内容
                })
                data = resp.json()
                
                if "item" in data:
                    return data
                else:
                    logger.error(f"获取草稿列表失败: {data}")
                    return None
        except Exception as e:
            logger.error(f"获取草稿列表异常: {e}")
            return None
    
    async def get_draft(self, media_id: str) -> Optional[Dict[str, Any]]:
        """获取草稿详情"""
        token = await self.get_access_token()
        if not token:
            return None
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"media_id": media_id})
                data = resp.json()
                
                if "news_item" in data:
                    return data
                else:
                    logger.error(f"获取草稿详情失败: {data}")
                    return None
        except Exception as e:
            logger.error(f"获取草稿详情异常: {e}")
            return None
    
    async def update_draft(self, media_id: str, index: int, article: Dict[str, Any]) -> bool:
        """更新草稿中的单篇文章"""
        token = await self.get_access_token()
        if not token:
            return False
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/draft/update?access_token={token}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={
                    "media_id": media_id,
                    "index": index,
                    "articles": article
                })
                data = resp.json()
                
                if data.get("errcode") == 0:
                    return True
                else:
                    logger.error(f"更新草稿失败: {data}")
                    return False
        except Exception as e:
            logger.error(f"更新草稿异常: {e}")
            return False
    
    async def delete_draft(self, media_id: str) -> bool:
        """删除草稿"""
        token = await self.get_access_token()
        if not token:
            return False
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/draft/delete?access_token={token}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"media_id": media_id})
                data = resp.json()
                
                if data.get("errcode") == 0:
                    return True
                else:
                    logger.error(f"删除草稿失败: {data}")
                    return False
        except Exception as e:
            logger.error(f"删除草稿异常: {e}")
            return False

