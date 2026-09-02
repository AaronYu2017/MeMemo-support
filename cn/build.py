#!/usr/bin/env python3
"""从 mememo.life 的五语言真源，生成 mememo.com.cn 的简体单语站。

设计原则（单一真源、单向注入）
------------------------------------------------
* 两站共有的内容 —— 产品介绍、截图、法律条款 —— 只存在于仓库根目录的
  index.html / privacy-zh.html / terms-zh.html / support-zh.html。
  改一处，push 更新国际站，跑一次本脚本更新内地站。
* 内地专属的东西（备案号、将来的安卓入口 / FAQ）放在 cn/extras/，
  只在构建时注入，绝不写回真源，国际站因此永远保持干净。
* 产物写到 dist-cn/，不进 git（仓库根目录就是 GitHub Pages 的网站根目录，
  提交产物会把内地站副本发布到未备案的 mememo.life 上）。产物随时可重新生成。

用法：python3 cn/build.py
"""

import hashlib
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist-cn"

KEEP_LANG = "zh"

# 内地站页脚必须展示【网站】备案号并链到工信部（法定要求）。
# 刻意不展示任何 App 备案号：App 备案号的公示义务在 App 内与应用商店展示页，
# 网站没有代为公示的义务，且 iOS App 备案属个人主体、与本站公司主体不一致。
ICP_WEBSITE = "沪ICP备2026035044号-2"
ICP_URL = "https://beian.miit.gov.cn/"

# 公安联网备案（2026-09-02 过审，普陀网安）。与 ICP 是两套独立备案：ICP 归
# 工信部管、查工信部；这条归公安管、查全国互联网安全管理服务平台。
# 平台原文要求「备案编号图标在前，备案编号在右」，所以图标不是装饰，是格式
# 的一部分；并要求 30 个工作日内挂上。
# 号码、链接、rel 全部照抄平台「点击复制备案编号HTML代码」给的片段：code 参数
# 取的是**不带**「沪公网安备」前缀与「号」后缀的纯数字，rel 是 noreferrer
# （本站别处用 noopener）。不按本仓库的习惯改写，避免查询链接对不上。
GONGAN_NUMBER = "沪公网安备31010702010665号"
GONGAN_URL = "https://beian.mps.gov.cn/#/query/webSearch?code=31010702010665"
GONGAN_ICON = "beian-gongan.png"

# 内地站页脚的版权行写【单位名称】，不写商标名。
# 依据工信部备案后处理要求：部分省份管局（文档点名江苏）要求网站底部的
# 版权所有与单位名称保持一致。上海未被点名，但备案主体是公司、版权却署
# 商标名本身就不自洽，且这类口径会变——先做到位比收到整改通知再改便宜。
# 文档还说明版权所有一般显示在 ICP 备案号上方，故公司名归版权行、
# 备案号那格只留号，不重复出现。
# 刻意只注入内地站：mememo.life 面向海外，且其隐私政策以 Aaron Yu 个人作为
# GDPR 数据控制者，挂中文公司全称会与那句话打架。
OPERATOR = "上海于马科技有限公司"
COPYRIGHT = f"© 2026 {OPERATOR} 版权所有"

# 简体单语站的干净 URL：privacy-zh.html -> privacy.html
PAGE_RENAME = {
    "faq-zh.html": "faq.html",
    "privacy-zh.html": "privacy.html",
    "terms-zh.html": "terms.html",
    "support-zh.html": "support.html",
}

ICON_VERSION = "2"

SHOWCASE = ["day", "me", "month", "week", "year"]

# 内地访问不到的站点。链接留在内地站上不只是"点不开"：浏览器会一直等到超时，
# 用户看到的是页面卡住而不是一个坏链接。国际站保留它们，只在本构建里摘掉。
BLOCKED_IN_CN = (
    "x.com",
    "twitter.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "t.me",
)

log: list[str] = []


def note(msg: str) -> None:
    log.append(msg)


def strip_other_languages(soup: BeautifulSoup) -> int:
    """删掉除简体外所有语言的内容块。

    保留 data-i18n="zh" 属性本身：CSS 靠 [data-i18n]{display:none} +
    html[data-lang="zh"] [data-i18n="zh"]{display:revert} 这一对规则显示内容，
    把属性摘掉反而会让全站文字消失。
    """
    removed = 0
    for el in list(soup.select("[data-i18n]")):
        if el.decomposed or el.get("data-i18n") == KEEP_LANG:
            continue
        el.decompose()
        removed += 1
    return removed


