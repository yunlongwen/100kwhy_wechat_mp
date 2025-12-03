# 降噪 AI广播编辑器 PRD文档

## 项目概述

这是一个AI驱动的广播内容编辑工具，用于将专业的AI技术文章转化为通俗易懂的广播稿件，并提供语音合成功能。

## AI提示词

以下是用于生成完整网页应用的AI提示词：

```
作为一位资深的全栈开发工程师，请帮我创建一个名为"降噪"的AI广播编辑网页应用。这个应用需要将专业的AI文章转化为通俗易懂的广播内容。

技术要求：
1. 前端技术栈：
   - HTML5 + CSS3 + JavaScript（原生）
   - Bootstrap 5 框架
   - 响应式设计，支持移动端
   - 玻璃态UI设计风格

2. 核心功能模块：
   A. 文本输入和编辑模块
      - 系统提示词（可展开/折叠）
      - 原始文案输入区
      - AI生成内容显示区
      - 支持一键清空和复制功能
   
   B. AI模型集成
      - 使用 MiniMax Text-01 模型
      - 异步请求处理
      - 完整的错误处理机制
   
   C. 语音合成功能
      - 使用MiniMax T2A v2接口
      - 支持自定义音色（superhuangclone）
      - 播放控制（播放/暂停）
      - MP3下载功能
      - 语音参数调节（语速、音量、音调、情绪）

3. 数据持久化：
   - 使用localStorage存储系统提示词
   - 保存用户语音设置偏好

4. UI/UX设计要求：
   - 简洁现代的界面设计
   - 玻璃态拟态设计风格
   - 响应式布局
   - 清晰的视觉反馈
   - 优雅的加载动画
   - Toast提示消息

5. 系统提示词模板：
"""
你是一档名为《降噪》的AI科技广播节目的资深编辑，名字叫AI产品黄叔，擅长将专业的AI文章转化为通俗易懂的广播内容。请将以下原始内容改写成适合播报的稿件。

原始内容
{{input}}
====End======

要求：
1. 请先全面的阅读一遍所有的新闻
2. 使用AI产品黄叔的身份，用幽默风趣的大白话，给AI小白讲清楚最新的资讯
3. 开场先概要说说今天发生了哪些大事
4. 每个新闻控制在100字以内，确保听众能在短时间内抓住重点
5. 语言风格要求：
   - 用生动的口语化表达，用大白话讲出专业性
   - 适当使用语气词增加自然感（比如"嗯"、"那么"、"其实"等）
   - 避免过于口语化的方言用语
   - 像跟朋友聊天一样轻松自然
6. 在保持通俗易懂的同时，准确传达AI技术的关键概念
7. 适当增加转场语，使话题之间衔接自然
"""

6. 代码规范：
   - 遵循现代JavaScript最佳实践
   - 清晰的代码注释
   - 模块化组织代码
   - 优雅的错误处理
   - 合理的变量命名

7. 文件结构：
```
project/
├── static/
│   ├── css/
│   │   ├── style.css    # 主样式
│   │   └── theme.css    # 主题样式
│   └── js/
│       └── main.js      # 主逻辑
├── index.html           # 主页面
└── README.md           # 项目文档
```

请基于以上要求，生成一个完整的、可直接部署的网页应用。确保代码结构清晰，注释完整，并包含必要的错误处理和用户体验优化。
```

## 功能规格

### 1. 文本处理模块
- 系统提示词编辑和保存
- 原始文案输入
- AI内容生成
- 文本复制和清空

### 2. AI模型集成
- MiniMax Text-01 模型
- 异步请求处理
- 错误处理机制

### 3. 语音功能
- 语音合成（T2A）
- 自定义音色
- 播放控制
- MP3下载
- 参数调节

### 4. 用户界面
- 响应式布局
- 玻璃态设计
- 操作反馈
- 错误提示

## 技术架构

### 前端技术栈
- HTML5
- CSS3
- JavaScript（原生）
- Bootstrap 5

### API集成

#### 1. MiniMax Text-01 对话接口
- 接口地址：`https://api.minimax.chat/v1/text/chatcompletion_v2`
- 请求方法：POST
- 请求头：
  ```json
  {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
  }
  ```
- 请求体格式：
  ```json
  {
    "model": "MiniMax-Text-01",
    "messages": [
      {
        "role": "system",
        "content": "系统提示词"
      },
      {
        "role": "user",
        "content": "用户输入"
      }
    ]
  }
  ```
- 响应格式：
  ```json
  {
    "id": "response_id",
    "choices": [
      {
        "message": {
          "role": "assistant",
          "content": "AI回复内容"
        }
      }
    ]
  }
  ```

#### 2. MiniMax T2A v2 语音合成接口
- 接口地址：`API：https://api.minimax.chat/v1/t2a_v2`
- 请求方法：

group_id="请填写您的group_id"
api_key="请填写您的api_key"
curl --location 'https://api.minimax.chat/v1/t2a_v2?GroupId=${group_id}' \
--header 'Authorization: Bearer $MiniMax_API_KEY' \
--header 'Content-Type: application/json' \
--data '{
    "model": "speech-01-turbo",
    "text": "真正的危险不是计算机开始像人一样思考，而是人开始像计算机一样思考。计算机只是可以帮我们处理一些简单事务。",
    "stream": false,
    "voice_setting":{
        "voice_id": "superhuangclone",
        "speed": 1.2,
        "vol": 1,
        "pitch": 0,
        "emotion": "happy"
    },
    "pronunciation_dict":{
        "tone": ["处理/(chu3)(li3)", "危险/dangerous"]
    },
    "audio_setting":{
        "sample_rate": 32000,
        "bitrate": 128000,
        "format": "mp3",
        "channel": 1
    }
  }'
- 响应格式：返回二进制音频数据（MP3格式）

### 数据存储
- localStorage

## 注意事项

1. API密钥安全性
2. 错误处理机制
3. 响应式设计适配
4. 浏览器兼容性
5. 性能优化
6. 将网页部署到本地服务器环境中运行，这样就能避免CORS的限制，使API请求能够正常工作。

## 后续优化建议

1. 添加对话历史记录
2. 支持多轮对话
3. 增加更多音色选项
4. 支持批量语音导出
5. 添加语音识别功能
6. 优化语音缓存机制
