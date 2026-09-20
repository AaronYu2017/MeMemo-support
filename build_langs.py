#!/usr/bin/env python3
"""从 index.html 生成各语言首页 /<lang>/index.html（只给 mememo.life）。

**为什么需要它**（2026-09-16，iOS todo 76）：首页是全站唯一没有语言变体的页面，
而它恰好是 priority 1.0 的那一个。内页 faq / privacy / terms / support 各有
5 个语言 URL、sitemap 里 120 条 hreflang；首页只有一个 URL。

后果不是"日本用户看不懂"——首页的 JS 早就会按 navigator.language 自动切，
**人这一侧一直是好的**。坏的是搜索引擎：Google 索引的是 URL，没有日语地址
就不存在一个能参与日语搜索排名的页面。外加五种语言的正文都在 HTML 里靠
`display:none` 切换，而 Google 明确降权隐藏文本。

**做法照抄 cn/build.py**（同仓已有的剥离管线，不另写一套）：
剥掉其余语言的 data-i18n 块 → 把语言写死 → 换头部字段。
三处 cn 不需要而这里需要的：

1. **相对路径要改成根相对。** 页面从 / 搬到 /ja/ 之后，`icon.png`
   会解析成 `/ja/icon.png`。实测 index.html 有 73 处相对引用
   （27 src + 25 data-src + 21 href），一处不改就是一片 404。
   ⚠️ 不用 `<base href="/">`：那会让 `#features` 这类页内锚点变成跳转到 /。
2. **语言切换器要变成真链接**，不是 JS 原地切——本页只有一种语言的内容，
   原地切等于切到空白。页脚那五个 `<a>` 顺便变成可被爬取的语言互链。
3. **不剥语言切换器**（cn 站是单语站所以整个拿掉，这里要留着让人能换）。

⛔ **只发 mememo.life。** com.cn 已向管局承诺简体单语，不加语言首页。
本脚本写的是子目录，而 `build_sitemap.site_pages()` 是 `ROOT.glob("*.html")`
**非递归** ⇒ cn/build.py 不会把这些页吃进去。改那个 glob 之前先想起这一行。

用法：python3 build_langs.py   （改完 index.html 就要重跑，然后跑 build_sitemap.py）
"""

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

# 关于 index.html 那段语言脚本的事实只有一个真源，见 build_sitemap.py 里的长注释
from build_sitemap import lang_maps, lang_script_span

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "index.html"

# 语言首页地址。
#
# 🔄 **2026-09-16 当天改过一次，第一版把简体放在 / 是错的。**
# 第一版的理由是「/ 本身首屏就是简体，另建 /zh/ 会成为近重复、还要分走已有排名」。
# 那不是一个决定，是**继承** —— 保住了现状却没问现状对不对。三条证据都指向英文：
#   · 内页 faq/privacy/terms/support 的**裸文件名全是 `<html lang="en">`**，
#     且它们 sitemap 的 x-default 指向英文那一份 ⇒ 全站只有首页是例外
#   · ASC 的 App 主语言是 **en-US**（面向 175 个国家，只适配了 5 种语言）
#   · GSC 三个月实测：全站 8 次点击 / 约 207 次曝光，
#     点击来自韩国 3 / 日本 2 / 美国 1 / 丹麦 1 / 越南 1，**简体读者零点击**；
#     前十国家里**没有中国大陆**（Google 在那边打不开，大陆走 mememo.com.cn）
#     ⇒ 「改 / 会打散已有中文排名」这个顾虑**不成立**，没有排名可失去
#
# 所以 / = 英文 + x-default，与 faq.html 完全同构：
# x-default 的语义是「来客语言一个都没匹配上」，而那批人要的就是英文 ⇒
# 两者受众重合，合成同一页是**消掉一个重复**，不是制造一个双重身份。
LANG_HOMES = {
    "en": "/",
    "zh": "/zh/",
    "zh-Hant": "/zh-Hant/",
    "ja": "/ja/",
    "ko": "/ko/",
}
# 要生成的（/ 已经是英文页，不生成）
GENERATE = ["zh", "zh-Hant", "ja", "ko"]

HTML_LANG = {"zh": "zh-CN", "zh-Hant": "zh-TW", "ja": "ja", "ko": "ko", "en": "en"}



def rewrite_relative_urls(soup: BeautifulSoup) -> int:
    """把相对引用改成根相对。页内锚点 / 绝对地址 / mailto: 一律不动。"""
    n = 0
    for tag in soup.find_all(True):
        for attr in ("src", "data-src", "href", "poster"):
            v = tag.get(attr)
            if not isinstance(v, str) or not v:
                continue
            if v.startswith(("http://", "https://", "//", "#", "mailto:", "tel:", "data:", "/")):
                continue
            tag[attr] = "/" + v
            n += 1
    return n


