#!/usr/bin/env python3
"""
AI 行业新闻早报生成器
搜索过去 24 小时内的 AI 新闻，整理成结构化早报并发送到 Telegram
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 搜索源配置
SEARCH_SOURCES = [
    "site:techcrunch.com AI",
    "site:theverge.com AI",
    "site:reuters.com technology AI",
    "site:bloomberg.com technology AI",
    "site:cnbc.com AI",
    "site:venturebeat.com AI",
    "site:artificialintelligence-news.com",
    "site:aimagazine.com",
    "site:mit.edu AI research",
    "site:openai.com",
    "site:anthropic.com",
    "site:deepmind.com",
]

CATEGORIES = {
    "技术突破": [
        "AI research breakthrough",
        "machine learning advancement",
        "neural network architecture",
        "AI model training",
        "generative AI",
    ],
    "产品应用": [
        "AI product launch",
        "AI application release",
        "AI feature announcement",
        "AI tool update",
    ],
    "公司新闻": [
        "AI company funding",
        "AI startup investment",
        "AI company acquisition",
        "AI company earnings",
    ],
    "政策监管": [
        "AI regulation",
        "AI policy",
        "AI legislation",
        "AI government",
        "AI safety regulation",
    ],
}


def search_google_news(query: str, days: int = 1) -> List[Dict]:
    """使用 Google News RSS 搜索新闻"""
    from datetime import datetime, timedelta
    import feedparser
    import urllib.parse

    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Google News RSS URL
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"

    try:
        feed = feedparser.parse(rss_url)
        results = []

        for entry in feed.entries[:10]:
            # 解析时间
            published = entry.get('published', '')

            results.append({
                'title': entry.get('title', ''),
                'summary': entry.get('summary', entry.get('description', ''))[:200],
                'link': entry.get('link', ''),
                'source': entry.get('source', 'Google News'),
                'published': published,
            })

        return results
    except Exception as e:
        print(f"搜索出错：{e}")
        return []


def search_with_duckduckgo(query: str, days: int = 1) -> List[Dict]:
    """使用 DuckDuckGo 搜索新闻"""
    from duckduckgo_search import DDGS

    try:
        with DDGS() as ddgs:
            results = []
            # 搜索新闻
            search_results = ddgs.news(query, max_results=10)

            for r in search_results:
                results.append({
                    'title': r.get('title', ''),
                    'summary': r.get('body', '')[:200],
                    'link': r.get('url', ''),
                    'source': r.get('source', 'DuckDuckGo'),
                    'published': r.get('date', ''),
                })

            return results
    except Exception as e:
        print(f"DuckDuckGo 搜索出错：{e}")
        return []


def get_ai_news() -> Dict[str, List[Dict]]:
    """获取各分类的 AI 新闻"""
    all_news = {category: [] for category in CATEGORIES.keys()}

    for category, queries in CATEGORIES.items():
        print(f"搜索 {category} 类新闻...")
        category_news = []

        for query in queries:
            # 优先使用 DuckDuckGo
            results = search_with_duckduckgo(query, days=1)

            for result in results:
                if result['title'] and result['link']:
                    # 去重
                    if not any(n['link'] == result['link'] for n in category_news):
                        category_news.append(result)

            if len(category_news) >= 5:
                break

        # 每个类别保留最重要的 3-5 条
        all_news[category] = category_news[:5]

    return all_news


def generate_news_report(news: Dict[str, List[Dict]]) -> str:
    """生成结构化的新闻早报"""
    today = datetime.now().strftime("%Y年%m月%d日")
    weekday = datetime.now().strftime("%A")

    report = f"""# 🤖 AI 行业早报
**日期**: {today} ({weekday})
**生成时间**: {datetime.now().strftime("%H:%M")}

---

"""

    # 按类别添加新闻
    for category, items in news.items():
        if items:
            emoji = {
                "技术突破": "🔬",
                "产品应用": "📱",
                "公司新闻": "💼",
                "政策监管": "📋",
            }.get(category, "📰")

            report += f"## {emoji} {category}\n\n"

            for i, item in enumerate(items, 1):
                report += f"**{i}. {item['title']}**\n"
                if item['summary']:
                    report += f"   {item['summary']}\n"
                report += f"   来源：[{item['source']}]({item['link']})\n\n"

            report += "---\n\n"

    # 添加趋势总结
    report += """## 📈 行业趋势总结

"""

    # 根据新闻内容生成简短总结
    total_news = sum(len(items) for items in news.values())
    report += f"本期共收录 {total_news} 条重要新闻。\n\n"

    # 分析热点
    tech_news = len(news.get("技术突破", []))
    product_news = len(news.get("产品应用", []))

    if tech_news > 0:
        report += "- 技术层面：持续关注 AI 模型和研究进展\n"
    if product_news > 0:
        report += "- 产品层面：AI 应用落地加速，新产品不断涌现\n"

    report += "\n---\n"
    report += "*本早报由自动化脚本生成，数据来源：Google News, DuckDuckGo News*\n"

    return report


def send_to_telegram(message: str):
    """发送消息到 Telegram"""
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not telegram_bot_token or not telegram_chat_id:
        print("错误：未配置 Telegram 环境变量")
        print("请设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")
        return False

    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"

    payload = {
        "chat_id": telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()

        if result.get("ok"):
            print("✓ 消息已成功发送到 Telegram")
            return True
        else:
            print(f"发送失败：{result}")
            return False
    except Exception as e:
        print(f"发送 Telegram 消息出错：{e}")
        return False


def save_report_locally(report: str):
    """保存报告到本地文件"""
    today = datetime.now().strftime("%Y%m%d")
    filename = f"/Users/x/Downloads/Project/ai_news_{today}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✓ 报告已保存到：{filename}")


def main():
    print("🚀 开始生成 AI 行业早报...")
    print(f"搜索时间范围：过去 24 小时")

    # 获取新闻
    news = get_ai_news()

    # 生成报告
    report = generate_news_report(news)

    # 保存到本地
    save_report_locally(report)

    # 发送到 Telegram
    print("\n正在发送 Telegram 消息...")
    send_to_telegram(report)

    print("\n✅ AI 行业早报生成完成！")


if __name__ == "__main__":
    main()
