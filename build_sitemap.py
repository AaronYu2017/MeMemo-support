#!/usr/bin/env python3
"""生成 mememo.life 的 sitemap.xml 与 robots.txt（仓库根目录 = 该站的网站根目录）。

**为什么需要它**：2026-09-02 查到两个站的 /sitemap.xml 与 /robots.txt 都是 404，
而外链几乎为零。搜索引擎发现新站主要靠外链、sitemap 提交、robots 指引这三条路，
三条同时不通，所以百度至今没有收录——那不是排名问题，是入口没开。在这之前调
关键词的回报是零，因为没有页面在被评估。

**内地站不由这里管**：mememo.com.cn 的那两个文件由 cn/build.py 写进 dist-cn/，
随每次构建自动重算，页面增减不会漏。这里管的是国际站，它没有构建步骤，是
GitHub Pages 直接发布仓库根目录。

⚠️ **这个脚本要手动跑**（`python3 build_sitemap.py`），所以有忘记跑的风险。
兜底放在 cn/build.py 的自检里：它会核对本文件生成的 sitemap 是否覆盖了仓库根
目录下所有 *.html，漏了就构建失败。也就是说只要还部署内地站，就不会静默过期。

hreflang：faq / privacy / terms / support 四组各有 5 个语言 URL，不声明的话
Google 可能把它们判成互相重复的内容，或者给英语用户推中文页。

⚠️ **首页那段 2026-09-16 改了**（iOS todo 76）。此前这里写着「首页是单 URL 靠 JS
切语言，没有语言变体，所以只出现一次」——那句描述是准确的，但那个状态是缺陷：
首页是全站唯一没有语言变体的页面，而它恰好是 priority 1.0 的那一个。
人这一侧一直是好的（JS 会按 navigator.language 自动切），坏的是搜索引擎：
Google 索引的是 URL，没有日语地址就不存在一个能参与日语搜索排名的页面。
现在 /zh/ /zh-Hant/ /ja/ /ko/ 由 build_langs.py 生成，与 / 组成一个 hreflang 簇。

**/ 是英文页，兼作 x-default** —— 与 faq.html 完全同构（裸地址 = 英文 = x-default）。
x-default 的语义是「来客语言一个都没匹配上」，而那批人要的就是英文 ⇒ 受众重合，
合成一页是消掉重复而不是制造双重身份。
⚠️ 同日第一版曾把简体放在 /，那是**继承现状而非决定**。三条证据推翻它：内页裸文件名
全是 `<html lang="en">`；ASC 主语言是 en-US；GSC 三个月实测 8 次点击全部来自
韩/日/美/丹麦/越南，前十国家无中国大陆（大陆走 mememo.com.cn）⇒ 没有中文排名可失去。
"""

# 本机 python3 是 Xcode 自带的 3.9，而下面用到了 `str | None`（PEP 604，3.10+）。
# 延迟求值让注解不在运行时被解析，脚本因此在 3.9 上也能跑。
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://mememo.life"

# 语言后缀 -> hreflang 代码。zh-Hans/zh-Hant 用完整写法：单写 "zh" 时
# Google 会自己猜简繁，而这两者的目标读者是分开的。
LANGS = {
    "": "en",
    "-zh": "zh-Hans",
    "-zh-Hant": "zh-Hant",
    "-ja": "ja",
    "-ko": "ko",
}

FAMILIES = ["faq", "privacy", "terms", "support"]

# 首页语言簇。值是 URL 路径，不是文件名——/ja/ 背后是 ja/index.html，
# 由 build_langs.py 生成。改这里就要同步改那边的 LANG_HOMES。
HOME_LANGS = {
    "en": "/",
    "zh-Hans": "/zh/",
    "zh-Hant": "/zh-Hant/",
    "ja": "/ja/",
    "ko": "/ko/",
}
HOME_X_DEFAULT = "/"  # 与 en 同址，和内页 faq.html 的做法一致

# 站点验证文件不是内容页。搜索平台要求它们以固定文件名躺在网站根目录，
# 但它们不该进 sitemap，也不该被要求带 description / canonical。
# 2026-09-04 加 googleb18e0224b4b10b76.html 当天就把下面那条"每个 *.html
# 都要在 sitemap 里"的自检打成了误报——守卫本身也会因为环境变化而失准。
VERIFY_FILE = re.compile(
    r"^(google[0-9a-f]+|baidu_verify_[\w-]+|BingSiteAuth)\.(html|xml)$"
)