def strip_other_languages(soup: BeautifulSoup, keep: str) -> int:
    """删掉除 keep 外所有语言的内容块。

    保留 data-i18n 属性本身：CSS 靠 [data-i18n]{display:none} +
    html[data-lang=X] [data-i18n=X]{display:revert} 这一对规则显示内容，
    把属性摘掉反而会让全站文字消失。（同 cn/build.py）
    """
    n = 0
    for el in list(soup.select("[data-i18n]")):
        if el.decomposed or el.get("data-i18n") == keep:
            continue
        el.decompose()
        n += 1
    return n


def pin_language(soup: BeautifulSoup, lang: str) -> None:
    """把首页脚本里的"原地切语言"换成"写死本语言 + 跳转到别的地址"。

    这一步是必需的，不是清理：原脚本首次访问会读 navigator.language，
    日语浏览器打开 /en/ 会调 setLang('ja')，而日语内容已被剥掉 ⇒ 整页空白。
    （cn/build.py 的 pin_language_to_zh 记的是同一个坑。）
    """
    homes = ", ".join(f"'{k}':'{v}'" for k, v in LANG_HOMES.items())
    for tag in soup.find_all("script"):
        code = tag.string
        if not code:
            continue
        span = lang_script_span(code)
        if not span:
            continue
        start, end = span
        repl = (
            f"/* 语言首页：本页只含 {lang} 的内容，其余语言已在构建时剥掉。\n"
            "     所以切换必须是**跳转**，不能原地切——原地切等于切到空白。\n"
            "     生成器：build_langs.py。 */\n"
            f"  document.documentElement.setAttribute('data-lang', '{lang}');\n"
            f"  document.documentElement.setAttribute('lang', '{HTML_LANG[lang]}');\n"
            f"  loadShowcaseForLang('{lang}');\n"
            # 🔴 **这里故意不写 localStorage。** 到达 /ko/ 是「App 按自己的语言把人
            #    送过来」，不是「用户选了韩语」。此前每个语言首页都会写，于是访问过
            #    一次 /ko/ 之后，英语 App 送到 / 的用户会读到 ko 而看到韩语 ——
            #    链条全自动，不需要任何手动切换（第 103 条，2026-09-20 实测复现）。
            #    在本页点语言按钮是**跳转**到另一个语言首页，那一页同样不写；
            #    真正的显式选择只发生在 / 的原地切换上，由 index.html 的 persist 管。
            f"  const LANG_HOMES = {{{homes}}};\n"
            "  document.querySelectorAll('[data-lang-btn]').forEach(b => {\n"
            "    b.addEventListener('click', () => {\n"
            "      const t = LANG_HOMES[b.getAttribute('data-lang-btn')];\n"
            "      if (t) location.href = t;\n"
            "    });\n"
            "  });"
        )
        tag.string = code[:start] + repl + code[end:]
        return
    sys.exit("✗ 找不到语言切换脚本 —— index.html 结构变了，先更新本脚本")


def wire_switchers(soup: BeautifulSoup, lang: str) -> None:
    """页脚语言列换成真实链接（可被爬取的语言互链）；顶栏按钮标出当前语言。"""
    for a in soup.select("[data-lang-link]"):
        target = LANG_HOMES.get(a.get("data-lang-link"))
        if target:
            a["href"] = target
    for b in soup.select("[data-lang-btn]"):
        cls = [c for c in (b.get("class") or []) if c != "active"]
        if b.get("data-lang-btn") == lang:
            cls.append("active")
        b["class"] = cls


def set_head(soup: BeautifulSoup, lang: str, titles: dict, descs: dict) -> None:
    soup.html["lang"] = HTML_LANG[lang]
    soup.html["data-lang"] = lang
    soup.title.string = titles[lang]
    soup.select_one('meta[name="description"]')["content"] = descs[lang]
    soup.select_one('link[rel="canonical"]')["href"] = "https://mememo.life" + LANG_HOMES[lang]


def main() -> int:
    html = SRC.read_text(encoding="utf-8")
    maps = lang_maps(html)
    titles, descs = maps["titles"], maps["descs"]
    missing = [l for l in LANG_HOMES if l not in titles or l not in descs]
    if missing:
        sys.exit(f"✗ index.html 的 titles/descs 缺语言：{missing}")

    for lang in GENERATE:
        soup = BeautifulSoup(html, "html.parser")
        removed = strip_other_languages(soup, lang)
        urls = rewrite_relative_urls(soup)
        pin_language(soup, lang)
        wire_switchers(soup, lang)
        set_head(soup, lang, titles, descs)

        out = ROOT / lang / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(str(soup), encoding="utf-8")
        size = out.stat().st_size / 1024
        print(f"  ✅ {LANG_HOMES[lang]:12} 剥掉 {removed:3} 个他语块 · 改写 {urls:3} 个相对引用 · {size:5.0f} KB")

    print(f"\n生成 {len(GENERATE)} 个语言首页。/ 是英文页，兼作 x-default（首屏英文 + JS 自动切）。")
    print("⚠️ 接着跑 python3 build_sitemap.py 更新 hreflang。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