def strip_language_switchers(soup: BeautifulSoup) -> None:
    """移除顶栏语言按钮组，和页脚整列「语言」。"""
    for div in list(soup.select("div.lang")):
        if div.select("[data-lang-btn]"):
            div.decompose()
            note("移除顶栏语言按钮组")

    for a in list(soup.select("[data-lang-link]")):
        if a.decomposed:
            continue
        col = a.find_parent("div", class_="foot-col")
        if col is not None:
            col.decompose()
            note("移除页脚「语言」整列")
        else:
            a.decompose()

    # 法律页顶部的语言导航
    for nav in list(soup.select("div.nav-langs")):
        nav.decompose()
        note("移除法律页语言导航")


def strip_cloudflare(soup: BeautifulSoup) -> None:
    """移除 Cloudflare 统计脚本：境外脚本，内地访问会拖慢首屏。"""
    for tag in list(soup.find_all("script")):
        src = tag.get("src") or ""
        if "cloudflareinsights" in src or "cloudflareinsights" in (tag.string or ""):
            tag.decompose()
            note("移除 Cloudflare 统计脚本")


def pin_language_to_zh(soup: BeautifulSoup) -> None:
    """把首页脚本里的语言切换机制换成写死简体。

    这一步是必需的，不是清理。原脚本首次访问时会读 navigator.language，
    浏览器是英文就调 setLang('en')；而英文内容已被剥掉，页面会整片空白。
    """
    for tag in soup.find_all("script"):
        code = tag.string
        if not code or "const setLang = (lang) =>" not in code:
            continue
        start = code.index("const setLang = (lang) => {")
        end_anchor = "} catch(e){ setLang('zh'); }"
        end = code.index(end_anchor) + len(end_anchor)
        replacement = (
            "/* 内地站为简体单语：语言切换机制已在构建时移除。\n"
            "     原逻辑会按浏览器语言自动切换，在单语站上会导致白屏。 */\n"
            "  document.documentElement.setAttribute('data-lang', 'zh');\n"
            "  document.documentElement.setAttribute('lang', 'zh-CN');\n"
            "  loadShowcaseForLang('zh');"
        )
        tag.string = code[:start] + replacement + code[end:]
        note("语言切换机制替换为固定简体（防白屏）")
        return
    note("⚠️ 未找到语言切换脚本，跳过")


def strip_blocked_links(soup: BeautifulSoup) -> None:
    """摘掉指向内地访问不到的站点的链接（目前只有页脚的 X）。

    刻意做在构建步骤里、不改真源：mememo.life 面向海外，X 在那边是有效入口。
    这正是"内地专属差异只在构建时注入、绝不写回真源"的用法。
    """
    for a in list(soup.find_all("a", href=True)):
        host = urlparse(a["href"]).netloc.lower()
        if any(host == d or host.endswith("." + d) for d in BLOCKED_IN_CN):
            label = a.get("aria-label") or host
            a.decompose()
            note(f"移除内地不可达链接：{label}")


def simplify_lang_css(soup: BeautifulSoup) -> None:
    """把五语言的显隐规则收敛成简体一条。

    只动这一条：它是唯一一条"少了会出错"的语言规则。其余散落的
    html[data-lang="ja"] / [data-lang="ko"] 字体规则是死代码但完全无害
    （data-lang 已被写死为 zh，永不命中），拿正则去切 CSS 的风险
    大于省下的那一点体积，刻意不动。
    """
    old = (
        'html[data-lang="zh"] [data-i18n="zh"],\n'
        '  html[data-lang="zh-Hant"] [data-i18n="zh-Hant"],\n'
        '  html[data-lang="ja"] [data-i18n="ja"],\n'
        '  html[data-lang="ko"] [data-i18n="ko"],\n'
        '  html[data-lang="en"] [data-i18n="en"]{display:revert;}'
    )
    new = 'html[data-lang="zh"] [data-i18n="zh"]{display:revert;}'
    for tag in soup.find_all("style"):
        css = tag.string
        if css and old in css:
            tag.string = css.replace(old, new)
            note("语言显隐 CSS 收敛为简体一条")
            return
    note("⚠️ 未找到语言显隐 CSS 规则")


