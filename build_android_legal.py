#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the Android OAuth landing page and five-language legal pages.

The existing privacy/terms families belong to the iOS app and its individual
publisher. Android uses Google Drive and a company publisher, so the two
platforms must not share legal copy even though they share mememo.life.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://mememo.life"
UPDATED = "2026-09-22"

LANGS = {
    "": {"html": "en", "label": "EN"},
    "-zh": {"html": "zh-CN", "label": "简体"},
    "-zh-Hant": {"html": "zh-TW", "label": "繁體"},
    "-ja": {"html": "ja", "label": "日本語"},
    "-ko": {"html": "ko", "label": "한국어"},
}

COPY = {
    "": {
        "privacy_title": "MeMemo for Android · Privacy Policy",
        "privacy_desc": "Privacy policy for MeMemo on Android, including local storage, optional Google Drive sync, Google account data, retention, deletion, and your choices.",
        "privacy_h1": "Privacy Policy for Android",
        "privacy_sub": "Your records stay under your control.",
        "terms_title": "MeMemo for Android · Terms of Service",
        "terms_desc": "Terms of service for MeMemo on Android, including local-first storage, optional Google Drive sync, Google Play purchases, and service limitations.",
        "terms_h1": "Terms of Service for Android",
        "terms_sub": "Please read these terms before using MeMemo for Android.",
        "effective": "Effective and updated: September 22, 2026",
        "overview": "Android Overview",
        "privacy": "Privacy Policy",
        "terms": "Terms of Service",
        "back": "Back to MeMemo",
        "landing_title": "MeMemo for Android · Local-first life journal",
        "landing_desc": "MeMemo for Android is a local-first life journal with optional Google Drive sync for Android devices and recovery.",
        "landing_h1": "Your life, one page at a time.",
        "landing_sub": "A calm, local-first journal with optional Google Drive sync.",
        "publisher": "Published by Shanghai Yuma Technology Co., Ltd.",
        "landing_body": """
<section><h2>About MeMemo</h2><p>MeMemo helps you record summaries, plans, keywords, and reflections across lifetime, year, month, week, and day views. Core records stay on your Android device.</p></section>
<section><h2>Optional Google Drive sync</h2><p>If you choose to enable it, MeMemo stores supported records in the hidden app-specific folder of your own Google Drive. This supports Android device-to-device sync, reinstall or device-change recovery, conflict handling, and history recovery.</p><p>MeMemo requests only the Google identity information needed to show and isolate the selected account, plus the non-sensitive <code>drive.appdata</code> scope. The developer cannot access your journal or Drive sync files.</p></section>
<section><h2>How Google data is used</h2><p>Google API data is not used for advertising, analytics, credit decisions, AI training, or data brokerage. The app has no third-party advertising, analytics, or tracking SDK. Google Play separately processes purchases and entitlement status.</p></section>
""",
        "privacy_body": """
<section><h2>Overview</h2><p>This policy applies to the Android version of MeMemo ("we", "our", "the app"), published by Shanghai Yuma Technology Co., Ltd. (上海于马科技有限公司). MeMemo is a local-first life journal. You can use it without a MeMemo account and without enabling cloud sync.</p></section>
<section><h2>Data handled by the app</h2><p>We do not operate a server that receives, stores, or processes your journal content. The app processes the following data on your device:</p><ul><li>journal summaries, notes, keywords, plans, completion state, stars, deletions, and conflict versions;</li><li>profile choices such as birthday, age calculation, life length, theme color, and fixed icon age;</li><li>device-only settings such as language, appearance, reminders, and app-lock credentials;</li><li>if you enable Google Drive sync, the confirmed Google email address and a SHA-256-derived account key based on Google's stable account identifier.</li></ul><p>OAuth access tokens are kept only in process memory. They are not written to the MeMemo database, settings, logs, or sync files.</p></section>
<section><h2>Optional Google Drive sync</h2><p>If you choose to enable sync, MeMemo requests <code>openid</code>, <code>userinfo.email</code>, and the non-sensitive <code>drive.appdata</code> scope. The email is shown so you can confirm the account. The stable account identifier is used only to prevent data from different Google accounts from being mixed.</p><p>Journal content and the synced profile choices listed above are stored in the hidden, app-specific folder of your Google Drive. Files in this folder do not appear in your normal Drive file list and cannot be shared. Language, appearance, reminders, app-lock credentials, OAuth tokens, and purchase credentials are not put into sync files.</p><p>Google API data is used only for Android device-to-device sync, reinstall or device-change recovery, conflict handling, and history recovery. We do not use it for advertising, analytics, credit decisions, AI training, or data brokerage. Our use and transfer of Google API data complies with the <a href="https://developers.google.com/terms/api-services-user-data-policy">Google API Services User Data Policy</a>, including the Limited Use requirements.</p></section>
<section><h2>Developer access and sharing</h2><p>We cannot read your journal or Google Drive sync files. We have no journal server and do not receive your Google access token. Only the app on a device you authorize can access its own hidden Drive folder during the authorization period.</p><p>We do not sell your data. At your direction, synced data is transferred to Google Drive solely to provide sync and recovery. The app contains no third-party advertising, analytics, or tracking SDK.</p></section>
<section><h2>Google Play and this website</h2><p>Google Play processes purchases and may provide the app with purchase status and a purchase token so it can determine your entitlement. We do not receive your payment-card details. Google Play and Google Drive are governed by Google's own terms and privacy policy.</p><p>This website uses Cloudflare Web Analytics for aggregate page and performance measurement. According to Cloudflare, it uses no cookies, does not track people across sites, and does not collect or use visitors' personal data. It never receives your MeMemo journal.</p></section>
<section><h2>Retention, disabling, revocation, and deletion</h2><ul><li><strong>Delete content in MeMemo:</strong> the deletion is synced when sync is enabled. Redundant historical objects are kept for at least 30 days for recovery before they become eligible for permanent cleanup.</li><li><strong>Turn off sync:</strong> local data and existing Drive data remain. Turning sync on again with the same account can continue from that data.</li><li><strong>Revoke MeMemo access in your Google Account:</strong> syncing stops, but existing hidden Drive data is not deleted.</li><li><strong>Delete or clear the app:</strong> local app data is removed, but hidden Drive data is not automatically deleted.</li><li><strong>Delete all hidden Drive data:</strong> open Google Drive settings, choose Manage apps, find MeMemo, then choose Options and Delete hidden app data. This deletes the app's entire Drive <code>appDataFolder</code> and cannot be undone. Keep a local copy or export first.</li></ul></section>
<section><h2>Security and international processing</h2><p>Data sent to Google Drive uses HTTPS and Google's standard encryption in transit and at rest. MeMemo does not currently claim end-to-end encryption and does not provide a separate sync password or recovery code. Google may process Drive data in the locations described in its privacy documentation.</p></section>
<section><h2>Children and your rights</h2><p>MeMemo is not directed at children and does not knowingly collect children's information on our servers. Depending on your location, you may have rights of access, correction, deletion, portability, restriction, objection, or complaint. Because we do not possess your journal, most actions are exercised directly in the app or your Google Drive settings. Contact us if you need help.</p></section>
<section><h2>Data controller and contact</h2><div class="callout"><p><strong>Shanghai Yuma Technology Co., Ltd. (上海于马科技有限公司)</strong><br />Shanghai, China<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div></section>
<section><h2>Changes to this policy</h2><p>We may update this policy when the app, law, or third-party services change. The updated date and current version will be posted on this page.</p></section>
""",
        "terms_body": """
<section><h2>Acceptance</h2><p>By downloading, installing, or using MeMemo for Android ("the app"), you agree to these terms. If you do not agree, do not use the app.</p></section>
<section><h2>Service</h2><p>MeMemo is a local-first personal life journal for summaries, plans, keywords, and related records across lifetime, year, month, week, and day views. Core records are stored on your device. Optional Google Drive sync stores supported records in your own Google account's hidden app-specific folder.</p></section>
<section><h2>Your content</h2><p>You retain ownership of content you create. We claim no ownership of your journal. You are responsible for the content you create and for complying with applicable law.</p></section>
<section><h2>Google Drive sync</h2><p>Sync is optional and requires a Google account, network access, available Drive storage, and authorization. It is subject to Google's terms, availability, quotas, and technical limits. Turning off sync or revoking access stops future synchronization but does not automatically delete existing hidden Drive data. See the Android Privacy Policy for deletion instructions.</p></section>
<section><h2>Purchases</h2><p>Android purchases are processed by Google Play and are subject to Google Play's terms. A lifetime unlock is tied to the Google Play account and entitlement information made available by Google. We do not receive your payment-card details. Refunds, reversals, and revoked purchases may change entitlement as permitted by Google Play rules and applicable law.</p></section>
<section><h2>Backups and data integrity</h2><p>No storage or synchronization system can guarantee that data will never be lost. Keep exports or other backups of important records. Before deleting the app, clearing app data, changing accounts, or deleting hidden Drive data, confirm that you have the copy you need.</p></section>
<section><h2>Availability and changes</h2><p>The app is provided as available. Features may change to improve reliability, comply with law, or respond to platform requirements. We do not guarantee uninterrupted or error-free service. Material changes to these terms will be posted with an updated date.</p></section>
<section><h2>Limitation of liability</h2><p>To the maximum extent permitted by law, Shanghai Yuma Technology Co., Ltd. is not liable for indirect, incidental, special, or consequential loss arising from use of the app, including data loss caused by device failure, account loss, network failure, or third-party service interruption. Nothing in these terms excludes rights or liability that cannot legally be excluded.</p></section>
<section><h2>Contact</h2><div class="callout"><p><strong>Shanghai Yuma Technology Co., Ltd. (上海于马科技有限公司)</strong><br />Shanghai, China<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div></section>
""",
    },
    "-zh": {
        "privacy_title": "我记 Android 版 · 隐私政策",
        "privacy_desc": "我记 Android 版隐私政策，说明本机存储、可选 Google Drive 同步、Google 账号数据、保留、删除与用户选择。",
        "privacy_h1": "Android 版隐私政策",
        "privacy_sub": "你的记录，始终由你掌控。",
        "terms_title": "我记 Android 版 · 服务条款",
        "terms_desc": "我记 Android 版服务条款，说明本机优先存储、可选 Google Drive 同步、Google Play 购买与服务边界。",
        "terms_h1": "Android 版服务条款",
        "terms_sub": "使用我记 Android 版前，请阅读以下条款。",
        "effective": "生效及更新日期：2026 年 9 月 22 日",
        "overview": "Android 版说明",
        "privacy": "隐私政策",
        "terms": "服务条款",
        "back": "返回我记",
        "landing_title": "我记 Android 版 · 本机优先的人生记录",
        "landing_desc": "我记 Android 版是本机优先的人生记录应用，可选使用 Google Drive 在 Android 设备间同步与恢复。",
        "landing_h1": "一页页，记下你的人生。",
        "landing_sub": "安静、本机优先，可选 Google Drive 同步。",
        "publisher": "由上海于马科技有限公司发布",
        "landing_body": """
<section><h2>关于我记</h2><p>我记帮你在人生、年、月、周、日五层时间视图中记录总结、计划、关键词和回顾。核心记录保存在你的 Android 设备上。</p></section>
<section><h2>可选的 Google Drive 同步</h2><p>开启后，我记会把受支持的记录存入你自己 Google Drive 的隐藏应用专用空间，用于 Android 设备间同步、换机或重装恢复、冲突处理与历史恢复。</p><p>我记只请求显示和隔离已选账号所必需的 Google 身份信息，以及非敏感的 <code>drive.appdata</code> 范围。开发者无法访问你的日记或 Drive 同步文件。</p></section>
<section><h2>Google 数据的用途</h2><p>Google API 数据不用于广告、分析、信用评估、AI 训练或数据中介业务。本应用不含第三方广告、分析或追踪 SDK。Google Play 单独处理购买与权益状态。</p></section>
""",
        "privacy_body": """
<section><h2>概述</h2><p>本政策适用于上海于马科技有限公司（“我们”、“本应用”）发布的我记 Android 版。我记是本机优先的人生记录应用。不注册我记账号、不开启云同步也可使用。</p></section>
<section><h2>应用处理的数据</h2><p>我们不运营用于接收、存储或处理你日记内容的服务器。本应用会在你的设备上处理：</p><ul><li>一句话、备注、关键词、计划、完成状态、星标、删除状态与冲突版本；</li><li>生日、年龄算法、人生长度、主题色和固定图标年龄等资料选择；</li><li>语言、外观、提醒和应用锁凭据等仅存在本机的设置；</li><li>如开启 Google Drive 同步，会保存你确认的 Google 邮箱，以及由 Google 稳定账号标识派生的 SHA-256 脱敏账号键。</li></ul><p>OAuth access token 只存在于进程内存，不写入我记数据库、设置、日志或同步文件。</p></section>
<section><h2>可选的 Google Drive 同步</h2><p>开启同步时，我记会请求 <code>openid</code>、<code>userinfo.email</code> 以及非敏感的 <code>drive.appdata</code> 范围。邮箱仅用于让你确认同步账号；稳定账号标识仅用于防止不同 Google 账号的数据被混合。</p><p>日记内容和上述参与同步的资料选择会保存到你 Google Drive 的隐藏应用专用空间。这些文件不出现在普通 Drive 文件列表中，也不可分享。语言、外观、提醒、应用锁凭据、OAuth token 和购买凭证不进入同步文件。</p><p>Google API 数据仅用于 Android 设备间同步、换机或重装恢复、冲突处理与历史恢复，不用于广告、分析、信用评估、AI 训练或数据中介业务。我们对 Google API 数据的使用和转移遵守 <a href="https://developers.google.com/terms/api-services-user-data-policy">Google API 服务用户数据政策</a>，包括 Limited Use 要求。</p></section>
<section><h2>开发者访问与数据分享</h2><p>我们无法读取你的日记或 Google Drive 同步文件。我们没有日记服务器，也不接收你的 Google access token。只有你授权设备上的本应用能在授权期内访问自己的 Drive 隐藏空间。</p><p>我们不出售你的数据。开启同步后，数据只会按你的选择传给 Google Drive，用于同步和恢复。本应用不含第三方广告、分析或追踪 SDK。</p></section>
<section><h2>Google Play 与本网站</h2><p>Google Play 处理购买，并可向本应用提供购买状态和购买 token，用于判定使用权益。我们不会收到你的支付卡信息。Google Play 和 Google Drive 另受 Google 自身条款与隐私政策约束。</p><p>本网站使用 Cloudflare Web Analytics 统计汇总页面访问和性能。根据 Cloudflare 的说明，该服务不使用 cookie、不跨网站追踪个人、不收集或使用访客个人数据，也绝不会获得你的我记日记。</p></section>
<section><h2>保留、关闭、撤权与删除</h2><ul><li><strong>在我记中删除内容：</strong>开启同步时，删除状态会被同步。为支持恢复，冗余历史对象至少保留 30 天，之后才会进入可永久清理状态。</li><li><strong>关闭同步：</strong>本机数据和已有 Drive 数据都会保留。使用原账号重新开启后可继续同步。</li><li><strong>在 Google 账号中撤销我记访问权限：</strong>同步会停止，但已有 Drive 隐藏数据不会被删除。</li><li><strong>删除应用或清除应用数据：</strong>本机数据会被删除，Drive 隐藏数据不会自动删除。</li><li><strong>删除全部 Drive 隐藏数据：</strong>打开 Google Drive 设置，选择“管理应用”，找到 MeMemo，再选择“选项”与“删除隐藏的应用数据”。这会删除本应用的整个 Drive <code>appDataFolder</code>，无法恢复。操作前请保留本机副本或导出数据。</li></ul></section>
<section><h2>安全与跨境处理</h2><p>传往 Google Drive 的数据使用 HTTPS 和 Google 提供的标准传输与静态加密。我记当前不宣称端到端加密，也不提供独立同步密码或恢复码。Google 可在其隐私说明列明的地点处理 Drive 数据。</p></section>
<section><h2>儿童与你的权利</h2><p>我记不面向儿童，我们也不会在自有服务器上故意收集儿童信息。根据你所在地，你可能享有访问、更正、删除、可携带、限制、反对或投诉等权利。由于我们不持有你的日记，大部分操作需由你直接在应用或 Google Drive 设置中完成。如需帮助，请联系我们。</p></section>
<section><h2>数据控制者与联系方式</h2><div class="callout"><p><strong>上海于马科技有限公司（Shanghai Yuma Technology Co., Ltd.）</strong><br />中国上海<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div></section>
<section><h2>政策变更</h2><p>应用、法律或第三方服务变化时，我们可能更新本政策。更新日期与最新版本会发布在本页。</p></section>
""",
        "terms_body": """
<section><h2>接受条款</h2><p>下载、安装或使用我记 Android 版（“本应用”），即表示你同意本条款。如不同意，请勿使用。</p></section>
<section><h2>服务说明</h2><p>我记是本机优先的个人人生记录应用，可在人生、年、月、周、日视图中记录总结、计划、关键词及相关内容。核心记录保存在你的设备上。可选的 Google Drive 同步会把受支持的记录存入你自己 Google 账号的隐藏应用专用空间。</p></section>
<section><h2>你的内容</h2><p>你保留自己创建内容的所有权。我们不对你的日记主张所有权。你应对自己创建的内容及其合法性负责。</p></section>
<section><h2>Google Drive 同步</h2><p>同步是可选功能，需要 Google 账号、网络连接、可用 Drive 存储空间与用户授权，并受 Google 的条款、可用性、配额和技术限制约束。关闭同步或撤销访问权限会停止后续同步，但不会自动删除已有 Drive 隐藏数据。删除方法见 Android 版隐私政策。</p></section>
<section><h2>购买</h2><p>Android 版购买由 Google Play 处理，并受 Google Play 条款约束。永久解锁与 Google Play 账号及 Google 提供的权益信息关联。我们不会收到你的支付卡信息。退款、冲正或购买被撤销时，我们可按 Google Play 规则和适用法律调整权益。</p></section>
<section><h2>备份与数据完整性</h2><p>任何存储或同步系统都无法保证数据永不丢失。重要记录请保留导出文件或其他备份。删除应用、清除应用数据、更换账号或删除 Drive 隐藏数据前，请确认已保留所需副本。</p></section>
<section><h2>可用性与变更</h2><p>本应用按实际可用状态提供。为改善可靠性、遵守法律或应对平台要求，功能可能调整。我们不保证服务永不中断或毫无错误。条款的重大变更会随更新日期发布。</p></section>
<section><h2>责任限制</h2><p>在法律允许的最大范围内，上海于马科技有限公司不对因使用本应用产生的间接、附带、特殊或后果性损失承担责任，包括设备故障、账号丢失、网络故障或第三方服务中断导致的数据丢失。本条款不排除法律不允许排除的权利或责任。</p></section>
<section><h2>联系我们</h2><div class="callout"><p><strong>上海于马科技有限公司（Shanghai Yuma Technology Co., Ltd.）</strong><br />中国上海<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div></section>
""",
    },
}


