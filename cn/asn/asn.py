#!/usr/bin/env python3
"""App Store Server Notifications V2 接收端 —— 有人买断/退款时几秒内推到 Bark。

为什么存在：App Store Connect 的销售报告最快也有约 10 小时延迟，而那个延迟在
Apple 的**报表管线**里，任何 API 轮询都继承同样的延迟。Server Notifications 走的是
交易事件管线，是 Apple 唯一的实时通路。2026-06 曾因「改价后连续 3 天零付费」动用
代码审查 + ASC 核查 + 借真机三重验证才排除虚惊 —— 一条活着的通知管线几秒就能回答。

四个入口，同一个文件：
  application               WSGI 可调用对象，gunicorn 跑它（接收 + 验签 + 落盘 + 推送）
  python3 asn.py drain      补推没推成功的 + 清过期（systemd timer 每 5 分钟）
  python3 asn.py heartbeat  主动让 Apple 发一条 TEST 通知，验证整条管线活着
  python3 asn.py tail       人看的最近若干条

设计要点（都是有代价换来的，改之前先读）：
  1. **先落盘再回 200，推送失败不影响回 200。** 反过来做的话，推送一失败 Apple 就
     不再重试，那条购买永久丢失。落盘成功即视为我们已接管，Bark 随时可以补发。
  2. 落盘失败才回 500 —— 那是唯一该让 Apple 重试的情况。
  3. **按 notificationUUID 去重。** 我们在回 200 **之前**同步推 Bark（最多 8 秒），
     Apple 等不到 200 就会重试 —— 不去重的话同一笔购买会推两次。见过的 UUID
     直接回 200，不再推。
  4. 生产与沙盒**分成两个路径**，各自一个 verifier。SignedDataVerifier 会校验
     payload 里的 environment 与自己构造时的是否一致，混在一个路径上必然有一边报错。
  5. 路径带一段不可猜的 token，把扫描器挡在 Python 之外（nginx 层就 404）。
     真正的防线是验签，token 只是省掉噪音。
  6. 存储用 sqlite，**一个文件**同时承担流水、去重、待推送队列。早先的
     「只追加 jsonl + spool 目录」做不了前两件事：去重要另建索引，按时间清理要
     原地重写文件，而重写会跟多个 gunicorn worker 抢写。sqlite 一次全解决。
"""

import hmac
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier, VerificationException

# 在**模块导入时**配好，不能只在 main() 里配：gunicorn 直接 import application，
# 那条路径不经过 main()。不配的话 logging 会退到 lastResort（只输出 WARNING 以上），
# 于是"收到一条真实购买"这种 INFO 会被静默丢掉，journalctl 里什么都看不到。
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("asn")

# ---------------------------------------------------------------- 配置

def _load_env_file(path="/etc/mememo-asn.env"):
    """systemd 通过 EnvironmentFile= 注入，这里是给手工跑 drain/heartbeat/selftest 用的。
    已经在环境里的变量优先，不覆盖。"""
    f = Path(os.environ.get("ASN_ENV_FILE", path))
    if not f.exists():
        return
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env_file()


def _env(name, default=None, required=False):
    v = os.environ.get(name, default)
    if required and not v:
        raise SystemExit(f"缺少环境变量 {name}（见 /etc/mememo-asn.env）")
    return v


BUNDLE_ID     = _env("ASN_BUNDLE_ID", "com.aaronyu.mememo")
APP_APPLE_ID  = int(_env("ASN_APP_APPLE_ID", "6760353728"))
PATH_TOKEN    = _env("ASN_PATH_TOKEN", required=True)
CERTS_DIR     = Path(_env("ASN_CERTS_DIR", "/opt/mememo-asn/certs"))
DATA_DIR      = Path(_env("ASN_DATA_DIR", "/var/lib/mememo-asn"))
BARK_BASE     = _env("ASN_BARK_BASE", "https://api.day.app").rstrip("/")
def _bark_key(raw):
    """Bark App 里给的是整条测试 URL，不是裸 key。与其让人手工截取（`l`/`1`、`O`/`0`
    抄错一个就静默失败），不如两种形态都收下：
        EXAMPLEkeyNOTreal1234
        https://api.day.app/EXAMPLEkeyNOTreal1234/这里改成你自己的推送内容
    """
    raw = (raw or "").strip()
    if "/" not in raw:
        return raw
    tail = raw.split("://", 1)[-1]                  # 去掉 scheme
    parts = [p for p in tail.split("/") if p]
    return parts[1] if len(parts) > 1 and "." in parts[0] else parts[0]