def set_icp_footer(soup: BeautifulSoup) -> None:
    """页脚挂【网站】备案号并链到工信部。

    上海不是广东，按工信部备案后处理要求应挂网站备案号（带 -N 后缀），
    而不是主体备案号。target="_blank" 是文档给的通用代码写法。
    """
    replaced = False
    for a in soup.find_all("a", href=re.compile("beian.miit.gov.cn")):
        a.attrs = {"href": ICP_URL, "target": "_blank", "rel": "noopener"}
        a.string = ICP_WEBSITE
        replaced = True
    if replaced:
        note(f"页脚备案号 -> {ICP_WEBSITE}")
    else:
        note("⚠️ 页脚未找到备案号链接")


def set_gongan_footer(soup: BeautifulSoup) -> None:
    """在 ICP 备案号**前面**挂公安联网备案号（警徽在前，号在右）。

    必须在 set_icp_footer 之后跑：靠 ICP 那个 <a> 定位插入点。这样做而不是
    按类名或位置找，是因为两种页脚的结构不同 —— 首页是 .foot-bottom 下几个
    并列元素，子页是 <footer> 下若干 <div>，各含一个 <a>。跟着 ICP 走在两种
    结构里都落在同一个视觉位置，不用分支，也不会随版式微调漂走。

    公安号在前、ICP 在后，与公安部平台自己的页脚一致（Aaron 2026-09-02 指定，
    对照 beian.mps.gov.cn 底部的「京公网安备… 京ICP备…」）。

    两个号会被包进同一个 <span>，这不是装饰：首页页脚是
    `display:flex; justify-content:space-between`，两个号若各自成为一个 flex
    item，会被推到行的两端而不是并排。包起来之后它们是一个 item，视觉上成组，
    与参照页脚一致。子页那种 <div><a></a></div> 结构里多一层 inline span
    没有任何影响，所以两边共用一套代码。

    图标用 <img> 而不是背景图：页脚没有可挂样式的钩子，而平台要求图标必须
    可见；行内 style 保证它不依赖 legal-style.css 里是否恰好有合适的规则。

    ⚠️ **`display:inline-block` 是这里唯一起作用的一条，不能删。** 本站 CSS
    有一条全局 `img{display:block}`，块级图片独占一行 —— 首版部署后线上就是
    警徽在上、编号在下（Aaron 2026-09-02 发现），恰好违反平台「图标在前、
    编号在右」的格式要求。对块级盒子而言 `vertical-align` 无效、
    `white-space:nowrap` 也拦不住换行，**只有把它改回行内级才有用**；这一条
    是量出来的（浏览器里读 computed style 找到那条全局规则），不是推出来的。
    行内 style 的优先级高于样式表选择器，所以写在这里就够，不必改 CSS。

    另两条是配套：
    * `vertical-align:middle` + `top:-2px` 的垂直对齐。middle 把图标中心对到
      「基线 + 半个 x-height」，而汉字的墨迹几乎占满 em 框、视觉重心比拉丁
      小写字母高，所以纯 middle 会显得偏低 —— 线上量到图标中心比文字行盒
      中心低 1.05px（Aaron 肉眼先发现的，量完确认属实）。上移 2px 同时补掉
      这 1px 和汉字墨迹偏高的那部分。要再微调改这个数即可。
    * 链接上的 `white-space:nowrap` 防的是另一回事 —— 首页页脚是
      `display:flex; flex-wrap:wrap`，被挤窄时中文可在任意字之间断行，
      nowrap 让整条一起换行而不是把警徽和号码劈开。两个号之间留了一个空格
      作为断行机会，所以窄屏上是「两个号分两行」而不是横向溢出。
    """
    anchor = soup.find("a", href=ICP_URL)
    if anchor is None:
        note("⚠️ 未找到 ICP 链接，公安备案号无处可插")
        return
    if soup.find("a", href=GONGAN_URL):  # 幂等：重复跑不会插两遍
        return

    link = soup.new_tag(
        "a",
        href=GONGAN_URL,
        target="_blank",
        rel="noreferrer",
        style="white-space:nowrap;margin-right:8px;",
    )
    icon = soup.new_tag(
        "img",
        src=GONGAN_ICON,
        alt="",
        width="16",
        height="18",
        style=(
            "display:inline-block;vertical-align:middle;"
            "position:relative;top:-1px;margin-right:4px;"
        ),
    )
    link.append(icon)
    link.append(GONGAN_NUMBER)

    # 把两个号包成一组：公安在前、ICP 在后，中间一个空格既是间距也是断行机会。
    group = anchor.wrap(soup.new_tag("span"))
    group.insert(0, " ")
    group.insert(0, link)
    note(f"页脚公安备案号 -> {GONGAN_NUMBER}（置于 ICP 之前）")


