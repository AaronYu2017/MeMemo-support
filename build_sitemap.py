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

    # 自检：仓库根目录下每个 *.html 都必须在 sitemap 里
    pages = {p.name for p in ROOT.glob("*.html")}
    listed = set(re.findall(r"<loc>[^<]*/([^/<]+\.html)</loc>", sitemap))
    listed |= {"index.html"}  # 首页以 / 收录
    missing = sorted(pages - listed)
    if missing:
        print(f"✗ 这些页面没进 sitemap：{missing}", file=sys.stderr)
        return 1

    print(f"✅ sitemap.xml（{sitemap.count('<url>')} 个 URL，含 hreflang）+ robots.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