def _attr(html: str, tag: str, match_attr: str, match_val: str, want: str) -> str | None:
    """从 html 里找 <tag ... match_attr="match_val" ...>，返回它的 want 属性。

    ⚠️ **与属性顺序无关**，这是本函数存在的全部理由。根目录那些页是手写的
    （`<link rel="canonical" href=...>`），而 build_langs.py 生成的语言首页经过
    BeautifulSoup，属性被按字母重排成 `<link href=... rel="canonical">`。
    各写一份顺序敏感的正则 = 两套规则，而本仓已经因为规则分叉栽过一次
    （2026-09-04，站点验证文件被两处同时误判）。分叉的表现不是报错，
    是某一边静默失准。
    """
    for m in re.finditer(r"<" + tag + r"\b([^>]*)>", html, re.I):
        attrs = dict(re.findall(r'([\w:-]+)\s*=\s*"([^"]*)"', m.group(1)))
        if attrs.get(match_attr, "").lower() == match_val.lower():
            return attrs.get(want)
    return None


def page_description(html: str) -> str | None:
    return _attr(html, "meta", "name", "description", "content")


def page_canonical_of(html: str) -> str | None:
    return _attr(html, "link", "rel", "canonical", "href")


# ── 关于 index.html 那段语言脚本的事实，只允许存在一处定义 ──────────────
#
# 有三个消费方：build_langs.py（生成语言首页时把语言钉死）、cn/build.py
# （内地站钉简体 + 重写 head）、以及本文件的自检。各抄一份正则就是三套规则，
# 而本仓 2026-09-04 已经因为规则分叉栽过一次（站点验证文件被两处同时误判）。
# 分叉的表现不是报错，是某一边静默失准。
#
# 2026-09-16 实测到的第二种形态：`} catch(e){ setLang('zh'); }` 这个锚点被
# **写死在两个文件里**，当天把兜底语言从 zh 改成 en，两处同时炸。
# 炸是好事（比静默生成半截页面强），但不该炸两次。

LANG_SCRIPT_HEAD = "const setLang = (lang) => {"
# ⚠️ 不要写死兜底语言：它是会变的（2026-09-16 由 'zh' 改为 'en'）
LANG_SCRIPT_TAIL = re.compile(r"\}\s*catch\(e\)\{\s*setLang\('[^']+'\);\s*\}")


def lang_script_span(code: str) -> tuple[int, int] | None:
    """在一段 <script> 文本里定位「语言切换机制」的起止，找不到返回 None。"""
    if LANG_SCRIPT_HEAD not in code:
        return None
    m = LANG_SCRIPT_TAIL.search(code)
    if not m:
        return None
    return code.index(LANG_SCRIPT_HEAD), m.end()


def lang_maps(html: str) -> dict[str, dict[str, str]]:
    """取 index.html 脚本里的 titles / descs 两张表。

    标题与摘要**只有这一个真源**。任何地方要写某语言的 title/description，
    都从这里取，不另写一份 —— 两份措辞迟早分叉，而分叉的表现是搜索结果里
    显示的和页面上写的不一样。
    """
    out = {}
    for var in ("titles", "descs"):
        m = re.search(r"const " + var + r" = \{(.*?)\n    \};", html, re.S)
        if not m:
            sys.exit(f"✗ index.html 里找不到 const {var} —— 脚本结构变了")
        out[var] = dict(re.findall(r"'([^']+)':'((?:[^'\\]|\\.)*)'", m.group(1)))
    return out


def site_pages() -> set[str]:
    """仓库根目录里算作「内容页」的 *.html。

    cn/build.py 也 import 这个函数。两处必须对「什么算一页」有同一个定义，
    各写一份迟早会分叉，而分叉的表现是某一边静默漏检。
    """
    return {p.name for p in ROOT.glob("*.html") if not VERIFY_FILE.match(p.name)}


def page_canonical(name: str) -> str:
    """该页应有的自指 canonical。首页是 SITE + "/"，不是 index.html。"""
    return f"{SITE}/" if name == "index.html" else f"{SITE}/{name}"


