#!/usr/bin/env python3
"""从 cn/faq/faq.json 生成 5 个语言版本的 FAQ 页面到仓库根目录。

为什么是独立页面而不是首页的一个区块：首页已有 1275 行，26 条问答再乘
5 种语言就是 260 个内容块；独立页面有自己的 URL（SEO 与结构化数据都更
干净），也和现有的 privacy / terms / support 五语言分页保持同一套模式。

为什么不加序号：序号在中间插入新问题时会整体位移，而所有已发出去的
「看第 N 条」会静默失效。改用锚点（#faq-export 这类），可点击、不随
顺序变化失效、搜索引擎也用它做深链。

产物是**提交进 git 的**（与 dist-cn 不同）：mememo.life 由 GitHub Pages
直接发布仓库根目录。内地站那份由 cn/build.py 从 faq-zh.html 再加工。

用法：python3 cn/faq/build_faq.py
"""

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = json.loads((Path(__file__).parent / "faq.json").read_text(encoding="utf-8"))

# 语言 -> (输出文件名, html lang 属性, 语言切换条上的名字)
LANGS = {
    "zh":      ("faq-zh.html",      "zh-CN", "简体"),
    "zh-Hant": ("faq-zh-Hant.html", "zh-TW", "繁體"),
    "en":      ("faq.html",         "en",    "EN"),
    "ja":      ("faq-ja.html",      "ja",    "日本語"),
    "ko":      ("faq-ko.html",      "ko",    "한국어"),
}

SUFFIX = {"zh": "-zh", "zh-Hant": "-zh-Hant", "en": "", "ja": "-ja", "ko": "-ko"}

# 只有简体版挂备案号，与现有 privacy-zh / terms-zh / support-zh 一致。
# 内地站那份由 cn/build.py 把它换成网站备案号。
ICP = ('<div><a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener">'
       '我记 App 备案号：沪ICP备2026017841号-1A</a></div>')

CF = ('<!-- Cloudflare Web Analytics --><script defer '
      "src='https://static.cloudflareinsights.com/beacon.min.js' "
      'data-cf-beacon=\'{"token": "edb36f2cff1141f3bcf8ea60aab347a4"}\'></script>'
      '<!-- End Cloudflare Web Analytics -->')

STYLE = """
  .faq-jump{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px;}
  .faq-jump a{
    font-size:13px;padding:6px 12px;border:1px solid var(--line,#e8e8ed);
    border-radius:999px;color:var(--muted,#86868b);text-decoration:none;
    transition:background .15s,color .15s,border-color .15s;
  }
  .faq-jump a:hover{background:var(--ink,#1d1d1f);color:#fff;border-color:var(--ink,#1d1d1f);}
  .faq-item{border-bottom:1px solid var(--line,#e8e8ed);}
  .faq-item summary{
    list-style:none;cursor:pointer;padding:16px 32px 16px 0;position:relative;
    font-size:16px;font-weight:500;line-height:1.5;
  }
  .faq-item summary::-webkit-details-marker{display:none;}
  .faq-item summary::after{
    content:"";position:absolute;right:8px;top:50%;width:8px;height:8px;
    border-right:1.6px solid var(--muted,#86868b);border-bottom:1.6px solid var(--muted,#86868b);
    transform:translateY(-70%) rotate(45deg);transition:transform .2s;
  }
  .faq-item[open] summary::after{transform:translateY(-30%) rotate(-135deg);}
  .faq-item summary:hover{color:var(--blue,#0071e3);}
  .faq-a{padding:0 32px 20px 0;color:var(--ink-2,#424245);line-height:1.85;}
  /* 顶栏是 position:sticky、高 52px（+1px 下边框）。锚点跳转必须把这段让出来，
     否则目标标题正好钻到顶栏底下——这一点在页面顶部看不出来，只有真的点跳转才暴露。
     取值让目标最终停在顶栏下方约 30px：
       板块 56 + section 自带 28px 内边距 = 84
       问答 68 + summary 自带 16px 内边距 = 84  （两者视觉位置一致） */
  .content section[id]{scroll-margin-top:56px;}
  .faq-item{scroll-margin-top:68px;}
"""


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def build(lang: str) -> str:
    fname, html_lang, _ = LANGS[lang]
    page = DATA["page"]
    t = lambda key: page[key][lang]  # noqa: E731
    sfx = SUFFIX[lang]

    langbar = "\n".join(
        f'    <a href="{LANGS[l][0]}" class="{"active" if l == lang else ""}">{LANGS[l][2]}</a>'
        for l in LANGS
    )

    jump = "\n".join(
        f'  <a href="#sec-{s["id"]}">{esc(s["title"][lang])}</a>' for s in DATA["sections"]
    )

    body = []
    for s in DATA["sections"]:
        body.append(f'<section id="sec-{s["id"]}">')
        body.append(f'  <h2>{esc(s["title"][lang])}</h2>')
        for it in s["items"]:
            body.append(f'  <details class="faq-item" id="faq-{it["id"]}">')
            body.append(f'    <summary>{esc(it["q"][lang])}</summary>')
            body.append(f'    <div class="faq-a">{esc(it["a"][lang])}</div>')
            body.append("  </details>")
        body.append("</section>\n")

    # FAQPage 结构化数据：让百度 / Google 直接在搜索结果里展开问答
    ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "inLanguage": html_lang,
        "mainEntity": [
            {
                "@type": "Question",
                "name": it["q"][lang],
                "acceptedAnswer": {"@type": "Answer", "text": it["a"][lang]},
            }
            for s in DATA["sections"]
            for it in s["items"]
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>我记 · {esc(t('title'))}</title>
<meta name="description" content="{esc(t('sub'))}" />
<link rel="icon" href="icon.png" />
<link rel="stylesheet" href="legal-style.css" />
<style>{STYLE}</style>
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=1)}
</script>
</head>
<body>