def set_copyright(soup: BeautifulSoup) -> None:
    """版权行改写成单位名称（理由见 COPYRIGHT 常量上方注释）。"""
    hit = False
    for text in list(soup.find_all(string=re.compile("All rights reserved"))):
        text.replace_with(COPYRIGHT)
        hit = True
    if hit:
        note(f"版权行 -> {COPYRIGHT}")
    else:
        note("⚠️ 未找到版权行")


def rewrite_links(soup: BeautifulSoup) -> None:
    """*-zh.html -> 干净 URL（单语站不需要语言后缀）。"""
    for a in soup.find_all("a", href=True):
        target = PAGE_RENAME.get(a["href"])
        if target:
            a["href"] = target


def build_page(src: Path, dest_name: str) -> None:
    soup = BeautifulSoup(src.read_text(encoding="utf-8"), "html.parser")

    removed = strip_other_languages(soup)
    if removed:
        note(f"{src.name}: 移除 {removed} 个非简体内容块")
    strip_language_switchers(soup)
    strip_cloudflare(soup)
    strip_blocked_links(soup)
    if src.name == "index.html":
        simplify_lang_css(soup)
        pin_language_to_zh(soup)
    set_icons(soup)
    set_icp_footer(soup)
    set_gongan_footer(soup)
    set_copyright(soup)
    rewrite_links(soup)
    bust_asset_cache(soup)

    html = soup.decode(formatter="html5")
    (DIST / dest_name).write_text(html, encoding="utf-8")
    note(f"写出 {dest_name}（{len(html) // 1024} KB）")


def make_favicon() -> None:
    """生成浏览器会主动去要、但源站没有的图标文件。

    /favicon.ico —— 页面里虽然已声明 <link rel="icon" href="icon.png">，
    但搜索引擎爬虫（百度）和微信 / 小红书的链接预览会直接去要这个默认路径。
    用多尺寸真 ico 容器而不是把 PNG 改扩展名：.ico 是容器格式，改名部分环境不认。

    /apple-touch-icon*.png —— nginx 日志显示 macOS Safari 的图标抓取器每次都
    请求这两个路径并拿到 404。iOS「添加到主屏幕」用的也是它。180×180 是 Apple
    的规格；两个文件名都给，老版本 Safari 只认 -precomposed 那个。
    """
    src = Image.open(ROOT / "icon.png")
    src.convert("RGBA").save(
        DIST / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)]
    )
    touch = src.convert("RGB").resize((180, 180), Image.LANCZOS)
    touch.save(DIST / "apple-touch-icon.png")
    touch.save(DIST / "apple-touch-icon-precomposed.png")
    note("生成 favicon.ico + apple-touch-icon（180×180，含 -precomposed）")


def set_icons(soup: BeautifulSoup) -> None:
    """声明 apple-touch-icon，并给图标 URL 挂版本号。

    版本号是为了绕开 Safari 的图标库：它按 URL 记住"这个站的图标长什么样"，
    而且不随设置里的「移除网站数据」一起清掉。换一个它没见过的 URL，
    才会真正重新抓取。
    """
    icon_links = soup.select('link[rel~="icon"]')
    if not icon_links:
        return
    for link in icon_links:
        href = link.get("href", "")
        if href and "?" not in href:
            link["href"] = f"{href}?v={ICON_VERSION}"
    if not soup.select('link[rel="apple-touch-icon"]'):
        tag = soup.new_tag("link")
        tag.attrs = {
            "rel": "apple-touch-icon",
            "href": f"apple-touch-icon.png?v={ICON_VERSION}",
        }
        icon_links[0].insert_after(tag)


SITE_CN = "https://www.mememo.com.cn"


def write_sitemap() -> None:
    """内地站的 sitemap.xml 与 robots.txt。

    2026-09-02 查到两个站的这两个文件都是 404，而外链几乎为零。搜索引擎发现
    新站主要靠外链、sitemap 提交、robots 指引三条路，三条同时不通，所以百度
    至今未收录——那不是排名问题，是入口没开，在这之前调关键词的回报是零。

    随构建自动重算，页面增减不会漏；国际站那份没有构建步骤，由仓库根目录的
    build_sitemap.py 手动生成，兜底见 verify()。

    内地站是简体单语，不需要 hreflang。
    """
    pages = ["index.html", *PAGE_RENAME.values()]
    urls = "\n".join(
        f"  <url>\n"
        f"    <loc>{SITE_CN}/{'' if p == 'index.html' else p}</loc>\n"
        f"    <changefreq>{'weekly' if p == 'index.html' else 'monthly'}</changefreq>\n"
        f"    <priority>{'1.0' if p == 'index.html' else '0.8'}</priority>\n"
        f"  </url>"
        for p in pages
    )
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n",
        encoding="utf-8",
    )
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_CN}/sitemap.xml\n",
        encoding="utf-8",
    )
    note(f"生成 sitemap.xml（{len(pages)} 个 URL）+ robots.txt")


