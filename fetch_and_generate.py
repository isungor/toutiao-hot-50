#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全网热榜看板 - 数据抓取 & HTML 生成脚本
数据源: 60s.viki.moe API (免费，无需认证)
"""

import json
import urllib.request
import urllib.error
import re
import sys
from datetime import datetime, timezone, timedelta

# ========== 配置 ==========
API_BASE = "https://60s.viki.moe/v2"
TIMEOUT = 15  # 秒

# 北京时区
BJ_TZ = timezone(timedelta(hours=8))

# 头条汽车筛选关键词
AUTO_KEYWORDS = [
    "车", "新能源", "比亚迪", "特斯拉", "丰田", "本田", "宝马", "奔驰",
    "奥迪", "蔚来", "理想", "小鹏", "吉利", "长安", "大众", "福特",
    "保时捷", "比亚迪", "华为", "小米汽车", "小米SU", "乐道", "方程豹",
    "自动驾驶", "充电", "续航", "混动", "纯电", "发动机", "变速箱",
    "汽车", "轿车", "SUV", "MPV", "销量", "召回", "碰撞", "油价",
    "充电桩", "路测", "试驾", "上市", "首发", "亮相"
]


# ========== 数据抓取 ==========
def fetch_json(url):
    """请求API并返回JSON数据"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == 200 and data.get("data"):
                return data["data"]
            return []
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}", file=sys.stderr)
        return []


def normalize_dcd(items):
    """标准化懂车帝数据"""
    result = []
    for i, item in enumerate(items[:10]):
        result.append({
            "rank": item.get("rank", i + 1),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "hot": item.get("score_desc", str(item.get("score", ""))),
            "hot_num": item.get("score", 0),
        })
    return result


def normalize_toutiao(items, limit=20):
    """标准化今日头条数据"""
    result = []
    for i, item in enumerate(items[:limit]):
        result.append({
            "rank": i + 1,
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "hot": item.get("hot_value", 0),
            "hot_num": item.get("hot_value", 0),
            "label": item.get("label", ""),
        })
    return result


def normalize_douyin(items, limit=20):
    """标准化抖音数据"""
    result = []
    for i, item in enumerate(items[:limit]):
        result.append({
            "rank": i + 1,
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "hot": item.get("hot_value", 0),
            "hot_num": item.get("hot_value", 0),
        })
    return result


def normalize_weibo(items, limit=20):
    """标准化微博数据"""
    result = []
    for i, item in enumerate(items[:limit]):
        result.append({
            "rank": i + 1,
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "hot": item.get("hot_value", 0),
            "hot_num": item.get("hot_value", 0),
            "label": item.get("label", ""),
        })
    return result


def filter_toutiao_auto(items):
    """从头条数据中筛选汽车相关条目"""
    result = []
    for item in items:
        title = item.get("title", "")
        for kw in AUTO_KEYWORDS:
            if kw in title:
                result.append(item)
                break
        if len(result) >= 10:
            break
    return normalize_toutiao(result, 10)


def filter_weibo_by_label(items, limit=10):
    """从微博数据中按标题关键词筛选文娱类条目"""
    entertainment_keywords = [
        "文娱", "影视", "综艺", "明星", "音乐", "电影", "电视剧", "演出", "娱乐",
        "浪姐", "歌手", "乘风", "演唱会", "票房", "热巴", "杨幂", "刘诗诗", "张柏芝",
        "白鹿", "迪丽热巴", "王力宏", "柯南", "何猷君", "奚梦瑶", "方媛", "李纯",
        "徐志胜", "张嘉益", "痞幼", "沈腾", "孙颖莎", "柳智敏", "Faker", "李乃文",
        "梅婷", "选秀"
    ]
    result = []
    for item in items:
        title = item.get("title", "")
        match = False
        for kw in entertainment_keywords:
            if kw in title:
                match = True
                break
        if match:
            result.append(item)
        if len(result) >= limit:
            break
    return normalize_weibo(result, limit)