BARK_KEY      = _bark_key(_env("ASN_BARK_KEY", ""))
# 在线吊销检查（OCSP）默认关：这台机器在国内，OCSP 抖一下就会把**真实购买通知**
# 判成验签失败丢掉；而它防的是"Apple 叶子证书被盗且已吊销"——对一条私人购买提醒
# 来说，可用性风险远大于那个。离线链校验（签名 + 有效期 + 链到 Apple 根）照做。
ONLINE_CHECKS = _env("ASN_ONLINE_CHECKS", "0") == "1"

DB_PATH        = DATA_DIR / "notifications.db"
# 保留期。对账用不到更久，而留着的是交易号/金额/地区这类数据 —— 没有理由永久存。
RETENTION_DAYS = int(_env("ASN_RETENTION_DAYS", "90"))

# 我们关心的通知类型。用字符串比而不是枚举成员，是为了库里还没有的新类型不会 AttributeError。
ALERT_TYPES = {"ONE_TIME_CHARGE", "REFUND", "REFUND_REVERSED", "REVOKE", "CONSUMPTION_REQUEST"}


def _root_certificates():
    certs = sorted(CERTS_DIR.glob("*.cer"))
    if not certs:
        raise SystemExit(f"{CERTS_DIR} 里没有根证书（从 apple.com/certificateauthority 取 AppleRootCA-G3.cer）")
    return [p.read_bytes() for p in certs]


_VERIFIERS = {}

def verifier_for(env_name):
    """env_name: 'prod' | 'sandbox'"""
    if env_name not in _VERIFIERS:
        environment = Environment.PRODUCTION if env_name == "prod" else Environment.SANDBOX
        _VERIFIERS[env_name] = SignedDataVerifier(
            _root_certificates(), ONLINE_CHECKS, environment, BUNDLE_ID,
            APP_APPLE_ID if env_name == "prod" else None,
        )
    return _VERIFIERS[env_name]


def _s(v):
    """枚举 -> 字符串；已经是字符串/None 就原样返回。"""
    return getattr(v, "value", v)


# ---------------------------------------------------------------- 存储

SCHEMA = """
CREATE TABLE IF NOT EXISTS notifications (
    uuid        TEXT PRIMARY KEY,          -- notificationUUID，去重就靠它
    received_at INTEGER NOT NULL,
    endpoint    TEXT    NOT NULL,          -- prod | sandbox
    kind        TEXT,                      -- notificationType
    subtype     TEXT,
    environment TEXT,
    payload     TEXT    NOT NULL,          -- 完整记录的 JSON
    pushed_at   INTEGER                    -- NULL = 还没推成功
);
CREATE INDEX IF NOT EXISTS idx_pending  ON notifications(pushed_at);
CREATE INDEX IF NOT EXISTS idx_received ON notifications(received_at);
"""


def db():
    """每次调用开一个连接。WAL + busy_timeout 是为了多个 gunicorn worker 并发写
    不会 'database is locked'；synchronous=FULL 保证回 200 时数据真的落到磁盘了 ——
    这条端点的全部承诺就建立在这个 fsync 上。"""
    import sqlite3
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA busy_timeout=15000")
    conn.executescript(SCHEMA)
    return conn


def store(record):
    """写入一条。返回 True=新的，False=之前见过（Apple 重试）。写失败往上抛。"""
    with db() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO notifications"
            " (uuid, received_at, endpoint, kind, subtype, environment, payload)"
            " VALUES (?,?,?,?,?,?,?)",
            (record["id"], record["received_at"], record["endpoint"],
             record["notification_type"], record["subtype"], record["environment"],
             json.dumps(record, ensure_ascii=False, sort_keys=True)),
        )
        return cur.rowcount == 1