COPY.update({
    "-zh-Hant": {
        "privacy_title": "我記 Android 版 · 隱私政策",
        "privacy_desc": "我記 Android 版隱私政策，說明本機儲存、可選 Google Drive 同步、Google 帳號資料、保留、刪除與使用者選擇。",
        "privacy_h1": "Android 版隱私政策",
        "privacy_sub": "你的記錄，始終由你掌控。",
        "terms_title": "我記 Android 版 · 使用條款",
        "terms_desc": "我記 Android 版使用條款，說明本機優先儲存、可選 Google Drive 同步、Google Play 購買與服務界限。",
        "terms_h1": "Android 版使用條款",
        "terms_sub": "使用我記 Android 版前，請閱讀以下條款。",
        "effective": "生效及更新日期：2026 年 9 月 22 日",
        "overview": "Android 版說明",
        "privacy": "隱私政策",
        "terms": "使用條款",
        "back": "返回我記",
        "landing_title": "我記 Android 版 · 本機優先的人生記錄",
        "landing_desc": "我記 Android 版是本機優先的人生記錄應用，可選使用 Google Drive 在 Android 裝置間同步與復原。",
        "landing_h1": "一頁頁，記下你的人生。",
        "landing_sub": "安靜、本機優先，可選 Google Drive 同步。",
        "publisher": "由上海于马科技有限公司發布",
        "landing_body": """
<section><h2>關於我記</h2><p>我記幫你在人生、年、月、週、日五層時間視圖中記錄摘要、計畫、關鍵詞和回顧。核心記錄儲存於你的 Android 裝置。</p></section>
<section><h2>可選的 Google Drive 同步</h2><p>開啟後，我記會將受支援的記錄儲存至你自己 Google Drive 的隱藏應用專用空間，用於 Android 裝置間同步、換機或重裝復原、衝突處理與歷史復原。</p><p>我記只要求顯示與隔離所選帳號所必需的 Google 身分資訊，以及非敏感的 <code>drive.appdata</code> 範圍。開發者無法存取你的日記或 Drive 同步檔案。</p></section>
<section><h2>Google 資料的用途</h2><p>Google API 資料不用於廣告、分析、信用評估、AI 訓練或資料中介業務。本應用不含第三方廣告、分析或追蹤 SDK。Google Play 另行處理購買與權益狀態。</p></section>
""",
        "privacy_body": """
<section><h2>概述</h2><p>本政策適用於上海于马科技有限公司（Shanghai Yuma Technology Co., Ltd.，以下稱「我們」、「本應用」）發布的我記 Android 版。我記是本機優先的人生記錄應用，不註冊我記帳號、不開啟雲端同步也可使用。</p></section>
<section><h2>本機處理的資料</h2><p>我們不營運用於接收、儲存或處理你日記內容的伺服器。本應用在你的裝置上處理日記、備註、關鍵詞、計畫、完成狀態、星標、刪除與衝突版本，以及生日、年齡算法、人生長度、主題色和固定圖示年齡。語言、外觀、提醒與應用鎖憑證只儲存於當前裝置。</p><p>開啟 Google Drive 同步後，應用會儲存你確認的 Google 電子郵件地址，以及由 Google 穩定帳號識別碼衍生的 SHA-256 脫敏帳號鍵。OAuth access token 只存在於程序記憶體，不寫入資料庫、設定、日誌或同步檔案。</p></section>
<section><h2>可選的 Google Drive 同步</h2><p>開啟同步時，我記會要求 <code>openid</code>、<code>userinfo.email</code> 和非敏感的 <code>drive.appdata</code> 範圍。郵件地址用於讓你確認同步帳號；穩定帳號識別碼只用於防止不同 Google 帳號的資料混合。</p><p>參與同步的日記與個人資料儲存在你 Google Drive 的隱藏應用專用空間，不會出現於一般 Drive 檔案清單中，也無法分享。語言、外觀、提醒、應用鎖憑證、OAuth token 和購買憑證不會進入同步檔案。</p><p>Google API 資料只用於 Android 裝置間同步、重裝或換機復原、衝突處理與歷史復原，不用於廣告、分析、信用評估、AI 訓練或資料中介業務。我們遵守 <a href="https://developers.google.com/terms/api-services-user-data-policy">Google API Services User Data Policy</a> 與 Limited Use 要求。</p></section>
<section><h2>開發者存取與分享</h2><p>我們無法讀取你的日記或 Google Drive 同步檔案，也不會收到你的 Google access token。只有你授權裝置上的本應用能在授權期間存取自己的 Drive 隱藏空間。我們不出售資料。資料只會依你的選擇傳送至 Google Drive，用於同步與復原。應用不含第三方廣告、分析或追蹤 SDK。</p></section>
<section><h2>Google Play 與本網站</h2><p>Google Play 處理購買，並可向本應用提供購買狀態與購買 token 以判定權益。我們不會收到你的付款卡資料。本網站使用 Cloudflare Web Analytics 進行匯總頁面與效能測量。依 Cloudflare 說明，它不使用 cookie、不跨網站追蹤個人、不收集或使用訪客個人資料，也不會得到你的我記日記。</p></section>
<section><h2>保留、停用、撤銷與刪除</h2><ul><li><strong>在我記內刪除內容：</strong>開啟同步時，刪除狀態會被同步。冗餘歷史物件至少保留 30 天以支援復原，之後才有資格被永久清理。</li><li><strong>關閉同步：</strong>本機與已有 Drive 資料都會保留。</li><li><strong>在 Google 帳號撤銷我記存取權：</strong>同步會停止，但已有隱藏 Drive 資料不會刪除。</li><li><strong>刪除應用或清除應用資料：</strong>會刪除本機資料，不會自動刪除 Drive 隱藏資料。</li><li><strong>刪除所有 Drive 隱藏資料：</strong>開啟 Google Drive 設定，選擇「管理應用程式」，找到 MeMemo，再選擇「選項」與「刪除隱藏的應用程式資料」。此操作會刪除整個 Drive <code>appDataFolder</code>，且無法復原。請先保留本機副本或匯出。</li></ul></section>
<section><h2>安全、跨境處理與權利</h2><p>傳送至 Google Drive 的資料使用 HTTPS 與 Google 的標準傳輸和靜態加密。我記不聲稱端對端加密，也沒有獨立同步密碼或復原碼。Google 可能在其隱私說明所載地點處理 Drive 資料。依所在地法律，你可能擁有存取、更正、刪除、可攜、限制、異議與申訴等權利。由於我們不持有你的日記，大部分操作需直接在應用或 Google Drive 設定中完成。</p></section>
<section><h2>資料控制者與聯絡方式</h2><div class="callout"><p><strong>Shanghai Yuma Technology Co., Ltd.（上海于马科技有限公司）</strong><br />中國上海<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div><p>應用、法律或第三方服務變更時，我們可能更新本政策，並在本頁列出更新日期。</p></section>
""",
        "terms_body": """
<section><h2>接受條款</h2><p>下載、安裝或使用我記 Android 版（「本應用」），即表示你同意本條款。如不同意，請勿使用。</p></section>
<section><h2>服務說明</h2><p>我記是本機優先的個人人生記錄應用，可於人生、年、月、週、日視圖記錄摘要、計畫、關鍵詞與相關內容。核心記錄儲存於你的裝置。可選的 Google Drive 同步會把支援的記錄儲存於你自己 Google 帳號的隱藏應用專用空間。</p></section>
<section><h2>你的內容</h2><p>你保留自己建立內容的所有權。我們不對你的日記主張所有權。你應對自己建立內容的合法性負責。</p></section>
<section><h2>Google Drive 同步</h2><p>同步是可選功能，需要 Google 帳號、網路連線、可用 Drive 儲存空間與使用者授權，並受 Google 的條款、可用性、配額與技術限制約束。關閉同步或撤銷存取權會停止後續同步，但不會自動刪除已有 Drive 隱藏資料。刪除方式請見 Android 版隱私政策。</p></section>
<section><h2>購買</h2><p>Android 版購買由 Google Play 處理，並受 Google Play 條款約束。永久解鎖與 Google Play 帳號及 Google 提供的權益資訊關聯。我們不會收到你的付款卡資料。退款、沖正或購買被撤銷時，權益可依 Google Play 規則與適用法律調整。</p></section>
<section><h2>備份、可用性與變更</h2><p>任何儲存或同步系統都無法保證資料永不遺失。重要記錄請保留匯出檔或其他備份。刪除應用、清除應用資料、更換帳號或刪除 Drive 隱藏資料前，請確認已保留所需副本。功能可能為改善可靠性、遵守法律或回應平台要求而調整；我們不保證服務絕不中斷或完全無錯。</p></section>
<section><h2>責任限制</h2><p>在法律允許的最大範圍內，Shanghai Yuma Technology Co., Ltd.（上海于马科技有限公司）不對因使用本應用產生的間接、附帶、特殊或結果性損失負責，包括因裝置故障、帳號遺失、網路故障或第三方服務中斷所導致的資料遺失。本條款不排除法律不允許排除的權利或責任。</p></section>
<section><h2>聯絡我們</h2><div class="callout"><p><strong>Shanghai Yuma Technology Co., Ltd.（上海于马科技有限公司）</strong><br />中國上海<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div></section>
""",
    },
    "-ja": {
        "privacy_title": "MeMemo Android 版 · プライバシーポリシー",
        "privacy_desc": "MeMemo Android 版のプライバシーポリシー。端末保存、任意の Google Drive 同期、Google アカウント情報、保持、削除、選択肢を説明します。",
        "privacy_h1": "Android 版プライバシーポリシー",
        "privacy_sub": "あなたの記録は、あなたの管理下にあります。",
        "terms_title": "MeMemo Android 版 · 利用規約",
        "terms_desc": "MeMemo Android 版の利用規約。ローカル優先の保存、任意の Google Drive 同期、Google Play での購入、サービスの制限を説明します。",
        "terms_h1": "Android 版利用規約",
        "terms_sub": "MeMemo Android 版をご利用になる前にお読みください。",
        "effective": "施行・更新日：2026年9月22日",
        "overview": "Android 版について",
        "privacy": "プライバシーポリシー",
        "terms": "利用規約",
        "back": "MeMemo に戻る",
        "landing_title": "MeMemo Android 版 · ローカル優先のライフジャーナル",
        "landing_desc": "MeMemo Android 版は、Android 端末間の同期と復元に任意の Google Drive 同期を利用できるローカル優先のライフジャーナルです。",
        "landing_h1": "人生を、1ページずつ。",
        "landing_sub": "穏やかなローカル優先の日記。Google Drive 同期は任意です。",
        "publisher": "Shanghai Yuma Technology Co., Ltd.（上海于马科技有限公司）が提供",
        "landing_body": """
<section><h2>MeMemo について</h2><p>MeMemo は、人生、年、月、週、日の各ビューでまとめ、予定、キーワード、振り返りを記録するアプリです。主な記録は Android 端末に保存されます。</p></section>
<section><h2>任意の Google Drive 同期</h2><p>有効にすると、対応する記録をあなた自身の Google Drive の非表示アプリ専用領域に保存し、Android 端末間の同期、再インストールや機種変更時の復元、競合解決、履歴復元に使用します。</p><p>MeMemo が要求するのは、選択したアカウントの表示と分離に必要な Google 身元情報と、非機密の <code>drive.appdata</code> スコープだけです。開発者はあなたの日記や Drive 同期ファイルにアクセスできません。</p></section>
<section><h2>Google データの利用目的</h2><p>Google API データを広告、分析、信用判定、AI 学習、データ売買に使用しません。本アプリに第三者の広告、分析、追跡 SDK はありません。Google Play は購入と権利状態を別途処理します。</p></section>
""",
        "privacy_body": """
<section><h2>概要</h2><p>本ポリシーは、Shanghai Yuma Technology Co., Ltd.（上海于马科技有限公司。以下「当社」、「本アプリ」）が提供する MeMemo Android 版に適用されます。MeMemo はローカル優先のライフジャーナルです。MeMemo アカウントの登録やクラウド同期なしで利用できます。</p></section>
<section><h2>端末で処理するデータ</h2><p>当社は、日記内容を受信、保存、処理するサーバーを運営していません。本アプリは端末上で、日記、メモ、キーワード、予定、完了状態、お気に入り、削除状態、競合バージョン、生年月日、年齢計算、人生の長さ、テーマ色、固定アイコン年齢を処理します。言語、外観、リマインダー、アプリロックの認証情報は端末のみに保存されます。</p><p>Google Drive 同期を有効にすると、確認済みの Google メールアドレスと、Google の安定したアカウント識別子から導出した SHA-256 アカウントキーを保存します。OAuth access token はプロセス内メモリにのみ保持し、データベース、設定、ログ、同期ファイルには書き込みません。</p></section>
<section><h2>任意の Google Drive 同期</h2><p>同期を有効にすると、MeMemo は <code>openid</code>、<code>userinfo.email</code>、非機密の <code>drive.appdata</code> スコープを要求します。メールアドレスは同期先アカウントの確認に、安定した識別子は異なる Google アカウントのデータ混在防止にのみ使用します。</p><p>同期対象の日記とプロフィール選択は、あなたの Google Drive の非表示アプリ専用領域に保存されます。通常の Drive ファイル一覧には表示されず、共有できません。言語、外観、リマインダー、アプリロック認証情報、OAuth token、購入情報は同期ファイルに含まれません。</p><p>Google API データは Android 端末間の同期、再インストールや機種変更時の復元、競合解決、履歴復元のみに使用し、広告、分析、信用判定、AI 学習、データ売買には使用しません。当社は <a href="https://developers.google.com/terms/api-services-user-data-policy">Google API Services User Data Policy</a> と Limited Use 要件を遵守します。</p></section>
<section><h2>開発者のアクセスと共有</h2><p>当社は、あなたの日記や Google Drive 同期ファイルを読み取れません。Google access token も受信しません。許可期間中、許可した端末上の本アプリのみが自分の Drive 非表示領域にアクセスできます。当社はデータを販売しません。データはあなたの選択により、同期と復元のためにのみ Google Drive へ送信されます。本アプリに第三者の広告、分析、追跡 SDK はありません。</p></section>
<section><h2>Google Play と本ウェブサイト</h2><p>Google Play は購入を処理し、権利判定のために購入状態と購入 token を本アプリへ提供する場合があります。当社はカード情報を受け取りません。本ウェブサイトは Cloudflare Web Analytics を使用して、集計ページビューとパフォーマンスを測定します。Cloudflare の説明では、cookie を使用せず、サイト横断の個人追跡や訪問者の個人データの収集・利用を行いません。MeMemo の日記がウェブサイトに送信されることはありません。</p></section>
<section><h2>保持、停止、許可取り消し、削除</h2><ul><li><strong>MeMemo 内で削除：</strong>同期が有効な場合、削除状態も同期されます。復元のための冗長履歴オブジェクトは少なくとも 30 日間保持され、その後に永久削除の対象になります。</li><li><strong>同期をオフ：</strong>端末データと既存の Drive データは残ります。</li><li><strong>Google アカウントで MeMemo のアクセスを取り消す：</strong>同期は停止しますが、既存の Drive 非表示データは削除されません。</li><li><strong>アプリを削除またはデータを消去：</strong>端末データは削除されますが、Drive 非表示データは自動削除されません。</li><li><strong>Drive の全非表示データを削除：</strong>Google Drive の設定で「アプリを管理」から MeMemo を選び、「オプション」の「非表示のアプリデータを削除」を選択します。Drive <code>appDataFolder</code> 全体が復元不能に削除されるため、事前に端末のコピーまたは書き出しを保持してください。</li></ul></section>
<section><h2>セキュリティ、国際処理、あなたの権利</h2><p>Google Drive への送信には HTTPS と Google の標準的な転送中・保管時の暗号化が使われます。MeMemo は現在、エンドツーエンド暗号化を謳っておらず、別途の同期パスワードや復元コードも提供していません。Google は同社のプライバシー説明に記載された場所で Drive データを処理する場合があります。お住まいの地域により、アクセス、訂正、削除、ポータビリティ、処理制限、異議、苦情申立ての権利があります。当社は日記を保有しないため、多くの操作はアプリまたは Google Drive 設定で直接行います。</p></section>
<section><h2>データ管理者と連絡先</h2><div class="callout"><p><strong>Shanghai Yuma Technology Co., Ltd.（上海于马科技有限公司）</strong><br />中国・上海<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div><p>アプリ、法令、第三者サービスに変更があった場合、本ポリシーを更新し、更新日を本ページに掲載します。</p></section>
""",
        "terms_body": """
<section><h2>同意</h2><p>MeMemo Android 版（「本アプリ」）をダウンロード、インストール、または利用することで、本規約に同意したものとします。同意しない場合は利用しないでください。</p></section>
<section><h2>サービス</h2><p>MeMemo は、人生、年、月、週、日の各ビューでまとめ、予定、キーワードなどを記録するローカル優先の個人用ライフジャーナルです。主な記録は端末に保存されます。任意の Google Drive 同期は、対応データをあなた自身の Google アカウントの非表示アプリ専用領域に保存します。</p></section>
<section><h2>ユーザーコンテンツ</h2><p>あなたが作成したコンテンツの所有権はあなたに帰属します。当社は日記の所有権を主張しません。作成するコンテンツと適用法令の遵守については、あなたが責任を負います。</p></section>
<section><h2>Google Drive 同期</h2><p>同期は任意であり、Google アカウント、ネットワーク、利用可能な Drive 容量、許可が必要です。Google の規約、可用性、クォータ、技術的制限に従います。同期をオフにしたり許可を取り消したりすると、今後の同期は停止しますが、既存の Drive 非表示データは自動削除されません。削除手順は Android 版プライバシーポリシーをご覧ください。</p></section>
<section><h2>購入</h2><p>Android 版の購入は Google Play が処理し、Google Play の規約に従います。永久アンロックは Google Play アカウントと Google が提供する権利情報に関連付けられます。当社は支払カード情報を受け取りません。返金、取消し、購入の無効化により、Google Play のルールと適用法令に従って権利が変更される場合があります。</p></section>
<section><h2>バックアップ、可用性、変更</h2><p>いかなる保存・同期システムもデータが決して失われないことを保証できません。重要な記録は書き出しや別のバックアップを保持してください。アプリ削除、データ消去、アカウント変更、Drive 非表示データ削除の前に必要なコピーを確認してください。機能は信頼性改善、法令遵守、プラットフォーム要件への対応のため変更される場合があり、中断のない動作や無エラーを保証しません。</p></section>
<section><h2>責任の制限</h2><p>法律で認められる最大限の範囲で、Shanghai Yuma Technology Co., Ltd.（上海于马科技有限公司）は、端末障害、アカウント喪失、通信障害、第三者サービス中断によるデータ喪失を含む、本アプリの利用に起因する間接的、付随的、特別または結果的損失について責任を負いません。法律上除外できない権利または責任を本規約が除外することはありません。</p></section>
<section><h2>お問い合わせ</h2><div class="callout"><p><strong>Shanghai Yuma Technology Co., Ltd.（上海于马科技有限公司）</strong><br />中国・上海<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div></section>
""",
    },
    "-ko": {
        "privacy_title": "Android용 MeMemo · 개인정보 처리방침",
        "privacy_desc": "Android용 MeMemo 개인정보 처리방침으로, 기기 저장, 선택적 Google Drive 동기화, Google 계정 데이터, 보관, 삭제 및 사용자 선택을 안내합니다.",
        "privacy_h1": "Android용 개인정보 처리방침",
        "privacy_sub": "기록에 대한 통제권은 항상 사용자에게 있습니다.",
        "terms_title": "Android용 MeMemo · 이용약관",
        "terms_desc": "Android용 MeMemo 이용약관으로, 로컬 우선 저장, 선택적 Google Drive 동기화, Google Play 구매 및 서비스 제한을 안내합니다.",
        "terms_h1": "Android용 이용약관",
        "terms_sub": "Android용 MeMemo를 사용하기 전에 본 약관을 읽어 주십시오.",
        "effective": "시행 및 업데이트: 2026년 9월 22일",
        "overview": "Android 소개",
        "privacy": "개인정보 처리방침",
        "terms": "이용약관",
        "back": "MeMemo로 돌아가기",
        "landing_title": "Android용 MeMemo · 로컬 우선 인생 기록",
        "landing_desc": "Android용 MeMemo는 Android 기기 간 동기화와 복구를 위해 선택적 Google Drive 동기화를 제공하는 로컬 우선 인생 기록 앱입니다.",
        "landing_h1": "인생을 한 페이지씩.",
        "landing_sub": "차분하고 로컬 우선인 기록. Google Drive 동기화는 선택 사항입니다.",
        "publisher": "Shanghai Yuma Technology Co., Ltd.(上海于马科技有限公司) 제공",
        "landing_body": """
<section><h2>MeMemo 소개</h2><p>MeMemo는 인생, 연, 월, 주, 일 보기에서 요약, 계획, 키워드, 회고를 기록하도록 돕습니다. 핵심 기록은 Android 기기에 저장됩니다.</p></section>
<section><h2>선택적 Google Drive 동기화</h2><p>활성화하면 지원되는 기록을 사용자 Google Drive의 숨겨진 앱 전용 공간에 저장합니다. Android 기기 간 동기화, 재설치 또는 기기 변경 복구, 충돌 처리, 기록 복구에 사용합니다.</p><p>MeMemo는 선택한 계정을 표시하고 분리하는 데 필요한 Google 신원 정보와 민감하지 않은 <code>drive.appdata</code> 범위만 요청합니다. 개발자는 사용자의 일기나 Drive 동기화 파일에 접근할 수 없습니다.</p></section>
<section><h2>Google 데이터 사용 목적</h2><p>Google API 데이터를 광고, 분석, 신용 판단, AI 학습, 데이터 판매에 사용하지 않습니다. 본 앱에는 제3자 광고, 분석 또는 추적 SDK가 없습니다. Google Play는 구매와 권한 상태를 별도로 처리합니다.</p></section>
""",
        "privacy_body": """
<section><h2>개요</h2><p>본 방침은 Shanghai Yuma Technology Co., Ltd.(上海于马科技有限公司, 이하 '당사', '본 앱')가 제공하는 Android용 MeMemo에 적용됩니다. MeMemo는 로컬 우선 인생 기록 앱입니다. MeMemo 계정 등록이나 클라우드 동기화 없이도 사용할 수 있습니다.</p></section>
<section><h2>기기에서 처리하는 데이터</h2><p>당사는 일기 내용을 수신, 저장 또는 처리하는 서버를 운영하지 않습니다. 본 앱은 기기에서 일기, 메모, 키워드, 계획, 완료 상태, 즐겨찾기, 삭제 상태, 충돌 버전, 생년월일, 나이 계산 방식, 인생 길이, 테마 색상, 고정 아이콘 나이를 처리합니다. 언어, 화면 모드, 알림, 앱 잠금 자격 증명은 현재 기기에만 저장됩니다.</p><p>Google Drive 동기화를 켜면 확인한 Google 이메일 주소와 Google의 안정적인 계정 식별자에서 파생된 SHA-256 계정 키가 저장됩니다. OAuth access token은 프로세스 메모리에만 유지하며 데이터베이스, 설정, 로그 또는 동기화 파일에 기록하지 않습니다.</p></section>
<section><h2>선택적 Google Drive 동기화</h2><p>동기화를 켜면 MeMemo는 <code>openid</code>, <code>userinfo.email</code>, 민감하지 않은 <code>drive.appdata</code> 범위를 요청합니다. 이메일은 동기화 계정을 확인하는 데, 안정적인 식별자는 서로 다른 Google 계정의 데이터가 섞이지 않도록 하는 데만 사용합니다.</p><p>동기화 대상 일기와 프로필 선택은 사용자 Google Drive의 숨겨진 앱 전용 공간에 저장됩니다. 일반 Drive 파일 목록에 나타나지 않고 공유할 수 없습니다. 언어, 화면 모드, 알림, 앱 잠금 자격 증명, OAuth token, 구매 자격 증명은 동기화 파일에 포함되지 않습니다.</p><p>Google API 데이터는 Android 기기 간 동기화, 재설치 또는 기기 변경 복구, 충돌 처리, 기록 복구에만 사용하며 광고, 분석, 신용 판단, AI 학습, 데이터 판매에 사용하지 않습니다. 당사는 <a href="https://developers.google.com/terms/api-services-user-data-policy">Google API Services User Data Policy</a>와 Limited Use 요건을 준수합니다.</p></section>
<section><h2>개발자 접근 및 공유</h2><p>당사는 사용자의 일기나 Google Drive 동기화 파일을 읽을 수 없고 Google access token을 받지 않습니다. 승인 기간 동안 사용자가 승인한 기기의 본 앱만 자신의 Drive 숨겨진 공간에 접근할 수 있습니다. 당사는 데이터를 판매하지 않으며, 사용자의 선택에 따라 동기화와 복구 목적으로만 Google Drive에 전송합니다. 본 앱에는 제3자 광고, 분석 또는 추적 SDK가 없습니다.</p></section>
<section><h2>Google Play 및 본 웹사이트</h2><p>Google Play는 구매를 처리하고 권한 판단을 위해 구매 상태와 구매 token을 앱에 제공할 수 있습니다. 당사는 결제 카드 정보를 받지 않습니다. 본 웹사이트는 Cloudflare Web Analytics로 집계 페이지 및 성능을 측정합니다. Cloudflare의 설명에 따르면 cookie를 사용하지 않고, 사이트 간 개인을 추적하지 않으며, 방문자의 개인 데이터를 수집하거나 사용하지 않습니다. MeMemo 일기가 웹사이트로 전송되지 않습니다.</p></section>
<section><h2>보관, 중지, 접근 철회 및 삭제</h2><ul><li><strong>MeMemo에서 콘텐츠 삭제:</strong> 동기화가 켜져 있으면 삭제 상태도 동기화됩니다. 복구를 위한 중복 기록 객체는 최소 30일 동안 보관된 후 영구 정리 대상이 됩니다.</li><li><strong>동기화 끄기:</strong> 기기 데이터와 기존 Drive 데이터가 모두 남습니다.</li><li><strong>Google 계정에서 MeMemo 접근 철회:</strong> 동기화는 멈추지만 기존 Drive 숨겨진 데이터는 삭제되지 않습니다.</li><li><strong>앱 삭제 또는 앱 데이터 지우기:</strong> 기기 데이터는 삭제되지만 Drive 숨겨진 데이터는 자동 삭제되지 않습니다.</li><li><strong>Drive의 모든 숨겨진 데이터 삭제:</strong> Google Drive 설정의 '앱 관리'에서 MeMemo를 찾고 '옵션' 및 '숨겨진 앱 데이터 삭제'를 선택합니다. Drive <code>appDataFolder</code> 전체가 복구할 수 없게 삭제되므로 미리 기기 사본이나 내보낸 파일을 보관하십시오.</li></ul></section>
<section><h2>보안, 국제 처리 및 사용자 권리</h2><p>Google Drive로 전송되는 데이터에는 HTTPS와 Google의 표준 전송 및 보관 암호화가 적용됩니다. MeMemo는 현재 종단 간 암호화를 표방하지 않고 별도의 동기화 암호나 복구 코드를 제공하지 않습니다. Google은 자신의 개인정보 문서에 명시된 지역에서 Drive 데이터를 처리할 수 있습니다. 거주 지역에 따라 열람, 정정, 삭제, 이동, 처리 제한, 이의 제기, 민원 제기 권리가 있을 수 있습니다. 당사가 일기를 보유하지 않으므로 대부분의 작업은 앱 또는 Google Drive 설정에서 직접 수행합니다.</p></section>
<section><h2>데이터 관리자 및 문의</h2><div class="callout"><p><strong>Shanghai Yuma Technology Co., Ltd.(上海于马科技有限公司)</strong><br />중국 상하이<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div><p>앱, 법률 또는 제3자 서비스가 변경되면 본 방침을 업데이트하고 업데이트 날짜를 이 페이지에 게시합니다.</p></section>
""",
        "terms_body": """
<section><h2>약관 동의</h2><p>Android용 MeMemo('본 앱')를 다운로드, 설치 또는 사용하면 본 약관에 동의하는 것으로 간주됩니다. 동의하지 않으면 사용하지 마십시오.</p></section>
<section><h2>서비스</h2><p>MeMemo는 인생, 연, 월, 주, 일 보기에서 요약, 계획, 키워드 및 관련 기록을 작성할 수 있는 로컬 우선 개인 인생 기록 앱입니다. 핵심 기록은 기기에 저장됩니다. 선택적 Google Drive 동기화는 지원되는 기록을 사용자 Google 계정의 숨겨진 앱 전용 공간에 저장합니다.</p></section>
<section><h2>사용자 콘텐츠</h2><p>사용자가 작성한 콘텐츠의 소유권은 사용자에게 있습니다. 당사는 일기에 대한 소유권을 주장하지 않습니다. 작성하는 콘텐츠와 적용 법률 준수에 대한 책임은 사용자에게 있습니다.</p></section>
<section><h2>Google Drive 동기화</h2><p>동기화는 선택 사항이며 Google 계정, 네트워크, 사용 가능한 Drive 용량, 승인이 필요합니다. Google의 약관, 가용성, 할당량 및 기술적 제한을 따릅니다. 동기화를 끄거나 접근을 철회하면 이후 동기화는 중지되지만 기존 Drive 숨겨진 데이터는 자동으로 삭제되지 않습니다. 삭제 방법은 Android 개인정보 처리방침을 참고하십시오.</p></section>
<section><h2>구매</h2><p>Android 구매는 Google Play가 처리하며 Google Play 약관을 따릅니다. 평생 잠금 해제는 Google Play 계정과 Google이 제공하는 권한 정보에 연결됩니다. 당사는 결제 카드 정보를 받지 않습니다. 환불, 취소 또는 구매 철회 시 Google Play 규칙과 적용 법률에 따라 권한이 변경될 수 있습니다.</p></section>
<section><h2>백업, 가용성 및 변경</h2><p>어떠한 저장 또는 동기화 시스템도 데이터가 절대 손실되지 않음을 보장할 수 없습니다. 중요한 기록은 내보내기 파일이나 다른 백업을 유지하십시오. 앱 삭제, 앱 데이터 지우기, 계정 변경, Drive 숨겨진 데이터 삭제 전에 필요한 사본을 확인하십시오. 신뢰성 개선, 법률 준수, 플랫폼 요구 사항 대응을 위해 기능이 변경될 수 있으며 중단 없고 오류 없는 서비스를 보장하지 않습니다.</p></section>
<section><h2>책임 제한</h2><p>법률이 허용하는 최대 범위 내에서 Shanghai Yuma Technology Co., Ltd.(上海于马科技有限公司)는 기기 고장, 계정 손실, 네트워크 장애, 제3자 서비스 중단에 따른 데이터 손실을 포함하여 본 앱 사용으로 발생하는 간접적, 부수적, 특별 또는 결과적 손해에 대해 책임지지 않습니다. 법적으로 배제할 수 없는 권리나 책임은 본 약관으로 배제되지 않습니다.</p></section>
<section><h2>문의</h2><div class="callout"><p><strong>Shanghai Yuma Technology Co., Ltd.(上海于马科技有限公司)</strong><br />중국 상하이<br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div></section>
""",
    },
})


