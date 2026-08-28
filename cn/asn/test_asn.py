#!/usr/bin/env python3
"""存储层的回归测试。在服务器上跑：

    cd /opt/mememo-asn && venv/bin/python test_asn.py

不碰网络、不碰真实数据库（用临时目录），跑完自己清理。

**这些不变量都是有代价换来的，别在不理解的情况下改绿它**：
  - 同一个 notificationUUID 只算一次（Apple 重试时不能重复推送）
  - 不同 UUID 必须都算新的（否则去重就成了"全都吞掉"，比不去重更糟）
  - purge 只清已推送的（没推出去的留着，它是看得见的信号）
"""

import json
import os
import shutil
import sys
import tempfile
import time

TMP = tempfile.mkdtemp(prefix="asn-test-")
os.environ.update({
    "ASN_DATA_DIR": TMP,
    "ASN_PATH_TOKEN": "test-token-not-a-real-one",
    "ASN_BARK_KEY": "",                     # 确保测试不会真的发推送
    "ASN_RETENTION_DAYS": "90",
    "ASN_ENV_FILE": "/nonexistent",         # 别读服务器上的真配置
})
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asn                                                   # noqa: E402

FAILED = []


def check(cond, what):
    if cond:
        print(f"  ✓ {what}")
    else:
        print(f"  ✗ {what}")
        FAILED.append(what)


def rec(uuid_, kind="ONE_TIME_CHARGE", at=None):
    return {
        "id": uuid_, "received_at": at or int(time.time()), "endpoint": "prod",
        "notification_type": kind, "subtype": None, "environment": "Production",
        "transaction": {"productId": "mememo.pro", "transactionId": "tx-" + uuid_},
    }


print("去重")
check(asn.store(rec("A")) is True,  "第一次收到 A：算新的")
check(asn.store(rec("A")) is False, "再收到 A：认出是重复")          # ← 核心不变量
check(asn.store(rec("B")) is True,  "收到 B：不同 UUID 仍算新的")    # ← 证明不是"全都吞"

print("待推送队列")
check(len(asn.pending()) == 2, "两条都还没推，都在队列里")
asn.mark_pushed("A")
p = asn.pending()
check(len(p) == 1 and p[0]["id"] == "B", "标记 A 已推后，队列里只剩 B")

print("保留期")
old = int(time.time()) - 100 * 86400          # 100 天前，超过 90 天保留期
asn.store(rec("OLD_PUSHED", at=old)); asn.mark_pushed("OLD_PUSHED")
asn.store(rec("OLD_PENDING", at=old))
n = asn.purge()
ids = {r["id"] for r in asn.recent(200 * 86400)}
check(n == 1, "清掉 1 条（只有已推送的那条过期记录）")
check("OLD_PUSHED" not in ids,  "过期且已推送的：清掉了")
check("OLD_PENDING" in ids,     "过期但没推出去的：留着（它是信号，不能悄悄删）")
check("A" in ids and "B" in ids, "没过期的：一条没动")

print("时间窗")
check(len(asn.recent(300)) == 2, "recent(5分钟) 只看到 A 和 B，看不到 100 天前那两条")

print("展示层")
t, b = asn.describe(rec("C"))
check("买断" in t and "mememo.pro" in b, f"买断通知的文案：{t} / {b}")
t, _ = asn.describe(rec("D", kind="REFUND"))
check("退款" in t, f"退款通知的文案：{t}")
t, _ = asn.describe({**rec("E"), "environment": "Sandbox"})
check(t.startswith("[Sandbox]"), f"沙盒通知带环境前缀：{t}")

print("坏数据不能吃掉提醒")
# 真实交易第一次流经 describe() 时，字段形态可能跟合成数据不一样。deliver() 要是
# 因此抛异常：WSGI 那边回 500 -> Apple 重试 -> 被去重挡下 -> **提醒永远发不出**；
# drain 那边整个循环挂掉。所以 deliver() 必须是全函数（total），坏数据也得推出去。
_pushed = []
_orig_push = asn.push_bark
asn.push_bark = lambda t, b, level="timeSensitive": (_pushed.append((t, b)), True)[1]
try:
    broken = rec("BROKEN")
    broken["transaction"] = "这不是个 dict"        # 让 describe() 里的 tx.get 炸掉
    asn.store(broken)
    raised = None
    try:
        ok = asn.deliver(broken)
    except Exception as e:                                   # noqa: BLE001
        raised = e
    check(raised is None, f"describe 炸了也不往外抛（实际：{raised!r}）")
    check(_pushed and "购买或退款" in _pushed[-1][0], "退回了最简文案，提醒仍然发出去了")
    check(not asn.pending() or all(r["id"] != "BROKEN" for r in asn.pending()),
          "推成功后仍然正确标记了已推送")