def filter_weibo_tech(items, limit=10):
    """从微博数据中按标题关键词筛选科技类条目"""
    tech_keywords = [
        "科技", "数码", "手机", "AI", "芯片", "互联网", "技术", "App", "软件",
        "智能", "机器人", "苹果", "华为", "iPhone", "小米", "比亚迪", "特斯拉",
        "理想", "蔚来", "新能源", "半导体", "5G", "6G", "CPU", "GPU", "自动驾驶",
        "支付", "支付宝", "A股", "黄金", "库克", "降价", "换代"
    ]
    result = []
    for item in items:
        title = item.get("title", "")
        match = False
        for kw in tech_keywords:
            if kw in title:
                match = True
                break
        if match:
            result.append(item)
        if len(result) >= limit:
            break
    return normalize_weibo(result, limit)


# ========== HTML 生成 ==========
def format_hot(val):
    """格式化热度值"""
    n = int(val) if isinstance(val, (int, float)) else 0
    s = str(val).strip()
    if "w" in s.lower() or "万" in s:
        return s
    if n >= 100000000:
        return f"{n / 100000000:.1f}亿"
    if n >= 10000:
        return f"{n / 10000:.1f}万"
    if n > 0:
        return str(n)
    return s


def build_board_html(board_id, icon, title, accent_color, accent_bg, items):
    """生成单个看板HTML"""
    item_count = len(items)
    max_hot = max((item.get("hot_num", 0) for item in items), default=1) or 1

    items_html = ""
    for item in items:
        rank = item.get("rank", 0)
        title_text = item.get("title", "")
        url = item.get("url", "#")
        hot = format_hot(item.get("hot", 0))
        hot_num = item.get("hot_num", 0)
        pct = round(hot_num / max_hot * 100) if max_hot > 0 else 0
        label = item.get("label", "")

        rank_cls = "rank-top" if rank <= 3 else ("rank-accent" if rank <= 10 else "rank-normal")

        items_html += f"""      <div class="item" onclick="window.open('{url}','_blank')">
        <div class="rank {rank_cls}">{rank}</div>
        <div class="item-body">
          <a class="item-title" href="{url}" target="_blank" rel="noopener">{title_text}</a>
          <div class="item-foot">
            <div class="bar-wrap"><div class="bar-fill" style="width:{pct}%;background:linear-gradient(90deg,{accent_color},{accent_bg})"></div></div>
            <span class="hot-num">{hot}</span>
          </div>
        </div>
      </div>
"""

    return f"""  <div class="board" id="{board_id}">
    <div class="board-head">
      <span class="icon">{icon}</span>
      <span class="board-name">{title}</span>
      <span class="badge" style="background:{accent_color};color:#fff">TOP {item_count}</span>
    </div>
    <div class="list">
{items_html}    </div>
  </div>
"""


def generate_html(boards_data):
    """生成完整的HTML页面"""
    now_bj = datetime.now(BJ_TZ)
    update_time = now_bj.strftime("%Y-%m-%d %H:%M")

    boards_html = ""
    for board in boards_data:
        boards_html += build_board_html(
            board["id"], board["icon"], board["title"],
            board["color"], board["color_light"], board["items"]
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全网热榜看板</title>
<style>
:root {{
  --bg: #f0f2f5;
  --card: #ffffff;
  --text: #1a1a2e;
  --text2: #6b7280;
  --border: #e5e7eb;
  --shadow: 0 2px 8px rgba(0,0,0,0.06);
  --radius: 12px;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #0a0a0f;
    --card: #16161d;
    --text: #e8e8ed;
    --text2: #6e6e78;
    --border: #2a2a35;
    --shadow: 0 2px 8px rgba(0,0,0,0.3);
  }}
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  min-height: 100vh;
}}
.header {{
  text-align: center;
  padding: 32px 16px 12px;
}}
.header h1 {{
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}}
.header .sub {{
  font-size: 13px;
  color: var(--text2);
  margin-top: 6px;
}}
.header .sub span {{
  display: inline-block;
  background: rgba(102,126,234,0.1);
  color: #667eea;
  padding: 2px 10px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 12px;
  margin-left: 6px;
}}
.boards {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  max-width: 1400px;
  margin: 16px auto;
  padding: 0 16px 24px;
}}
.board {{
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}}
.board.span-2 {{ grid-column: span 2; }}
.board.span-3 {{ grid-column: span 3; }}
.board.span-4 {{ grid-column: span 4; }}