def asset_version(name: str) -> str:
    """按文件内容算的短哈希，用作缓存击穿参数。

    nginx 给 css/图片发 `expires 30d`、给 HTML 发 `no-cache`，这个组合本身
    是对的——但前提是资源 URL 会随内容改变。否则就是 2026-09-02 那次的形态：
    HTML 更新了、CSS 还是旧的，页面拿新结构配旧样式，看起来就是「改了但没
    生效」。而且**只有内地站会这样**：GitHub Pages 给 mememo.life 发的是
    max-age=600，十分钟自愈，于是同一次改动在两个站上表现不同，很容易被
    误判成代码问题。这次就是 Aaron 报「com.cn 怎么没居中」，而我第一次验证
    时手动加了 cache-busting 参数，验的是文件不是用户看到的东西，没发现。

    刻意不复用上面 ICON_VERSION 那种手写常量：手写要求人记得改，而忘了改
    不会报错、不会构建失败，只会让线上悄悄停在旧版本——和 feature flag 忘了
    翻回去是同一类问题。按内容算就没有「记得」这一步。
    """
    return hashlib.sha1((ROOT / name).read_bytes()).hexdigest()[:8]


def bust_asset_cache(soup: BeautifulSoup) -> None:
    """给 30 天长缓存的静态资源挂上内容版本号。"""
    for link in soup.find_all("link", href=True):
        if link["href"] == "legal-style.css":
            link["href"] = f"legal-style.css?v={asset_version('legal-style.css')}"
    for img in soup.find_all("img", src=True):
        if img["src"] == GONGAN_ICON:
            img["src"] = f"{GONGAN_ICON}?v={asset_version('cn/extras/' + GONGAN_ICON)}"


def copy_assets() -> None:
    shutil.copy2(ROOT / "icon.png", DIST / "icon.png")
    shutil.copy2(ROOT / "legal-style.css", DIST / "legal-style.css")
    shutil.copy2(ROOT / "cn" / "extras" / GONGAN_ICON, DIST / GONGAN_ICON)
    make_favicon()

    opt = DIST / "screens" / "opt"
    opt.mkdir(parents=True, exist_ok=True)
    for name in SHOWCASE:
        img = ROOT / "screens" / "opt" / f"{name}-zh.webp"
        shutil.copy2(img, opt / img.name)
    note(f"复制资源：icon + legal-style.css + 警徽 + {len(SHOWCASE)} 张简体截图")