finally:
    asn.push_bark = _orig_push

print("代码里不能出现真实密钥")
# 2026-08-28 真的泄漏过一次：我把 Aaron 的 Bark device key 当成 docstring 里的
# 示例和测试常量写进了代码，而 MeMemo-support 是**公开**仓库。
# 教训不是"下次注意"——是拿真值当示例这件事本身太自然了，必须自动查。
_here = os.path.dirname(os.path.abspath(__file__))
_real_env = "/etc/mememo-asn.env"
_secrets = []
if os.path.exists(_real_env):
    for line in open(_real_env, encoding="utf-8"):
        k, _, v = line.strip().partition("=")
        if k in ("ASN_BARK_KEY", "ASN_PATH_TOKEN") and len(v) >= 12:
            # Bark 那个可能是整条 URL，取出 key 再比
            _secrets.append((k, asn._bark_key(v) if k == "ASN_BARK_KEY" else v))
if not _secrets:
    print("  · 跳过（这台机器上没有 /etc/mememo-asn.env，无真值可比）")
for _name, _val in _secrets:
    _leaked = []
    for _f in sorted(os.listdir(_here)):
        _fp = os.path.join(_here, _f)
        if not os.path.isfile(_fp) or _f == "asn.env":      # asn.env 本就该有，且已 gitignore
            continue
        try:
            if _val in open(_fp, encoding="utf-8", errors="ignore").read():
                _leaked.append(_f)
        except OSError:
            pass
    check(not _leaked, f"{_name} 的真实值没出现在代码里" + (f"（泄漏在：{', '.join(_leaked)}）" if _leaked else ""))

print("Bark key 归一化")
K = "EXAMPLEkeyNOTreal1234"
for raw, what in [
    (K,                                        "裸 key"),
    (f"https://api.day.app/{K}",               "URL 无路径"),
    (f"https://api.day.app/{K}/这里改成你自己的推送内容", "Bark 里复制的整条测试 URL"),
    (f"https://api.day.app/{K}/标题/正文?sound=minuet", "带标题正文和参数的 URL"),
    (f"  {K}  ",                               "前后有空格"),
]:
    check(asn._bark_key(raw) == K, f"{what} -> 取出 key")
check(asn._bark_key("") == "", "空值仍是空值（未配置时要能识别）")

print("shell 脚本：变量名后面不能紧跟多字节字符")
# macOS 自带的 bash 3.2 在 **UTF-8 locale** 下，会把多字节字符的第一个字节吞进
# 变量名：`echo "$what（$got）"` 变成去找一个叫 what\xef 的变量，set -u 下直接
# 报 unbound variable，脚本当场死。
#
# 这个坑 2026-08-28 真的炸过一次（deploy-asn.sh 的端到端检查）。之所以必须自动查：
# **开发机的 locale 是 C，测不出来；Aaron 的 Terminal 是 en_US.UTF-8，必炸。**
# 靠"记得加花括号"是靠不住的，因为写的人看不到失败。
import re
_multibyte_after_var = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])")
for sh in sorted(f for f in os.listdir(_here) if f.endswith(".sh")):
    body = open(os.path.join(_here, sh), encoding="utf-8").read()
    bad = [f"行{body[:m.start()].count(chr(10))+1} {m.group(0)}"
           for m in _multibyte_after_var.finditer(body)]
    check(not bad, f"{sh} 里没有 $var 紧跟多字节字符" + (f"（发现：{'; '.join(bad)}，改成 ${{var}}）" if bad else ""))

shutil.rmtree(TMP, ignore_errors=True)
print()
if FAILED:
    print(f"❌ {len(FAILED)} 项未通过：" + "；".join(FAILED))
    sys.exit(1)
print("✅ 全部通过")