def mark_pushed(uuid_):
    with db() as conn:
        conn.execute("UPDATE notifications SET pushed_at=? WHERE uuid=?", (int(time.time()), uuid_))


def pending():
    with db() as conn:
        return [json.loads(r["payload"]) for r in
                conn.execute("SELECT payload FROM notifications WHERE pushed_at IS NULL"
                             " ORDER BY received_at")]


def recent(seconds):
    cutoff = int(time.time()) - seconds
    with db() as conn:
        return [json.loads(r["payload"]) for r in
                conn.execute("SELECT payload FROM notifications WHERE received_at >= ?"
                             " ORDER BY received_at", (cutoff,))]


def purge():
    """清掉过了保留期的记录。**只清已推送的** —— 没推出去的留着，它会一直出现在
    drain 里，那本身就是个看得见的信号；悄悄删掉才是坏事。"""
    cutoff = int(time.time()) - RETENTION_DAYS * 86400
    with db() as conn:
        n = conn.execute("DELETE FROM notifications WHERE received_at < ?"
                         " AND pushed_at IS NOT NULL", (cutoff,)).rowcount
    if n:
        log.info("清掉 %d 条超过 %d 天的记录", n, RETENTION_DAYS)
    return n


# ---------------------------------------------------------------- 推送

def push_bark(title, body, level="timeSensitive"):
    """成功返回 True。任何失败都只记日志、不抛 —— 调用方靠 drain 补推，不靠异常。"""
    if not BARK_KEY:
        log.warning("未配置 ASN_BARK_KEY，跳过推送：%s / %s", title, body)
        return False
    import requests
    try:
        r = requests.post(
            f"{BARK_BASE}/push",
            json={
                "device_key": BARK_KEY,
                "title": title,
                "body": body,
                "group": "MeMemo",
                "level": level,
                "sound": "cashregister",
            },
            timeout=8,
        )
        ok = r.status_code == 200 and r.json().get("code") == 200
        if not ok:
            log.error("Bark 推送失败 %s %s", r.status_code, r.text[:300])
        return ok
    except Exception as e:                                   # noqa: BLE001
        log.error("Bark 推送异常：%s", e)
        return False


def describe(record):
    """把一条通知变成人看的标题和正文。"""
    ntype = record.get("notification_type")
    sub   = record.get("subtype")
    tx    = record.get("transaction") or {}
    env   = record.get("environment", "")
    tag   = "" if env == "Production" else f"[{env}] "

    price, currency = tx.get("price"), tx.get("currency")
    money = f"{price / 1000:.2f} {currency}" if isinstance(price, int) and currency else "金额未提供"
    where = tx.get("storefront") or "?"
    product = tx.get("productId") or "?"

    if ntype == "ONE_TIME_CHARGE":
        family = "（家庭共享）" if tx.get("inAppOwnershipType") == "FAMILY_SHARED" else ""
        return f"{tag}💰 有人买断了{family}", f"{money} · {where} · {product}"
    if ntype == "REFUND":
        return f"{tag}↩️ 退款", f"{money} · {where} · {product}"
    if ntype == "TEST":
        return f"{tag}✅ 管线正常", "Apple 的测试通知已送达并验签通过"
    return f"{tag}ℹ️ {ntype}", f"{sub or ''} · {product}".strip(" ·")


def deliver(record):
    """推送成功就记 pushed_at；失败就留着 pushed_at=NULL，交给 drain 补。

    ⚠️ **这个函数绝不抛异常**，这一点是刻意的。调用方有两个：WSGI 请求路径和
    drain。它要是抛了：
      - WSGI 那边回 500 -> Apple 重试 -> 第二次被去重挡下回 200 -> **提醒永远发不出**
      - drain 那边整个循环挂掉 -> 后面排队的也一起卡住
    而最可能抛的地方恰恰是 describe()：真实交易第一次流经这里时，字段形态可能
    跟合成测试数据不一样。宁可推一条粗糙的，也不能因为文案渲染失败就不推。
    """
    try:
        title, body = describe(record)
    except Exception as e:                                   # noqa: BLE001
        log.exception("文案渲染失败，退回最简形态：%s", e)
        title = "💰 有购买或退款事件"
        body = f"{record.get('notification_type') or '?'} · 文案渲染失败，详情看 asn.py tail"
    try:
        if push_bark(title, body):
            mark_pushed(record["id"])
            return True
    except Exception as e:                                   # noqa: BLE001
        log.exception("推送环节异常：%s", e)
    return False


