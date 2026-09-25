#!/usr/bin/env python3
"""Build the five Android FAQ pages from one translated content source.

This exists because the iOS FAQ describes Apple ID and iCloud. Remove this
generator only when Android help moves to another maintained source.
"""

from html import escape
from pathlib import Path

from build_android_legal import LANGS, ROOT, SITE, COPY, language_links

CONTENT = {
    "": {
        "title": "MeMemo for Android · FAQ",
        "description": "Answers about MeMemo for Android, Google Drive sync, backups, purchases, and data removal.",
        "heading": "Frequently Asked Questions",
        "intro": "Answers for the Android version of MeMemo.",
        "questions": [
            ("Where are my records stored?", "Your records start on your Android device. If you turn on Google Drive sync, supported records are also stored in the hidden app-specific space of your own Drive account. MeMemo does not operate a journal server."),
            ("How do I move to a new Android phone?", "Turn on Google Drive sync with your chosen Google account before switching phones. On the new phone, choose the same account and confirm recovery. You can also export a JSON backup and import it on the new device."),
            ("What happens if I uninstall the app?", "Uninstalling removes the local copy. Existing Google Drive data is not automatically deleted. If sync was off, recovery requires a backup you exported earlier."),
            ("How can I back up or export my data?", "In Settings, use Export data for a readable PDF, Markdown, or plain-text file. Use the backup export for a JSON file that MeMemo can import later. Keep exported files somewhere you control."),
            ("How do purchases work?", "The Android version offers a 7-day trial and a one-time lifetime unlock through Google Play. Purchases belong to your Google Play account. Restore the purchase with the same account after reinstalling."),
            ("Does Android sync directly with iPhone or iPad?", "No. Google Drive sync currently works between Android devices only. iOS uses its own iCloud sync. Do not expect edits on one platform to appear automatically on the other."),
            ("How do I delete synced data?", "Turning off sync or revoking access stops future syncing but keeps existing Drive data. To remove it, open Google Drive Settings, Manage apps, MeMemo, then Delete hidden app data. Keep an export first if you may need the records."),
        ],
    },
    "-zh": {
        "title": "我记 Android 版 · 常见问题",
        "description": "我记 Android 版关于 Google Drive 同步、备份、购买和数据删除的常见问题。",
        "heading": "常见问题",
        "intro": "关于我记 Android 版的常见疑问。",
        "questions": [
            ("记录保存在哪里？", "记录首先保存在你的 Android 设备上。开启 Google Drive 同步后，受支持的记录也会存入你自己 Drive 账号的隐藏应用专用空间。我记不运营日记服务器。"),
            ("换一台安卓手机怎样恢复？", "换机前先用选定的 Google 账号开启 Drive 同步。新手机上选择同一账号并确认恢复。你也可以导出 JSON 备份，再在新手机上导入。"),
            ("卸载 App 后会怎样？", "卸载会清除本机副本，已有的 Google Drive 数据不会自动删除。如果未开启同步，只有事先导出的备份可用于恢复。"),
            ("怎样备份或导出数据？", "在设置中使用“导出数据”生成便于阅读的 PDF、Markdown 或纯文本文件；使用备份导出生成可供我记日后导入的 JSON 文件。请把导出文件保存在你能掌控的位置。"),
            ("购买如何生效？", "Android 版提供 7 天试用，之后可通过 Google Play 一次性买断。购买资格绑定 Google Play 账号；重装后使用同一账号恢复购买。"),
            ("安卓与 iPhone、iPad 会实时同步吗？", "不会。Google Drive 同步目前只在安卓设备之间工作，iOS 使用独立的 iCloud 同步。不要预期在一端修改的内容会自动出现在另一端。"),
            ("怎样删除云端同步数据？", "关闭同步或撤销授权只会停止后续同步，已有 Drive 数据仍会保留。要删除，请在 Google Drive 设置中依次进入“管理应用” →“MeMemo”→“删除隐藏的应用数据”。如果日后可能需要记录，请先导出。"),
        ],
    },
    "-zh-Hant": {
        "title": "我記 Android 版 · 常見問題",
        "description": "我記 Android 版關於 Google Drive 同步、備份、購買與資料刪除的常見問題。",
        "heading": "常見問題",
        "intro": "關於我記 Android 版的常見疑問。",
        "questions": [
            ("記錄儲存在哪裡？", "記錄首先儲存在你的 Android 裝置上。開啟 Google Drive 同步後，支援同步的記錄也會存入你自己 Drive 帳戶的隱藏應用程式專用空間。我記不營運日記伺服器。"),
            ("換一部 Android 手機如何還原？", "換機前先用選定的 Google 帳戶開啟 Drive 同步。新手機上選擇同一帳戶並確認還原。你也可以匯出 JSON 備份，再在新手機上匯入。"),
            ("解除安裝 App 後會怎樣？", "解除安裝會清除裝置上的副本，現有的 Google Drive 資料不會自動刪除。若未開啟同步，只能使用事先匯出的備份還原。"),
            ("如何備份或匯出資料？", "在設定中使用「匯出資料」產生便於閱讀的 PDF、Markdown 或純文字檔；使用備份匯出產生可供我記日後匯入的 JSON 檔。請將匯出檔案存放在你能掌控的位置。"),
            ("購買如何生效？", "Android 版提供 7 天試用，之後可透過 Google Play 一次性買斷。購買資格綁定 Google Play 帳戶；重新安裝後請使用同一帳戶恢復購買。"),
            ("Android 與 iPhone、iPad 會即時同步嗎？", "不會。Google Drive 同步目前只在 Android 裝置之間運作，iOS 使用獨立的 iCloud 同步。請勿預期在一端修改的內容會自動出現在另一端。"),
            ("如何刪除雲端同步資料？", "關閉同步或撤銷授權只會停止後續同步，現有 Drive 資料仍會保留。要刪除，請在 Google Drive 設定中依序進入「管理應用程式」→「MeMemo」→「刪除隱藏的應用程式資料」。若日後可能需要記錄，請先匯出。"),
        ],
    },
    "-ja": {
        "title": "MeMemo Android 版 · よくある質問",
        "description": "MeMemo Android 版の Google Drive 同期、バックアップ、購入、データ削除に関するよくある質問。",
        "heading": "よくある質問",
        "intro": "MeMemo Android 版についての回答をまとめました。",
        "questions": [
            ("記録はどこに保存されますか？", "記録はまず Android 端末に保存されます。Google Drive 同期を有効にすると、対応する記録はご自身の Drive アカウントの非表示のアプリ専用領域にも保存されます。MeMemo は日記用サーバーを運営していません。"),
            ("新しい Android 端末へ移すには？", "機種変更前に、使用する Google アカウントで Drive 同期を有効にしてください。新しい端末では同じアカウントを選び、復元を確認します。JSON バックアップを書き出して、新しい端末で読み込むこともできます。"),
            ("アプリを削除するとどうなりますか？", "端末内のデータは削除されます。既存の Google Drive データは自動では削除されません。同期を使っていなかった場合は、事前に書き出したバックアップが必要です。"),
            ("バックアップや書き出しの方法は？", "設定の「データを書き出す」から、閲覧用の PDF、Markdown、テキストを作成できます。バックアップの書き出しでは、後から MeMemo に読み込める JSON ファイルを作成します。ファイルはご自身で管理できる場所に保管してください。"),
            ("購入はどのように適用されますか？", "Android 版には 7 日間の体験期間があり、その後 Google Play で一度だけ購入すると永続的に利用できます。購入は Google Play アカウントに紐付きます。再インストール後は同じアカウントで購入を復元してください。"),
            ("Android と iPhone・iPad は自動で同期しますか？", "いいえ。Google Drive 同期は現在 Android 端末間のみで利用できます。iOS 版は別の iCloud 同期を使用します。一方での編集がもう一方に自動反映されることはありません。"),
            ("クラウドの同期データを削除するには？", "同期をオフにしたりアクセスを取り消したりしても、既存の Drive データは残ります。削除するには Google Drive の設定から「アプリの管理」→「MeMemo」→「非表示のアプリデータを削除」を選びます。必要な記録は先に書き出してください。"),
        ],
    },
    "-ko": {
        "title": "MeMemo Android · 자주 묻는 질문",
        "description": "MeMemo Android의 Google Drive 동기화, 백업, 구매 및 데이터 삭제에 관한 자주 묻는 질문입니다.",
        "heading": "자주 묻는 질문",
        "intro": "MeMemo Android 버전에 관한 답변을 모았습니다.",
        "questions": [
            ("기록은 어디에 저장되나요?", "기록은 먼저 Android 기기에 저장됩니다. Google Drive 동기화를 켜면 지원되는 기록이 본인 Drive 계정의 숨겨진 앱 전용 공간에도 저장됩니다. MeMemo는 일기 서버를 운영하지 않습니다."),
            ("새 Android 휴대전화로 옮기려면 어떻게 하나요?", "휴대전화를 바꾸기 전에 사용할 Google 계정으로 Drive 동기화를 켜세요. 새 기기에서 같은 계정을 선택하고 복원을 확인하세요. JSON 백업을 내보내 새 기기에서 가져올 수도 있습니다."),
            ("앱을 삭제하면 어떻게 되나요?", "기기에 저장된 사본은 삭제됩니다. 기존 Google Drive 데이터는 자동으로 삭제되지 않습니다. 동기화를 사용하지 않았다면 미리 내보낸 백업이 있어야 복원할 수 있습니다."),
            ("백업이나 내보내기는 어떻게 하나요?", "설정의 데이터 내보내기에서 읽기용 PDF, Markdown 또는 일반 텍스트 파일을 만들 수 있습니다. 백업 내보내기에서는 나중에 MeMemo로 가져올 수 있는 JSON 파일을 만듭니다. 파일은 직접 관리할 수 있는 곳에 보관하세요."),
            ("구매는 어떻게 적용되나요?", "Android 버전에는 7일 체험 기간이 있으며, 이후 Google Play에서 한 번 구매하면 영구적으로 사용할 수 있습니다. 구매 권한은 Google Play 계정에 연결됩니다. 재설치 후 같은 계정으로 구매를 복원하세요."),
            ("Android와 iPhone·iPad가 자동으로 동기화되나요?", "아니요. Google Drive 동기화는 현재 Android 기기 사이에서만 작동합니다. iOS 버전은 별도의 iCloud 동기화를 사용합니다. 한쪽에서 수정한 내용이 다른 쪽에 자동으로 나타나지는 않습니다."),
            ("클라우드 동기화 데이터를 삭제하려면?", "동기화를 끄거나 접근 권한을 철회해도 기존 Drive 데이터는 남습니다. 삭제하려면 Google Drive 설정에서 '앱 관리' → 'MeMemo' → '숨겨진 앱 데이터 삭제'를 선택하세요. 필요한 기록은 먼저 내보내세요."),
        ],
    },
}


