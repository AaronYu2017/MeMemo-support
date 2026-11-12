"""内地站安卓边界：漏标、编码链接和额外页面不能绕过产物检查。

运行：python3 -m unittest cn.test_android_boundary -v
"""

import json
import unittest

from bs4 import BeautifulSoup

from cn.build import android_residue, strip_android


class AndroidBoundaryTests(unittest.TestCase):
    def test_strip_removes_nested_android_blocks_and_preserves_ios(self):
        soup = BeautifulSoup(
            '<footer><div data-platform="ios"><a href="privacy-zh.html">隐私政策</a></div>'
            '<div data-platform="android"><span data-platform="android">即将上线</span>'
            '<a href="android-zh.html">版说明</a></div></footer>',
            "html.parser",
        )
        strip_android(soup)
        self.assertEqual(len(soup.select('[data-platform="ios"] a')), 1)
        self.assertEqual(android_residue("index.html", str(soup)), [])
        self.assertNotIn("即将上线", soup.get_text())

    def test_unmarked_notices_in_all_five_languages_are_rejected(self):
        for text in ("安卓版即将上线", "Android 版即將上線", "Android coming soon",
                     "Android 版は近日公開", "Android 버전 출시 예정"):
            with self.subTest(text=text):
                self.assertTrue(android_residue("index.html", f"<span>{text}</span>"))

    def test_unmarked_relative_absolute_and_encoded_links_are_rejected(self):
        for href in ("faq-android-zh.html", "/privacy-android.html",
                     "https://mememo.life/terms-ANDROID.html", "/%61ndroid.html"):
            with self.subTest(href=href):
                problems = android_residue("support.html", f'<a href="{href}">说明</a>')
                self.assertIn("support.html 残留 android 链接", problems)

    def test_google_drive_split_across_markup_or_entities_is_rejected(self):
        for text in ("Google Drive", "Google&nbsp;Drive", "<b>Google</b> <i>Drive</i>"):
            with self.subTest(text=text):
                self.assertIn("index.html 残留 Google Drive", android_residue("index.html", text))

    def test_google_service_addresses_are_rejected_without_visible_names(self):
        for address in ("https://PLAY.GOOGLE.com/store/apps", "https://drive.google.com/"):
            with self.subTest(address=address):
                self.assertTrue(android_residue("index.html", f'<a href="{address}">下载</a>'))

    def test_extra_android_page_is_rejected_even_if_empty(self):
        self.assertIn("extra/Android.html 不应生成安卓页面",
                      android_residue("extra/Android.html", "<html></html>"))

    def test_empty_android_marker_is_rejected(self):
        self.assertIn("index.html 残留安卓内容块",
                      android_residue("index.html", '<div data-platform="android"></div>'))

    def test_structured_data_cannot_hide_android_residue(self):
        self.assertTrue(android_residue("faq.html",
                        '<script type="application/ld+json">{"name":"安卓版即将上线"}</script>'))

    def test_existing_mainland_platform_faq_text_is_allowed(self):
        # 内地站原有的「有安卓版吗」等纯文字问答要保留，不能被当成残留。
        self.assertEqual(android_residue("faq.html",
                         '<details><summary>有安卓版吗？</summary>正在做。Google Play 版分开购买。</details>'), [])

    def test_strip_keeps_faq_structured_data_in_sync_with_visible_questions(self):
        data = {"@type": "FAQPage", "mainEntity": [
            {"name": "有安卓版吗？", "acceptedAnswer": {"text": "即将上线"}},
            {"name": "iPad 能用吗？", "acceptedAnswer": {"text": "能"}},
        ]}
        soup = BeautifulSoup(
            '<details data-platform="android"><summary>有安卓版吗？</summary>即将上线</details>'
            '<details><summary>iPad 能用吗？</summary>能</details>'
            '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>',
            "html.parser",
        )
        strip_android(soup)
        self.assertEqual(len(soup.select("details")), 1)
        self.assertEqual(json.loads(soup.script.string)["mainEntity"], [data["mainEntity"][1]])
        self.assertEqual(android_residue("faq.html", str(soup)), [])

    def test_css_selectors_do_not_count_as_visible_android_content(self):
        self.assertEqual(android_residue("index.html", '<style>.android { color: red; }</style>'), [])

    def test_ios_and_mainland_links_are_accepted(self):
        html = ('<div data-platform="ios">iCloud 同步</div>'
                '<a href="https://apps.apple.com/app/id6760353728">App Store</a>'
                '<a href="https://beian.miit.gov.cn/">备案</a>')
        self.assertEqual(android_residue("index.html", html), [])


if __name__ == "__main__":
    unittest.main()
