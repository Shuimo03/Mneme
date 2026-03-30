# Mneme

Mneme 是一个信息摘要订阅机器人，自动从多个高质量信息源收集、去重、通过 LLM 总结内容，支持 Web 界面浏览或推送到指定渠道。

## 信息源

- Anthropic Blog
- Meta Engineering Blog
- arXiv
- Hacker News

## 技术栈

| 类别 | 框架/库 |
|------|---------|
| 编程语言 | Python 3.13+ |
| HTTP 客户端 | httpx, requests |
| Web 爬虫 | crawl4ai (>=0.8.0) |
| RSS 解析 | feedparser |
| Web 框架 | FastAPI (>=0.128.0) |
| 数据验证 | Pydantic |
| 包管理 | uv |

## 架构

```
Source Adapters → Collector → Summarizer → Web UI / Notifier
```

- **Source Adapters** (`src/adapters/`): 独立模块，从各信息源抓取和解析内容，输出统一数据结构
- **Collector** (`src/collector.py`): 调度运行，调用适配器，内容去重
- **Summarizer** (`src/summarizer.py`): 使用 LLM 压缩文章为摘要
- **Web UI** (`src/web/`): Web 界面，在线浏览和搜索已收集的文章
- **Notifier** (`src/notifier.py`): 推送结果到配置渠道（微信、Telegram 等）

## 数据模型

```python
class Article(BaseModel):
    id: str              # 唯一标识 (URL 或 hash)
    source: str          # 来源标识
    title: str           # 文章标题
    published_at: datetime  # 发布时间
    url: str             # 原文链接
    raw_content: str = ""  # 正文内容
```

## 快速开始

```bash
# 安装依赖
uv sync

# 运行应用
python main.py

# 添加新依赖
uv add <package>
```

## 当前状态

**已完成：**
- 项目基础架构
- Meta Engineering Blog 适配器（抓取 + 解析 + 存储）
- 文件存储系统
- 标题提取工具

**待完成：**
- Anthropic Blog、arXiv、Hacker News 适配器
- 信息去重功能
- LLM 摘要集成
- Web 界面（在线浏览和搜索）
- 推送通道（微信/Telegram）
- 定时调度系统
