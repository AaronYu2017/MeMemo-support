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

shutil.rmtree(TMP, ignore_errors=True)
print()
if FAILED:
    print(f"❌ {len(FAILED)} 项未通过：" + "；".join(FAILED))
    sys.exit(1)
print("✅ 全部通过")
