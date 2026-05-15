#!/usr/bin/env node
/**
 * 全网热榜看板 - 数据抓取 & HTML 生成脚本 (Node.js版)
 * 用于本地测试；GitHub Actions 使用 Python 版 (fetch_and_generate.py)
 */

const https = require('https');

const API_BASE = 'https://60s.viki.moe/v2';
const TIMEOUT = 15000;

// 头条汽车筛选关键词
const AUTO_KEYWORDS = [
  '车','新能源','比亚迪','特斯拉','丰田','本田','宝马','奔驰','奥迪','蔚来','理想','小鹏','吉利','长安','大众','福特',
  '保时捷','华为','小米汽车','小米SU','乐道','方程豹','自动驾驶','充电','续航','混动','纯电','发动机','变速箱',
  '汽车','轿车','SUV','MPV','销量','召回','碰撞','油价','充电桩','路测','试驾','上市','首发','亮相'
];

function nowBJ() {
  return new Date(Date.now() + 8 * 3600 * 1000);
}

function formatBJ(d) {
  const dt = new Date(d);
  return `${dt.getUTCFullYear()}-${String(dt.getUTCMonth()+1).padStart(2,'0')}-${String(dt.getUTCDate()).padStart(2,'0')} ${String(dt.getUTCHours()).padStart(2,'0')}:${String(dt.getUTCMinutes()).padStart(2,'0')}`;
}

