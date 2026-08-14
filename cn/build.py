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

import re
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist-cn"

KEEP_LANG = "zh"

# 内地站页脚必须展示【网站】备案号并链到工信部（法定要求）。
# 刻意不展示任何 App 备案号：App 备案号的公示义务在 App 内与应用商店展示页，
# 网站没有代为公示的义务，且 iOS App 备案属个人主体、与本站公司主体不一致。
ICP_WEBSITE = "沪ICP备2026035044号-2"
ICP_URL = "https://beian.miit.gov.cn/"

# 简体单语站的干净 URL：privacy-zh.html -> privacy.html
PAGE_RENAME = {
    "privacy-zh.html": "privacy.html",
    "terms-zh.html": "terms.html",
    "support-zh.html": "support.html",
}

SHOWCASE = ["day", "me", "month", "week", "year"]

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
    """把页脚备案号换成本站的网站备案号。"""
    replaced = False
    for a in soup.find_all("a", href=re.compile("beian.miit.gov.cn")):
        a.attrs = {"href": ICP_URL, "target": "_blank", "rel": "noopener"}
        a.string = ICP_WEBSITE
        replaced = True
    if replaced:
        note(f"页脚备案号 -> {ICP_WEBSITE}")
    else:
        note("⚠️ 页脚未找到备案号链接")


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
    if src.name == "index.html":
        simplify_lang_css(soup)
        pin_language_to_zh(soup)
    set_icp_footer(soup)
    rewrite_links(soup)

    html = soup.decode(formatter="html5")
    (DIST / dest_name).write_text(html, encoding="utf-8")
    note(f"写出 {dest_name}（{len(html) // 1024} KB）")


def copy_assets() -> None:
    shutil.copy2(ROOT / "icon.png", DIST / "icon.png")
    shutil.copy2(ROOT / "legal-style.css", DIST / "legal-style.css")

    opt = DIST / "screens" / "opt"
    opt.mkdir(parents=True, exist_ok=True)
    for name in SHOWCASE:
        img = ROOT / "screens" / "opt" / f"{name}-zh.webp"
        shutil.copy2(img, opt / img.name)
    note(f"复制资源：icon + legal-style.css + {len(SHOWCASE)} 张简体截图")


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
    if ICP_WEBSITE not in index:
        problems.append("首页缺少网站备案号")
    if "2026017841" in index:
        problems.append("残留 iOS App 备案号（不应出现在本站）")

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
    return problems


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    build_page(ROOT / "index.html", "index.html")
    for src_name, dest_name in PAGE_RENAME.items():
        build_page(ROOT / src_name, dest_name)
    copy_assets()

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