<nav class="nav">
  <a class="nav-brand" href="index.html">
    <img src="icon.png" alt="MeMemo" />
    <span>我记</span>
    <span class="en">MeMemo</span>
  </a>
  <div class="nav-langs">
{langbar}
  </div>
</nav>

<header class="page-head">
  <div class="eyebrow">{page['eyebrow']}</div>
  <h1>{esc(t('title'))}</h1>
  <p class="sub">{esc(t('sub'))}</p>
</header>

<nav class="subnav">
  <a href="faq{sfx}.html" class="active">{esc(t('nav_faq'))}</a>
  <a href="support{sfx}.html" class="">{esc(t('nav_support'))}</a>
  <a href="privacy{sfx}.html" class="">{esc(t('nav_privacy'))}</a>
  <a href="terms{sfx}.html" class="">{esc(t('nav_terms'))}</a>
</nav>

<main class="content">

<div class="faq-jump">
{jump}
</div>

{chr(10).join(body)}
</main>

<footer class="page-foot">
  <div class="foot-links">
    <a href="index.html">{esc(t('back'))}</a>
    <a href="mailto:aaron@mememo.life">aaron@mememo.life</a>
  </div>
  <div>&copy; 2026 MeMemo&trade; &middot; 我记&trade;. All rights reserved.</div>
{ICP if lang == 'zh' else ''}
</footer>

{CF}
</body>
</html>
"""


def main() -> int:
    problems = []
    for lang, (fname, _, _) in LANGS.items():
        out = build(lang)
        (ROOT / fname).write_text(out, encoding="utf-8")
        print(f"  · {fname}  ({len(out) // 1024} KB)")

        # 自检：每个页面都要有全部问答，且不能混进别的语言
        for s in DATA["sections"]:
            for it in s["items"]:
                if f'id="faq-{it["id"]}"' not in out:
                    problems.append(f"{fname} 缺少 {it['id']}")
                if esc(it["q"][lang]) not in out:
                    problems.append(f"{fname} 缺少 {it['id']} 的问题文本")
        for other in LANGS:
            if other == lang:
                continue
            q = DATA["sections"][0]["items"][0]["q"]
            if q[other] != q[lang] and esc(q[other]) in out:
                problems.append(f"{fname} 混进了 {other} 的内容")
        if '"@type": "FAQPage"' not in out:
            problems.append(f"{fname} 缺少 FAQPage 结构化数据")

    n = sum(len(s["items"]) for s in DATA["sections"])
    if problems:
        print("\n构建自检未通过：")
        print("\n".join(f"  ✗ {p}" for p in sorted(set(problems))))
        return 1
    print(f"\n✅ 5 个语言版本 × {n} 条问答，自检通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