.board-head {{
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 14px 10px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: var(--card);
  z-index: 10;
}}
.board-head .icon {{ font-size: 18px; }}
.board-head .board-name {{
  font-size: 14px;
  font-weight: 700;
  flex: 1;
}}
.board-head .badge {{
  font-size: 10px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 8px;
  letter-spacing: 0.5px;
}}

.list {{
  flex: 1;
  padding: 4px 6px 8px;
  overflow-y: auto;
  max-height: 520px;
}}
.item {{
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 6px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}}
.item:hover {{ background: rgba(0,0,0,0.03); }}
@media (prefers-color-scheme: dark) {{
  .item:hover {{ background: rgba(255,255,255,0.03); }}
}}

.rank {{
  min-width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  border-radius: 6px;
  margin-top: 2px;
  flex-shrink: 0;
}}
.rank-top {{
  background: linear-gradient(135deg, #ff6b35, #ee5a24);
  color: #fff;
  box-shadow: 0 2px 6px rgba(238,90,36,0.25);
}}
.rank-accent {{
  background: rgba(102,126,234,0.1);
  color: #667eea;
}}
.rank-normal {{
  background: var(--bg);
  color: var(--text2);
  font-weight: 600;
}}

.item-body {{ flex: 1; min-width: 0; }}
.item-title {{
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  text-decoration: none;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  transition: opacity 0.15s;
}}
.item-title:hover {{ opacity: 0.6; }}

.item-foot {{
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}}
.bar-wrap {{
  flex: 1;
  height: 3px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}}
.bar-fill {{
  height: 100%;
  border-radius: 2px;
  min-width: 4px;
}}
.hot-num {{
  font-size: 10px;
  color: var(--text2);
  white-space: nowrap;
  flex-shrink: 0;
  min-width: 30px;
  text-align: right;
}}

.footer {{
  text-align: center;
  padding: 16px;
  font-size: 11px;
  color: var(--text2);
  border-top: 1px solid var(--border);
  max-width: 1400px;
  margin: 0 auto;
}}
.footer a {{
  color: #667eea;
  text-decoration: none;
}}
.footer a:hover {{ text-decoration: underline; }}

.back-top {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--card);
  border: 1px solid var(--border);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 99;
}}
.back-top.show {{ opacity: 1; }}
.back-top:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}

