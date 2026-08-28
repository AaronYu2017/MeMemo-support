# 购买实时提醒（App Store Server Notifications V2）

有人买断或退款时，几秒内推一条 Bark 到 Aaron 手机上。

## 为什么存在

App Store Connect 的销售报告**最快也有约 10 小时延迟**（网页版「24 小时内」报告已是最快的一档，
ASC 官方 iOS App 更慢且不推送）。而那 10 小时的延迟在 Apple 的**报表管线**里 ——
任何 API 轮询读的都是同一条管线、继承同样的延迟，**轮询救不了**。

Server Notifications 走的是另一条管线（交易事件驱动，不是报表），是 Apple 唯一的实时通路。

比"即时快感"更硬的理由：改价之后，"没有新订单"到底是市场反应还是内购链路坏了，
凭报表要等到第二天才有第一手信号，排查一次要动用代码审查 + ASC 核查 + 借真机实测。
**一条活着的通知管线能在几秒内回答那个问题。**

零客户端代码 —— App 一行不改、不新增任何网络请求、**不动隐私政策**。这是它压倒其他方案的理由
（"App 内购买成功后自己上报"要往自己服务器发购买事件，跟"数据只在你的设备和私人 iCloud"的
产品身份直接冲突）。

## 放在哪，为什么

跑在 **47.116.184.7**（于马科技，锚着 `沪ICP备2026035044号-2` 网站备案 + 安卓 App 备案），
挂在已备案的 `www.mememo.com.cn` 下的**一个路径**，刻意不新开子域名 —— 新子域名要动备案。

另一台 `47.103.38.30`（Aaron 个人，锚 iOS App 备案）不行：它的域名 `yuxingbin.com` 无 DNS 解析，
在大陆 ECS 上用未备案域名提供 80/443 会被接入商拦。

主体不一致不是问题：内购在个人 Apple 账号下、服务器是公司主体，但这只是个接收 webhook 的
HTTPS 端点，不是面向用户的服务。也不触碰号-2 向管局承诺的「禁 UGC 与站内交易」——
交易发生在 App Store，这里只接收通知。

## 结构

| 文件 | 作用 |
|---|---|
| `asn.py` | 全部逻辑。`application` 是 WSGI 入口；`drain` / `heartbeat` / `selftest` 是子命令 |
| `requirements.txt` | 固定版本。这台机器不能"某天自动升级把它升坏了" |
| `asn.env.example` | 配置模板。真实值放 `asn.env`（**不进 git，本仓库公开**） |
| `systemd/` | 服务 + 补推 timer（5 分钟）+ 心跳 timer（每周一 10:00） |
| `nginx/asn.conf.template` | 端点的 location 片段，token 部署时填入 |
| `deploy-asn.sh` | 一键部署，幂等，失败自动回滚 |

## 三个不显然的设计决定

**1. 先落盘再回 200，推送失败不影响回 200。**
反过来做的话（推送成功才回 200），推送一失败 Apple 就不再重试，那条购买永久丢失。
落盘成功即视为我们已接管；Bark 随时可以补发。**只有落盘失败才回 500** —— 那是唯一
该让 Apple 重试的情况。

**2. 生产与沙盒是两个路径。**
`SignedDataVerifier` 会校验 payload 里的 environment 与自己构造时的是否一致，
混在一个路径上必然有一边报错。ASC 本来也是分开填两个 URL。

**3. 在线吊销检查（OCSP）默认关。**
它防的是"Apple 叶子证书被盗且已吊销"；代价是这台国内机器 OCSP 抖一下就会把**真实购买通知**
判成验签失败丢掉。对一条私人购买提醒来说，可用性风险远大于那个。离线链校验
（签名 + 有效期 + 链到 Apple 根）照做，那才是真正的防线。想开就把 `ASN_ONLINE_CHECKS=1`。

## 心跳：为什么必须有

**沉默是有歧义的**：没有购买通知 = 没人买，**或者** 端点挂了 —— 两者外观完全相同。
不解决这个，这套东西迟早会在你不知道的时候死掉。

Apple 自己给了解法：`TEST` 通知类型 + Request a Test Notification 接口。
每周一 10:00 主动请求一条，收到就推「✅ 管线正常」。**哪周没收到，就说明该去看了。**

心跳需要 **In-App Purchase API 密钥**（App Store Connect → 用户和访问 → 集成 → App 内购买项目），
这是**独立于** App Store Connect API 密钥的另一种密钥，填在 `ASN_IAP_KEY_*`。

## 部署

```bash
cp cn/asn/asn.env.example cn/asn/asn.env
openssl rand -hex 16              # 填进 ASN_PATH_TOKEN
# 填 ASN_BARK_KEY（Bark App 首页那串）
bash cn/asn/deploy-asn.sh
```

脚本跑完会打印两个 URL，填进 App Store Connect → App → App 信息 →
App Store Server Notifications，版本选 **Version 2**。

改了 `ASN_PATH_TOKEN` 就必须同步改 ASC 里的两个 URL，否则通知全部 404。

## 排查

```bash
ssh root@<server> 'journalctl -u mememo-asn -f'                    # 实时日志
ssh root@<server> 'tail -5 /var/lib/mememo-asn/notifications.jsonl' # 永久流水
ssh root@<server> 'ls /var/lib/mememo-asn/spool/'                   # 有文件=有提醒没推出去
ssh root@<server> 'cd /opt/mememo-asn && venv/bin/python asn.py heartbeat'  # 手动端到端验证
```

`notifications.jsonl` 是永久流水，只追加不改写；`spool/` 里是**还没推送成功**的，
推成功就删。所以 `spool/` 空 = 一切正常。
