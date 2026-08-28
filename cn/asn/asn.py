#!/usr/bin/env python3
"""App Store Server Notifications V2 接收端 —— 有人买断/退款时几秒内推到 Bark。

为什么存在：App Store Connect 的销售报告最快也有约 10 小时延迟，而那个延迟在
Apple 的**报表管线**里，任何 API 轮询都继承同样的延迟。Server Notifications 走的是
交易事件管线，是 Apple 唯一的实时通路。2026-06 曾因「改价后连续 3 天零付费」动用
代码审查 + ASC 核查 + 借真机三重验证才排除虚惊 —— 一条活着的通知管线几秒就能回答。

三个入口，同一个文件：
  application            WSGI 可调用对象，gunicorn 跑它（接收 + 验签 + 落盘 + 推送）
  python3 asn.py drain   把没推成功的补推一遍（systemd timer 每 5 分钟）
  python3 asn.py heartbeat  主动让 Apple 发一条 TEST 通知，验证整条管线活着

设计要点（都是有代价换来的，改之前先读）：
  1. **先落盘再回 200，推送失败不影响回 200。** 反过来做的话，推送一失败 Apple 就
     不再重试，那条购买永久丢失。落盘成功即视为我们已接管，Bark 随时可以补发。
  2. 落盘失败才回 500 —— 那是唯一该让 Apple 重试的情况。
  3. 生产与沙盒**分成两个路径**，各自一个 verifier。SignedDataVerifier 会校验
     payload 里的 environment 与自己构造时的是否一致，混在一个路径上必然有一边报错。
  4. 路径带一段不可猜的 token，把扫描器挡在 Python 之外（nginx 层就 404）。
     真正的防线是验签，token 只是省掉噪音。
"""

import base64
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
BARK_KEY      = _env("ASN_BARK_KEY", "")
# 在线吊销检查（OCSP）默认关：这台机器在国内，OCSP 抖一下就会把**真实购买通知**
# 判成验签失败丢掉；而它防的是"Apple 叶子证书被盗且已吊销"——对一条私人购买提醒
# 来说，可用性风险远大于那个。离线链校验（签名 + 有效期 + 链到 Apple 根）照做。
ONLINE_CHECKS = _env("ASN_ONLINE_CHECKS", "0") == "1"

SPOOL_DIR = DATA_DIR / "spool"
LEDGER    = DATA_DIR / "notifications.jsonl"

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


# ---------------------------------------------------------------- 落盘

def _fsync_write(path, data):
    """写完 fsync 再原子改名 —— 断电/OOM 时不会留下半条记录。"""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    dirfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)


def persist(record):
    """写 spool（待推送）+ 追加 ledger（永久流水）。任一失败都往上抛。"""
    SPOOL_DIR.mkdir(parents=True, exist_ok=True)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(record, ensure_ascii=False, sort_keys=True).encode()

    _fsync_write(SPOOL_DIR / f"{record['received_at']}-{record['id']}.json", blob)

    with open(LEDGER, "ab") as f:
        f.write(blob + b"\n")
        f.flush()
        os.fsync(f.fileno())


# ---------------------------------------------------------------- 推送

def push_bark(title, body, level="timeSensitive"):
    """成功返回 True。任何失败都只记日志、不抛 —— 调用方靠 spool 补推，不靠异常。"""
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
    """推送成功就删掉 spool 文件；失败留着，交给 drain。"""
    title, body = describe(record)
    if push_bark(title, body):
        for p in SPOOL_DIR.glob(f"*-{record['id']}.json"):
            p.unlink(missing_ok=True)
        return True
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
        persist(record)
    except Exception as e:                                   # noqa: BLE001
        # 唯一该让 Apple 重试的分支：我们没能接管这条通知。
        log.exception("落盘失败，回 500 让 Apple 重试：%s", e)
        return _reply(start_response, "500 Internal Server Error", "persist failed")

    log.info("[%s] %s %s tx=%s", env_name, record["notification_type"], record.get("subtype") or "",
             (record.get("transaction") or {}).get("transactionId"))

    if record["notification_type"] in ALERT_TYPES or record["notification_type"] == "TEST":
        deliver(record)          # 失败不影响回 200 —— spool 里还留着，drain 会补

    return _reply(start_response, "200 OK", "ok")


# ---------------------------------------------------------------- 补推

def drain():
    """把 spool 里没推成功的补推一遍。systemd timer 每 5 分钟跑一次。"""
    if not SPOOL_DIR.exists():
        return 0
    sent = failed = 0
    for p in sorted(SPOOL_DIR.glob("*.json")):
        try:
            record = json.loads(p.read_text())
        except Exception as e:                               # noqa: BLE001
            log.error("spool 文件坏了，跳过 %s：%s", p.name, e)
            continue
        if deliver(record):
            sent += 1
        else:
            failed += 1
    if sent or failed:
        log.info("补推完成：成功 %d，仍失败 %d", sent, failed)
    return failed


# ---------------------------------------------------------------- 心跳

def _recent_ledger(seconds):
    """读流水尾部，返回最近 N 秒内的记录。"""
    if not LEDGER.exists():
        return []
    cutoff = time.time() - seconds
    out = []
    with open(LEDGER, "rb") as f:
        # 只读尾部 256KB，流水再长也不用整file读进来
        try:
            f.seek(-262_144, os.SEEK_END)
            f.readline()
        except OSError:
            f.seek(0)
        for line in f:
            try:
                r = json.loads(line)
            except Exception:                                # noqa: BLE001
                continue
            if r.get("received_at", 0) >= cutoff:
                out.append(r)
    return out


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
    ours = [r for r in _recent_ledger(300) if r.get("notification_type") == "TEST"]

    if verdict == "SUCCESS" and ours:
        log.info("心跳正常：Apple 已投递且本机已验签落盘")
        return 0

    detail = f"Apple 投递结果={verdict or '超时未出结果'}；本机收到 TEST={'是' if ours else '否'}"
    log.error("心跳失败：%s", detail)
    push_bark("⚠️ 购买提醒管线异常", detail, level="active")
    return 1


# ---------------------------------------------------------------- 入口

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "drain":
        return 0 if drain() == 0 else 1
    if cmd == "heartbeat":
        return heartbeat()
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