# ---------------------------------------------------------------- 解码

def decode(signed_payload, env_name):
    """验签并摊平成一条可 JSON 序列化的记录。验签失败抛 VerificationException。"""
    v = verifier_for(env_name)
    p = v.verify_and_decode_notification(signed_payload)
    data = p.data

    record = {
        "id": p.notificationUUID or str(uuid.uuid4()),
        "received_at": int(time.time()),
        "endpoint": env_name,
        "notification_type": _s(p.notificationType) or getattr(p, "rawNotificationType", None),
        "subtype": _s(p.subtype) or getattr(p, "rawSubtype", None),
        "signed_date": p.signedDate,
        "environment": _s(getattr(data, "environment", None)) if data else None,
        "bundle_id": getattr(data, "bundleId", None) if data else None,
    }

    signed_tx = getattr(data, "signedTransactionInfo", None) if data else None
    if signed_tx:
        try:
            t = v.verify_and_decode_signed_transaction(signed_tx)
            record["transaction"] = {
                "transactionId": t.transactionId,
                "originalTransactionId": t.originalTransactionId,
                "productId": t.productId,
                "purchaseDate": t.purchaseDate,
                "quantity": t.quantity,
                "type": _s(t.type),
                "inAppOwnershipType": _s(t.inAppOwnershipType),
                "storefront": t.storefront,
                "price": t.price,
                "currency": t.currency,
                "revocationDate": t.revocationDate,
                "revocationReason": _s(t.revocationReason),
            }
        except Exception as e:                               # noqa: BLE001
            # 交易信息解不开不该丢掉整条通知 —— 类型和 UUID 已经够发提醒了。
            log.error("交易信息解码失败（通知本身已验签通过）：%s", e)
            record["transaction_error"] = str(e)

    return record


# ---------------------------------------------------------------- WSGI

def _reply(start_response, status, text=""):
    body = text.encode()
    start_response(status, [("Content-Type", "text/plain; charset=utf-8"),
                            ("Content-Length", str(len(body)))])
    return [body]


def application(environ, start_response):
    path = environ.get("PATH_INFO", "")
    parts = [p for p in path.split("/") if p]

    # 期望 /asn/<token>/{prod,sandbox}。nginx 已经按 token 收窄过一次，
    # 这里再比一次是防配置漂移，用 compare_digest 避免计时侧信道。
    if len(parts) != 3 or parts[0] != "asn" or parts[2] not in ("prod", "sandbox") \
            or not hmac.compare_digest(parts[1], PATH_TOKEN):
        return _reply(start_response, "404 Not Found")

    if environ.get("REQUEST_METHOD") != "POST":
        return _reply(start_response, "405 Method Not Allowed")

    env_name = parts[2]

    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        return _reply(start_response, "400 Bad Request", "bad content-length")
    if length <= 0 or length > 1_048_576:
        return _reply(start_response, "400 Bad Request", "bad length")

    try:
        signed = json.loads(environ["wsgi.input"].read(length))["signedPayload"]
    except Exception:                                        # noqa: BLE001
        return _reply(start_response, "400 Bad Request", "expected {\"signedPayload\": \"...\"}")

    try:
        record = decode(signed, env_name)
    except VerificationException as e:
        # 不是 Apple 发的（或链坏了）。回 400 而不是 5xx：让 Apple 重试没有意义。
        log.warning("[%s] 验签失败：%s", env_name, e)
        return _reply(start_response, "400 Bad Request", "verification failed")
    except Exception as e:                                   # noqa: BLE001
        log.exception("[%s] 解码异常：%s", env_name, e)
        return _reply(start_response, "400 Bad Request", "decode failed")

    try:
        is_new = store(record)
    except Exception as e:                                   # noqa: BLE001
        # 唯一该让 Apple 重试的分支：我们没能接管这条通知。
        log.exception("落盘失败，回 500 让 Apple 重试：%s", e)
        return _reply(start_response, "500 Internal Server Error", "persist failed")

    if not is_new:
        # Apple 的重试。八成是因为我们上一次回 200 回慢了（推 Bark 最多 8 秒）。
        # 已经收下了，也已经提醒过了，直接确认，别再推一遍。
        log.info("[%s] 重复通知，已忽略 uuid=%s", env_name, record["id"])
        return _reply(start_response, "200 OK", "ok (duplicate)")

    log.info("[%s] %s %s tx=%s", env_name, record["notification_type"], record.get("subtype") or "",
             (record.get("transaction") or {}).get("transactionId"))

    if record["notification_type"] in ALERT_TYPES or record["notification_type"] == "TEST":
        deliver(record)          # 失败不影响回 200 —— 库里 pushed_at 还是 NULL，drain 会补

    return _reply(start_response, "200 OK", "ok")