function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: TIMEOUT }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const j = JSON.parse(data);
          resolve(j.code === 200 && j.data ? j.data : []);
        } catch (e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

function normalizeDcd(items, limit = 10) {
  return items.slice(0, limit).map((d, i) => ({
    rank: d.rank || i + 1,
    title: d.title || '',
    url: d.url || '',
    hot: d.score_desc || String(d.score || ''),
    hot_num: d.score || 0,
  }));
}

function normalizeToutiao(items, limit = 20) {
  return items.slice(0, limit).map((d, i) => ({
    rank: i + 1,
    title: d.title || '',
    url: d.link || '',
    hot: d.hot_value || 0,
    hot_num: d.hot_value || 0,
    label: d.label || '',
  }));
}

function normalizeDouyin(items, limit = 20) {
  return items.slice(0, limit).map((d, i) => ({
    rank: i + 1,
    title: d.title || '',
    url: d.link || '',
    hot: d.hot_value || 0,
    hot_num: d.hot_value || 0,
  }));
}

function normalizeWeibo(items, limit = 20) {
  return items.slice(0, limit).map((d, i) => ({
    rank: i + 1,
    title: d.title || '',
    url: d.link || '',
    hot: d.hot_value || 0,
    hot_num: d.hot_value || 0,
    label: d.label || '',
  }));
}

function filterByKeywords(items, keywords, limit = 10) {
  const result = [];
  for (const item of items) {
    const t = item.title || '';
    for (const kw of keywords) {
      if (t.includes(kw)) { result.push(item); break; }
    }
    if (result.length >= limit) break;
  }
  return result;
}

const ENT_KW = ['文娱','影视','综艺','明星','音乐','电影','电视剧','演出','娱乐','浪姐','歌手','乘风','芒果','选秀','演唱会','票房','热搜','热巴','杨幂','刘诗诗','张柏芝','白鹿','迪丽热巴','王力宏','名侦探柯南','何猷君','奚梦瑶','方媛','李纯','徐志胜','张嘉益','痞幼','沈腾','孙颖莎','柳智敏','Faker','徐志胜','李乃文','梅婷','黄圣依'];
const TECH_KW = ['科技','数码','手机','AI','芯片','互联网','技术','App','软件','智能','机器人','苹果','华为','iPhone','小米','比亚迪','特斯拉','理想','蔚来','新能源','半导体','5G','6G','CPU','GPU','自动驾驶','支付','支付宝','A股','黄金','黄金','库克','降价','换代'];
const AUTO_KW = ['车','新能源','比亚迪','特斯拉','丰田','本田','宝马','奔驰','奥迪','蔚来','理想','小鹏','吉利','长安','大众','福特','保时捷','华为','小米汽车','小米SU','乐道','方程豹','自动驾驶','充电','续航','混动','纯电','发动机','变速箱','汽车','轿车','SUV','MPV','销量','召回','碰撞','油价','充电桩','路测','试驾','上市','首发','亮相','东风日产','问界','智界','享界','极氪','零跑','岚图','深蓝','哪吒'];

function formatHot(val) {
  const s = String(val).trim();
  if (/w/i.test(s) || s.includes('万')) return s;
  const n = parseInt(val) || 0;
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿';
  if (n >= 10000) return (n / 10000).toFixed(1) + '万';
  return n > 0 ? String(n) : s;
}

function buildBoardHTML(id, icon, title, color, colorLight, items) {
  const count = items.length;
  const maxHot = Math.max(...items.map(i => i.hot_num || 0), 1);

  const itemsHTML = items.map(item => {
    const { rank, title: t, url, hot, hot_num } = item;
    const pct = Math.round((hot_num || 0) / maxHot * 100);
    const rc = rank <= 3 ? 'rank-top' : rank <= 10 ? 'rank-accent' : 'rank-normal';
    const safeUrl = (url || '#').replace(/'/g, '&#39;');
    const safeTitle = t.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return `      <div class="item" onclick="window.open('${safeUrl}','_blank')">
        <div class="rank ${rc}">${rank}</div>
        <div class="item-body">
          <a class="item-title" href="${safeUrl}" target="_blank" rel="noopener">${safeTitle}</a>
          <div class="item-foot">
            <div class="bar-wrap"><div class="bar-fill" style="width:${pct}%;background:#555"></div></div>
            <span class="hot-num">${formatHot(hot)}</span>
          </div>
        </div>
      </div>`;
  }).join('\n');

  return `  <div class="board" id="${id}">
    <div class="board-head">
      <span class="icon">${icon}</span>
      <span class="board-name">${title}</span>
      <span class="badge" style="background:${color};color:#fff">TOP ${count}</span>
    </div>
    <div class="list">
${itemsHTML}
    </div>
  </div>`;
}

function generateHTML(boards) {
  const updateTime = formatBJ(nowBJ());
  const boardsHTML = boards.map(b => buildBoardHTML(b.id, b.icon, b.title, b.color, b.colorLight, b.items)).join('\n');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全网热榜看板</title>
<style>
:root{--bg:#f0f2f5;--card:#fff;--text:#1a1a2e;--text2:#6b7280;--border:#e5e7eb;--shadow:0 2px 8px rgba(0,0,0,.06);--radius:12px}
@media(prefers-color-scheme:dark){:root{--bg:#0a0a0f;--card:#16161d;--text:#e8e8ed;--text2:#6e6e78;--border:#2a2a35;--shadow:0 2px 8px rgba(0,0,0,.3)}}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh}
.header{text-align:center;padding:32px 16px 12px}
.header h1{font-size:24px;font-weight:800;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.5px}
.header .sub{font-size:13px;color:var(--text2);margin-top:6px}
.header .sub span{display:inline-block;background:rgba(102,126,234,.1);color:#667eea;padding:2px 10px;border-radius:20px;font-weight:600;font-size:12px;margin-left:6px}
.boards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;max-width:1400px;margin:16px auto;padding:0 16px 24px}
.board{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden;display:flex;flex-direction:column}
.board.span-2{grid-column:span 2}.board.span-3{grid-column:span 3}.board.span-4{grid-column:span 4}
.board-head{display:flex;align-items:center;gap:6px;padding:12px 14px 10px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--card);z-index:10}
.board-head .icon{font-size:18px}
.board-head .board-name{font-size:14px;font-weight:700;flex:1}
.board-head .badge{font-size:10px;font-weight:700;padding:1px 7px;border-radius:8px;letter-spacing:.5px}
.list{flex:1;padding:4px 6px 8px;overflow-y:auto;max-height:520px}
.item{display:flex;align-items:flex-start;gap:8px;padding:6px;border-radius:8px;cursor:pointer;transition:background .15s}
.item:hover{background:rgba(0,0,0,.03)}
@media(prefers-color-scheme:dark){.item:hover{background:rgba(255,255,255,.03)}}
.rank{min-width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;border-radius:6px;margin-top:2px;flex-shrink:0}
.rank-top{background:linear-gradient(135deg,#ff6b35,#ee5a24);color:#fff;box-shadow:0 2px 6px rgba(238,90,36,.25)}
.rank-accent{background:rgba(102,126,234,.1);color:#667eea}
.rank-normal{background:var(--bg);color:var(--text2);font-weight:600}
.item-body{flex:1;min-width:0}
.item-title{display:block;font-size:13px;font-weight:500;color:var(--text);text-decoration:none;line-height:1.5;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;transition:opacity .15s}
.item-title:hover{opacity:.6}
.item-foot{display:flex;align-items:center;gap:6px;margin-top:3px}
.bar-wrap{flex:1;height:3px;background:var(--border);border-radius:2px;overflow:hidden}
.bar-fill{height:100%;border-radius:2px;min-width:4px}
.hot-num{font-size:10px;color:var(--text2);white-space:nowrap;flex-shrink:0;min-width:30px;text-align:right}
.footer{text-align:center;padding:16px;font-size:11px;color:var(--text2);border-top:1px solid var(--border);max-width:1400px;margin:0 auto}
.footer a{color:#667eea;text-decoration:none}.footer a:hover{text-decoration:underline}
.back-top{position:fixed;bottom:24px;right:24px;width:36px;height:36px;border-radius:50%;background:var(--card);border:1px solid var(--border);box-shadow:0 2px 8px rgba(0,0,0,.1);display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:16px;opacity:0;transition:opacity .3s;z-index:99}
.back-top.show{opacity:1}.back-top:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.15)}
@media(max-width:1100px){.boards{grid-template-columns:repeat(2,1fr)}.board.span-2,.board.span-3,.board.span-4{grid-column:span 2}}
@media(max-width:640px){.boards{grid-template-columns:1fr;gap:10px}.board.span-2,.board.span-3,.board.span-4{grid-column:span 1}.header h1{font-size:20px}.list{max-height:none}}
</style>
</head>
<body>
<div class="header"><h1>全网热榜看板</h1><div class="sub">数据每日 18:00 自动更新 <span>${updateTime}</span></div></div>
<div class="boards">
${boardsHTML}
</div>
<div class="footer">数据来源: <a href="https://60s.viki.moe" target="_blank">60s API</a> · 部署于 <a href="https://pages.github.com" target="_blank">GitHub Pages</a></div>
<div class="back-top" id="backTop" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</div>
<script>window.addEventListener('scroll',function(){document.getElementById('backTop').classList.toggle('show',window.scrollY>400)});</script>
</body>
</html>`;
}

async function main() {
  console.log('='.repeat(50));
  console.log(`全网热榜看板 - ${formatBJ(nowBJ())}`);
  console.log('='.repeat(50));

  console.log('\n[1/4] 懂车帝热榜...');
  const dcd = await fetchJSON(`${API_BASE}/dongchedi`);
  console.log(`  → ${dcd.length} 条`);

  console.log('[2/4] 今日头条...');
  const toutiao = await fetchJSON(`${API_BASE}/toutiao`);
  console.log(`  → ${toutiao.length} 条`);

  console.log('[3/4] 抖音热榜...');
  const douyin = await fetchJSON(`${API_BASE}/douyin`);
  console.log(`  → ${douyin.length} 条`);

  console.log('[4/4] 微博热搜...');
  const weibo = await fetchJSON(`${API_BASE}/weibo`);
  console.log(`  → ${weibo.length} 条`);

  const dcdHot = normalizeDcd(dcd, 10);
  const ttAuto = filterByKeywords(toutiao, AUTO_KEYWORDS, 10).map((d, i) => ({
    rank: i + 1, title: d.title || '', url: d.link || '', hot: d.hot_value || 0, hot_num: d.hot_value || 0,
  }));
  const ttHot = normalizeToutiao(toutiao, 20);
  const dyHot = normalizeDouyin(douyin, 20);
  const wbHot = normalizeWeibo(weibo, 20);
  const wbAuto = filterByKeywords(weibo, AUTO_KW, 15).map((d, i) => ({
    rank: i + 1, title: d.title || '', url: d.link || '', hot: d.hot_value || 0, hot_num: d.hot_value || 0,
  }));
  const wbEnt = filterByKeywords(weibo, ENT_KW, 10).map((d, i) => ({
    rank: i + 1, title: d.title || '', url: d.link || '', hot: d.hot_value || 0, hot_num: d.hot_value || 0,
  }));
  const wbTech = filterByKeywords(weibo, TECH_KW, 10).map((d, i) => ({
    rank: i + 1, title: d.title || '', url: d.link || '', hot: d.hot_value || 0, hot_num: d.hot_value || 0,
  }));

  const boards = [
    { id: 'dcd-hot',  icon: '🏎', title: '懂车帝热榜', color: '#00b894', colorLight: '#55efc4', items: dcdHot },
    { id: 'tt-auto',  icon: '🔧', title: '头条汽车',  color: '#0984e3', colorLight: '#74b9ff', items: ttAuto },
    { id: 'tt-hot',   icon: '📰', title: '今日头条',  color: '#ff4757', colorLight: '#ff6b81', items: ttHot },
    { id: 'dy-hot',   icon: '🎵', title: '抖音热榜',  color: '#1a1a2e', colorLight: '#636e72', items: dyHot },
    { id: 'wb-hot',   icon: '📱', title: '微博热搜',  color: '#ff4500', colorLight: '#ff6348', items: wbHot },
    { id: 'wb-auto',  icon: '🚗', title: '微博汽车',  color: '#e17055', colorLight: '#fab1a0', items: wbAuto },
    { id: 'wb-ent',   icon: '🎬', title: '微博文娱',  color: '#e84393', colorLight: '#fd79a8', items: wbEnt },
    { id: 'wb-tech',  icon: '💻', title: '微博科技',  color: '#6c5ce7', colorLight: '#a29bfe', items: wbTech },
  ];

  const html = generateHTML(boards);
  const fs = require('fs');
  const outPath = process.argv[2] || 'index.html';
  fs.writeFileSync(outPath, html, 'utf-8');
  console.log(`\n✅ ${outPath} (${Buffer.byteLength(html)} bytes)`);

  const empty = boards.filter(b => b.items.length === 0).map(b => b.title);
  if (empty.length) { console.log(`⚠️ 无数据: ${empty.join(', ')}`); process.exit(1); }
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