def render(suffix: str) -> str:
    c = CONTENT[suffix]
    site = COPY[suffix]
    filename = f"faq-android{suffix}.html"
    questions = "\n".join(
        f"<section><h2>{escape(question)}</h2><p>{escape(answer)}</p></section>"
        for question, answer in c["questions"]
    )
    return f"""<!DOCTYPE html>
<html lang="{LANGS[suffix]['html']}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{escape(c['title'])}</title>
<meta name="description" content="{escape(c['description'])}" />
<link rel="canonical" href="{SITE}/{filename}" />
<link rel="icon" href="icon.png" />
<link rel="stylesheet" href="legal-style.css" />
</head>
<body>
<nav class="nav"><a class="nav-brand" href="android{suffix}.html"><img src="icon.png" alt="MeMemo" /><span>MeMemo</span><span class="en">Android</span></a><div class="nav-langs">
{language_links('faq-android', suffix)}
</div></nav>
<header class="page-head"><div class="eyebrow">Android</div><h1>{escape(c['heading'])}</h1><p class="sub">{escape(c['intro'])}</p></header>
<nav class="subnav"><a href="android{suffix}.html">{site['overview']}</a><a href="faq-android{suffix}.html" class="active">{escape(c['heading'])}</a><a href="privacy-android{suffix}.html">{site['privacy']}</a><a href="terms-android{suffix}.html">{site['terms']}</a></nav>
<main class="content">
{questions}
<section><h2>{'Need help?' if not suffix else {'-zh': '还需要帮助？', '-zh-Hant': '還需要協助？', '-ja': 'お問い合わせ', '-ko': '도움이 더 필요하신가요?'}[suffix]}</h2><p><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></section>
</main>
<footer class="page-foot"><div class="foot-links"><a href="android{suffix}.html">← {site['back']}</a></div><div class="foot-legal"><div>&copy; 2026 MeMemo™ · 我记™. Shanghai Yuma Technology Co., Ltd.</div></div></footer>
<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "edb36f2cff1141f3bcf8ea60aab347a4"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>"""


def main() -> None:
    assert set(CONTENT) == set(LANGS)
    assert {len(item['questions']) for item in CONTENT.values()} == {7}
    for suffix in LANGS:
        (ROOT / f"faq-android{suffix}.html").write_text(render(suffix), encoding="utf-8")


if __name__ == "__main__":
    main()