def build() -> tuple[str, str]:
    urls: list[str] = []

    # 首页语言簇：/ 与四个语言首页互相声明 hreflang
    missing_homes = [
        path for path in HOME_LANGS.values()
        if path != "/" and not (ROOT / path.strip("/") / "index.html").exists()
    ]
    if missing_homes:
        sys.exit(f"✗ 缺少语言首页：{missing_homes} —— 先跑 python3 build_langs.py")

    home_alts = "".join(
        f'    <xhtml:link rel="alternate" hreflang="{code}" href="{SITE}{path}"/>\n'
        for code, path in HOME_LANGS.items()
    )
    home_alts += (
        f'    <xhtml:link rel="alternate" hreflang="x-default" '
        f'href="{SITE}{HOME_X_DEFAULT}"/>\n'
    )
    for path in HOME_LANGS.values():
        urls.append(
            f"  <url>\n"
            f"    <loc>{SITE}{path}</loc>\n"
            f"{home_alts}"
            f"    <changefreq>weekly</changefreq>\n"
            f"    <priority>1.0</priority>\n"
            f"  </url>"
        )

    for fam in FAMILIES:
        variants = {sfx: f"{fam}{sfx}.html" for sfx in LANGS}
        missing = [f for f in variants.values() if not (ROOT / f).exists()]
        if missing:
            sys.exit(f"✗ 缺少页面：{missing} —— 页面集变了，请更新 FAMILIES/LANGS")
        alts = "".join(
            f'    <xhtml:link rel="alternate" hreflang="{code}" '
            f'href="{SITE}/{variants[sfx]}"/>\n'
            for sfx, code in LANGS.items()
        )
        # x-default 指英文版：没有匹配语言时给谁看
        alts += (
            f'    <xhtml:link rel="alternate" hreflang="x-default" '
            f'href="{SITE}/{variants[""]}"/>\n'
        )
        for sfx in LANGS:
            urls.append(
                f"  <url>\n"
                f"    <loc>{SITE}/{variants[sfx]}</loc>\n"
                f"{alts}"
                f"    <changefreq>monthly</changefreq>\n"
                f"    <priority>0.8</priority>\n"
                f"  </url>"
            )

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )

    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
    )
    return sitemap, robots


def main() -> int:
    sitemap, robots = build()
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")

    problems: list[str] = []

    # 自检 1：仓库根目录下每个内容页都必须在 sitemap 里
    pages = site_pages()
    listed = set(re.findall(r"<loc>[^<]*/([^/<]+\.html)</loc>", sitemap))
    listed |= {"index.html"}  # 首页以 / 收录
    for name in sorted(pages - listed):
        problems.append(f"{name} 没进 sitemap")

    # 自检 2 与 3：每个内容页都要有 description，且 canonical 自指到正确地址。
    #
    # 为什么值得一条自检：2026-09-02 那笔 SEO 只改了 index.html 和 5 个
    # faq*.html，privacy / terms / support 共 15 页一个 description 都没加。
    # 没人疏忽，是**没有任何东西会报错**——最后是 Bing 的 Site Scan 替我们
    # 发现的，隔了两天。canonical 同理：/ 与 /index.html 返回同一份内容，
    # 内链指 index.html 而 sitemap 指 /，不自指就是让搜索引擎自己猜。
    for name in sorted(pages):
        html = (ROOT / name).read_text(encoding="utf-8")
        desc = page_description(html)
        if not desc or not desc.strip():
            problems.append(f"{name} 缺 meta description")
        c = page_canonical_of(html)
        if not c:
            problems.append(f"{name} 缺 canonical")
        elif c != page_canonical(name):
            problems.append(
                f"{name} canonical 指错了：{c}（应为 {page_canonical(name)}）"
            )

    # 自检 4：语言首页也要有 description 与自指 canonical。
    # 根目录那套 glob 是非递归的（刻意如此：cn/build.py 共用它，
    # 递归会把语言首页吃进内地站，而内地站已向管局承诺简体单语），
    # 所以子目录必须单列一条，否则这四页没有任何守卫。
    for code, path in HOME_LANGS.items():
        if path == "/":
            continue
        f = ROOT / path.strip("/") / "index.html"
        html = f.read_text(encoding="utf-8")
        desc = page_description(html)
        if not desc or not desc.strip():
            problems.append(f"{path} 缺 meta description")
        c = page_canonical_of(html)
        if not c:
            problems.append(f"{path} 缺 canonical")
        elif c != f"{SITE}{path}":
            problems.append(f"{path} canonical 指错了：{c}（应为 {SITE}{path}）")
        if "navigator.language" in html:
            problems.append(f"{path} 还留着语言自动检测 —— 其余语言已剥掉，会白屏")

    if problems:
        print("✗ 自检未通过：", file=sys.stderr)
        for p in problems:
            print(f"    {p}", file=sys.stderr)
        return 1

    print(f"✅ sitemap.xml（{sitemap.count('<url>')} 个 URL，含 hreflang）+ robots.txt")
    print(f"   {len(pages)} 个内容页，description / canonical 齐全")
    return 0


if __name__ == "__main__":
    sys.exit(main())