def copy_for(suffix: str) -> dict[str, str]:
    return COPY[suffix]


def language_links(family: str, active: str) -> str:
    return "\n".join(
        f'    <a href="{family}{suffix}.html" class="{"active" if suffix == active else ""}">{meta["label"]}</a>'
        for suffix, meta in LANGS.items()
    )


def legal_page(family: str, suffix: str) -> str:
    c = copy_for(suffix)
    meta = LANGS[suffix]
    is_privacy = family == "privacy-android"
    title = c["privacy_title" if is_privacy else "terms_title"]
    desc = c["privacy_desc" if is_privacy else "terms_desc"]
    h1 = c["privacy_h1" if is_privacy else "terms_h1"]
    sub = c["privacy_sub" if is_privacy else "terms_sub"]
    body = c["privacy_body" if is_privacy else "terms_body"].strip()
    filename = f"{family}{suffix}.html"
    return f"""<!DOCTYPE html>
<html lang="{meta['html']}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<meta name="description" content="{desc}" />
<link rel="canonical" href="{SITE}/{filename}" />
<link rel="icon" href="icon.png" />
<link rel="stylesheet" href="legal-style.css" />
</head>
<body>
<nav class="nav"><a class="nav-brand" href="android{suffix}.html"><img src="icon.png" alt="MeMemo" /><span>MeMemo</span><span class="en">Android</span></a><div class="nav-langs">
{language_links(family, suffix)}
</div></nav>
<header class="page-head"><div class="eyebrow">Android</div><h1>{h1}</h1><p class="sub">{sub}</p><div class="dates"><span>{c['effective']}</span></div></header>
<nav class="subnav"><a href="android{suffix}.html">{c['overview']}</a><a href="privacy-android{suffix}.html" class="{'active' if is_privacy else ''}">{c['privacy']}</a><a href="terms-android{suffix}.html" class="{'active' if not is_privacy else ''}">{c['terms']}</a></nav>
<main class="content">
{body}
</main>
<footer class="page-foot"><div class="foot-links"><a href="android{suffix}.html">← {c['back']}</a></div><div class="foot-legal"><div>&copy; 2026 MeMemo™ · 我记™. Shanghai Yuma Technology Co., Ltd.</div></div></footer>
<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "edb36f2cff1141f3bcf8ea60aab347a4"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>"""