# ---------------------------------------------------------------- 补推与清理

def drain():
    """补推没推成功的，顺便清过期。systemd timer 每 5 分钟跑一次。"""
    sent = failed = 0
    for record in pending():
        if deliver(record):
            sent += 1
        else:
            failed += 1
    if sent or failed:
        log.info("补推完成：成功 %d，仍失败 %d", sent, failed)
    purge()
    return failed


# ---------------------------------------------------------------- 心跳

def heartbeat():
    """让 Apple 主动发一条 TEST 通知，端到端验证整条管线还活着。

    沉默是有歧义的：没有购买通知 = 没人买 **或** 端点挂了，两者外观相同。
    这条心跳就是把歧义消掉的东西 —— 每周收到一条 ✅ 就说明管线通。
    不做它，这套东西迟早会在你不知道的时候死掉。
    """
    from appstoreserverlibrary.api_client import AppStoreServerAPIClient, APIException

    key_path  = _env("ASN_IAP_KEY_PATH", required=True)
    key_id    = _env("ASN_IAP_KEY_ID", required=True)
    issuer_id = _env("ASN_IAP_ISSUER_ID", required=True)

    client = AppStoreServerAPIClient(
        Path(key_path).read_bytes(), key_id, issuer_id, BUNDLE_ID, Environment.PRODUCTION,
    )

    try:
        token = client.request_test_notification().testNotificationToken
    except APIException as e:
        log.error("请求测试通知失败：%s", e)
        push_bark("⚠️ 购买提醒管线异常", f"连 Apple 的测试通知都请求不到：{e}", level="active")
        return 1
    log.info("已请求测试通知 token=%s", token)

    # Apple 侧的投递结果（权威）：它认为自己有没有送到、我们回了什么。
    verdict = None
    for _ in range(12):                       # 最多等 ~2 分钟
        time.sleep(10)
        try:
            status = client.get_test_notification_status(token)
        except APIException:
            continue                          # 通知还没投递时 Apple 会报 404，继续等
        attempts = status.sendAttempts or []
        if attempts:
            verdict = _s(attempts[-1].sendAttemptResult)
            if verdict == "SUCCESS":
                break

    # 我们自己这侧（补充）：验签过了、落盘了吗。Apple 说送到、我们却没记，
    # 说明 200 是 nginx 或别的东西回的，不是这个服务。
    ours = [r for r in recent(300) if r.get("notification_type") == "TEST"]

    if verdict == "SUCCESS" and ours:
        log.info("心跳正常：Apple 已投递且本机已验签落盘")
        return 0

    detail = f"Apple 投递结果={verdict or '超时未出结果'}；本机收到 TEST={'是' if ours else '否'}"
    log.error("心跳失败：%s", detail)
    push_bark("⚠️ 购买提醒管线异常", detail, level="active")
    return 1


# ---------------------------------------------------------------- 入口

def _warn_if_wrong_user():
    """以 root 跑 CLI 会在库旁边留下 root 属主的 -wal/-shm 文件，之后服务（以
    mememo-asn 身份跑）就写不进去了 —— 而且是**静默**失败：端点照收、验签照过，
    只是写不下去。用 `sudo -u mememo-asn` 跑。"""
    try:
        if os.geteuid() == 0 and DB_PATH.exists() and DB_PATH.stat().st_uid != 0:
            import pwd
            owner = pwd.getpwuid(DB_PATH.stat().st_uid).pw_name
            log.warning("你在用 root 跑，但数据库属于 %s。改用："
                        " sudo -u %s venv/bin/python asn.py ...", owner, owner)
    except Exception:                                        # noqa: BLE001
        pass


