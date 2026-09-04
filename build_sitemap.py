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
Google 可能把它们判成互相重复的内容，或者给英语用户推中文页。首页是单 URL
靠 JS 切语言，没有语言变体，所以只出现一次。
"""

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

# 站点验证文件不是内容页。搜索平台要求它们以固定文件名躺在网站根目录，
# 但它们不该进 sitemap，也不该被要求带 description / canonical。
# 2026-09-04 加 googleb18e0224b4b10b76.html 当天就把下面那条"每个 *.html
# 都要在 sitemap 里"的自检打成了误报——守卫本身也会因为环境变化而失准。
VERIFY_FILE = re.compile(
    r"^(google[0-9a-f]+|baidu_verify_[\w-]+|BingSiteAuth)\.(html|xml)$"
)


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

    # 首页：单 URL，JS 切语言，没有语言变体
    urls.append(
        f"  <url>\n"
        f"    <loc>{SITE}/</loc>\n"
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
        m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
        if not m or not m.group(1).strip():
            problems.append(f"{name} 缺 meta description")
        c = re.search(r'<link\s+rel="canonical"\s+href="([^"]*)"', html)
        if not c:
            problems.append(f"{name} 缺 canonical")
        elif c.group(1) != page_canonical(name):
            problems.append(
                f"{name} canonical 指错了：{c.group(1)}（应为 {page_canonical(name)}）"
            )

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