def verify() -> list[str]:
    """构建后自检：这些错误静态读代码看不出来，必须查产物。"""
    problems = []
    index = (DIST / "index.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(index, "html.parser")

    # 查 DOM 而不是查字符串：data-i18n="ja" 这类字符串同样出现在 CSS 选择器里，
    # 按字符串查会把死掉的样式规则误报成残留内容。
    leftovers = {
        el["data-i18n"]
        for el in soup.select("[data-i18n]")
        if el.get("data-i18n") != KEEP_LANG
    }
    for lang in sorted(leftovers):
        problems.append(f"仍残留 {lang} 内容块")

    if not soup.select('[data-i18n="zh"]'):
        problems.append("简体内容块被全部删光了")
    if soup.select("[data-lang-btn], [data-lang-link], div.nav-langs"):
        problems.append("仍残留语言切换入口")
    if "cloudflareinsights" in index:
        problems.append("仍残留 Cloudflare 脚本")
    if "navigator.language" in index:
        problems.append("语言自动切换未移除（会白屏）")
    for page in ["index.html", *PAGE_RENAME.values()]:
        html = (DIST / page).read_text(encoding="utf-8")
        if ICP_WEBSITE not in html:
            problems.append(f"{page} 缺少网站备案号")
        # 公安要求 30 个工作日内挂上，漏一页就是漏一页——与 ICP 同样逐页查。
        if GONGAN_NUMBER not in html:
            problems.append(f"{page} 缺少公安备案号")
        if GONGAN_URL not in html:
            problems.append(f"{page} 公安备案号未链到查询页")
        # 没有版本参数的样式表引用会被 nginx 的 expires 30d 冻住：HTML 是
        # no-cache 会立刻更新，CSS 不会，于是线上是新结构配旧样式。
        if 'href="legal-style.css"' in html:
            problems.append(f"{page} 样式表引用缺少内容版本号（会被 30 天缓存冻住）")
        # 查渲染后的文本而不是原始 HTML：soup.decode() 会把 © 编码成 &copy;，
        # 按字符串找字面的 © 永远找不到——查错对象会让替换成功的页面报成失败。
        page_text = BeautifulSoup(html, "html.parser").get_text()
        if COPYRIGHT not in page_text:
            problems.append(f"{page} 版权行未写单位名称")
        if "All rights reserved" in page_text:
            problems.append(f"{page} 残留商标署名的版权行")
    if "2026017841" in index:
        problems.append("残留 iOS App 备案号（不应出现在本站）")

    # sitemap 漏页是静默的：搜索引擎只是少抓一页，没有任何报错。
    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    for page in ["index.html", *PAGE_RENAME.values()]:
        loc = f"{SITE_CN}/" if page == "index.html" else f"{SITE_CN}/{page}"
        if f"<loc>{loc}</loc>" not in sitemap:
            problems.append(f"{page} 不在 sitemap 里")

    # 兜底国际站：那份 sitemap 要手动跑 build_sitemap.py 生成，有忘记的风险。
    # 内地站每次部署都会跑到这里，正好替它把关。
    life_sitemap = ROOT / "sitemap.xml"
    if not life_sitemap.exists():
        problems.append("仓库根目录缺 sitemap.xml（跑 python3 build_sitemap.py）")
    else:
        listed = set(re.findall(r"<loc>[^<]*/([^/<]+\.html)</loc>",
                                life_sitemap.read_text(encoding="utf-8")))
        listed.add("index.html")  # 首页以 / 收录
        stale = sorted({p.name for p in ROOT.glob("*.html")} - listed)
        if stale:
            problems.append(
                f"国际站 sitemap 已过期，缺 {stale}（跑 python3 build_sitemap.py）"
            )
    for page in ["index.html", *PAGE_RENAME.values()]:
        html = (DIST / page).read_text(encoding="utf-8")
        for domain in BLOCKED_IN_CN:
            if f"//{domain}" in html or f".{domain}/" in html:
                problems.append(f"{page} 残留内地不可达链接：{domain}")

    # 每个被引用的本地文件都要真的存在（死链在浏览器里才暴露，构建时先挡掉）
    local_refs = set()
    for page in ["index.html", *PAGE_RENAME.values()]:
        page_soup = BeautifulSoup((DIST / page).read_text(encoding="utf-8"), "html.parser")
        for attr in ("href", "src", "data-src"):
            for el in page_soup.select(f"[{attr}]"):
                ref = el[attr].split("#")[0].split("?")[0]
                if ref and not re.match(r"^(https?:|mailto:|tel:|data:|/)", ref):
                    local_refs.add(ref)
    for ref in sorted(local_refs):
        if not (DIST / ref).exists():
            problems.append(f"引用了不存在的文件：{ref}")
    note(f"本地引用自检：{len(local_refs)} 个路径")

    for page in PAGE_RENAME.values():
        if not (DIST / page).exists():
            problems.append(f"缺少页面：{page}")

    for name in ("favicon.ico", "apple-touch-icon.png", "apple-touch-icon-precomposed.png"):
        if not (DIST / name).exists():
            problems.append(f"缺少 {name}")
    ico = DIST / "favicon.ico"
    if ico.exists():
        with Image.open(ico) as im:
            if len(getattr(im, "ico", im).sizes()) < 2:
                problems.append("favicon.ico 不是多尺寸（部分环境不认单尺寸 ico）")
    for page in ["index.html", *PAGE_RENAME.values()]:
        page_soup = BeautifulSoup((DIST / page).read_text(encoding="utf-8"), "html.parser")
        if not page_soup.select('link[rel~="icon"]'):
            problems.append(f"{page} 没有声明站点图标")
    return problems


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    build_page(ROOT / "index.html", "index.html")
    for src_name, dest_name in PAGE_RENAME.items():
        build_page(ROOT / src_name, dest_name)
    copy_assets()
    write_sitemap()

    print("\n".join(f"  · {line}" for line in log))

    problems = verify()
    if problems:
        print("\n构建自检未通过：")
        print("\n".join(f"  ✗ {p}" for p in sorted(set(problems))))
        return 1
    print("\n✅ 构建自检全部通过 -> dist-cn/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