def main():
    _warn_if_wrong_user()
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "drain":
        return 0 if drain() == 0 else 1
    if cmd == "heartbeat":
        return heartbeat()
    if cmd == "verify-order":
        # 用一笔**真实**订单验证交易解码路径 —— 这是心跳验不到的那一段。
        # TEST 通知里没有交易信息，所以 verify_and_decode_signed_transaction
        # 和那 12 个字段的读取，在真实数据上一次都没跑过。
        # 订单号在 Apple 的购买收据邮件里（形如 MLxxxxxxxx）。
        # 只打印不推送。
        from appstoreserverlibrary.api_client import AppStoreServerAPIClient, APIException
        if len(sys.argv) < 3:
            print("用法：asn.py verify-order <订单号>  （Apple 购买收据邮件里那个）")
            return 2
        client = AppStoreServerAPIClient(
            Path(_env("ASN_IAP_KEY_PATH", required=True)).read_bytes(),
            _env("ASN_IAP_KEY_ID", required=True), _env("ASN_IAP_ISSUER_ID", required=True),
            BUNDLE_ID, Environment.PRODUCTION,
        )
        try:
            txs = client.look_up_order_id(sys.argv[2]).signedTransactions or []
        except APIException as e:
            print(f"❌ 查不到这个订单：{e}")
            return 1
        if not txs:
            print("查到了订单，但里面没有交易（可能不是本 App 的订单）")
            return 1
        v = verifier_for("prod")
        for i, signed in enumerate(txs, 1):
            t = v.verify_and_decode_signed_transaction(signed)   # ← 待验的那一步
            fake = {"id": f"verify-{i}", "received_at": int(time.time()), "endpoint": "prod",
                    "notification_type": "ONE_TIME_CHARGE", "subtype": None,
                    "environment": "Production",
                    "transaction": {"productId": t.productId, "transactionId": t.transactionId,
                                    "price": t.price, "currency": t.currency,
                                    "storefront": t.storefront,
                                    "inAppOwnershipType": _s(t.inAppOwnershipType)}}
            title, body = describe(fake)
            print(f"[{i}/{len(txs)}] 验签通过 ✅")
            print(f"      真实购买时收到的提醒会长这样：")
            print(f"      {title}")
            print(f"      {body}")
        return 0
    if cmd == "testpush":
        # 单独验证 Bark 这一条腿，不牵扯 Apple。管线是两段：
        # Apple -> 我们（验签落盘） 和 我们 -> Bark（推送）。
        # 出问题时能分别测，比整条一起猜快得多。
        ok = push_bark("🔔 测试推送", "如果你看到这条，说明 Bark 这一段是通的", level="active")
        print("✅ 推送成功，去看手机" if ok else "❌ 推送失败，看上面的日志")
        return 0 if ok else 1
    if cmd == "tail":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        with db() as conn:
            rows = conn.execute("SELECT * FROM notifications ORDER BY received_at DESC LIMIT ?",
                                (n,)).fetchall()
        if not rows:
            print("（还没收到过任何通知）")
        for r in reversed(rows):
            when = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["received_at"]))
            tx = (json.loads(r["payload"]).get("transaction") or {})
            state = "已推送" if r["pushed_at"] else "⚠️ 未推送"
            print(f"{when}  {r['endpoint']:<7} {r['kind'] or '?':<20} {state:<8} "
                  f"{tx.get('productId') or ''} {tx.get('transactionId') or ''}")
        return 0
    if cmd == "selftest":
        # 不碰网络：只证明配置读得到、根证书装得上、verifier 造得出来。
        for e in ("prod", "sandbox"):
            verifier_for(e)
        print(f"OK  bundle={BUNDLE_ID} appAppleId={APP_APPLE_ID} "
              f"根证书={len(_root_certificates())} 张 在线吊销检查={'开' if ONLINE_CHECKS else '关'} "
              f"Bark={'已配' if BARK_KEY else '未配'}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