def landing_page(suffix: str) -> str:
    c = copy_for(suffix)
    meta = LANGS[suffix]
    filename = f"android{suffix}.html"
    return f"""<!DOCTYPE html>
<html lang="{meta['html']}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{c['landing_title']}</title>
<meta name="description" content="{c['landing_desc']}" />
<link rel="canonical" href="{SITE}/{filename}" />
<link rel="icon" href="icon.png" />
<link rel="stylesheet" href="legal-style.css" />
</head>
<body>
<nav class="nav"><a class="nav-brand" href="/"><img src="icon.png" alt="MeMemo" /><span>MeMemo</span><span class="en">Android</span></a><div class="nav-langs">
{language_links("android", suffix)}
</div></nav>
<header class="page-head"><div class="eyebrow">MeMemo for Android</div><h1>{c['landing_h1']}</h1><p class="sub">{c['landing_sub']}</p><div class="dates"><span>{c['publisher']}</span></div></header>
<nav class="subnav"><a href="android{suffix}.html" class="active">{c['overview']}</a><a href="privacy-android{suffix}.html">{c['privacy']}</a><a href="terms-android{suffix}.html">{c['terms']}</a></nav>
<main class="content">
{c['landing_body'].strip()}
<section><h2>{c['overview']}</h2><div class="callout"><p><a href="privacy-android{suffix}.html">{c['privacy']}</a><br /><a href="terms-android{suffix}.html">{c['terms']}</a><br /><a href="mailto:aaron@mememo.life">aaron@mememo.life</a></p></div></section>
</main>
<footer class="page-foot"><div class="foot-links"><a href="/">← {c['back']}</a></div><div class="foot-legal"><div>&copy; 2026 MeMemo™ · 我记™. Shanghai Yuma Technology Co., Ltd.</div></div></footer>
<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "edb36f2cff1141f3bcf8ea60aab347a4"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>"""


def main() -> int:
    for suffix in LANGS:
        (ROOT / f"android{suffix}.html").write_text(
            landing_page(suffix),
            encoding="utf-8",
        )
    for family in ("privacy-android", "terms-android"):
        for suffix in LANGS:
            (ROOT / f"{family}{suffix}.html").write_text(
                legal_page(family, suffix),
                encoding="utf-8",
            )

    banned = ("iPhone", "iPad", "iCloud", "CloudKit", "Apple ID")
    outputs = [ROOT / f"android{suffix}.html" for suffix in LANGS] + [
        ROOT / f"{family}{suffix}.html"
        for family in ("privacy-android", "terms-android")
        for suffix in LANGS
    ]
    problems = []
    for path in outputs:
        html = path.read_text(encoding="utf-8")
        for word in banned:
            if word in html:
                problems.append(f"{path.name}: stale iOS term {word}")
        if "Shanghai Yuma Technology Co., Ltd." not in html:
            problems.append(f"{path.name}: missing Android publisher")
        if "Google Drive" not in html:
            problems.append(f"{path.name}: missing Google Drive disclosure")
    if problems:
        raise SystemExit("\n".join(problems))

    print(f"generated {len(outputs)} Android website pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