/* Mobile */
@media (max-width: 1100px) {{
  .boards {{ grid-template-columns: repeat(2, 1fr); }}
  .board.span-2, .board.span-3, .board.span-4 {{ grid-column: span 2; }}
}}
@media (max-width: 640px) {{
  .boards {{ grid-template-columns: 1fr; gap: 10px; }}
  .board.span-2, .board.span-3, .board.span-4 {{ grid-column: span 1; }}
  .header h1 {{ font-size: 20px; }}
  .list {{ max-height: none; }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>全网热榜看板</h1>
  <div class="sub">数据每日 18:00 自动更新 <span>{update_time}</span></div>
</div>

<div class="boards">
{boards_html}
</div>

<div class="footer">
  数据来源: <a href="https://60s.viki.moe" target="_blank">60s API</a> · 部署于 <a href="https://pages.github.com" target="_blank">GitHub Pages</a>
</div>

<div class="back-top" id="backTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</div>

<script>
window.addEventListener('scroll',function(){{
  document.getElementById('backTop').classList.toggle('show',window.scrollY>400);
}});
</script>
</body>
</html>"""


# ========== 主流程 ==========
def main():
    print("=" * 50)
    print(f"全网热榜看板 - 数据抓取 {datetime.now(BJ_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. 抓取基础数据（只需4个API）
    print("\n[1/4] 抓取懂车帝热榜...")
    dcd_raw = fetch_json(f"{API_BASE}/dongchedi")
    print(f"  → 获取 {len(dcd_raw)} 条")

    print("[2/4] 抓取今日头条热榜...")
    toutiao_raw = fetch_json(f"{API_BASE}/toutiao")
    print(f"  → 获取 {len(toutiao_raw)} 条")

    print("[3/4] 抓取抖音热榜...")
    douyin_raw = fetch_json(f"{API_BASE}/douyin")
    print(f"  → 获取 {len(douyin_raw)} 条")

    print("[4/4] 抓取微博热搜...")
    weibo_raw = fetch_json(f"{API_BASE}/weibo")
    print(f"  → 获取 {len(weibo_raw)} 条")

    # 2. 数据处理
    print("\n处理数据...")

    # 汽车热点 (懂车帝数据)
    auto_hot = normalize_dcd(dcd_raw[:10])
    print(f"  汽车热点: {len(auto_hot)} 条")

    # 懂车帝热点 (懂车帝数据)
    dcd_hot = normalize_dcd(dcd_raw[:10])
    print(f"  懂车帝热点: {len(dcd_hot)} 条")

    # 今日头条汽车榜 (从头条筛选汽车相关)
    toutiao_auto = filter_toutiao_auto(toutiao_raw)
    print(f"  头条汽车: {len(toutiao_auto)} 条 (筛选自头条)")

    # 今日头条热榜 TOP20
    toutiao_hot = normalize_toutiao(toutiao_raw, 20)
    print(f"  头条热榜: {len(toutiao_hot)} 条")

    # 抖音热榜 TOP20
    douyin_hot = normalize_douyin(douyin_raw, 20)
    print(f"  抖音热榜: {len(douyin_hot)} 条")

    # 微博热搜 TOP20
    weibo_hot = normalize_weibo(weibo_raw, 20)
    print(f"  微博热搜: {len(weibo_hot)} 条")

    # 微博文娱 (从微博筛选)
    weibo_ent = filter_weibo_by_label(weibo_raw, 10)
    print(f"  微博文娱: {len(weibo_ent)} 条 (筛选自微博)")

    # 微博科技 (从微博筛选)
    weibo_tech = filter_weibo_tech(weibo_raw, 10)
    print(f"  微博科技: {len(weibo_tech)} 条 (筛选自微博)")

    # 3. 组装看板
    boards = [
        {"id": "auto-hot",    "icon": "🚗", "title": "汽车热点",     "color": "#2ed573", "color_light": "#7bed9f", "items": auto_hot},
        {"id": "dcd-hot",     "icon": "🏎", "title": "懂车帝",       "color": "#00b894", "color_light": "#55efc4", "items": dcd_hot},
        {"id": "tt-auto",     "icon": "🔧", "title": "头条汽车",     "color": "#0984e3", "color_light": "#74b9ff", "items": toutiao_auto},
        {"id": "tt-hot",      "icon": "📰", "title": "今日头条",     "color": "#ff4757", "color_light": "#ff6b81", "items": toutiao_hot},
        {"id": "dy-hot",      "icon": "🎵", "title": "抖音热榜",     "color": "#1a1a2e", "color_light": "#636e72", "items": douyin_hot},
        {"id": "wb-hot",      "icon": "📱", "title": "微博热搜",     "color": "#ff4500", "color_light": "#ff6348", "items": weibo_hot},
        {"id": "wb-ent",      "icon": "🎬", "title": "微博文娱",     "color": "#e84393", "color_light": "#fd79a8", "items": weibo_ent},
        {"id": "wb-tech",     "icon": "💻", "title": "微博科技",     "color": "#6c5ce7", "color_light": "#a29bfe", "items": weibo_tech},
    ]

    # 4. 生成 HTML
    html = generate_html(boards)

    # 5. 写入文件
    output_path = "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    file_size = len(html.encode("utf-8"))
    print(f"\n✅ 生成完成: {output_path} ({file_size:,} bytes)")

    # 检查空看板
    empty_boards = [b["title"] for b in boards if len(b["items"]) == 0]
    if empty_boards:
        print(f"⚠️  以下看板无数据: {', '.join(empty_boards)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
